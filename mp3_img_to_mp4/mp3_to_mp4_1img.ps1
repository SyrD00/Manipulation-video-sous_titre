[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Add-Type -AssemblyName System.Windows.Forms

# 1. Sélection du Dossier contenant les MP3 (Pop-up de sélection de dossier)
$folderDialog = New-Object System.Windows.Forms.FolderBrowserDialog
$folderDialog.Description = "Sélectionnez le dossier contenant tous vos fichiers MP3"

if ($folderDialog.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) { exit }
$mp3Folder = $folderDialog.SelectedPath

# 2. Sélection Image (Pop-up de sélection d'image)
$imgDialog = New-Object System.Windows.Forms.OpenFileDialog
$imgDialog.Title = "Sélectionnez l'image unique pour l'ensemble des MP3"
$imgDialog.Filter = "Images (*.png;*.jpg;*.jpeg;*.webp;*.bmp)|*.png;*.jpg;*.jpeg;*.webp;*.bmp"
$imgDialog.InitialDirectory = $mp3Folder

if ($imgDialog.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) { exit }
$imgPath = $imgDialog.FileName

# Récupération de tous les MP3 du dossier
$mp3Files = Get-ChildItem -Path $mp3Folder -Filter "*.mp3"

if ($mp3Files.Count -eq 0) {
    Write-Host "Aucun fichier MP3 trouvé dans ce dossier." -ForegroundColor Red
    exit
}

Write-Host "`nTraitement de $($mp3Files.Count) fichiers MP3..." -ForegroundColor Cyan

$count = 1
$total = $mp3Files.Count

# 3. Traitement individuel de chaque MP3 avec ta commande FFmpeg exacte
foreach ($mp3 in $mp3Files) {
    $mp3Path = $mp3.FullName
    $outputPath = [System.IO.Path]::ChangeExtension($mp3Path, ".mp4")

    Write-Host "[$count/$total] Création ultra-rapide pour : $($mp3.Name)" -ForegroundColor Green

    ffmpeg -y -loop 1 -framerate 1 -i "$imgPath" -i "$mp3Path" `
        -map 0:v:0 -map 1:a:0 `
        -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,format=nv12" `
        -c:v h264_qsv -preset 1 -b:v 150k `
        -r 1 -c:a copy `
        -shortest "$outputPath"

    $count++
}

Write-Host "`nTerminé !" -ForegroundColor Yellow