[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Add-Type -AssemblyName System.Windows.Forms

$downloadsFolder = Join-Path $env:USERPROFILE "Downloads"

# ============================================================
# CONFIGURATION
# ============================================================

# 1.5 = +50 % | 1.8 = +80 % | 2.0 = +100 % (1.8 est la limite propre recommandée)
#$volume = 1.8

# Résolution
$width  = 1920
$height = 1080

# ============================================================
# SÉLECTION MP3
# ============================================================

$mp3Dialog = New-Object System.Windows.Forms.OpenFileDialog
$mp3Dialog.Title = "Sélectionnez votre fichier MP3"
$mp3Dialog.Filter = "Fichiers Audio MP3 (*.mp3)|*.mp3"
$mp3Dialog.InitialDirectory = $downloadsFolder

if ($mp3Dialog.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) { exit }
$mp3Path = $mp3Dialog.FileName

# ============================================================
# SÉLECTION IMAGE
# ============================================================

$imgDialog = New-Object System.Windows.Forms.OpenFileDialog
$imgDialog.Title = "Sélectionnez l'image"
$imgDialog.Filter = "Images (*.png;*.jpg;*.jpeg;*.webp;*.bmp)|*.png;*.jpg;*.jpeg;*.webp;*.bmp"
$imgDialog.InitialDirectory = $downloadsFolder

if ($imgDialog.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) { exit }
$imgPath = $imgDialog.FileName

# ============================================================
# SORTIE
# ============================================================

$outputPath = [System.IO.Path]::ChangeExtension($mp3Path, ".mp4")

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " GENERATION CLEAN (+80% SANS CRÊTES)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================
# DÉTECTION QSV
# ============================================================

$qsv = ffmpeg -hide_banner -encoders 2>$null | Select-String "h264_qsv"

# ============================================================
# FILTRES
# ============================================================

$videoFilter = "scale=${width}:${height}:force_original_aspect_ratio=decrease,pad=${width}:${height}:(ow-iw)/2:(oh-ih)/2"

# Augmentation du son + Limiteur anti-clipping (bloque à -0.5dB max pour éviter les pics)
#$audioFilter = "volume=${volume},alimiter=limit=0.95:level=disabled"

# ============================================================
# ENCODAGE
# ============================================================

if ($null -ne $qsv) {

    Write-Host "Intel Quick Sync détecté." -ForegroundColor Green
    Write-Host "Encodage QSV..." -ForegroundColor Green
    Write-Host ""

    & ffmpeg -y `
        -hide_banner `
        -loglevel warning `
        -loop 1 `
        -framerate 1 `
        -i "$imgPath" `
        -i "$mp3Path" `
        -map 0:v:0 `
        -map 1:a:0 `
        -vf "$videoFilter,format=nv12" `
        -c:v h264_qsv `
        -preset 1 `
        -global_quality 30 `
        -r 1 `
        -af "$audioFilter" `
        -c:a aac `
        -b:a 320k `
        -shortest `
        -movflags +faststart `
        "$outputPath"

}
else {

    Write-Host "QSV non disponible." -ForegroundColor Yellow
    Write-Host "Encodage CPU ultrarapide..." -ForegroundColor Yellow
    Write-Host ""

    & ffmpeg -y `
        -hide_banner `
        -loglevel warning `
        -loop 1 `
        -framerate 1 `
        -i "$imgPath" `
        -i "$mp3Path" `
        -map 0:v:0 `
        -map 1:a:0 `
        -vf "$videoFilter" `
        -c:v libx264 `
        -preset ultrafast `
        -tune stillimage `
        -crf 30 `
        -r 1 `
        -threads 0 `
        -af "$audioFilter" `
        -c:a aac `
        -b:a 320k `
        -shortest `
        -movflags +faststart `
        "$outputPath"
}

# ============================================================
# FIN
# ============================================================

if ($LASTEXITCODE -eq 0 -and (Test-Path $outputPath)) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host " TERMINE !" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Fichier créé : $outputPath" -ForegroundColor Cyan
}
else {
    Write-Host "`nERREUR !" -ForegroundColor Red
}