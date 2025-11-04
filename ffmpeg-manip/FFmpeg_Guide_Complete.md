
# 🎬 Le Guide Ultime de FFmpeg

Un guide complet et pratique pour convertir, ré-encoder ou incruster des sous-titres dans des vidéos en utilisant  **FFmpeg** , avec ou sans accélération matérielle (Intel, NVIDIA, AMD).

## 📖 Sommaire

1. [Introduction à FFmpeg](#introduction-à-ffmpeg)
   [Commandes de Base](#commandes-de-base)
   [Conversion simple (sans ré-encodage)](#conversion-simple-sans-ré-encodage)
   [Extraire l’audio](#extraire-laudio)
   [Couper sans réencoder](#couper-sans-réencoder)
   [Comprendre les Formats et Conteneurs](#comprendre-les-formats-et-conteneurs)
   [Ré-encodage CPU (libx264)](#ré-encodage-cpu-libx264)
   [Ré-encodage Matériel (GPU)](#ré-encodage-matériel-gpu)
   [Intel (Quick Sync Video – QSV)](#intel-quick-sync-video--qsv)
   [NVIDIA (NVENC)](#nvidia-nvenc)
   [AMD (AMF)](#amd-amf)
   [Incrustation de Sous-titres (Hardsub)](#incrustation-de-sous-titres-hardsub)
   [Conversion en Lot (Batch)](#conversion-en-lot-batch)
   [PowerShell (Windows)](#powershell-windows)
   [Bash (Linux/macOS)](#bash-linuxmacos)
   [Utilitaires et Astuces](#utilitaires-et-astuces)
   [Mesurer le temps d’exécution](#mesurer-le-temps-dexécution)
   [Notes et optimisations](#notes-et-optimisations)
   [Résumé Rapide](#résumé-rapide)

## Introduction à FFmpeg

FFmpeg est un outil en ligne de commande puissant pour :

* Encoder / décoder des vidéos
* Ajouter ou incruster des sous-titres
* Convertir entre formats
* Extraire l’audio ou compresser des fichiers vidéo

## Commandes de Base

### Conversion simple (sans ré-encodage)

Copie les flux vidéo et audio sans les modifier. Rapide, mais ne fonctionne que si les codecs sont déjà compatibles avec le conteneur de sortie (par ex. H.264 + AAC dans un MP4).

```
ffmpeg -i input.mkv -c copy output.mp4
```

* `-i input.mkv` : fichier source
* `-c copy` : copie vidéo et audio sans ré-encodage

### Extraire l’audio

Extrait la piste audio sans la ré-encoder.

```
ffmpeg -i video.mp4 -vn -acodec copy audio.aac
```

* `-vn` : désactive la vidéo (Video None)
* `-acodec copy` : copie le codec audio

### Couper sans réencoder

Coupe une section d'une vidéo très rapidement en copiant les flux.

```
ffmpeg -ss 00:00:10 -to 00:00:30 -i input.mp4 -c copy output.mp4
```

* `-ss` : (Seek) Heure de début
* `-to` : Heure de fin

## Comprendre les Formats et Conteneurs

MP4 est un conteneur, pas un codec.
Un fichier `.mp4` peut contenir :

* Vidéo : H.264 / HEVC / AV1 / MPEG-4
* Audio : AAC / AC3 / MP3 / Opus

Réencoder permet d’assurer une compatibilité universelle (par ex. H.264 + AAC) :

```
ffmpeg -i input.mp4 -c:v libx264 -c:a aac -b:a 192k output.mp4
```

## Ré-encodage CPU (libx264)

L'encodeur H.264 universel (CPU). Compatible partout, mais plus lent.

```
ffmpeg -i input.mkv -c:v libx264 -preset ultrafast -crf 23 -c:a copy output.mp4
```

| Option                | Description                                                |
| --------------------- | ---------------------------------------------------------- |
| `-c:v libx264`      | encodeur H.264 (CPU)                                       |
| `-crf 23`           | Qualité constante (18–28, plus bas = meilleure qualité) |
| `-preset ultrafast` | Vitesse max, taille plus grande                            |
| `-c:a copy`         | Copie l'audio sans perte                                   |

**Comparatif des presets :**

| Preset    | Vitesse         | Qualité      | Taille     |
| --------- | --------------- | ------------- | ---------- |
| ultrafast | 🚀 Très rapide | 😐 Moyenne    | 📦 Grande  |
| medium    | ⚖️ Moyenne    | 😊 Bonne      | 📦 Moyenne |
| slow      | 🐢 Lent         | 😍 Excellente | 📦 Petite  |

💡 **Recommandé :** `-preset slow -crf 22` (excellent compromis qualité/taille)

## Ré-encodage Matériel (GPU)

Utilise le GPU pour un encodage beaucoup plus rapide.

### Intel (Quick Sync Video – QSV)

**1. Vérifier la compatibilité QSV**

```
# Linux
ffmpeg -encoders | grep qsv
# Windows PowerShell
ffmpeg -encoders | Select-String qsv
```

Doit afficher `h264_qsv` et/ou `hevc_qsv`.

**2. Commandes QSV de base (HEVC → H.264)**
Utilise le décodage matériel HEVC et l'encodage matériel H.264.

```
ffmpeg -c:v hevc_qsv -i input.mkv -c:v h264_qsv -preset veryfast -b:v 4M -c:a copy output.mp4
```

**3. Conversion 10 bits → 8 bits (NV12)**
Requis si votre source est en 10 bits (P010) et que vous ciblez H.264 8 bits (NV12).

```
ffmpeg -init_hw_device qsv=hw -filter_hw_device hw \
-c:v hevc_qsv -i input.mkv \
-vf "format=nv12,hwupload" \
-c:v h264_qsv -preset veryfast -b:v 4M -c:a copy output_fixed.mp4
```

* `format=nv12` : convertit en 8 bits (NV12) sur le CPU
* `hwupload` : renvoie la vidéo au GPU pour l'encodage

**4. Appliquer un filtre (ex: sous-titres) avec QSV**
Le filtrage se fait sur le CPU, il faut donc télécharger la vidéo du GPU, appliquer le filtre, et la renvoyer.

```
ffmpeg -hwaccel qsv -c:v h264_qsv -i input.mp4 -vf "hwdownload,format=nv12,ass=subs.ass,hwupload" -c:v h264_qsv -preset fast -c:a copy output.mp4
```

* `hwdownload` → transfère la frame GPU → CPU
* `format=nv12` → convertit au format logiciel
* `ass=subs.ass` → applique le filtre de sous-titres
* `hwupload` → renvoie la frame au GPU pour l'encodage

### NVIDIA (NVENC)

```
ffmpeg -hwaccel cuda -i input.mkv -c:v h264_nvenc -preset fast -cq 23 -c:a copy output.mp4
```

* `-hwaccel cuda` : utilise l'accélération CUDA pour le décodage (si possible)
* `-c:v h264_nvenc` : encodeur H.264 de NVIDIA
* `-cq 23` : qualité constante (similaire à `-crf`)

### AMD (AMF)

```
ffmpeg -hwaccel dxva2 -i input.mp4 -c:v h264_amf -quality speed -c:a copy output.mp4
```

* `-hwaccel dxva2` : accélération matérielle (Windows)
* `-c:v h264_amf` : encodeur H.264 d'AMD
* `-quality speed` : privilégie la vitesse

**Exemple plus complet (avec sous-titres et gestion de qualité CQP) :**

```
ffmpeg -hwaccel dxva2 -i "SL8.mp4" -vf "ass=F.ass" -c:v h264_amf -quality speed -rc cqp -qp_i 22 -qp_p 25 -qp_b 27 -c:a copy "SL8sub.mp4"
```

* `-rc cqp` : (Rate Control) Constant Quantization Parameter
* `-qp_i 22 -qp_p 25 -qp_b 27` : réglages de qualité fins pour les frames I, P, et B

**Cas AMD avec Direct3D 11 (plus récent) :**

```
ffmpeg -hwaccel d3d11va -i FF.mp4 -pix_fmt yuv420p -c:v h264_amf -c:a aac -b:a 192k FF1sub.mp4
```

* `pix_fmt yuv420p` : force le 8-bit (utile si le GPU ne supporte pas le 10-bit)

## Incrustation de Sous-titres (Hardsub)

"Graver" les sous-titres dans l'image vidéo.

**1. Identifier la piste de sous-titres**

```
ffmpeg -i input.mkv
```

➡️ Repérez le numéro `Stream #0:x` du sous-titre voulu.

**2. Graver le sous-titre**

**CPU (libx264) - Plus simple**
Utilise le filtre `ass` (pour .ass ou .srt).

```
ffmpeg -i input.mp4 -vf "ass=subtitles.ass" -c:v libx264 -preset fast -c:a copy output.mp4
```

Si les sous-titres sont dans le conteneur (ex: .mkv) :

```
ffmpeg -i input.mkv -vf "ass=input.mkv" -c:v libx264 -preset fast -c:a copy output.mp4
```

(S'il y a plusieurs pistes, spécifiez-la : `ass=input.mkv:stream_index=2`)

**GPU (Ex: QSV)**
(Voir la section QSV ci-dessus pour la commande `hwdownload`/`hwupload`)

```
ffmpeg -hwaccel qsv -c:v h264_qsv -i input.mp4 -vf "hwdownload,format=nv12,ass=subs.ass,hwupload" -c:v h264_qsv -preset fast -c:a copy output.mp4
```

## Conversion en Lot (Batch)

### PowerShell (Windows)

Convertit tous les `.mkv` du dossier en `.mp4` en utilisant QSV.

```
Get-ChildItem *.mkv | ForEach-Object {
  $input = $_.FullName
  $output = $_.BaseName + ".mp4"
  # Adaptez la commande ffmpeg ci-dessous
  ffmpeg -c:v hevc_qsv -i "$input" -vf format=nv12 -c:v h264_qsv -c:a aac -b:a 192k "$output"
}
```

### Bash (Linux/macOS)

```
#!/bin/bash
for file in *.mkv; do
  output="${file%.mkv}.mp4"
  # Adaptez la commande ffmpeg ci-dessous
  ffmpeg -c:v hevc_qsv -i "$file" -vf format=nv12 -c:v h264_qsv -c:a aac -b:a 192k "$output"
done
```

## Utilitaires et Astuces

### Mesurer le temps d’exécution

**Windows PowerShell**

```
Measure-Command { ffmpeg -i in.mkv -c:v h264_qsv -b:v 4M -c:a copy out.mp4 }
```

**Linux/macOS**

```
time ffmpeg -i in.mkv -c:v h264_qsv -b:v 4M -c:a copy out.mp4
```

### Notes et optimisations

* `-preset` : contrôle le compromis vitesse/qualité (ultrafast, fast, medium, slow)
* `-crf` (CPU) / `-cq` (GPU) : ajuste la qualité (plus bas = meilleure qualité)
* `-pix_fmt yuv420p` : améliore la compatibilité (force le 8-bit YUV 4:2:0)
* `-c:a copy` : garde l’audio original (toujours plus rapide et meilleure qualité)

## Résumé Rapide

| Objectif                              | Commande recommandée                                                                      |
| ------------------------------------- | ------------------------------------------------------------------------------------------ |
| Conversion rapide sans ré-encodage   | `ffmpeg -i in.mkv -c copy out.mp4`                                                       |
| Ré-encodage CPU universel            | `ffmpeg -i in.mkv -c:v libx264 -crf 23 -preset slow -c:a aac out.mp4`                    |
| Accélération Intel QSV (HEVC->H264) | `ffmpeg -c:v hevc_qsv -i in.mkv -vf format=nv12 -c:v h264_qsv -b:v 4M -c:a copy out.mp4` |
| NVIDIA NVENC                          | `ffmpeg -hwaccel cuda -i in.mkv -c:v h264_nvenc -preset fast -cq 23 -c:a copy out.mp4`   |
| AMD AMF                               | `ffmpeg -hwaccel dxva2 -i in.mkv -c:v h264_amf -quality speed -c:a copy out.mp4`         |
| Incruster sous-titres (CPU)           | `ffmpeg -i in.mp4 -vf "ass=subs.ass" -c:v libx264 -preset fast -c:a copy out.mp4`        |
