param(
    [Parameter(Mandatory = $true)]
    [Guid]$ExecutionEndpointId,

    [Parameter(Mandatory = $true)]
    [string]$Password
)

$ErrorActionPreference = "Stop"
$composeFile = Join-Path $PSScriptRoot "..\docker-compose.yml"
$username = $ExecutionEndpointId.ToString("D")

docker compose -f $composeFile --profile mqtt exec -T mosquitto `
    mosquitto_passwd -b /mosquitto/data/password_file $username $Password
if ($LASTEXITCODE -ne 0) {
    throw "Failed to provision MQTT credentials for execution endpoint $username."
}

docker compose -f $composeFile --profile mqtt kill -s HUP mosquitto
if ($LASTEXITCODE -ne 0) {
    throw "Credential was written, but Mosquitto failed to reload its password file."
}

Write-Host "Provisioned endpoint-scoped MQTT subscription for $username."
