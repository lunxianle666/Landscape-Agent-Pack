#Requires -Version 5.1
[CmdletBinding()]
param([string]$InstallRoot=(Join-Path $env:LOCALAPPDATA 'Landscape-Agent-Pack'),[string]$SkillsDirectory,[string]$PythonExe,[string]$NodeExe,[string]$RingoDirectory,[switch]$UseExistingDependency,[switch]$RunGeometrySmoke,[switch]$RunSketchUpSmoke,[switch]$DiagnosticOnly,[switch]$RerunSmoke)
$ErrorActionPreference='Stop'
$env:PYTHONIOENCODING='utf-8'
$env:PYTHONDONTWRITEBYTECODE='1'
$package=Split-Path $PSScriptRoot -Parent
if ($env:OS -ne 'Windows_NT') { throw 'Windows is required.' }
# --- Phase 3: result collector + summary printer ---
$Results = New-Object System.Collections.Generic.List[object]
function Add-Result([string]$Item,[string]$Status,[string]$Detail){ $Results.Add([pscustomobject]@{Item=$Item;Status=$Status;Detail=$Detail}) }
function Show-Summary {
  Write-Host ''
  Write-Host '========================================'
  Write-Host 'Landscape Agent Pack Setup Summary'
  Write-Host '========================================'
  foreach($x in $Results){
    $c = if($x.Status -eq 'PASS'){'Green'} elseif($x.Status -eq 'WARN'){'Yellow'} else {'Red'}
    Write-Host ('{0,-22} {1,-5} {2}' -f $x.Item,$x.Status,$x.Detail) -ForegroundColor $c
  }
  $fail=@($Results|Where-Object{$_.Status -eq 'FAIL'}).Count
  $warn=@($Results|Where-Object{$_.Status -eq 'WARN'}).Count
  $overall = if($fail -gt 0){'FAIL'} elseif($warn -gt 0){'WARN'} else {'PASS'}
  Write-Host '----------------------------------------'
  Write-Host ("Overall: {0}  (FAIL={1} WARN={2})" -f $overall,$fail,$warn)
  if($run){ Write-Host ("Runs/logs: " + $run) }
  Write-Host ("Rule entry: " + (Join-Path $InstallRoot 'pack-rules\AGENT_CONTEXT.md'))
  Write-Host 'Next: open your MCP-capable Agent and load AGENT_CONTEXT.md.'
  Write-Host '========================================'
}
if (-not $PythonExe) {
    foreach ($candidate in @('py.exe','python.exe')) {
        $cmd=Get-Command $candidate -ErrorAction SilentlyContinue
        if ($cmd) {
            if ($candidate -eq 'py.exe') { $found=& $cmd.Source -3.12 -c 'import sys;print(sys.executable)' 2>$null } else { $found=& $cmd.Source -c 'import sys;print(sys.executable)' 2>$null }
            if ($LASTEXITCODE -eq 0 -and $found -and $found -notmatch 'WindowsApps') { $PythonExe=$found.Trim();break }
        }
    }
}
if (-not $PythonExe) {
    Add-Result 'Python' 'FAIL' '未找到 Python 3.11+ x64（推荐 3.12）。从 https://www.python.org/downloads/ 安装，或用 -PythonExe 指定。'
    Show-Summary; exit 1
}
& $PythonExe -B -c 'import sys;assert sys.version_info >= (3,11) and sys.maxsize > 2**32'
if ($LASTEXITCODE -ne 0) {
    Add-Result 'Python' 'FAIL' "版本不满足 3.11+ x64：$PythonExe （推荐 3.12）"
    Show-Summary; exit 1
}
$pyVer = & $PythonExe -c 'import sys; print(sys.version_info[0], sys.version_info[1], sys.version_info[2])'
Add-Result 'Python' 'PASS' (($pyVer -split '\s+' | Where-Object {$_}) -join '.')
$InstallRoot=[IO.Path]::GetFullPath($InstallRoot)
# Never stage into a client config directory or modify an existing package source.
if ($InstallRoot -eq [IO.Path]::GetFullPath($package)) { throw 'Choose a separate installation directory.' }
$runtimeCursor=$InstallRoot
while ($runtimeCursor) {
    if ((Test-Path -LiteralPath $runtimeCursor) -and ((Get-Item -LiteralPath $runtimeCursor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'Linked runtime paths are unsupported.' }
    $parent=Split-Path $runtimeCursor -Parent
    if ($parent -eq $runtimeCursor) { break };$runtimeCursor=$parent
}
# --- Phase 3: DiagnosticOnly (read-only) ---
if ($DiagnosticOnly) {
  Add-Result 'Mode' 'PASS' 'DiagnosticOnly (read-only; no install)'
  try { $scripts=& $PythonExe -B (Join-Path $PSScriptRoot 'verify-dependency.py'); $mcp=Join-Path $scripts.Trim() 'autocad-mcp.exe'; Add-Result 'AutoCAD MCP Pro' 'PASS' $mcp }
  catch { Add-Result 'AutoCAD MCP Pro' 'WARN' '当前 Python 未安装 autocad-mcp-pro（新机器预期）' }
  $data=& (Join-Path $PSScriptRoot 'check-environment.ps1') -PythonExe $PythonExe
  if ($data.progid) { Add-Result 'AutoCAD ProgID' 'PASS' $data.progid } else { Add-Result 'AutoCAD ProgID' 'FAIL' '未检测到 AutoCAD COM 注册' }
  if ($data.com.status -eq 'PASS') { Add-Result 'AutoCAD COM' 'PASS' 'connected' } else { Add-Result 'AutoCAD COM' 'WARN' '打开 AutoCAD 后即可连接（未自动启动）' }
  $pr=Join-Path $InstallRoot 'pack-rules\AGENT_CONTEXT.md'
  if (Test-Path $pr) { Add-Result 'pack-rules' 'PASS' $pr } else { Add-Result 'pack-rules' 'WARN' '尚未安装（pack-rules 不存在）' }
  if ($data.node) { Add-Result 'Node (optional)' 'PASS' $data.node } else { Add-Result 'Node (optional)' 'WARN' '仅影响 SketchUp，不影响 AutoCAD 主链' }
  if ($data.ringo_extension_present) { Add-Result 'Ringo (optional)' 'PASS' '' } else { Add-Result 'Ringo (optional)' 'WARN' '仅影响 SketchUp，不影响 AutoCAD 主链' }
  Add-Result 'SketchUp (optional)' $(if($data.sketchup_paths -and $data.sketchup_paths.Count -gt 0){'PASS'}else{'WARN'}) '未配置不阻塞 AutoCAD 主链'
  if (Test-Path $pr) { & $PythonExe -B (Join-Path $PSScriptRoot 'verify-rules.py') --root (Join-Path $InstallRoot 'pack-rules') --packed 2>&1 | ForEach-Object { Write-Host $_ } }
  $run=$null
  $diagFail=@($Results|Where-Object{$_.Status -eq 'FAIL'}).Count
  Show-Summary; if($diagFail -gt 0){exit 1} else {exit 0}
}
New-Item -ItemType Directory -Path $InstallRoot -Force | Out-Null
# --- Phase 3: RerunSmoke (use existing runtime; never reinstall) ---
if ($RerunSmoke) {
  $venvPy=Join-Path $InstallRoot 'runtime\Scripts\python.exe'
  if (-not (Test-Path $venvPy)) { Add-Result 'RerunSmoke' 'FAIL' "runtime not installed: $InstallRoot\runtime （不自动重装，请先正常安装）"; Show-Summary; exit 1 }
  $PythonExe=$venvPy
  Add-Result 'Mode' 'PASS' 'RerunSmoke (using existing runtime)'
  try { $scripts=& $PythonExe -B (Join-Path $PSScriptRoot 'verify-dependency.py'); $mcp=Join-Path $scripts.Trim() 'autocad-mcp.exe'; Add-Result 'AutoCAD MCP Pro' 'PASS' $mcp }
  catch { Add-Result 'AutoCAD MCP Pro' 'FAIL' '已安装 runtime 中缺少 autocad-mcp-pro'; Show-Summary; exit 1 }
  $data=& (Join-Path $PSScriptRoot 'check-environment.ps1') -PythonExe $PythonExe
  if (-not $data.progid) { Add-Result 'AutoCAD ProgID' 'FAIL' '未检测到 AutoCAD COM'; Show-Summary; exit 1 }
  Add-Result 'AutoCAD ProgID' 'PASS' $data.progid
  if ($data.com.status -eq 'PASS') { Add-Result 'AutoCAD COM' 'PASS' 'connected' } else { Add-Result 'AutoCAD COM' 'WARN' '打开 AutoCAD 后重连' }
  $run=Join-Path $InstallRoot ('runs\smoke-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
  New-Item -ItemType Directory -Path (Join-Path $run 'smoke-drawings') -Force | Out-Null
  $smokeArgs=@('-B',(Join-Path $package 'tests\smoke\smoke_test.py'),'--mcp-exe',$mcp,'--progid',$data.progid,'--output',$run)
  if ($RunGeometrySmoke) { $smokeArgs += '--geometry' }
  & $PythonExe @smokeArgs; $smokeExit=$LASTEXITCODE
  Add-Result 'AutoCAD Smoke Test' $(if($smokeExit -eq 0){'PASS'}else{'FAIL'}) "exit=$smokeExit"
  Add-Result 'SketchUp (optional)' 'WARN' 'not run in RerunSmoke'
  Show-Summary; exit $smokeExit
}
# --- Phase 3: existing-install notice (non-interactive; just prints options) ---
if ((Test-Path -LiteralPath (Join-Path $InstallRoot 'runtime\Scripts\python.exe')) -and -not $UseExistingDependency) {
  Write-Host 'Existing installation detected at' $InstallRoot
  Write-Host '  Diagnostic: powershell -File installer\install.ps1 -DiagnosticOnly'
  Write-Host '  RerunSmoke: powershell -File installer\install.ps1 -RerunSmoke'
  Write-Host '  (Continuing normal install in 3s; Ctrl+C to abort...)'
  Start-Sleep -Seconds 3
}
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
Add-Result 'AutoCAD MCP Pro' 'PASS' '1.5.1 (com)'
$data=& (Join-Path $PSScriptRoot 'check-environment.ps1') -PythonExe $PythonExe
if (-not $data.progid) { throw 'AutoCAD desktop COM registration not detected.' }
Add-Result 'AutoCAD ProgID' 'PASS' $data.progid
if ($data.com.status -eq 'PASS') { Add-Result 'AutoCAD COM' 'PASS' 'connected' } else { Add-Result 'AutoCAD COM' 'WARN' '打开 AutoCAD 后连接' }
if (-not $NodeExe) { $NodeExe=$data.node }
if (-not $RingoDirectory) { $RingoDirectory=$data.ringo }
if ($NodeExe) {
    $v=& $NodeExe --version
    if ($LASTEXITCODE -ne 0 -or [int]($v.TrimStart('v').Split('.')[0]) -lt 22) { Add-Result 'Node (optional)' 'WARN' 'Node <22；仅影响 SketchUp' } else { Add-Result 'Node (optional)' 'PASS' $v }
} else { Add-Result 'Node (optional)' 'WARN' '未检测到；仅影响 SketchUp，不影响 AutoCAD 主链' }
if ($data.ringo_extension_present) { Add-Result 'Ringo (optional)' 'PASS' '已安装' } else { Add-Result 'Ringo (optional)' 'WARN' '未配置；仅影响 SketchUp' }
Add-Result 'SketchUp (optional)' $(if($data.sketchup_paths -and $data.sketchup_paths.Count -gt 0){'PASS'}else{'WARN'}) '未配置不阻塞 AutoCAD 主链'
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
# --- Copy runtime rule set to <InstallRoot>\pack-rules (Phase 2, minimal increment) ---
$packRules=Join-Path $InstallRoot 'pack-rules'
New-Item -ItemType Directory -Path $packRules -Force | Out-Null
$ruleFiles=@('AGENT_CONTEXT.md','standards\autocad-safety-rules.md','standards\landscape-workflow.md','guards\README.md','docs\LIMITATIONS.md','docs\THREE_STEP_CHECK_CN.md')
$manifestFiles=@()
foreach ($rel in $ruleFiles) {
  $src=Join-Path $package $rel; $dst=Join-Path $packRules $rel
  New-Item -ItemType Directory -Path (Split-Path $dst) -Force | Out-Null
  Copy-Item -LiteralPath $src -Destination $dst -Force
  $manifestFiles += [pscustomobject]@{ relative_path=$rel; sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $dst).Hash }
}
[ordered]@{ pack_version='v0.1.0-rc2'; rule_entry='AGENT_CONTEXT.md'; mode_default='autocad'; files=$manifestFiles } | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $packRules 'manifest.json') -Encoding UTF8
Add-Result 'Landscape Rules' 'PASS' "$($ruleFiles.Count) files -> pack-rules"
$vr=& $PythonExe -B (Join-Path $PSScriptRoot 'verify-rules.py') --root $packRules --packed 2>&1
$vr | ForEach-Object { Write-Host $_ }
$vrCode=$LASTEXITCODE
Add-Result 'Rule Verification' $(if($vrCode -eq 0){'PASS'}else{'FAIL'}) ''
$run=Join-Path $InstallRoot ('runs\'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'-'+[guid]::NewGuid().ToString('N').Substring(0,8))
$allowed=Join-Path $run 'smoke-drawings'
New-Item -ItemType Directory -Path $allowed -Force | Out-Null
& (Join-Path $PSScriptRoot 'generate-mcp-config.ps1') -McpExe $mcp -ProgID $data.progid -AllowedDirectory $allowed -OutputDirectory (Join-Path $run 'config')
Add-Result 'MCP Config' 'PASS' "片段已生成：$run\config （需人工合并）"
$smokeArgs=@('-B',(Join-Path $package 'tests\smoke\smoke_test.py'),'--mcp-exe',$mcp,'--progid',$data.progid,'--output',$run)
if ($RunGeometrySmoke) { $smokeArgs += '--geometry' }
if ($RunSketchUpSmoke) {
    $smokeArgs += '--sketchup'
    if ($NodeExe -and $RingoDirectory) { $smokeArgs += @('--node',$NodeExe,'--ringo',$RingoDirectory) }
}
& $PythonExe @smokeArgs
$smokeExit=$LASTEXITCODE
Add-Result 'AutoCAD Smoke Test' $(if($smokeExit -eq 0){'PASS'}else{'FAIL'}) "exit=$smokeExit  (结果: $run)"
Write-Host ('Local results: '+$run)
Write-Host 'AutoCAD results retain upstream raw errors and Guard postconditions. SketchUp is optional. No third-party redraw Skill was installed.'
Show-Summary
if ($smokeExit -ne 0) { exit $smokeExit }
exit 0
