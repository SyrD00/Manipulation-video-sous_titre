#requires -Version 7.0

$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# ============================================================
# CONFIGURATION
# ============================================================

$FFmpeg = "C:\ffmpeg\bin\ffmpeg.exe"
$FFprobe = "C:\ffmpeg\bin\ffprobe.exe"

if (-not (Test-Path -LiteralPath $FFmpeg)) {
    $cmd = Get-Command ffmpeg -ErrorAction SilentlyContinue
    if ($null -ne $cmd) {
        $FFmpeg = $cmd.Source
    }
}

if (-not (Test-Path -LiteralPath $FFprobe)) {
    $cmd = Get-Command ffprobe -ErrorAction SilentlyContinue
    if ($null -ne $cmd) {
        $FFprobe = $cmd.Source
    }
}

if (-not (Test-Path -LiteralPath $FFmpeg)) {
    throw "FFmpeg introuvable."
}

if (-not (Test-Path -LiteralPath $FFprobe)) {
    throw "FFprobe introuvable."
}

$QsvEncoder = "h264_qsv"
$QsvPreset = "fast"
$QsvQuality = "20"

# ============================================================
# EXECUTION PROCESSUS NATIF
# ============================================================

function Invoke-Native {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Executable,

        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    $psi = [System.Diagnostics.ProcessStartInfo]::new()
    $psi.FileName = $Executable
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true

    foreach ($argument in $Arguments) {
        [void]$psi.ArgumentList.Add([string]$argument)
    }

    $process = [System.Diagnostics.Process]::new()
    $process.StartInfo = $psi

    [void]$process.Start()

    $stdoutTask = $process.StandardOutput.ReadToEndAsync()
    $stderrTask = $process.StandardError.ReadToEndAsync()

    $process.WaitForExit()

    return [PSCustomObject]@{
        ExitCode = $process.ExitCode
        StdOut   = $stdoutTask.Result
        StdErr   = $stderrTask.Result
    }
}

# ============================================================
# FENETRE DE PROGRESSION
# ============================================================

function New-ProgressWindow {

    $form = [System.Windows.Forms.Form]::new()
    $form.Text = "Fusion Video Intelligente"
    $form.StartPosition = "CenterScreen"
    $form.Width = 720
    $form.Height = 180
    $form.FormBorderStyle = "FixedDialog"
    $form.MaximizeBox = $false
    $form.MinimizeBox = $true

    $stage = [System.Windows.Forms.Label]::new()
    $stage.Left = 18
    $stage.Top = 12
    $stage.Width = 670
    $stage.Height = 24
    $stage.Font = [System.Drawing.Font]::new(
        "Segoe UI",
        10,
        [System.Drawing.FontStyle]::Bold
    )

    $detail = [System.Windows.Forms.Label]::new()
    $detail.Left = 18
    $detail.Top = 40
    $detail.Width = 670
    $detail.Height = 22

    $bar = [System.Windows.Forms.ProgressBar]::new()
    $bar.Left = 18
    $bar.Top = 68
    $bar.Width = 670
    $bar.Height = 28
    $bar.Minimum = 0
    $bar.Maximum = 1000

    $status = [System.Windows.Forms.Label]::new()
    $status.Left = 18
    $status.Top = 104
    $status.Width = 670
    $status.Height = 36

    [void]$form.Controls.Add($stage)
    [void]$form.Controls.Add($detail)
    [void]$form.Controls.Add($bar)
    [void]$form.Controls.Add($status)

    $form.Show()
    [System.Windows.Forms.Application]::DoEvents()

    return [PSCustomObject]@{
        Form = $form
        Stage = $stage
        Detail = $detail
        Bar = $bar
        Status = $status
    }
}

function Update-ProgressWindow {
    param(
        [Parameter(Mandatory = $false)]
        $Ui,

        [double]$Percent = 0,

        [string]$Stage = "",

        [string]$Detail = "",

        [string]$Status = ""
    )

    if ($null -eq $Ui) {
        return
    }

    $safePercent = [Math]::Max(0, [Math]::Min(100, $Percent))
    $Ui.Stage.Text = $Stage
    $Ui.Detail.Text = $Detail
    $Ui.Status.Text = $Status
    $Ui.Bar.Value = [int]($safePercent * 10)

    [System.Windows.Forms.Application]::DoEvents()
}

function Close-ProgressWindow {
    param($Ui)

    if ($null -ne $Ui) {
        try {
            $Ui.Form.Close()
            $Ui.Form.Dispose()
        }
        catch {
        }
    }
}

# ============================================================
# OUTILS
# ============================================================

function Format-Duration {
    param([double]$Seconds)

    $secondsSafe = [Math]::Max(0, $Seconds)
    $timeSpan = [TimeSpan]::FromSeconds($secondsSafe)

    return $timeSpan.ToString("hh\:mm\:ss")
}

function Parse-Rational {
    param([AllowNull()][string]$Value)

    if ([string]::IsNullOrWhiteSpace($Value)) {
        return $null
    }

    if ($Value -match "^(-?\d+(?:\.\d+)?)/(-?\d+(?:\.\d+)?)$") {
        $numerator = [double]::Parse(
            $Matches[1],
            [Globalization.CultureInfo]::InvariantCulture
        )

        $denominator = [double]::Parse(
            $Matches[2],
            [Globalization.CultureInfo]::InvariantCulture
        )

        if ($denominator -eq 0) {
            return $null
        }

        return ($numerator / $denominator)
    }

    $number = 0.0

    if (
        [double]::TryParse(
            $Value,
            [Globalization.NumberStyles]::Float,
            [Globalization.CultureInfo]::InvariantCulture,
            [ref]$number
        )
    ) {
        return $number
    }

    return $null
}

function Get-PrimaryVideoStreams {
    param($Probe)

    return @(
        $Probe.streams |
        Where-Object {
            $_.codec_type -eq "video" -and
            (
                $null -eq $_.disposition -or
                $_.disposition.attached_pic -ne 1
            )
        }
    )
}

function Get-AudioStreams {
    param($Probe)

    return @(
        $Probe.streams |
        Where-Object {
            $_.codec_type -eq "audio"
        }
    )
}

# ============================================================
# FFPROBE
# ============================================================

function Get-VideoInfo {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    $arguments = @(
        "-v", "error",
        "-print_format", "json",
        "-show_streams",
        "-show_format",
        "-i", $Path
    )

    $result = Invoke-Native -Executable $FFprobe -Arguments $arguments

    if ($result.ExitCode -ne 0) {
        throw "FFprobe a echoue pour : $Path`n$($result.StdErr)"
    }

    if ([string]::IsNullOrWhiteSpace($result.StdOut)) {
        throw "FFprobe n a retourne aucune donnee pour : $Path"
    }

    try {
        $probe = $result.StdOut | ConvertFrom-Json
    }
    catch {
        throw "JSON FFprobe invalide pour : $Path"
    }

    $primaryVideos = @(Get-PrimaryVideoStreams -Probe $probe)
    $allVideos = @(
        $probe.streams |
        Where-Object { $_.codec_type -eq "video" }
    )

    $audios = @(Get-AudioStreams -Probe $probe)

    $subtitles = @(
        $probe.streams |
        Where-Object { $_.codec_type -eq "subtitle" }
    )

    $dataStreams = @(
        $probe.streams |
        Where-Object { $_.codec_type -eq "data" }
    )

    if ($primaryVideos.Count -lt 1) {
        throw "Aucun flux video principal trouve dans : $Path"
    }

    $duration = 0.0

    if ($null -ne $probe.format.duration) {
        [void][double]::TryParse(
            [string]$probe.format.duration,
            [Globalization.NumberStyles]::Float,
            [Globalization.CultureInfo]::InvariantCulture,
            [ref]$duration
        )
    }

    return [PSCustomObject]@{
        Path            = $Path
        Name            = [System.IO.Path]::GetFileName($Path)
        Probe           = $probe
        Video           = $primaryVideos[0]
        VideoCount      = $primaryVideos.Count
        TotalVideoCount = $allVideos.Count
        Audio           = if ($audios.Count -gt 0) { $audios[0] } else { $null }
        AudioCount      = $audios.Count
        SubtitleCount   = $subtitles.Count
        DataCount       = $dataStreams.Count
        Duration        = $duration
        Fps             = Parse-Rational ([string]$primaryVideos[0].r_frame_rate)
    }
}

# ============================================================
# SIGNATURES COMPATIBILITE
# ============================================================

function Get-CodecSignature {
    param($Info)

    $v = $Info.Video
    $a = $Info.Audio

    $audioCodec = ""
    $audioSampleRate = ""
    $audioChannels = ""
    $audioLayout = ""
    $audioSampleFormat = ""
    $audioCodecTag = ""

    if ($null -ne $a) {
        $audioCodec = [string]$a.codec_name
        $audioSampleRate = [string]$a.sample_rate
        $audioChannels = [string]$a.channels
        $audioLayout = [string]$a.channel_layout
        $audioSampleFormat = [string]$a.sample_fmt
        $audioCodecTag = [string]$a.codec_tag_string
    }

    return [string]::Join("|", @(
        [string]$v.codec_name,
        [string]$v.profile,
        [string]$v.level,
        [string]$v.width,
        [string]$v.height,
        [string]$v.pix_fmt,
        [string]$v.field_order,
        [string]$v.sample_aspect_ratio,
        [string]$v.color_range,
        [string]$v.color_space,
        [string]$v.color_transfer,
        [string]$v.color_primaries,
        [string]$v.codec_tag_string,
        [string]$v.r_frame_rate,
        $audioCodec,
        $audioSampleRate,
        $audioChannels,
        $audioLayout,
        $audioSampleFormat,
        $audioCodecTag
    ))
}

function Test-LosslessCandidate {
    param(
        [Parameter(Mandatory = $true)]
        [System.Collections.Generic.List[object]]$Infos
    )

    $baseSignature = Get-CodecSignature -Info $Infos[0]

    foreach ($info in $Infos) {

        if ($info.VideoCount -ne 1) {
            return $false
        }

        if ($info.AudioCount -gt 1) {
            return $false
        }

        if ($info.SubtitleCount -ne 0) {
            return $false
        }

        if ($info.DataCount -ne 0) {
            return $false
        }

        if ((Get-CodecSignature -Info $info) -ne $baseSignature) {
            return $false
        }
    }

    return $true
}

function Test-NeedsCleanRemux {
    param($Info)

    return (
        $Info.TotalVideoCount -ne 1 -or
        $Info.AudioCount -gt 1
    )
}

# ============================================================
# CONCAT LIST
# ============================================================

function Escape-ConcatPath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    $normalized = $Path.Replace("\", "/")
    $normalized = $normalized.Replace("'", "'\''")

    return "file '$normalized'"
}

function Write-ConcatList {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Paths,

        [Parameter(Mandatory = $true)]
        [string]$ListPath
    )

    $lines = New-Object System.Collections.Generic.List[string]

    foreach ($path in $Paths) {
        [void]$lines.Add((Escape-ConcatPath -Path $path))
    }

    [System.IO.File]::WriteAllLines(
        $ListPath,
        $lines,
        [System.Text.UTF8Encoding]::new($false)
    )
}

# ============================================================
# FFMPEG AVEC PROGRESSION
# ============================================================

function Invoke-FFmpegProgress {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments,

        [Parameter(Mandatory = $true)]
        [double]$TotalSeconds,

        [Parameter(Mandatory = $true)]
        $Ui,

        [Parameter(Mandatory = $true)]
        [string]$Stage,

        [Parameter(Mandatory = $true)]
        [string]$Detail
    )

    $psi = [System.Diagnostics.ProcessStartInfo]::new()
    $psi.FileName = $FFmpeg
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true

    $globalArguments = @(
        "-hide_banner",
        "-loglevel", "error",
        "-nostdin",
        "-progress", "pipe:1",
        "-stats_period", "0.25"
    )

    foreach ($argument in $globalArguments) {
        [void]$psi.ArgumentList.Add($argument)
    }

    foreach ($argument in $Arguments) {
        [void]$psi.ArgumentList.Add([string]$argument)
    }

    $process = [System.Diagnostics.Process]::new()
    $process.StartInfo = $psi

    [void]$process.Start()

    $stderrTask = $process.StandardError.ReadToEndAsync()

    $currentSeconds = 0.0
    $speed = ""

    Update-ProgressWindow `
        -Ui $Ui `
        -Percent 0 `
        -Stage $Stage `
        -Detail $Detail `
        -Status "FFmpeg demarre..."

    while ($true) {

        $line = $process.StandardOutput.ReadLine()

        if ($null -eq $line) {
            break
        }

        if ($line.StartsWith("out_time=")) {

            $timeText = $line.Substring(9)
            $timeSpan = [TimeSpan]::Zero

            if (
                [TimeSpan]::TryParse(
                    $timeText,
                    [Globalization.CultureInfo]::InvariantCulture,
                    [ref]$timeSpan
                )
            ) {
                $currentSeconds = [Math]::Max(
                    0,
                    $timeSpan.TotalSeconds
                )
            }
        }
        elseif ($line.StartsWith("speed=")) {
            $speed = $line.Substring(6)
        }

        $percent = 0.0

        if ($TotalSeconds -gt 0) {
            $percent = 100.0 * $currentSeconds / $TotalSeconds
        }

        $message = "{0:0.0}%   {1} / {2}" -f `
            [Math]::Min(100, $percent), `
            (Format-Duration $currentSeconds), `
            (Format-Duration $TotalSeconds)

        if (-not [string]::IsNullOrWhiteSpace($speed)) {
            $message = $message + "   " + $speed
        }

        Update-ProgressWindow `
            -Ui $Ui `
            -Percent $percent `
            -Stage $Stage `
            -Detail $Detail `
            -Status $message
    }

    $process.WaitForExit()

    $stderr = $stderrTask.Result

    return [PSCustomObject]@{
        ExitCode = $process.ExitCode
        StdErr = $stderr
    }
}

# ============================================================
# VALIDATION DES TIMESTAMPS
# ============================================================

function Get-PacketPts {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,

        [Parameter(Mandatory = $true)]
        [ValidateSet("v", "a")]
        [string]$StreamType
    )

    $selector = $StreamType + ":0"

    $result = Invoke-Native `
        -Executable $FFprobe `
        -Arguments @(
            "-v", "error",
            "-select_streams", $selector,
            "-show_packets",
            "-show_entries", "packet=pts_time,duration_time",
            "-of", "csv=p=0",
            "-i", $Path
        )

    if ($result.ExitCode -ne 0) {
        throw "Impossible de lire les timestamps du flux $StreamType : $Path`n$($result.StdErr)"
    }

    $items = New-Object System.Collections.Generic.List[object]

    foreach ($line in ($result.StdOut -split "`r?`n")) {

        if ([string]::IsNullOrWhiteSpace($line)) {
            continue
        }

        $parts = $line.Split(",")

        if ($parts.Count -lt 1) {
            continue
        }

        $pts = 0.0

        if (
            -not [double]::TryParse(
                $parts[0].Trim(),
                [Globalization.NumberStyles]::Float,
                [Globalization.CultureInfo]::InvariantCulture,
                [ref]$pts
            )
        ) {
            continue
        }

        $duration = 0.0

        if ($parts.Count -ge 2) {
            [void][double]::TryParse(
                $parts[1].Trim(),
                [Globalization.NumberStyles]::Float,
                [Globalization.CultureInfo]::InvariantCulture,
                [ref]$duration
            )
        }

        [void]$items.Add(
            [PSCustomObject]@{
                Pts = $pts
                Duration = $duration
            }
        )
    }

    return @($items.ToArray())
}

function Test-PtsSequence {
    param(
        [Parameter(Mandatory = $true)]
        [object[]]$Packets,

        [Parameter(Mandatory = $true)]
        [double]$JoinTime,

        [Parameter(Mandatory = $true)]
        [double]$MaxAllowedJump
    )

    if ($Packets.Count -lt 2) {
        return [PSCustomObject]@{
            Valid = $false
            Message = "Trop peu de paquets pour valider les timestamps."
        }
    }

    # PTS should be monotonic. DTS is intentionally not tested because H.264
    # can have B-frame reordering.
    $previous = $Packets[0].Pts

    for ($index = 1; $index -lt $Packets.Count; $index++) {

        $current = $Packets[$index].Pts

        if ($current -lt ($previous - 0.050)) {
            return [PSCustomObject]@{
                Valid = $false
                Message = (
                    "PTS non monotones : {0:0.000} -> {1:0.000}" -f
                    $previous,
                    $current
                )
            }
        }

        $previous = $current
    }

    # Find the packets immediately before and after the expected join.
    $before = $null
    $after = $null

    foreach ($packet in $Packets) {

        if ($packet.Pts -le $JoinTime) {
            $before = $packet
            continue
        }

        $after = $packet
        break
    }

    if ($null -eq $before -or $null -eq $after) {
        return [PSCustomObject]@{
            Valid = $false
            Message = (
                "Impossible de trouver les paquets autour de la jonction a {0:0.000}s." -f
                $JoinTime
            )
        }
    }

    $jump = $after.Pts - $before.Pts

    if ($jump -gt $MaxAllowedJump) {
        return [PSCustomObject]@{
            Valid = $false
            Message = (
                "Saut de timestamp detecte autour de {0:0.000}s : {1:0.000}s." -f
                $JoinTime,
                $jump
            )
        }
    }

    # Also inspect a few neighbouring packets. This catches a burst of
    # duplicated/dropped timestamps immediately around the join.
    $beforeIndex = -1

    for ($index = 0; $index -lt $Packets.Count; $index++) {
        if ($Packets[$index].Pts -le $JoinTime) {
            $beforeIndex = $index
        }
        else {
            break
        }
    }

    $localStart = [Math]::Max(1, $beforeIndex - 4)
    $localEnd = [Math]::Min($Packets.Count - 1, $beforeIndex + 5)

    for ($index = $localStart; $index -le $localEnd; $index++) {

        $delta = $Packets[$index].Pts - $Packets[$index - 1].Pts

        if ($delta -lt -0.050) {
            return [PSCustomObject]@{
                Valid = $false
                Message = (
                    "Retour de timestamp detecte autour de {0:0.000}s." -f
                    $JoinTime
                )
            }
        }

        if ($delta -gt $MaxAllowedJump) {
            return [PSCustomObject]@{
                Valid = $false
                Message = (
                    "Grand intervalle de timestamp ({0:0.000}s) autour de {1:0.000}s." -f
                    $delta,
                    $JoinTime
                )
            }
        }
    }

    return [PSCustomObject]@{
        Valid = $true
        Message = (
            "OK : jonction {0:0.000}s, ecart PTS {1:0.000}s." -f
            $JoinTime,
            $jump
        )
    }
}

function Test-TimestampContinuity {
    param(
        [Parameter(Mandatory = $true)]
        [string]$OutputPath,

        [Parameter(Mandatory = $true)]
        [double[]]$JoinTimes
    )

    if ($JoinTimes.Count -eq 0) {
        return [PSCustomObject]@{
            Valid = $true
            Message = "Aucune jonction a tester."
        }
    }

    try {
        $videoPackets = @(Get-PacketPts -Path $OutputPath -StreamType "v")
    }
    catch {
        return [PSCustomObject]@{
            Valid = $false
            Message = $_.Exception.Message
        }
    }

    # Video VFR can legitimately have variable frame durations, so 0.75 s
    # is deliberately permissive while still catching large discontinuities.
    $videoMaxJump = 0.75

    foreach ($joinTime in $JoinTimes) {

        $videoCheck = Test-PtsSequence `
            -Packets $videoPackets `
            -JoinTime $joinTime `
            -MaxAllowedJump $videoMaxJump

        if (-not $videoCheck.Valid) {
            return $videoCheck
        }

        Write-Host ("  Timestamp video : " + $videoCheck.Message)
    }

    # Audio is much more regular. If an audio stream exists, validate it too.
    $audioProbe = Invoke-Native `
        -Executable $FFprobe `
        -Arguments @(
            "-v", "error",
            "-select_streams", "a:0",
            "-show_entries", "stream=index",
            "-of", "csv=p=0",
            "-i", $OutputPath
        )

    if ($audioProbe.ExitCode -eq 0 -and -not [string]::IsNullOrWhiteSpace($audioProbe.StdOut)) {

        try {
            $audioPackets = @(Get-PacketPts -Path $OutputPath -StreamType "a")
        }
        catch {
            return [PSCustomObject]@{
                Valid = $false
                Message = $_.Exception.Message
            }
        }

        $audioMaxJump = 0.25

        foreach ($joinTime in $JoinTimes) {

            $audioCheck = Test-PtsSequence `
                -Packets $audioPackets `
                -JoinTime $joinTime `
                -MaxAllowedJump $audioMaxJump

            if (-not $audioCheck.Valid) {
                return $audioCheck
            }

            Write-Host ("  Timestamp audio : " + $audioCheck.Message)
        }
    }

    return [PSCustomObject]@{
        Valid = $true
        Message = "Continuite des timestamps OK."
    }
}

# ============================================================
# VALIDATION SORTIE
# ============================================================

function Test-OutputFile {
    param(
        [Parameter(Mandatory = $true)]
        [string]$OutputPath,

        [Parameter(Mandatory = $true)]
        [double]$ExpectedDuration,

        [Parameter(Mandatory = $true)]
        [int]$SegmentCount,

        [Parameter(Mandatory = $false)]
        [double[]]$JoinTimes = @()
    )

    if (-not (Test-Path -LiteralPath $OutputPath)) {
        return $false
    }

    try {
        $info = Get-VideoInfo -Path $OutputPath
    }
    catch {
        Write-Host ("Validation FFprobe : " + $_.Exception.Message) -ForegroundColor Red
        return $false
    }

    if ($info.VideoCount -ne 1) {
        Write-Host "Validation : le fichier de sortie ne contient pas exactement 1 flux video principal." -ForegroundColor Red
        return $false
    }

    if ($info.AudioCount -gt 1) {
        Write-Host "Validation : plusieurs flux audio dans la sortie." -ForegroundColor Red
        return $false
    }

    $durationTolerance = [Math]::Max(
        0.5,
        0.25 * $SegmentCount
    )

    $durationError = [Math]::Abs(
        $info.Duration - $ExpectedDuration
    )

    if ($durationError -gt $durationTolerance) {
        Write-Host (
            "Validation duree : ECHEC | attendu {0:0.000}s, obtenu {1:0.000}s, ecart {2:0.000}s." -f
            $ExpectedDuration,
            $info.Duration,
            $durationError
        ) -ForegroundColor Red

        return $false
    }

    Write-Host (
        "Validation duree : OK | attendu {0:0.000}s, obtenu {1:0.000}s." -f
        $ExpectedDuration,
        $info.Duration
    )

    if ($JoinTimes.Count -gt 0) {

        $timestampCheck = Test-TimestampContinuity `
            -OutputPath $OutputPath `
            -JoinTimes $JoinTimes

        if (-not $timestampCheck.Valid) {
            Write-Host (
                "Validation timestamps : ECHEC | " +
                $timestampCheck.Message
            ) -ForegroundColor Red

            return $false
        }

        Write-Host "Validation timestamps : OK" -ForegroundColor Green
    }

    $decodeTest = Invoke-Native `
        -Executable $FFmpeg `
        -Arguments @(
            "-hide_banner",
            "-loglevel", "error",
            "-i", $OutputPath,
            "-map", "0:v:0",
            "-map", "0:a:0?",
            "-f", "null",
            "NUL"
        )

    if ($decodeTest.ExitCode -ne 0) {

        Write-Host (
            "Validation decode : ECHEC`n" +
            $decodeTest.StdErr
        ) -ForegroundColor Red

        return $false
    }

    Write-Host "Validation decode : OK" -ForegroundColor Green

    return $true
}

# ============================================================
# TEST H264 QSV
# ============================================================

function Test-QsvEncoder {

    $result = Invoke-Native `
        -Executable $FFmpeg `
        -Arguments @(
            "-hide_banner",
            "-loglevel", "error",
            "-f", "lavfi",
            "-i", "color=c=black:s=128x72:r=30",
            "-t", "0.5",
            "-an",
            "-c:v", $QsvEncoder,
            "-preset", "veryfast",
            "-global_quality", "25",
            "-f", "null",
            "NUL"
        )

    if ($result.ExitCode -ne 0) {
        throw "L encodeur h264_qsv n a pas pu etre initialise.`n$($result.StdErr)"
    }
}

# ============================================================
# CONSTRUCTION DU FILTER COMPLEX
# ============================================================

function Build-ReencodeFilter {
    param(
        [Parameter(Mandatory = $true)]
        [System.Collections.Generic.List[object]]$Infos,

        [Parameter(Mandatory = $true)]
        [int]$Width,

        [Parameter(Mandatory = $true)]
        [int]$Height,

        [Parameter(Mandatory = $true)]
        [string]$FpsExpression,

        [Parameter(Mandatory = $true)]
        [int]$SampleRate
    )

    $parts = New-Object System.Collections.Generic.List[string]
    $concatInputs = [System.Text.StringBuilder]::new()

    for ($index = 0; $index -lt $Infos.Count; $index++) {

        # IMPORTANT :
        # Ne jamais utiliser "$index:v:0" en PowerShell.
        # PowerShell peut interpreter "$index:v" comme une variable de scope.
        # La concatenation ci-dessous produit litteralement [0:v:0].

        $videoFilter =
            "[" + $index + ":v:0]" +
            "scale=" + $Width + ":" + $Height +
            ":force_original_aspect_ratio=decrease," +
            "pad=" + $Width + ":" + $Height +
            ":(ow-iw)/2:(oh-ih)/2," +
            "fps=fps=" + $FpsExpression + "," +
            "format=nv12," +
            "setsar=1," +
            "setpts=PTS-STARTPTS" +
            "[v" + $index + "]"

        [void]$parts.Add($videoFilter)
        [void]$concatInputs.Append(
            "[v" + $index + "]"
        )

        if ($null -ne $Infos[$index].Audio) {

            $audioFilter =
                "[" + $index + ":a:0]" +
                "aresample=" + $SampleRate + "," +
                "aformat=sample_rates=" + $SampleRate +
                ":channel_layouts=stereo," +
                "asetpts=PTS-STARTPTS" +
                "[a" + $index + "]"

        }
        else {

            $durationText = $Infos[$index].Duration.ToString(
                "0.###",
                [Globalization.CultureInfo]::InvariantCulture
            )

            $audioFilter =
                "anullsrc=r=" + $SampleRate +
                ":cl=stereo," +
                "atrim=duration=" + $durationText + "," +
                "asetpts=PTS-STARTPTS" +
                "[a" + $index + "]"
        }

        [void]$parts.Add($audioFilter)

        [void]$concatInputs.Append(
            "[a" + $index + "]"
        )
    }

    $concatFilter =
        $concatInputs.ToString() +
        "concat=n=" + $Infos.Count +
        ":v=1:a=1[outv][outa]"

    [void]$parts.Add($concatFilter)

    return ($parts -join ";")
}

# ============================================================
# HEADER
# ============================================================

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " FUSION VIDEO INTELLIGENTE - FFmpeg / H264_QSV" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "FFmpeg  : $FFmpeg"
Write-Host "FFprobe : $FFprobe"
Write-Host "Encodeur: $QsvEncoder"
Write-Host ""

# ============================================================
# SELECTION
# ============================================================

$defaultFolder = Join-Path $env:USERPROFILE "Downloads\po"

if (-not (Test-Path -LiteralPath $defaultFolder)) {
    $defaultFolder = Join-Path $env:USERPROFILE "Downloads"
}

$dialog = [System.Windows.Forms.OpenFileDialog]::new()
$dialog.Title = "Selectionnez les videos a fusionner"
$dialog.Multiselect = $true
$dialog.InitialDirectory = $defaultFolder
$dialog.CheckFileExists = $true
$dialog.Filter = "Videos|*.mp4;*.mkv;*.mov;*.m4v;*.avi;*.ts;*.m2ts;*.mts;*.webm|Tous les fichiers|*.*"

$dialogResult = $dialog.ShowDialog()

if ($dialogResult -ne [System.Windows.Forms.DialogResult]::OK) {
    Write-Host "Selection annulee."
    exit 0
}

$files = @($dialog.FileNames)

if ($files.Count -lt 2) {
    throw "Selectionnez au moins 2 videos."
}

Write-Host "Fichiers selectionnes :"

for ($index = 0; $index -lt $files.Count; $index++) {
    Write-Host ("  {0:00}. {1}" -f ($index + 1), $files[$index])
}

Write-Host ""

# ============================================================
# TRAITEMENT PRINCIPAL
# ============================================================

$ui = New-ProgressWindow
$infos = [System.Collections.Generic.List[object]]::new()

try {

    # --------------------------------------------------------
    # ANALYSE
    # --------------------------------------------------------

    for ($index = 0; $index -lt $files.Count; $index++) {

        $percent = 100.0 * $index / $files.Count

        Update-ProgressWindow `
            -Ui $ui `
            -Percent $percent `
            -Stage "Analyse des videos" `
            -Detail (
                "{0}/{1} : {2}" -f `
                ($index + 1), `
                $files.Count, `
                [System.IO.Path]::GetFileName($files[$index])
            ) `
            -Status "FFprobe..."

        [void]$infos.Add(
            (Get-VideoInfo -Path $files[$index])
        )
    }

    Update-ProgressWindow `
        -Ui $ui `
        -Percent 100 `
        -Stage "Analyse terminee" `
        -Detail "" `
        -Status "Analyse OK"

    Start-Sleep -Milliseconds 200

    Write-Host ""
    Write-Host "================ ANALYSE ================" -ForegroundColor Yellow
    Write-Host ""

    foreach ($info in $infos) {

        Write-Host "[$($info.Name)]"
        Write-Host "  Duree   : $(Format-Duration $info.Duration)"
        Write-Host "  Video   : $($info.Video.codec_name) | $($info.Video.width)x$($info.Video.height) | $($info.Video.pix_fmt) | FPS $($info.Video.r_frame_rate)"

        if ($null -ne $info.Audio) {
            $layout = [string]$info.Audio.channel_layout

            if ([string]::IsNullOrWhiteSpace($layout)) {
                $layout = "n/a"
            }

            Write-Host "  Audio   : $($info.Audio.codec_name) | $($info.Audio.sample_rate) Hz | $($info.Audio.channels) ch | $layout"
        }
        else {
            Write-Host "  Audio   : aucun"
        }

        Write-Host "  Flux    : video=$($info.TotalVideoCount) (principaux=$($info.VideoCount)) | audio=$($info.AudioCount) | subtitle=$($info.SubtitleCount) | data=$($info.DataCount)"
        Write-Host ""
    }

    $totalDuration = (
        $infos |
        Measure-Object -Property Duration -Sum
    ).Sum

    # Expected positions of all joins in the final timeline.
    $joinTimesList = New-Object System.Collections.Generic.List[double]
    $runningJoin = 0.0

    for ($index = 0; $index -lt ($infos.Count - 1); $index++) {
        $runningJoin += $infos[$index].Duration
        [void]$joinTimesList.Add($runningJoin)
    }

    $joinTimes = $joinTimesList.ToArray()

    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $outputDirectory = Split-Path -Parent $files[0]
    $outputPath = Join-Path `
        $outputDirectory `
        ("Fusion_Intelligente_{0}.mp4" -f $timestamp)

    # --------------------------------------------------------
    # LOSSLESS
    # --------------------------------------------------------

    $losslessCandidate = Test-LosslessCandidate -Infos $infos

    if ($losslessCandidate) {

        Write-Host "============================================================" -ForegroundColor Green
        Write-Host " TENTATIVE FUSION LOSSLESS" -ForegroundColor Green
        Write-Host "============================================================"
        Write-Host ""
        Write-Host "Methode : concat demuxer + -c copy"
        Write-Host "Aucun reencodage video/audio si la validation reussit."
        Write-Host ""

        $tempDirectory = Join-Path `
            $env:TEMP `
            ("FusionVI_" + [Guid]::NewGuid().ToString("N"))

        New-Item `
            -ItemType Directory `
            -Path $tempDirectory `
            -Force |
            Out-Null

        try {

            $cleanRequired = $false

            foreach ($info in $infos) {
                if (Test-NeedsCleanRemux -Info $info) {
                    $cleanRequired = $true
                    break
                }
            }

            $workingFiles = New-Object System.Collections.Generic.List[string]

            if ($cleanRequired) {

                Write-Host "Remux lossless de nettoyage necessaire."
                Write-Host "Les flux A/V principaux restent en -c copy."
                Write-Host ""

                for ($index = 0; $index -lt $infos.Count; $index++) {

                    $cleanName = "clean_{0:00}.mp4" -f ($index + 1)
                    $cleanPath = Join-Path `
                        $tempDirectory `
                        $cleanName

                    $remuxArguments = @(
                        "-y",
                        "-i", $infos[$index].Path,
                        "-map", "0:v:0",
                        "-map", "0:a:0?",
                        "-map_metadata", "-1",
                        "-c", "copy",
                        "-movflags", "+faststart",
                        $cleanPath
                    )

                    $remuxResult = Invoke-FFmpegProgress `
                        -Arguments $remuxArguments `
                        -TotalSeconds $infos[$index].Duration `
                        -Ui $ui `
                        -Stage "Preparation LOSSLESS" `
                        -Detail (
                            "{0}/{1} : remux A/V sans reencodage" -f `
                            ($index + 1), `
                            $infos.Count
                        )

                    if ($remuxResult.ExitCode -ne 0) {
                        throw "Remux lossless impossible pour $($infos[$index].Name)`n$($remuxResult.StdErr)"
                    }

                    [void]$workingFiles.Add($cleanPath)
                }
            }
            else {

                foreach ($file in $files) {
                    [void]$workingFiles.Add($file)
                }
            }

            $concatList = Join-Path `
                $tempDirectory `
                "concat.txt"

            Write-ConcatList `
                -Paths $workingFiles.ToArray() `
                -ListPath $concatList

            $copyArguments = @(
                "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", $concatList,
                "-map", "0:v:0",
                "-map", "0:a:0?",
                "-c", "copy",
                "-movflags", "+faststart",
                "-avoid_negative_ts", "make_zero",
                $outputPath
            )

            $copyResult = Invoke-FFmpegProgress `
                -Arguments $copyArguments `
                -TotalSeconds $totalDuration `
                -Ui $ui `
                -Stage "Fusion LOSSLESS" `
                -Detail "Concat demuxer + stream copy"

            if ($copyResult.ExitCode -eq 0) {

                Update-ProgressWindow `
                    -Ui $ui `
                    -Percent 100 `
                    -Stage "Validation LOSSLESS" `
                    -Detail "Verification de la duree et du decode" `
                    -Status "Validation..."

                $valid = Test-OutputFile `
                    -OutputPath $outputPath `
                    -ExpectedDuration $totalDuration `
                    -SegmentCount $infos.Count

                if ($valid) {

                    Update-ProgressWindow `
                        -Ui $ui `
                        -Percent 100 `
                        -Stage "Fusion LOSSLESS terminee" `
                        -Detail "" `
                        -Status "Aucun reencodage A/V"

                    Write-Host ""
                    Write-Host "============================================================" -ForegroundColor Green
                    Write-Host " FUSION LOSSLESS REUSSIE" -ForegroundColor Green
                    Write-Host "============================================================" -ForegroundColor Green
                    Write-Host ""
                    Write-Host "Sortie : $outputPath"
                    Write-Host "Video/audio : -c copy"
                    Write-Host "Aucune recompression A/V."
                    Write-Host ""

                    Close-ProgressWindow -Ui $ui

                    Remove-Item `
                        -LiteralPath $tempDirectory `
                        -Recurse `
                        -Force `
                        -ErrorAction SilentlyContinue

                    exit 0
                }
            }

            Remove-Item `
                -LiteralPath $outputPath `
                -Force `
                -ErrorAction SilentlyContinue
        }
        catch {

            Write-Host ""
            Write-Host "Tentative lossless non retenue :" -ForegroundColor Yellow
            Write-Host $_.Exception.Message -ForegroundColor Yellow

            Remove-Item `
                -LiteralPath $outputPath `
                -Force `
                -ErrorAction SilentlyContinue
        }

        Remove-Item `
            -LiteralPath $tempDirectory `
            -Recurse `
            -Force `
            -ErrorAction SilentlyContinue
    }
    else {

        Write-Host "============================================================" -ForegroundColor Yellow
        Write-Host " LOSSLESS NON RETENU" -ForegroundColor Yellow
        Write-Host "============================================================"
        Write-Host ""
        Write-Host "Les flux A/V principaux ne sont pas suffisamment compatibles."
        Write-Host "Fallback automatique vers H.264 QSV."
        Write-Host ""
    }

    # --------------------------------------------------------
    # REENCODAGE QSV
    # --------------------------------------------------------

    Write-Host "============================================================" -ForegroundColor Magenta
    Write-Host " REENCODAGE H264_QSV" -ForegroundColor Magenta
    Write-Host "============================================================"
    Write-Host ""

    Test-QsvEncoder

    $width = [int]$infos[0].Video.width
    $height = [int]$infos[0].Video.height

    if (($width % 2) -ne 0) {
        $width--
    }

    if (($height % 2) -ne 0) {
        $height--
    }

    $fpsExpression = [string]$infos[0].Video.r_frame_rate

    if (
        [string]::IsNullOrWhiteSpace($fpsExpression) -or
        $fpsExpression -eq "0/0"
    ) {
        $fpsExpression = "30/1"
    }

    $sampleRate = 44100

    foreach ($info in $infos) {
        if ($null -ne $info.Audio) {
            $sampleRate = [int]$info.Audio.sample_rate
            break
        }
    }

    $filterComplex = Build-ReencodeFilter `
        -Infos $infos `
        -Width $width `
        -Height $height `
        -FpsExpression $fpsExpression `
        -SampleRate $sampleRate

    Write-Host "Resolution : ${width}x${height}"
    Write-Host "FPS        : $fpsExpression CFR"
    Write-Host "Encodeur   : $QsvEncoder"
    Write-Host "Preset     : $QsvPreset"
    Write-Host "Qualite    : $QsvQuality"
    Write-Host "Audio      : AAC ${sampleRate} Hz stereo"
    Write-Host ""

    Write-Host "Demarrage de FFmpeg..."
    Write-Host ""

    $reencodeArguments = New-Object System.Collections.Generic.List[string]

    [void]$reencodeArguments.Add("-y")

    foreach ($file in $files) {
        [void]$reencodeArguments.Add("-i")
        [void]$reencodeArguments.Add($file)
    }

    [void]$reencodeArguments.Add("-filter_complex")
    [void]$reencodeArguments.Add($filterComplex)
    [void]$reencodeArguments.Add("-map")
    [void]$reencodeArguments.Add("[outv]")
    [void]$reencodeArguments.Add("-map")
    [void]$reencodeArguments.Add("[outa]")
    [void]$reencodeArguments.Add("-c:v")
    [void]$reencodeArguments.Add($QsvEncoder)
    [void]$reencodeArguments.Add("-preset")
    [void]$reencodeArguments.Add($QsvPreset)
    [void]$reencodeArguments.Add("-global_quality")
    [void]$reencodeArguments.Add($QsvQuality)
    [void]$reencodeArguments.Add("-c:a")
    [void]$reencodeArguments.Add("aac")
    [void]$reencodeArguments.Add("-b:a")
    [void]$reencodeArguments.Add("192k")
    [void]$reencodeArguments.Add("-ar")
    [void]$reencodeArguments.Add([string]$sampleRate)
    [void]$reencodeArguments.Add("-ac")
    [void]$reencodeArguments.Add("2")
    [void]$reencodeArguments.Add("-map_metadata")
    [void]$reencodeArguments.Add("-1")
    [void]$reencodeArguments.Add("-metadata")
    [void]$reencodeArguments.Add("title=Fusion Video Intelligente")
    [void]$reencodeArguments.Add("-movflags")
    [void]$reencodeArguments.Add("+faststart")
    [void]$reencodeArguments.Add("-fps_mode")
    [void]$reencodeArguments.Add("cfr")
    [void]$reencodeArguments.Add($outputPath)

    # Le filter_complex est passe comme un seul argument.
    # Aucun formatage PowerShell -f n est applique dessus.

    $encodeResult = Invoke-FFmpegProgress `
        -Arguments $reencodeArguments.ToArray() `
        -TotalSeconds $totalDuration `
        -Ui $ui `
        -Stage "Reencodage H.264 QSV" `
        -Detail "Une seule session QSV pour garder le debit eleve"

    if ($encodeResult.ExitCode -ne 0) {
        throw "FFmpeg QSV a echoue.`n$($encodeResult.StdErr)"
    }

    Update-ProgressWindow `
        -Ui $ui `
        -Percent 100 `
        -Stage "Validation de la sortie" `
        -Detail "Verification de la duree et du decode" `
        -Status "Validation..."

    $outputValid = Test-OutputFile `
        -OutputPath $outputPath `
        -ExpectedDuration $totalDuration `
        -SegmentCount $infos.Count `
        -JoinTimes $joinTimes

    if (-not $outputValid) {
        throw "Le fichier QSV a ete cree mais sa validation a echoue."
    }

    Update-ProgressWindow `
        -Ui $ui `
        -Percent 100 `
        -Stage "Fusion terminee" `
        -Detail "" `
        -Status "Sortie H.264 QSV validee"

    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host " FUSION TERMINEE - H264_QSV" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Sortie : $outputPath"
    Write-Host ""
    Write-Host "Cette branche est un REENCODAGE :"
    Write-Host "- Video : H.264 QSV"
    Write-Host "- Audio : AAC 192k"
    Write-Host "- Donc elle n est pas lossless."
    Write-Host ""

    Close-ProgressWindow -Ui $ui
}
catch {

    Close-ProgressWindow -Ui $ui

    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Red
    Write-Host " ERREUR" -ForegroundColor Red
    Write-Host "============================================================" -ForegroundColor Red
    Write-Host ""
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""

    exit 1
}
