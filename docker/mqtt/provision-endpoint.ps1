param(
    [Parameter(Mandatory = $true)]
    [Guid]$ExecutionEndpointId,

    [Parameter(Mandatory = $true)]
    [string]$BearerToken,

    [string]$BackendBaseUrl = "https://localhost:5001"
)

$ErrorActionPreference = "Stop"
$uri = "$($BackendBaseUrl.TrimEnd('/'))/api/v1/management/execution-endpoints/$ExecutionEndpointId/mqtt-credential"
$result = Invoke-RestMethod -Method Post -Uri $uri -Headers @{ Authorization = "Bearer $BearerToken" }
$result.data | ConvertTo-Json -Depth 5
Write-Warning "The MQTT password is returned once. Store it directly in the endpoint secret store."
