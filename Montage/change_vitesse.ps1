param (
    [string]$InputFolder = "C:\Users\babak\Downloads\S\",
    [string]$OutputFolder = "C:\Users\babak\Downloads\S\Output\Vitesse_Modifiee",
    [double]$Vitesse = 1.05,
    
    # [OPTIMISATION 1] On passe à 6 vidéos en même temps pour saturer la carte graphique
    [int]$MaxProcessus = 6, 
    
    # [OPTIMISATION 2] On limite à 4 threads par vidéo pour ne pas faire planter le processeur
    [int]$Threads = 4,

    [string]$EncodeurVideo = "h264_qsv"
)

if (-not (Test-Path $OutputFolder)) {
    New-Item -ItemType Directory -Force -Path $OutputFolder | Out-Null
}

$PtsFactor = [math]::Round(1.0 / $Vitesse, 6)
$FiltreVideo = "setpts=$($PtsFactor)*PTS"
$FiltreAudio = "atempo=$Vitesse"

$Fichiers = Get-ChildItem -Path $InputFolder -Include *.mp4, *.mkv, *.mov, *.avi -Recurse | Where-Object { $_.DirectoryName -notmatch "Vitesse_Modifiee" }

Write-Host "Traitement de $($Fichiers.Count) vidéos à vitesse x$Vitesse (Mode ULTRA RAPIDE) avec $EncodeurVideo..." -ForegroundColor Cyan
$ProcessusActifs = @()

foreach ($Fichier in $Fichiers) {
    while ($ProcessusActifs.Count -ge $MaxProcessus) {
        Start-Sleep -Milliseconds 200
        $ProcessusActifs = $ProcessusActifs | Where-Object { $_.HasExited -eq $false }
    }

    $NomFichier = $Fichier.Name
    $CheminSortie = Join-Path $OutputFolder $NomFichier

    # Nettoyage des fichiers de 0 octet
    if (Test-Path $CheminSortie) {
        if ((Get-Item $CheminSortie).Length -eq 0) {
            Remove-Item $CheminSortie -Force
            Write-Host "Suppression du fichier corrompu (0 octet) : $NomFichier" -ForegroundColor Yellow
        } else {
            Write-Host "Le fichier $NomFichier est déjà traité." -ForegroundColor DarkGray
            continue
        }
    }

    Write-Host "Lancement : $NomFichier" -ForegroundColor Green -NoNewline

    $HasAudio = $false
    try {
        $AudioCheck = & ffprobe -v error -select_streams a:0 -show_entries stream=codec_name -of default=noprint_wrappers=1:nokey=1 "`"$($Fichier.FullName)`"" 2>$null
        if (-not [string]::IsNullOrWhiteSpace($AudioCheck)) { $HasAudio = $true }
    } catch {}

    # [OPTIMISATION 3] Ajout de "-threads $Threads" et "-preset 1" pour une vitesse de rendu maximale
    if ($HasAudio) {
        Write-Host " (Audio détecté)" -ForegroundColor DarkGray
        $ArgsFFmpeg = "-threads $Threads -y -i `"$($Fichier.FullName)`" -filter_complex `"[0:v]$FiltreVideo,format=nv12`[v];[0:a]$FiltreAudio`[a]`" -map `"[v]`" -map `"[a]`" -c:v $EncodeurVideo -preset 1 -global_quality 23 -r 30 -c:a aac -b:a 192k `"$CheminSortie`""
    } else {
        Write-Host " (Aucun audio, mode vidéo seule)" -ForegroundColor Yellow
        $ArgsFFmpeg = "-threads $Threads -y -i `"$($Fichier.FullName)`" -filter_complex `"[0:v]$FiltreVideo,format=nv12`[v]`" -map `"[v]`" -c:v $EncodeurVideo -preset 1 -global_quality 23 -r 30 `"$CheminSortie`""
    }

    $Proc = Start-Process -FilePath "ffmpeg" -ArgumentList $ArgsFFmpeg -PassThru -NoNewWindow
    $ProcessusActifs += $Proc
}

if ($ProcessusActifs.Count -gt 0) {
    Write-Host "`nAttente de la fin des derniers encodages..." -ForegroundColor Cyan
    $ProcessusActifs | Wait-Process
}
Write-Host "Toutes les vidéos sont prêtes !" -ForegroundColor Green