<# Export task-local Word samples through installed WPS for visual acceptance.

Run with PowerShell on a Windows machine with WPS. Never modifies the DOCX.
#>
param(
    [string]$InputDirectory = 'docs/rpt02/samples',
    [string]$OutputDirectory = 'build/rpt02-wps'
)
$ErrorActionPreference = 'Stop'
$inputRoot = (Resolve-Path -LiteralPath $InputDirectory).Path
New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null
$outputRoot = (Resolve-Path -LiteralPath $OutputDirectory).Path
$app = New-Object -ComObject KWPS.Application
$initialCount = $app.Documents.Count
$originalVisible = $app.Visible
$originalAlerts = $app.DisplayAlerts
$results = @()
try {
    if ($initialCount -eq 0) { $app.Visible = $false }
    $app.DisplayAlerts = 0
    foreach ($file in Get-ChildItem -LiteralPath $inputRoot -Filter '*.docx') {
        $doc = $null
        try {
            $doc = $app.Documents.Open($file.FullName, $false, $true)
            $pdf = Join-Path $outputRoot ($file.BaseName + '.pdf')
            $doc.ExportAsFixedFormat($pdf, 17)
            $results += [pscustomobject]@{
                filename = $file.Name
                docx_sha256 = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLower()
                pages = $doc.ComputeStatistics(2)
                tables = $doc.Tables.Count
                wps_version = $app.Version
                pdf_filename = [IO.Path]::GetFileName($pdf)
            }
        } finally {
            if ($null -ne $doc) { $doc.Close(0) }
        }
    }
} finally {
    $app.DisplayAlerts = $originalAlerts
    $app.Visible = $originalVisible
    if ($initialCount -eq 0) { $app.Quit() }
}
$results | ConvertTo-Json -Depth 3 | Set-Content -Encoding utf8 (Join-Path $outputRoot 'wps-render-results.json')
$results | Format-Table
