# ==============================================================================
# SCRIPT D'AUTOMATISATION FFMPEG : CONCATÉNATION DE CLIPS SNAPCHAT VFR -> CFR
# Mode opératoire : Normalisation individuelle à 30fps strict puis fusion rapide.
# Ordre chronologique inversé : De benoitqueen-368.mp4 à benoitqueen-237.mp4
# ==============================================================================

# 1. Configuration et dossier temporaire
$tmpDir = ".\fixed_temp"
if (-not (Test-Path $tmpDir)) { 
    New-Item -ItemType Directory -Path $tmpDir | Out-Null 
}

#exmple les videos : benoitqueen-368.mp4, benoitqueen-367.mp4, ..., benoitqueen-237.mp4

# 2. Sélection des fichiers cibles (boucle décroissante)
$files = 368..237 | ForEach-Object { "benoitqueen-$_.mp4" } | Where-Object { Test-Path $_ }

if ($files.Count -eq 0) {
    Write-Host "Erreur : Aucun fichier correspondant au motif 'benoitqueen-xxx.mp4' n'a été trouvé dans ce dossier." -ForegroundColor Red
    Exit
}

Write-Host "Étape 1 : Normalisation VFR -> CFR 30fps strict pour $($files.Count) fichiers..." -ForegroundColor Cyan
$count = 1

# 3. Boucle de normalisation individuelle
foreach ($file in $files) {
    Write-Progress -Activity "Normalisation en cours..." -Status "Fichier : $file ($count/$($files.Count))" -PercentComplete (($count / $files.Count) * 100)
    
    # Encodage ultra-rapide avec correction des timestamps et framerate fixe à 30fps
    & ffmpeg -y -hide_banner -loglevel error -i $file -vf "fps=30" -vsync cfr -c:v libx264 -preset ultrafast -crf 20 -c:a aac -b:a 128k -ar 44100 -ac 1 "$tmpDir\$file"
    
    $count++
}

Write-Host "Étape 2 : Génération de la liste des fichiers sains..." -ForegroundColor Cyan
$listContent = $files | ForEach-Object { "file '$tmpDir/$_'" }
Out-File -FilePath liste_fixed.txt -InputObject ($listContent -join "`r`n") -Encoding ascii

Write-Host "Étape 3 : Fusion finale instantanée..." -ForegroundColor Green
# Concaténation propre sans perte
& ffmpeg -y -f concat -safe 0 -i liste_fixed.txt -c copy video_finale.mp4

Write-Host "Étape 4 : Nettoyage du plan de travail..." -ForegroundColor Yellow
Remove-Item -Recurse -Force $tmpDir
Remove-Item -Force liste_fixed.txt

Write-Host "Terminé avec succès ! Le fichier final 'video_finale.mp4' est synchronisé." -ForegroundColor Green
