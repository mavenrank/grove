param([Parameter(Mandatory=$true)][string]$JobPath)
$ErrorActionPreference = 'Stop'
$job = Get-Content -LiteralPath $JobPath -Raw -Encoding UTF8 | ConvertFrom-Json
Add-Type -AssemblyName System.Runtime.WindowsRuntime
[Windows.Storage.StorageFile, Windows.Storage, ContentType=WindowsRuntime] | Out-Null
[Windows.Graphics.Imaging.BitmapDecoder, Windows.Foundation, ContentType=WindowsRuntime] | Out-Null
[Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType=WindowsRuntime] | Out-Null
[Windows.Globalization.Language, Windows.Globalization, ContentType=WindowsRuntime] | Out-Null
$asTask = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and $_.IsGenericMethod -and $_.GetParameters().Count -eq 1 -and
    $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'
} | Select-Object -First 1
function Await-WinRt($operation, [Type]$type) {
    $task = $asTask.MakeGenericMethod($type).Invoke($null, @($operation))
    $task.GetAwaiter().GetResult()
}
$engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage([Windows.Globalization.Language]::new($job.language))
if (-not $engine) { throw ('OCR language unavailable: ' + $job.language) }
$records = @()
foreach ($image in $job.images) {
    $stream = $null; $bitmap = $null
    try {
        $file = Await-WinRt ([Windows.Storage.StorageFile]::GetFileFromPathAsync($image.file)) ([Windows.Storage.StorageFile])
        $stream = Await-WinRt ($file.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
        $decoder = Await-WinRt ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
        $bitmap = Await-WinRt ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
        if ([Math]::Max($bitmap.PixelWidth, $bitmap.PixelHeight) -gt [Windows.Media.Ocr.OcrEngine]::MaxImageDimension) {
            throw 'Image exceeds OCR runtime dimensions'
        }
        $result = Await-WinRt ($engine.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult])
        $lines = @($result.Lines | ForEach-Object {
            @{text=$_.Text;words=@($_.Words | ForEach-Object {
                @{text=$_.Text;box=@{x=$_.BoundingRect.X;y=$_.BoundingRect.Y;width=$_.BoundingRect.Width;height=$_.BoundingRect.Height}}
            })}
        })
        $records += @{id=$image.id;status='candidate';text=$result.Text;lines=$lines;text_angle=$result.TextAngle}
    } catch {
        $records += @{id=$image.id;status='blocked';problem=$_.Exception.Message}
    } finally {
        if ($bitmap) { $bitmap.Dispose() }
        if ($stream) { $stream.Dispose() }
    }
}
@{adapter='windows-media-ocr';adapter_revision=1;language=$job.language;
  os_version=[Environment]::OSVersion.Version.ToString();max_dimension=[Windows.Media.Ocr.OcrEngine]::MaxImageDimension;
  confidence=$null;confidence_source='not exposed by Windows.Media.Ocr';results=$records} |
    ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $job.result -Encoding UTF8
