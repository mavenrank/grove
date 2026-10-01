param([Parameter(Mandatory=$true)][string]$JobPath)
$ErrorActionPreference = 'Stop'
$job = Get-Content -LiteralPath $JobPath -Raw -Encoding UTF8 | ConvertFrom-Json
# PowerPoint can share a process with user presentations; do not alter that session.
if (@(Get-Process POWERPNT -ErrorAction SilentlyContinue).Count -gt 0) {
    throw 'PowerPoint is already running; native batch rendering requires an idle application'
}
$app = $null; $presentation = $null
try {
    $app = New-Object -ComObject PowerPoint.Application
    $app.AutomationSecurity = 3 # msoAutomationSecurityForceDisable
    $app.DisplayAlerts = 1     # ppAlertsNone; security is set independently
    $presentation = $app.Presentations.Open($job.source, -1, -1, 0) # read-only copy, no window
    $height = [int][Math]::Round($job.width * $presentation.PageSetup.SlideHeight / $presentation.PageSetup.SlideWidth)
    if ($height -lt 1 -or $height -gt 4096) { throw 'Unsupported slide aspect ratio' }
    $slides = @()
    foreach ($number in $job.slides) {
        $target = Join-Path $job.output ('slide-' + $number + '.png')
        $slide = $presentation.Slides.Item([int]$number)
        try { $slide.Export($target, 'PNG', [int]$job.width, $height) }
        finally { [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($slide) }
        $slides += @{slide_number=[int]$number;file=('slide-' + $number + '.png')}
    }
    @{adapter='powerpoint-com';adapter_revision=1;office_version=$app.Version;
      os_version=[Environment]::OSVersion.Version.ToString();slide_count=$presentation.Slides.Count;
      width=[int]$job.width;height=$height;slides=$slides} | ConvertTo-Json -Depth 5 |
        Set-Content -LiteralPath (Join-Path $job.output 'renderer.json') -Encoding UTF8
} finally {
    if ($presentation) { $presentation.Close(); [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($presentation) }
    if ($app) {
        if ($app.Presentations.Count -eq 0) { $app.Quit() }
        [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($app)
    }
}
