
Add-Type -AssemblyName System.Windows.Forms

# ============================================================
# 1. Sélection des fichiers
# ============================================================

$dialog = New-Object System.Windows.Forms.OpenFileDialog
$dialog.Title = "Sélectionner les clips MP4"
$dialog.Filter = "Fichiers MP4 (*.mp4)|*.mp4"
$dialog.Multiselect = $true

if ($dialog.ShowDialog() -ne "OK") {
    exit
}

$files = $dialog.FileNames

Write-Host "Clips sélectionnés : $($files.Count)" -ForegroundColor Green

$success = 0
$errors  = 0

# ============================================================
# 2. Vérification de FFmpeg
# ============================================================

$ffmpeg = Get-Command ffmpeg.exe -ErrorAction SilentlyContinue

if (-not $ffmpeg) {
    Write-Host "FFmpeg est introuvable dans le PATH." -ForegroundColor Red
    exit
}

# ============================================================
# 3. Traitement
# ============================================================

foreach ($filePath in $files) {

    $fileItem = Get-Item -LiteralPath $filePath

    Write-Host ""
    Write-Host "Traitement de : $($fileItem.Name)" -ForegroundColor Cyan

    # Fichier temporaire dans le même dossier
    $tempOutput = Join-Path `
        $fileItem.DirectoryName `
        ".$($fileItem.BaseName)_repair_$([guid]::NewGuid().ToString('N')).mp4"

    # ========================================================
    # 4. FFmpeg
    #
    # setpts=N/(30*TB)
    #   -> reconstruit les timestamps vidéo à partir du numéro
    #      réel de chaque image.
    #
    # -r 30
    #   -> impose explicitement 30 fps à l'encodeur QSV.
    #
    # -fps_mode cfr
    #   -> sortie constante.
    #
    # aresample=async=1:first_pts=0
    #   -> reconstruit les timestamps audio à partir de 0.
    # ========================================================

    $ffmpegArgs = @(
        "-y",
        "-hide_banner",
        "-loglevel", "warning",

        "-i", $filePath,

        # ---------------- VIDEO ----------------
        "-map", "0:v:0",
        "-vf", "setpts=N/(30*TB),format=nv12",

        # Framerate de sortie explicitement supporté
        "-r", "30",
        "-fps_mode", "cfr",

        # Intel Quick Sync
        "-c:v", "h264_qsv",
        "-preset", "veryfast",

        # ---------------- AUDIO ----------------
        "-map", "0:a:0?",
        "-af", "aresample=async=1:first_pts=0",
        "-c:a", "aac",
        "-b:a", "192k",

        # ---------------- CONTENEUR ----------------
        "-avoid_negative_ts", "make_zero",
        "-map_metadata", "0",

        $tempOutput
    )

    & $ffmpeg.Source @ffmpegArgs

    if ($LASTEXITCODE -eq 0 -and (Test-Path -LiteralPath $tempOutput)) {

        try {
            Move-Item `
                -LiteralPath $tempOutput `
                -Destination $filePath `
                -Force

            Write-Host " -> SUCCÈS" -ForegroundColor Green
            $success++
        }
        catch {
            Write-Host " -> ERREUR lors du remplacement du fichier" -ForegroundColor Red
            Write-Host $_.Exception.Message -ForegroundColor DarkRed

            $errors++

            if (Test-Path -LiteralPath $tempOutput) {
                Remove-Item -LiteralPath $tempOutput -Force
            }
        }

    }
    else {

        Write-Host " -> ÉCHEC FFmpeg" -ForegroundColor Red
        $errors++

        if (Test-Path -LiteralPath $tempOutput) {
            Remove-Item -LiteralPath $tempOutput -Force
        }
    }
}

# ============================================================
# 5. Bilan
# ============================================================

Write-Host ""
Write-Host "================ BILAN ================" -ForegroundColor Yellow
Write-Host "Réussis : $success" -ForegroundColor Green
Write-Host "Échecs  : $errors" -ForegroundColor Red
Write-Host "========================================" -ForegroundColor Yellow
