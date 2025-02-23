#pour exécuter e srcipt=.\hardsub_generate.ps1


# Ce script va encoder une vidéo avec FFmpeg en utilisant le GPU AMD (h264_amf)

# Définir les chemins d'entrée et de sortie
$inputFile = "C:\Users\mamou\Videos\1\SL\6.mp4"  # Vidéo d'entrée
$outputFile = "C:\Users\mamou\Videos\1\SL\OUTPUT.mp4"  # Vidéo de sortie

# Commande FFmpeg pour l'encodage
ffmpeg -hwaccel dxva2 -i $inputFile -vf "ass=FUSION.ass" -c:v h264_amf -quality speed -rc cqp -qp_i 22 -qp_p 25 -qp_b 27 -c:a copy $outputFile

# Fin du script


