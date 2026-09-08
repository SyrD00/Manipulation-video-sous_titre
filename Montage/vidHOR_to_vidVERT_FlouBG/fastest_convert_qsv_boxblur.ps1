# ==============================================================================
# SCRIPT POWERSHELL 5.1 - CONVERSION VIDÉO PARALLÈLE (INTEL QSV OPTIMISÉ)
# ==============================================================================

# 1. CONFIGURATION DES DOSSIERS ET PARAMÈTRES

$dossierVideos = "C:\Users\babak\Downloads\S"

# [NOUVEAU] DOSSIER DE SORTIE : Là où les vidéos terminées seront sauvegardées
$dossierSortie = "C:\Users\babak\Downloads\S\Output"


# ==============================================================================
# POURQUOI UTILISER DES PROCESSUS MULTIPLES ET POURQUOI LA LIMITE DE 6 ?
# ==============================================================================
# 
# LE RÔLE DES PROCESSUS (Parallélisme des fichiers) :
# L'encodage matériel Intel QSV est très puissant. Si on traite 1 seule vidéo, 
# la puce graphique (GPU) n'est souvent utilisée qu'à 15 ou 20%. Lancer 
# plusieurs processus FFmpeg permet de "gaver" le GPU pour l'utiliser à 100%.
# 
# POURQUOI 6 PROCESSUS ($maxProcessus = 6) ? LE POINT D'ÉQUILIBRE :
# - Synergie avec le CPU : 6 processus × 4 threads = 24 threads au total. 
#   Cela correspond parfaitement aux capacités d'un processeur moderne puissant, 
#   le chargeant à 100% sans créer de goulot d'étranglement.
# - Limite de RAM / VRAM : Chaque vidéo traitée consomme de la mémoire vive et 
#   vidéo. Au-delà de 6 processus simultanés, on risque de saturer la mémoire 
#   et de faire planter l'ordinateur.
# - En résumé : 6 processus est un "sweet spot" qui maximise les composants 
#   (CPU + GPU + RAM) sans les surcharger.
# ==============================================================================
# [MAX PROCESSUS]
$maxProcessus = 6
 

# ==============================================================================
# POURQUOI LIMITER LES THREADS (ex: 4) AU LIEU DU MODE "AUTO" ?
# ==============================================================================
# 
# On pourrait penser que le mode auto (comportement par défaut) gèrerait mieux 
# les ressources. Mais en traitement par lots, c'est une très mauvaise idée qui 
# ralentirait l'ordinateur et le traitement.
# 
# LE PROBLÈME DU MODE "AUTO" EN PARALLÈLE :
# En mode auto (ou -threads 0), FFmpeg regarde le nombre de cœurs du processeur 
# et les utilise tous. C'est parfait pour UNE vidéo. 
# Mais si on traite 6 vidéos en même temps avec un processeur de 16 cœurs :
# - La vidéo 1 crée 16 threads.
# - La vidéo 2 crée 16 threads... etc.
# Résultat : 96 threads (6x16) se battent simultanément pour 16 cœurs physiques.
# 
# L'EMBOUTEILLAGE (THREAD THRASHING / CONTEXT SWITCHING) :
# C'est comme si 6 chefs cuisiniers ordonnaient à 16 commis de faire 6 recettes 
# différentes. Les commis passent plus de temps à changer d'outils qu'à cuisiner.
# 
# CONSÉQUENCES SUR LE PC :
# - Processeur "dans le vide" : 100% d'utilisation CPU, mais l'énergie sert 
#   à gérer les files d'attente plutôt qu'à calculer le flou (boxblur).
# - Ordinateur figé (Freeze) : Windows n'a plus de ressources pour fonctionner.
# - Encodage plus lent : Le processeur est tellement engorgé que le temps 
#   total s'allonge.
# - RAM saturée : Chaque thread créé par FFmpeg alloue de la mémoire vive.
# 
# LA RÈGLE D'OR :
# - 1 seule vidéo à la fois : -threads auto (Toutes les ressources pour 1 tâche)
# - Plusieurs vidéos : Limiter manuellement les threads (On divise les ressources 
#   pour que chaque tâche ait son propre couloir).
# ==============================================================================
# [THREADS PAR FFMPEG]
$threadsFFmpeg = 4

# ==============================================================================
# PARAMÈTRES DE QUALITÉ VIDÉO ET CORRESPONDANCE QSV
# ==============================================================================

# [PRESET QSV : L'EFFORT DE LA CARTE GRAPHIQUE]
# L'encodeur Intel (QSV) accepte 7 niveaux de réglage. 
# Vous pouvez utiliser soit le CHIFFRE (de 1 à 7), soit le MOT correspondant.
# ATTENTION : Chez Intel, plus le chiffre est petit, meilleure est la qualité.
#
# --- CORRESPONDANCE EXACTE (Chiffre = Mot) ---
# 1 = "veryslow" (Qualité absolue, encodage le plus lent. Fichier optimisé au max)
# 2 = "slower"   (Très haute qualité, très lent)
# 3 = "slow"     (Haute qualité, lent)
# 4 = "medium"   (LE POINT D'ÉQUILIBRE : excellent compromis qualité/vitesse)
# 5 = "fast"     (Rapide, légère perte de qualité)
# 6 = "faster"   (Très rapide, perte de qualité visible)
# 7 = "veryfast" (Vitesse extrême, mais beaucoup de pixels/carrés)
#
# Note : Vous aviez "1" à l'origine, ce qui forçait la carte graphique à 
# travailler à sa qualité maximale (et donc très lentement !).
# "medium" (ou 4) est généralement le meilleur choix pour les réseaux sociaux.
# ==============================================================================
$qsvPreset = "medium"


# [QUALITÉ GLOBALE - NOUVEAU]
# 23 = Standard, 18 = Haute qualité (Visuellement sans perte), 15 = Qualité extrême (Fichier très lourd)
$qualiteVideo = 23


# [ALGORITHME DE REDIMENSIONNEMENT - VIDÉO CENTRALE]
# "fast_bilinear" = Rapide mais un peu flou
# "bicubic" = Standard
# "lanczos" = Qualité maximale et très nette
$algoVideoCentrale = "lanczos"

# [IMAGES PAR SECONDE (FPS)]
# 30 = Format standard réseaux sociaux
# 60 = Format ultra-fluide (gaming, action)
$fpsSortie = 30


# [RÉSOLUTION DU CALCUL DU FLOU]
$blurWidth = 180
$blurHeight = 320


# ==============================================================================
# RÉGLAGES DU FLOU (BOXBLUR)
# ==============================================================================
# Le flou est défini par deux valeurs : la Force (Rayon) et la Qualité (Puissance).
#
# 1. $forceDuFlou (Le Rayon / Radius) :
#    - Rôle : Définit la distance d'étalement des pixels.
#    - MIN absolu : 0 (Aucun flou).
#    - MAX théorique : Environ 90 (la taille maximale du flou ne peut pas dépasser la moitié de l'image).
#    - MAX recommandé : 30 à 40 (Au-delà, l'image devient juste une couleur unie).
# 
# 2. $qualiteDuFlou (La Puissance / Power) :
#    - Rôle : Nombre de passages du filtre pour lisser le flou.
#    - MIN absolu : 0 (Filtre ignoré).
#    - MAX absolu : 10 (FFmpeg bloque à 10. Si tu mets 11, erreur).
#    - MAX recommandé : 2 ou 3.
#      * 1 = Très rapide, un peu "carré".
#      * 2 = Flou doux, temps de calcul doublé.
#      * 3 = Flou parfait (type gaussien), temps de calcul triplé.
#      * 4 à 10 = Différence invisible à l'oeil nu, mais processeur saturé pour rien.
#
# EXEMPLES DE RÉGLAGES IDÉAUX :
# - Flou léger (laisse deviner l'action) : Force = 5, Qualité = 1
# - Flou fort et élégant (très lisse)    : Force = 15, Qualité = 2
# ==============================================================================
$forceDuFlou = 15
$qualiteDuFlou = 2


# 2. PRÉPARATION DU DOSSIER DE SORTIE ET RÉCUPÉRATION DES FICHIERS VIDÉO
# Création du dossier de sortie s'il n'existe pas encore
if (-not (Test-Path $dossierSortie)) {
    New-Item -ItemType Directory -Force -Path $dossierSortie | Out-Null
    Write-Host "Création du dossier de sortie : $dossierSortie" -ForegroundColor DarkGray
}

# 1. On crée une liste de tous les formats vidéo que tu veux accepter
$formatsVideo = @(".mp4", ".mkv", ".mov", ".avi", ".wmv", ".flv", ".m4v", ".ts")

# 2. On récupère les fichiers et on vérifie s'ils font partie de la liste
$videos = Get-ChildItem -Path $dossierVideos -File |
    Where-Object { 
        ($_.Extension -in $formatsVideo) -and 
        ($_.Name -notlike "out_*") 
    }

if ($videos.Count -eq 0) {
    Write-Host "Aucune vidéo à traiter dans $dossierVideos." -ForegroundColor Yellow
    exit
}

Write-Host "Trouvé $($videos.Count) vidéo(s) à traiter ($maxProcessus FFmpeg simultanés | $threadsFFmpeg threads/FFmpeg | Preset: $qsvPreset | Flou: boxblur)." -ForegroundColor Cyan
Write-Host "--------------------------------------------------------"

$processusActifs = New-Object System.Collections.ArrayList

# 3. LANCEMENT DU TRAITEMENT PARALLÈLE
$tempsTotal = Measure-Command {

    foreach ($video in $videos) {

        # [MODIFICATION ICI] La vidéo est maintenant envoyée dans $dossierSortie
        $cheminSortie = Join-Path `
            -Path $dossierSortie `
            -ChildPath "out_qsv_$($video.Name)"

        # ----------------------------------------------------------------------
        # COMMANDE FFMPEG OPTIMISÉE ET CORRIGÉE
        # - Intégration des variables $forceDuFlou et $qualiteDuFlou
        # - Ajout de fps=30, setsar=1, format=nv12 pour l'encodeur Intel
        # - Ajout de -video_track_timescale 90000 pour la propreté des MP4
        # ----------------------------------------------------------------------
        $arguments = "-threads $threadsFFmpeg -i `"$($video.FullName)`" -filter_complex `"[0:v]scale=${blurWidth}:${blurHeight}:force_original_aspect_ratio=increase:sws_flags=fast_bilinear,crop=${blurWidth}:${blurHeight},boxblur=${forceDuFlou}:${qualiteDuFlou},scale=1080:1920:sws_flags=fast_bilinear[bg];[0:v]scale=1080:-1:sws_flags=${algoVideoCentrale}[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2,fps=$fpsSortie,setsar=1,format=nv12`" -c:v h264_qsv -preset $qsvPreset -global_quality $qualiteVideo -video_track_timescale 90000 -c:a copy `"$cheminSortie`" -y"
        
        # Attendre qu'une place se libère si la limite de processus est atteinte
        while (($processusActifs | Where-Object { -not $_.HasExited }).Count -ge $maxProcessus) {
            Start-Sleep -Milliseconds 100
        }

        # Nettoyage des processus terminés
        for ($i = $processusActifs.Count - 1; $i -ge 0; $i--) {
            if ($processusActifs[$i].HasExited) {
                $processusActifs.RemoveAt($i)
            }
        }

        # Démarrage de FFmpeg
        $pinfo = New-Object System.Diagnostics.ProcessStartInfo
        $pinfo.FileName = "ffmpeg.exe"
        $pinfo.Arguments = $arguments
        $pinfo.UseShellExecute = $false
        $pinfo.CreateNoWindow = $true

        $process = [System.Diagnostics.Process]::Start($pinfo)
        [void]$processusActifs.Add($process)

        Write-Host "Traitement lancé : $($video.Name)" -ForegroundColor Green
    }

    # Attente de la fin des derniers encodages
    while (($processusActifs | Where-Object { -not $_.HasExited }).Count -gt 0) {
        Start-Sleep -Milliseconds 100
    }
}

# 4. BILAN FINAL
Write-Host "--------------------------------------------------------"
Write-Host "Traitement terminé avec succès !" -ForegroundColor Cyan
Write-Host "Vidéos sauvegardées dans : $dossierSortie" -ForegroundColor Green
Write-Host "Temps total d'exécution : $($tempsTotal.TotalSeconds) secondes ($($tempsTotal.Minutes) min $($tempsTotal.Seconds) s)" -ForegroundColor Yellow
Write-Host "--------------------------------------------------------"