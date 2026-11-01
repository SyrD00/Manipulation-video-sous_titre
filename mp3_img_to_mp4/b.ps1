[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.Application]::EnableVisualStyles()

# 1. Sélection du fichier MP3
$mp3Dialog = New-Object System.Windows.Forms.OpenFileDialog
$mp3Dialog.Title = "Sélectionnez votre fichier MP3"
$mp3Dialog.Filter = "Fichiers audio (*.mp3)|*.mp3"

$resultMp3 = $mp3Dialog.ShowDialog()
if ($resultMp3 -ne 'OK') { 
    Write-Host "`nAucun fichier MP3 sélectionné ou erreur. Annulation." -ForegroundColor Red
    Read-Host "Appuyez sur Entrée pour quitter..."
    exit 
}
$mp3Path = $mp3Dialog.FileName
$mp3Folder = [System.IO.Path]::GetDirectoryName($mp3Path)

# 2. Sélection de l'Image
$imgDialog = New-Object System.Windows.Forms.OpenFileDialog
$imgDialog.Title = "Sélectionnez l'image pour la vidéo"
$imgDialog.Filter = "Images (*.png;*.jpg;*.jpeg;*.webp;*.bmp)|*.png;*.jpg;*.jpeg;*.webp;*.bmp"
$imgDialog.InitialDirectory = $mp3Folder

$resultImg = $imgDialog.ShowDialog()
if ($resultImg -ne 'OK') { 
    Write-Host "`nAucune image sélectionnée. Annulation." -ForegroundColor Red
    Read-Host "Appuyez sur Entrée pour quitter..."
    exit 
}
$imgPath = $imgDialog.FileName

# 3. Traitement FFmpeg
$mp3Name = [System.IO.Path]::GetFileName($mp3Path)
$outputPath = [System.IO.Path]::ChangeExtension($mp3Path, ".mp4")

Write-Host "`nCréation de la vidéo pour : $mp3Name" -ForegroundColor Green

ffmpeg -y -loop 1 -framerate 1 -i "$imgPath" -i "$mp3Path" `
    -map 0:v:0 -map 1:a:0 `
    -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,format=nv12" `
    -c:v h264_qsv -preset 1 -b:v 150k `
    -r 1 -c:a copy `
    -shortest "$outputPath"

Write-Host "`nTerminé ! Vidéo créée : $outputPath" -ForegroundColor Yellow
Read-Host "`nAppuyez sur Entrée pour quitter..."