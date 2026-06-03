param(
    [string]$Label = "manual snapshot"
)

$ErrorActionPreference = "Stop"

$toolsRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$logDir = Join-Path $toolsRoot "logs\system"
$logPath = Join-Path $logDir "system_snapshot.log"

New-Item -ItemType Directory -Force -Path $logDir | Out-Null

function Format-Bytes {
    param([double]$Bytes)

    if ($Bytes -ge 1TB) {
        return "{0:N2} TB" -f ($Bytes / 1TB)
    }

    if ($Bytes -ge 1GB) {
        return "{0:N2} GB" -f ($Bytes / 1GB)
    }

    if ($Bytes -ge 1MB) {
        return "{0:N2} MB" -f ($Bytes / 1MB)
    }

    return "{0:N0} B" -f $Bytes
}

function Get-GpuSnapshot {
    $nvidiaSmi = Get-Command nvidia-smi -ErrorAction SilentlyContinue

    if (-not $nvidiaSmi) {
        return @("GPU: unavailable (nvidia-smi not found)")
    }

    try {
        $gpuRows = & nvidia-smi `
            --query-gpu=name,utilization.gpu,memory.used,memory.total `
            --format=csv,noheader,nounits

        if (-not $gpuRows) {
            return @("GPU: unavailable (nvidia-smi returned no rows)")
        }

        $lines = @()

        foreach ($row in $gpuRows) {
            $parts = $row.Split(",") | ForEach-Object { $_.Trim() }

            if ($parts.Count -lt 4) {
                $lines += "GPU: unavailable (unexpected nvidia-smi row: $row)"
                continue
            }

            $name = $parts[0]
            $utilization = $parts[1]
            $memoryUsedMb = [double]$parts[2]
            $memoryTotalMb = [double]$parts[3]
            $memoryPercent = if ($memoryTotalMb -gt 0) {
                [Math]::Round(($memoryUsedMb / $memoryTotalMb) * 100, 1)
            } else {
                0
            }

            $lines += "GPU: $name, util=$utilization%, VRAM=$memoryUsedMb MB / $memoryTotalMb MB ($memoryPercent%)"
        }

        return $lines
    }
    catch {
        return @("GPU: unavailable ($($_.Exception.Message))")
    }
}

function Format-ProcessRows {
    param(
        [array]$Processes,
        [string]$Title
    )

    $lines = @($Title)

    if (-not $Processes -or $Processes.Count -eq 0) {
        $lines += "- none"
        return $lines
    }

    foreach ($process in $Processes) {
        $memory = Format-Bytes $process.WorkingSet64
        $cpu = if ($null -ne $process.CPU) { "{0:N2}s" -f $process.CPU } else { "n/a" }
        $lines += "- $($process.ProcessName) pid=$($process.Id) cpu=$cpu ram=$memory"
    }

    return $lines
}

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$processor = Get-CimInstance Win32_Processor | Select-Object -First 1
$os = Get-CimInstance Win32_OperatingSystem

$totalMemoryBytes = [double]$os.TotalVisibleMemorySize * 1KB
$freeMemoryBytes = [double]$os.FreePhysicalMemory * 1KB
$usedMemoryBytes = $totalMemoryBytes - $freeMemoryBytes
$usedMemoryPercent = if ($totalMemoryBytes -gt 0) {
    [Math]::Round(($usedMemoryBytes / $totalMemoryBytes) * 100, 1)
} else {
    0
}

$pythonProcesses = Get-Process -ErrorAction SilentlyContinue |
    Where-Object { $_.ProcessName -like "python*" } |
    Sort-Object WorkingSet64 -Descending |
    Select-Object -First 10

$dockerProcesses = Get-Process -ErrorAction SilentlyContinue |
    Where-Object {
        $_.ProcessName -like "*docker*" -or
        $_.ProcessName -like "*com.docker*" -or
        $_.ProcessName -like "*qdrant*"
    } |
    Sort-Object WorkingSet64 -Descending |
    Select-Object -First 10

$lines = @()
$lines += "============================================================"
$lines += "Timestamp: $timestamp"
$lines += "Label: $Label"
$lines += "CPU: $($processor.Name)"
$lines += "CPU Load: $($processor.LoadPercentage)%"
$lines += "RAM Used: $(Format-Bytes $usedMemoryBytes) / $(Format-Bytes $totalMemoryBytes) ($usedMemoryPercent%)"
$lines += Get-GpuSnapshot
$lines += Format-ProcessRows -Processes $pythonProcesses -Title "Python Processes:"
$lines += Format-ProcessRows -Processes $dockerProcesses -Title "Docker/Qdrant Processes:"
$lines += ""

$output = $lines -join [Environment]::NewLine

Write-Output $output
Add-Content -Path $logPath -Value $output -Encoding UTF8
