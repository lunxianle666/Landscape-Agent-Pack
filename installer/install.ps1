#Requires -Version 5.1
[CmdletBinding()]
param([string]$InstallRoot=(Join-Path $env:LOCALAPPDATA 'Landscape-Agent-Pack'),[string]$SkillsDirectory,[string]$PythonExe,[string]$NodeExe,[string]$RingoDirectory,[switch]$UseExistingDependency,[switch]$RunGeometrySmoke,[switch]$RunSketchUpSmoke)
$ErrorActionPreference='Stop'
$env:PYTHONIOENCODING='utf-8'
$env:PYTHONDONTWRITEBYTECODE='1'
$package=Split-Path $PSScriptRoot -Parent
if ($env:OS -ne 'Windows_NT') { throw 'Windows is required.' }
if (-not $PythonExe) {
    foreach ($candidate in @('py.exe','python.exe')) {
        $cmd=Get-Command $candidate -ErrorAction SilentlyContinue
        if ($cmd) {
            if ($candidate -eq 'py.exe') { $found=& $cmd.Source -3.12 -c 'import sys;print(sys.executable)' 2>$null } else { $found=& $cmd.Source -c 'import sys;print(sys.executable)' 2>$null }
            if ($LASTEXITCODE -eq 0 -and $found -and $found -notmatch 'WindowsApps') { $PythonExe=$found.Trim();break }
        }
    }
}
if (-not $PythonExe) { throw 'Install Python 3.12 x64 from python.org, or pass -PythonExe.' }
& $PythonExe -B -c 'import sys;assert sys.version_info >= (3,11) and sys.maxsize > 2**32'
if ($LASTEXITCODE -ne 0) { throw 'Python 3.11+ x64 required; only 3.12.10 has historical verification.' }
$InstallRoot=[IO.Path]::GetFullPath($InstallRoot)
# Never stage into a client config directory or modify an existing package source.
if ($InstallRoot -eq [IO.Path]::GetFullPath($package)) { throw 'Choose a separate installation directory.' }
$runtimeCursor=$InstallRoot
while ($runtimeCursor) {
    if ((Test-Path -LiteralPath $runtimeCursor) -and ((Get-Item -LiteralPath $runtimeCursor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'Linked runtime paths are unsupported.' }
    $parent=Split-Path $runtimeCursor -Parent
    if ($parent -eq $runtimeCursor) { break };$runtimeCursor=$parent
}
New-Item -ItemType Directory -Path $InstallRoot -Force | Out-Null
if (-not $UseExistingDependency) {
    $venv=Join-Path $InstallRoot 'runtime'
    if ((Test-Path -LiteralPath $venv) -and -not (Test-Path -LiteralPath (Join-Path $venv 'pyvenv.cfg'))) { throw 'Existing non-venv runtime directory preserved.' }
    if (-not (Test-Path -LiteralPath (Join-Path $venv 'Scripts\python.exe'))) {
        & $PythonExe -m venv $venv
        if ($LASTEXITCODE -ne 0) { throw 'venv creation failed.' }
    }
    $PythonExe=Join-Path $venv 'Scripts\python.exe'
    & $PythonExe -m pip install -r (Join-Path $PSScriptRoot 'requirements.txt')
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
}
$scripts=& $PythonExe -B (Join-Path $PSScriptRoot 'verify-dependency.py')
if ($LASTEXITCODE -ne 0) { throw 'AutoCAD MCP Pro 1.5.1 with COM dependencies is required.' }
$mcp=Join-Path $scripts.Trim() 'autocad-mcp.exe'
if (-not (Test-Path -LiteralPath $mcp)) { throw 'MCP command not found in selected Python Scripts.' }
$data=& (Join-Path $PSScriptRoot 'check-environment.ps1') -PythonExe $PythonExe
if (-not $data.progid) { throw 'AutoCAD desktop COM registration not detected.' }
if (-not $NodeExe) { $NodeExe=$data.node }
if (-not $RingoDirectory) { $RingoDirectory=$data.ringo }
if ($NodeExe) {
    $v=& $NodeExe --version
    if ($LASTEXITCODE -ne 0 -or [int]($v.TrimStart('v').Split('.')[0]) -lt 22) { Write-Warning 'Node >=22 is required for Ringo.' }
} else { Write-Warning 'Node not detected. Follow docs/INSTALL_WINDOWS.md for SketchUp.' }
if (-not $data.ringo_extension_present) { Write-Warning 'Ringo SketchUp 2023 extension not detected.' }
if (-not $SkillsDirectory) { $SkillsDirectory=Join-Path $env:USERPROFILE '.agents\skills' }
$SkillsDirectory=[IO.Path]::GetFullPath($SkillsDirectory)
# Preflight every target before writing any Skill. Refuse links and conflicts.
$source=Join-Path $package 'skills\sketchup-from-cad-landscape'
$target=Join-Path $SkillsDirectory 'sketchup-from-cad-landscape'
$cursor=$target
while ($cursor) {
    if ((Test-Path -LiteralPath $cursor) -and ((Get-Item -LiteralPath $cursor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'Linked installation targets are unsupported.' }
    $parent=Split-Path $cursor -Parent
    if ($parent -eq $cursor) { break };$cursor=$parent
}
if (Test-Path -LiteralPath $target) { throw 'Existing Skill preserved. Select a separate -SkillsDirectory for this RC; automatic overwrite is disabled.' }
New-Item -ItemType Directory -Path $SkillsDirectory -Force | Out-Null
Copy-Item -LiteralPath $source -Destination $target -Recurse
Write-Warning 'autocad-dwg-redraw is withheld pending upstream licensing; not installed.'
$run=Join-Path $InstallRoot ('runs\'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'-'+[guid]::NewGuid().ToString('N').Substring(0,8))
$allowed=Join-Path $run 'smoke-drawings'
New-Item -ItemType Directory -Path $allowed -Force | Out-Null
& (Join-Path $PSScriptRoot 'generate-mcp-config.ps1') -McpExe $mcp -ProgID $data.progid -AllowedDirectory $allowed -OutputDirectory (Join-Path $run 'config')
$smokeArgs=@('-B',(Join-Path $package 'tests\smoke\smoke_test.py'),'--mcp-exe',$mcp,'--progid',$data.progid,'--output',$run)
if ($RunGeometrySmoke) { $smokeArgs += '--geometry' }
if ($RunSketchUpSmoke) {
    $smokeArgs += '--sketchup'
    if ($NodeExe -and $RingoDirectory) { $smokeArgs += @('--node',$NodeExe,'--ringo',$RingoDirectory) }
}
& $PythonExe @smokeArgs
$smokeExit=$LASTEXITCODE
Write-Host ('Local results: '+$run)
Write-Host 'AutoCAD results retain upstream raw errors and Guard postconditions. SketchUp is optional. No third-party redraw Skill was installed.'
if ($smokeExit -ne 0) { exit $smokeExit }
exit 0
