param(
    [string]$SourcePath = (Join-Path $env:TEMP 'ghg-standard-input-word-qa\complete-appendix-b.xlsx'),
    [string]$OutputRoot = (Join-Path $env:TEMP 'ghg-standard-input-word-qa')
)
$ErrorActionPreference = 'Stop'

function Get-Sha256([string]$Path) {
    (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}
function Test-UnderTemp([string]$Path, [string]$TempRoot) {
    $full = [IO.Path]::GetFullPath($Path)
    $prefix = [IO.Path]::GetFullPath($TempRoot).TrimEnd('\') + '\'
    $full.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)
}
function Get-WorkbookAudit($Workbook) {
    $names = @()
    $sheets = @()
    foreach ($sheet in $Workbook.Worksheets) {
        $names += [string]$sheet.Name
        $sheets += [pscustomobject]@{
            name = [string]$sheet.Name
            protect_contents = [bool]$sheet.ProtectContents
            protect_drawing_objects = [bool]$sheet.ProtectDrawingObjects
            protect_scenarios = [bool]$sheet.ProtectScenarios
        }
    }
    [pscustomobject]@{ sheet_names = $names; sheets = $sheets }
}

$tempRoot = [IO.Path]::GetFullPath($env:TEMP).TrimEnd('\')
$sourceFull = [IO.Path]::GetFullPath((Resolve-Path -LiteralPath $SourcePath).Path)
if (-not (Test-UnderTemp $sourceFull $tempRoot)) { throw "Source must be inside TEMP; refusing: $sourceFull" }
$outputRootFull = [IO.Path]::GetFullPath($OutputRoot)
if (-not (Test-UnderTemp $outputRootFull $tempRoot)) { throw "OutputRoot must be inside TEMP; refusing: $outputRootFull" }
$runId = (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [guid]::NewGuid().ToString('N').Substring(0,8)
$runDir = Join-Path $outputRootFull ("native-excel-roundtrip-repro-" + $runId)
New-Item -ItemType Directory -Path $runDir -Force | Out-Null
$beforePath = Join-Path $runDir 'complete-appendix-b-before.xlsx'
$savedPath = Join-Path $runDir 'complete-appendix-b-native-roundtrip.xlsx'
$evidencePath = Join-Path $runDir 'native-roundtrip-com-evidence.json'
$sourceHashBefore = Get-Sha256 $sourceFull
$preexistingPids = @(Get-Process -Name EXCEL,et,wps,kwps -ErrorAction SilentlyContinue | ForEach-Object { [int]$_.Id })

$progKey = 'Registry::HKEY_CLASSES_ROOT\Excel.Application\CLSID'
$clsid = [string](Get-ItemProperty -LiteralPath $progKey).'(default)'
$serverKey = 'Registry::HKEY_CLASSES_ROOT\CLSID\' + $clsid + '\LocalServer32'
$registeredServer = [string](Get-ItemProperty -LiteralPath $serverKey).'(default)'
$match = [regex]::Match($registeredServer, '(?i)^\s*"?(.+?\.exe)"?(?:\s|$)')
if (-not $match.Success) { throw "Cannot parse Excel.Application LocalServer32: $registeredServer" }
$registeredExe = [IO.Path]::GetFullPath((Resolve-Path -LiteralPath $match.Groups[1].Value).Path)
$registeredVersion = (Get-Item -LiteralPath $registeredExe).VersionInfo.FileVersion

if (-not ('NativeExcelRoundtrip.User32' -as [type])) {
    Add-Type -Namespace NativeExcelRoundtrip -Name User32 -MemberDefinition '[System.Runtime.InteropServices.DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(System.IntPtr hWnd, out uint processId);'
}
$app = $null
$workbook = $null
$appPid = $null
$appExe = $null
$appVersion = $null
$initialWorkbooks = $null
$ownsInstance = $false
$registeredMatches = $false
$gatePassed = $false
$failure = $null
$beforeAudit = $null
$afterAudit = $null
$beforeHash = $null
$savedHash = $null
$sourceHashAfter = $null
try {
    # CoCreateInstance, never GetActiveObject. Verify the activated PID before opening anything.
    $app = New-Object -ComObject Excel.Application
    [uint32]$pidValue = 0
    [void][NativeExcelRoundtrip.User32]::GetWindowThreadProcessId([IntPtr]$app.Hwnd, [ref]$pidValue)
    $appPid = [int]$pidValue
    $ownsInstance = ($preexistingPids -notcontains $appPid)
    $initialWorkbooks = [int]$app.Workbooks.Count
    $process = Get-Process -Id $appPid
    $appExe = [IO.Path]::GetFullPath($process.Path)
    $appVersion = [string]$app.Version
    $registeredMatches = ([IO.Path]::GetFullPath($appExe) -ieq [IO.Path]::GetFullPath($registeredExe))
    $gatePassed = ($ownsInstance -and $initialWorkbooks -eq 0 -and $registeredMatches)
    if (-not $gatePassed) {
        throw "Safe-instance gate failed before opening a workbook (newPID=$ownsInstance, initialWorkbooks=$initialWorkbooks, registeredPathMatches=$registeredMatches)."
    }

    $app.Visible = $false
    $app.DisplayAlerts = $false
    $app.AskToUpdateLinks = $false
    Copy-Item -LiteralPath $sourceFull -Destination $beforePath
    Copy-Item -LiteralPath $sourceFull -Destination $savedPath
    $beforeHash = Get-Sha256 $beforePath
    $workbook = $app.Workbooks.Open($savedPath, 0, $false)
    $beforeAudit = Get-WorkbookAudit $workbook
    $workbook.Save()
    $workbook.Close($false)
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($workbook)
    $workbook = $null

    $workbook = $app.Workbooks.Open($savedPath, 0, $true)
    $afterAudit = Get-WorkbookAudit $workbook
    $workbook.Close($false)
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($workbook)
    $workbook = $null
    $savedHash = Get-Sha256 $savedPath
    $sourceHashAfter = Get-Sha256 $sourceFull
} catch {
    $failure = $_.Exception.Message
    if (-not $sourceHashAfter -and (Test-Path -LiteralPath $sourceFull)) { $sourceHashAfter = Get-Sha256 $sourceFull }
} finally {
    if ($workbook) {
        try { $workbook.Close($false) } catch {}
        try { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($workbook) } catch {}
    }
    if ($app) {
        # Quit only the new, empty automation instance verified above.
        if ($ownsInstance -and $initialWorkbooks -eq 0) { try { $app.Quit() } catch {} }
        try { [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($app) } catch {}
    }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}

$engine = if ([IO.Path]::GetFileName($appExe) -ieq 'et.exe') { 'WPS Office ET COM' } elseif ([IO.Path]::GetFileName($appExe) -ieq 'excel.exe') { 'Microsoft Excel COM' } else { [IO.Path]::GetFileName($appExe) + ' COM' }
$checks = @(
    [pscustomobject]@{ name = 'registered_server_matches_activated_process'; passed = [bool]$registeredMatches; detail = $appExe },
    [pscustomobject]@{ name = 'independent_instance_started_with_zero_workbooks'; passed = [bool]($ownsInstance -and $initialWorkbooks -eq 0); detail = @{ pid = $appPid; initial_workbooks = $initialWorkbooks; pid_was_preexisting = [bool](-not $ownsInstance) } },
    [pscustomobject]@{ name = 'nine_sheet_names_preserved'; passed = [bool]($beforeAudit -and $afterAudit -and $beforeAudit.sheet_names.Count -eq 9 -and (Compare-Object $beforeAudit.sheet_names $afterAudit.sheet_names -SyncWindow 0).Count -eq 0); detail = @{ before = $beforeAudit.sheet_names; after = $afterAudit.sheet_names } },
    [pscustomobject]@{ name = 'sheet_protection_flags_preserved'; passed = [bool]($beforeAudit -and $afterAudit -and (ConvertTo-Json -InputObject $beforeAudit.sheets -Depth 8 -Compress) -ceq (ConvertTo-Json -InputObject $afterAudit.sheets -Depth 8 -Compress)); detail = @{ before = $beforeAudit.sheets; after = $afterAudit.sheets } },
    [pscustomobject]@{ name = 'source_workbook_unchanged'; passed = [bool]($sourceHashBefore -and $sourceHashBefore -ceq $sourceHashAfter); detail = @{ before = $sourceHashBefore; after = $sourceHashAfter } },
    [pscustomobject]@{ name = 'native_saved_copy_exists'; passed = [bool]($savedHash -and (Test-Path -LiteralPath $savedPath)); detail = @{ before_copy_sha256 = $beforeHash; saved_copy_sha256 = $savedHash } }
)
$failedChecks = @($checks | Where-Object { -not $_.passed })
$status = if ($failure -or $failedChecks.Count -gt 0) { 'FAIL' } else { 'PASS' }
$report = [pscustomobject]@{
    status = $status
    failure = $failure
    engine = $engine
    prog_id = 'Excel.Application'
    clsid = $clsid
    registered_server = $registeredServer
    registered_exe = $registeredExe
    registered_file_version = $registeredVersion
    activated_exe = $appExe
    activated_file_version = if ($appExe -and (Test-Path -LiteralPath $appExe)) { (Get-Item -LiteralPath $appExe).VersionInfo.FileVersion } else { $null }
    application_version = $appVersion
    process_id = $appPid
    pid_was_preexisting = [bool](-not $ownsInstance)
    initial_workbooks = $initialWorkbooks
    gate_passed_before_open = $gatePassed
    source_path = $sourceFull
    source_sha256_before = $sourceHashBefore
    source_sha256_after = $sourceHashAfter
    before_copy_path = $beforePath
    before_copy_sha256 = $beforeHash
    saved_copy_path = $savedPath
    saved_copy_sha256 = $savedHash
    saved_copy_changed = [bool]($beforeHash -and $savedHash -and $beforeHash -cne $savedHash)
    run_directory = $runDir
    before_audit = $beforeAudit
    after_audit = $afterAudit
    checks = $checks
}
$report | ConvertTo-Json -Depth 16 | Set-Content -LiteralPath $evidencePath -Encoding utf8
Write-Output ("RUN_DIR=" + $runDir)
Write-Output (Get-Content -Raw -LiteralPath $evidencePath)
if ($status -ne 'PASS') { exit 1 }
