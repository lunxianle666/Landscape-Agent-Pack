#Requires -Version 5.1
[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$PythonExe)
$ErrorActionPreference='Stop'
$env:PYTHONIOENCODING='utf-8'
if ($env:OS -ne 'Windows_NT') { throw 'Windows is required.' }
$raw = & $PythonExe -B (Join-Path $PSScriptRoot 'environment_probe.py')
if ($LASTEXITCODE -ne 0) { throw 'Environment discovery failed.' }
$data = $raw | ConvertFrom-Json
Write-Host ('Python: '+$data.python.version+'; host integrity: '+$data.host_integrity.level)
foreach ($pair in $data.autocad_host_integrity) { Write-Host ('AutoCAD PID '+$pair.pid+' compatible integrity: '+$pair.compatible) }
foreach ($entry in $data.compatibility_entries) { if ($entry.runasadmin) { Write-Warning ('RUNASADMIN found in '+$entry.hive+' view '+$entry.view+'. No registry changes made.') } }
Write-Host ('GetActiveObject: '+$data.com.status)
if ($data.com.status -ne 'PASS') { Write-Warning 'Open licensed AutoCAD at the same integrity level as your AI host. No application was started or stopped.' }
return $data
