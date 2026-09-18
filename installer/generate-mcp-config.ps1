#Requires -Version 5.1
[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$McpExe,[Parameter(Mandatory=$true)][string]$ProgID,[Parameter(Mandatory=$true)][string]$AllowedDirectory,[Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference='Stop'
New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
foreach ($name in @('codex-autocad.toml','trae-autocad.json')) { if (Test-Path -LiteralPath (Join-Path $OutputDirectory $name)) { throw 'Refusing to overwrite generated configuration.' } }
# JSON basic string escaping is valid for these TOML basic strings too.
$command=ConvertTo-Json $McpExe -Compress
$cad=ConvertTo-Json $ProgID -Compress
$allowed=ConvertTo-Json $AllowedDirectory -Compress
$text=@"
[mcp_servers.autocad]
command = $command
startup_timeout_sec = 60
tool_timeout_sec = 90
[mcp_servers.autocad.env]
AUTOCAD_MCP_BACKEND = "com"
CAD_PROGID = $cad
DISCOVERY_MODE = "search"
ALLOWED_PATHS = $allowed
"@
$utf8=New-Object System.Text.UTF8Encoding($false)
[IO.File]::WriteAllText((Join-Path $OutputDirectory 'codex-autocad.toml'),$text,$utf8)
$entry=@{mcpServers=@{autocad=@{command=$McpExe;env=@{AUTOCAD_MCP_BACKEND='com';CAD_PROGID=$ProgID;DISCOVERY_MODE='search';ALLOWED_PATHS=$AllowedDirectory}}}}
[IO.File]::WriteAllText((Join-Path $OutputDirectory 'trae-autocad.json'),($entry | ConvertTo-Json -Depth 8),$utf8)
Write-Host 'Generated fragments only. Import/merge the autocad service after review; existing client configuration was not written.'
