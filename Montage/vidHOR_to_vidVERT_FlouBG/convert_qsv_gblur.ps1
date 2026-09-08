#Fermer Chrome et les programmes inutiles avant de lancer le batch peut être une vraie optimisation.

# ==============================================================================
# SCRIPT POWERSHELL 5.1 - CONVERSION VIDÉO PARALLÈLE (INTEL QSV)
# ==============================================================================
#
# OBJECTIF :
# Transformer une vidéo horizontale en vidéo verticale 1080x1920 pour TikTok /
# Shorts, avec :
#
#   - Un background rempli et fortement flouté
#   - La vidéo originale au premier plan
#   - Encodage H.264 avec Intel Quick Sync Video (QSV)
#   - Plusieurs vidéos FFmpeg traitées simultanément
#
# OPTIMISATIONS TESTÉES SUR LE PC :
#
#   1 FFmpeg  -> ~346 secondes
#   2 FFmpeg  -> ~263 secondes
#   3 FFmpeg  -> ~226 secondes
#   4 FFmpeg  -> ~209 secondes
#   5 FFmpeg  -> ~198 secondes
#   6 FFmpeg  -> ~197 secondes
#   7 FFmpeg  -> ~205 secondes
#   8 FFmpeg  -> ~210 secondes
#
# Conclusion :
# 6 FFmpeg simultanés est le meilleur réglage testé.
#
# Une deuxième optimisation a ensuite été testée :
#
#   GBlur en 1080x1920 -> ~197,5 secondes
#   GBlur en 540x960  -> ~184,9 secondes
#   GBlur en 360x640  -> ~215,2 secondes
#
# Conclusion :
# 540x960 est actuellement le meilleur compromis vitesse / rendu.
#
# ==============================================================================


# 1. CONFIGURATION DES DOSSIERS ET PARAMÈTRES
$dossierVideos = "C:\Users\babak\Downloads\SDP"


# [MAX PROCESSUS]
#
# Nombre maximum de FFmpeg exécutés simultanément.
#
# Tests précédents :
#
#   5 FFmpeg = ~198 secondes
#   6 FFmpeg = ~197 secondes
#   7 FFmpeg = ~205 secondes
#   8 FFmpeg = ~210 secondes
#
# 6 est donc actuellement le meilleur réglage trouvé.
$maxProcessus = 6


# [THREADS PAR FFMPEG]
#
# Nombre de threads CPU autorisés pour CHAQUE processus FFmpeg.
#
# Exemple avec :
#
#   $maxProcessus = 6
#   $threadsFFmpeg = 2
#
# Il peut y avoir jusqu'à environ :
#
#   6 × 2 = 12 threads
#
# IMPORTANT :
#
# Augmenter le nombre de threads ne signifie PAS forcément que FFmpeg sera
# plus rapide.
#
# Plusieurs FFmpeg fonctionnent simultanément et se partagent les ressources
# du processeur, de la mémoire et de QSV.
#
# Il peut donc arriver qu'une valeur plus élevée soit PLUS LENTE qu'une valeur
# plus faible.
#
# Tests réels effectués avec QSV sur cette machine :
#
#   1 thread  -> 59,77 s
#   2 threads -> 48,69 s ← tres bon
#   3 threads -> 44,68 s
#   4 threads -> 47,14 s
#   5 threads -> 48,42 s
#   7 threads -> 44,13 s  ← meilleur résultat mesuré
#   8 threads -> 44,99 s
#   9 threads -> 47,09 s
#   10 threads -> 45,91 s
#
# Ces mesures montrent que les performances ne sont pas linéaires.
#
# Dans les tests effectués, 7 threads a obtenu le meilleur temps individuel
# (44,13 secondes), mais l'écart avec 3 threads (44,68 secondes) est très
# faible.
#
# Il est donc préférable de tester plusieurs valeurs plutôt que de supposer
# que "plus de threads = plus rapide".
#mais je choisisirais 2 pour un reglage passe partout
#
# Pour tester facilement une autre configuration, il suffit de modifier cette
# variable.
#
# Exemple :
#
#   $threadsFFmpeg = 7
#
# donnera automatiquement à FFmpeg :
#
#   -threads 7
#
# La commande FFmpeg utilise ensuite la variable :
#
#   -threads $threadsFFmpeg
#
$threadsFFmpeg = 2



# [PRESET QSV]
#
#   1 = priorité à la vitesse
#   4 = compromis vitesse / compression
#   7 = priorité à la qualité
#
# On conserve 1 pour rechercher la vitesse maximale.
$qsvPreset = 1


# [INTENSITÉ DU FLOU - GBLUR]
#
#   sigma=5  -> flou léger
#   sigma=20 -> flou standard
#   sigma=50 -> flou très intense
#
# On conserve 50 comme dans les tests précédents.
$forceFlou = 50


# [RÉSOLUTION DU CALCUL DU FLOU]
#
# Le fichier final reste en 1080x1920.
#
# Mais le GBlur est calculé en 540x960 avant d'être agrandi.
#
# Cela permet de réduire fortement le nombre de pixels traités par le flou.
#
# 1080x1920 = 2 073 600 pixels
#  540x960  =   518 400 pixels
#
# Le GBlur travaille donc sur 4 fois moins de pixels.
#
# Tests réels :
#
#   1080x1920 -> ~197,5 secondes
#   540x960  -> ~184,9 secondes
#
# On conserve donc 540x960.
$blurWidth = 540
$blurHeight = 960


# 2. RÉCUPÉRATION DES FICHIERS VIDÉO

# Récupération de tous les fichiers MP4.
#
# Les fichiers commençant par "out_" sont ignorés afin d'éviter de retraiter
# les vidéos déjà générées.
$videos = Get-ChildItem -Path $dossierVideos -Filter *.mp4 |
    Where-Object { $_.Name -notlike "out_*" }


# Vérification : aucun fichier trouvé
if ($videos.Count -eq 0) {
    Write-Host "Aucune vidéo à traiter dans $dossierVideos." -ForegroundColor Yellow
    exit
}


# Affichage de la configuration utilisée
Write-Host "Trouvé $($videos.Count) vidéo(s) à traiter ($maxProcessus FFmpeg simultanés | $threadsFFmpeg threads/FFmpeg | Preset: $qsvPreset | Flou: $forceFlou)." -ForegroundColor Cyan
Write-Host "--------------------------------------------------------"


# Utilisation d'une ArrayList .NET pour gérer les processus FFmpeg.
#
# Chaque élément correspond à un processus FFmpeg actuellement lancé.
$processusActifs = New-Object System.Collections.ArrayList


# 3. LANCEMENT DU TRAITEMENT PARALLÈLE

$tempsTotal = Measure-Command {

    foreach ($video in $videos) {

        # Création du nom du fichier de sortie.
        $cheminSortie = Join-Path `
            -Path $video.DirectoryName `
            -ChildPath "out_qsv_$($video.Name)"


        # ----------------------------------------------------------------------
        # COMMANDE FFMPEG
        # ----------------------------------------------------------------------
        #
        # BACKGROUND :
        #
        #   vidéo originale
        #        ↓
        #   scale 540x960
        #        ↓
        #   crop 540x960
        #        ↓
        #   gblur sigma=50
        #        ↓
        #   scale 1080x1920
        #        ↓
        #   [bg]
        #
        #
        # PREMIER PLAN :
        #
        #   vidéo originale
        #        ↓
        #   scale largeur 1080
        #        ↓
        #   [fg]
        #
        #
        # FINAL :
        #
        #   [bg] + [fg]
        #        ↓
        #   overlay centré
        #
        #
        # ----------------------------------------------------------------------
        # THREADS
        # ----------------------------------------------------------------------
        #
        # La variable $threadsFFmpeg permet de modifier facilement le nombre
        # de threads utilisés par chaque FFmpeg.
        #
        # Au lieu d'avoir :
        #
        #   -threads 2
        #
        # on utilise :
        #
        #   -threads $threadsFFmpeg
        #
        # Ainsi, il suffit de modifier la configuration au début du script.
        #
        # Exemple :
        #
        #   $threadsFFmpeg = 2
        #
        # donnera :
        #
        #   -threads 2
        #
        # Si on met :
        #
        #   $threadsFFmpeg = 4
        #
        # FFmpeg recevra automatiquement :
        #
        #   -threads 4
        #
        #
        # ----------------------------------------------------------------------
        # QSV
        # ----------------------------------------------------------------------
        #
        # h264_qsv utilise Intel Quick Sync Video pour l'encodage H.264.
        #
        # Tes tests ont montré que QSV était plus rapide que libx264 sur
        # cette machine, donc on conserve QSV.
        #
        #
        # ----------------------------------------------------------------------
        # AUDIO
        # ----------------------------------------------------------------------
        #
        # -c:a copy copie directement l'audio sans le réencoder.
        #
        # Cela évite du travail supplémentaire.
        #
        # ----------------------------------------------------------------------

        $arguments = "-threads $threadsFFmpeg -i `"$($video.FullName)`" -filter_complex `"[0:v]scale=${blurWidth}:${blurHeight}:force_original_aspect_ratio=increase,crop=${blurWidth}:${blurHeight},gblur=sigma=$forceFlou,scale=1080:1920[bg];[0:v]scale=1080:-1[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2`" -c:v h264_qsv -preset $qsvPreset -global_quality 23 -c:a copy `"$cheminSortie`" -y"
        # Définition des arguments avec accélération GPU OpenCL
        
        # Attendre qu'une place se libère si la limite de processus est atteinte.
        while (($processusActifs | Where-Object { -not $_.HasExited }).Count -ge $maxProcessus) {
            Start-Sleep -Milliseconds 100
        }


        # Nettoyage des processus terminés.
        for ($i = $processusActifs.Count - 1; $i -ge 0; $i--) {

            if ($processusActifs[$i].HasExited) {
                $processusActifs.RemoveAt($i)
            }
        }


        # ----------------------------------------------------------------------
        # DÉMARRAGE DIRECT DE FFMPEG
        # ----------------------------------------------------------------------

        $pinfo = New-Object System.Diagnostics.ProcessStartInfo

        $pinfo.FileName = "ffmpeg.exe"
        $pinfo.Arguments = $arguments

        # Pas de Shell Windows intermédiaire.
        $pinfo.UseShellExecute = $false

        # Pas de fenêtre console FFmpeg.
        $pinfo.CreateNoWindow = $true


        # Lancement du processus FFmpeg.
        $process = [System.Diagnostics.Process]::Start($pinfo)


        # Ajout du processus à la liste des processus actifs.
        [void]$processusActifs.Add($process)


        # Affichage de la vidéo lancée.
        Write-Host "Traitement lancé : $($video.Name)" -ForegroundColor Green
    }


    # --------------------------------------------------------------------------
    # ATTENTE DE LA FIN DES DERNIERS ENCODAGES
    # --------------------------------------------------------------------------

    while (($processusActifs | Where-Object { -not $_.HasExited }).Count -gt 0) {
        Start-Sleep -Milliseconds 100
    }
}


# 4. BILAN FINAL

Write-Host "--------------------------------------------------------"

Write-Host "Traitement terminé avec succès !" -ForegroundColor Cyan

Write-Host "Temps total d'exécution : $($tempsTotal.TotalSeconds) secondes ($($tempsTotal.Minutes) min $($tempsTotal.Seconds) s)" -ForegroundColor Yellow

Write-Host "--------------------------------------------------------"