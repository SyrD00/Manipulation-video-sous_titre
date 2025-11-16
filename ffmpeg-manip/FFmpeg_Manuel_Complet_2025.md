# 🎬 Guide FFmpeg Personnel – Encodage GPU/CPU, Hardsub & Conversion Vidéo

*📘 Documentation personnelle complète pour maîtriser FFmpeg, l’encodage matériel (Intel QSV, AMD AMF, NVIDIA NVENC), la conversion HEVC→H.264, les hardsubs ASS/SRT, les formats de pixel, les scripts automatisés et toutes les subtilités du workflow vidéo.*

---

# ⭐ SOMMAIRE EXTRÊME (ULTRA DÉTAILLÉ)

# 1. 🎯 Introduction générale

# 🌟 Table des Matières (Cliquable + Émojis)

## 1. [🎯 Introduction générale](#-introduction-générale)

- [✨ 1.1 Pourquoi j’ai créé ce guide](#11-pourquoi-jai-créé-ce-guide-️)
- [🎬 1.2 FFmpeg : ce que ça permet vraiment](#12-ffmpeg--ce-que-ça-permet-vraiment-)
- [🖥️ 1.3 Mon matériel principal](#13-mon-matériel-principal-️)
- [📦 1.4 Codec vs Conteneur](#14-codec-vs-conteneur-)
- [❓ 1.5 Pourquoi réencoder ?](#15-pourquoi-réencoder--️)
- [⚡ 1.6 CPU vs GPU](#16-cpu-vs-gpu-)

## 2. [🛠️ Installation &amp; Configuration de FFmpeg](#️-installation--configuration-de-ffmpeg)

- [⬇️ 2.1 Téléchargement](#21-téléchargement)
- [🧩 2.2 Ajouter FFmpeg au PATH (Windows)](#22-ajouter-ffmpeg-au-path-windows)
  - [👤 2.2.1 Variables utilisateur](#221--variables-denvironnement-utilisateur)
  - [🖥️ 2.2.2 Variables système](#222--variables-système)
  - [🔍 2.2.3 Vérifier que FFmpeg est reconnu](#223--vérifier-que-ffmpeg-est-reconnu)
- [🧪 2.3 Vérifier les encodeurs disponibles](#23--vérifier-les-encodeurs-disponibles-libx264-qsv-nvenc-amf)
- [🔧 2.4 Vérifier le support matériel](#24--vérifier-le-support-matériel-qsvnvencamf)
- [⚙️ 2.5 Comprendre hwaccel](#25--comprendre-les-accélérations-matérielles-hwaccel)

## 3. [📘 Commandes FFmpeg essentielles](#-commandes-ffmpeg-essentielles)

- [🧱 3.1 Structure générale d’une commande](#31--structure-générale-dune-commande)
- [🎛️ 3.2 Options fondamentales](#32--options-fondamentales--i--cv--ca--vf--map)
- [📄 3.3 Copier un flux sans réencodage](#33--copier-un-flux-sans-réencodage)
- [🔄 3.4 MKV → MP4 sans réencodage](#34--conversion-mkv--mp4-sans-réencodage)
- [🚫 3.5 Limitations du copy](#35--quand-le-copy-échoe-eac3-dts)

## 4. [🧠 Encodage CPU avec libx264](#-encodage-cpu-avec-libx264)

- [❗ 4.1 Pourquoi utiliser le CPU ?](#41--pourquoi-utiliser-le-cpu-)
- [🎚️ 4.2 CRF : qualité vs taille](#42--crf--qualité-vs-taille)
- [📈 4.3 Presets libx264](#43--presets-libx264-ultrafast--veryslow)
- [📦 4.4 Commandes pratiques](#44--commandes-pratiques)
- [🎵 4.5 Réencodage audio AAC](#45--réencodage-audio-aac)

## 5. [💠 Encodage matériel Intel Quick Sync (QSV)](#-encodage-matériel-intel-quick-sync-qsv)

- [💡 5.1 Introduction à QSV](#51--introduction-à-qsv)
- [🔍 5.2 Décodage matériel vs logiciel](#52--décodage-matériel-vs-logiciel)
- [📹 5.3 Encodage h264_qsv](#53--encodage-h264-qsv)
- [🎞️ 5.4 Décodage hevc_qsv](#54--décodage-hevc-qsv)
- [🔗 5.5 Pipeline HEVC 10 bits → H.264 8 bits](#55--pipeline-complet--hevc-10-bits--h264-8-bits)
- [🎨 5.6 Importance du format NV12](#56--importance-du-format-nv12)
- [↕️ 5.7 hwupload / hwdownload](#57--hwupload--hwdownload--quand-et-pourquoi)
- [⚡ 5.8 Commandes QSV rapides (A, B1, B2)](#58--commandes-qsv-rapides-a-b1-b2)
- [🧠 5.9 look_ahead](#59--look_ahead--optimisation-ou-latence-)
- [🛑 5.10 Erreurs courantes QSV](#510--erreurs-courantes-qsv-et-corrections)

## 6. [🟩 Encodage NVIDIA NVENC](#-encodage-nvidia-nvenc)

- [💡 6.1 Principes](#61-principes)
- [🎚️ 6.2 Contrôle CQ](#62-cq-vs-crf)
- [⚙️ 6.3 Presets NVENC](#63-presets-nvenc)
- [🚀 6.4 Commandes rapides](#64-commandes-rapides)

## 7. [🟥 Encodage matériel AMD AMF/VCE](#-encodage-matériel-amd-amf-vce)

- [💬 7.1 Présentation](#71-présentation)
- [⚡ 7.2 d3d11va vs dxva2](#72-accélération-dxva2-vs-d3d11va)
- [🎛️ 7.3 Mode CQP](#73-mode-cqp)
- [🎯 7.4 QP_I / QP_P / QP_B](#74-paramètres-qp_i--qp_p--qp_b)
- [🎚️ 7.5 Compatibilité 8/10 bits](#75-compatibilité-810-bits)
- [🛠️ 7.6 Commandes AMD](#76-commandes-pratiques)

## 8. [✨ Hardsub — Sous-titres incrustés](#-hardsub-sous-titres-incrustés)

- [📜 8.1 ASS vs SRT](#81-ass-vs-srt)
- [📊 8.2 Lire les pistes MKV](#82-lire-les-pistes-dun-mkv)
- [🎯 8.3 Identifier la piste (si)](#83-identifier-la-bonne-piste-si)
- [📝 8.4 Hardsub fichier ASS externe](#84-hardsub-avec-fichier-ass)
- [🎞️ 8.5 Hardsub depuis le MKV](#85-hardsub-en-prenant-la-piste-du-mkv)
- [⚙️ 8.6 Pipeline QSV + hardsub](#86-qsv--hardsub--pipeline-complet)
- [🔥 8.7 Hardsub AMD](#87-amd--hardsub)
- [💚 8.8 Hardsub NVENC](#88-nvenc--hardsub)
- [🔽 8.9 hwdownload obligatoire (Intel)](#89-hwdownload--formatnv12--cas-intel)
- [🛑 8.10 Erreurs courantes](#810-erreurs-courantes--symptômes-et-solutions)

## 9. [🎞️ Conversion vidéo complète](#️-conversion-vidéo-complète)

- [🔄 9.1 Conversion HEVC → H.264](#91-conversion-vidéo-h265--h264)
- [🎧 9.2 Conversion audio AAC](#92-conversion-audio-eac3dts--aac)
- [📉 9.3 Bitrate &amp; qualité](#93-bitrate-et-qualité)
- [🎛️ 9.4 Exemples selon GPU](#94-exemples-pour-intel--amd--nvidia)

## 10. [🧾 Scripts utiles](#-scripts-utiles)

- [📌 10.1 Script Powershell — Hardsub AMD](#101-script-powershell--hardsub-amd)
- [📁 10.2 Script Powershell — Conversion QSV MKV](#102-script-powershell--conversion-qsv-de-lots-mkv)
- [🐧 10.3 Script Bash Linux](#103-script-bash-linux)
- [⏱️ 10.4 Mesurer le temps FFmpeg](#104-mesurer-le-temps-dexécution-ffmpeg)

## 11. [🎨 Formats de Pixel](#-formats-de-pixel-pixel-format)

- [🎛️ 11.1 yuv420p](#111-yuv420p)
- [🎛️ 11.2 yuv420p10le](#112-yuv420p10le)
- [🎨 11.3 NV12](#113-nv12)
- [📦 11.4 Compatibilité encodeurs](#114-compatibilité-des-encodeurs)
- [🤔 11.5 Pourquoi convertir ?](#115-pourquoi-la-conversion-cpugpu-est-nécessaire)

## 12. [📊 Rate Control (Débit vidéo)](#-rate-control-gestion-du-débit-vidéo)

- [🎚️ 12.1 CRF](#121-crf)
- [🎚️ 12.2 CQP](#122-cqp)
- [🎯 12.3 QP I/P/B](#123-qp-ipb)
- [📶 12.4 Bitrate CBR/VBR](#124-bitrate-cbrvbr)
- [🧠 12.5 look_ahead](#125-look_ahead-en-détail)

## 13. [🛑 Troubleshooting Général](#-troubleshooting-général)

- [🟥 13.1 Pixel format error](#131-current-pixel-format-is-unsupported)
- [🟥 13.2 Encoder error](#132-error-opening-encoder)
- [🟥 13.3 Décodage matériel non utilisé](#133-décodage-matériel-non-utilisé)
- [🟥 13.4 Cas HEVC 10 bits](#134-cas-hevc-10-bits--h264-qsv)
- [🟥 13.5 Hardsub ne marche pas](#135-hardsub-ne-sapplique-pas)
- [🟥 13.6 Problèmes audio](#136-problèmes-audio-eac3-dts)
- [🟥 13.7 Erreurs MP4](#137-mp4-non-compatible--erreur-lecteur)

## 14. [📚 Annexes — Tableaux &amp; Glossaire](#-annexes--tableaux-récapitulatifs)

- [📊 14.1 Comparatif GPU](#141-tableau-comparatif-gpu-intelamd-nvidia)
- [🎧 14.2 Codecs audio compatibles MP4](#142-codecs-audio-compatibles-mp4)
- [⚡ 14.3 Raccourcis FFmpeg](#143-raccourcis-de-commandes-utiles)
- [📝 14.4 Notes personnelles](#144-notes-personnelles)
- [📖 14.5 Glossaire](#145-glossaire)

## 1.1 Pourquoi j’ai créé ce guide ✍️

Ce document est mon **guide personnel ultime** pour FFmpeg.Il regroupe :

- toutes mes commandes importantes,
- toutes les explications que j’ai apprises,
- chaque cas spécial lié à **Intel QSV**,
- les solutions à mes erreurs les plus fréquentes,
- mes workflows de conversion (HEVC → H.264),
- mes méthodes de hardsub (ASS/SRT),
- toutes les subtilités CPU/GPU que j’ai découvertes.

👉 Il sert de **référence complète**, à la fois pédagogique et pratique.

---

## 1.2 FFmpeg : ce que ça permet vraiment 🧰

FFmpeg peut :

- 🔄 convertir des vidéos
- 🎞️ réencoder dans différents codecs
- 🚀 utiliser le GPU (Intel / AMD / NVIDIA)
- 💬 incruster des sous-titres (hardsub)
- 🧩 changer le conteneur (MKV → MP4)
- 🎶 copier l’audio sans perte
- 🧪 analyser des flux vidéo
- 🤖 automatiser via scripts

Sa logique :

> **Entrée → Filtres → Encodage/Copy → Sortie**

---

## 1.3 Mon matériel principal 🖥️

- CPU : **Intel** (Quick Sync Video compatible)
- GPU intégré :
  - décodage matériel HEVC/H.264
  - encodage matériel H.264
  - exige NV12 (format 8 bits)

👉 Le guide est optimisé pour **Intel QSV**, mais couvre aussi **AMD** et **NVIDIA** pour être complet.

---

## 1.4 Codec vs Conteneur 📦

### 🎞️ Codec = manière dont la vidéo est compressée

Ex :

- H.264
- H.265 / HEVC
- AV1
- AAC
- MP3

### 📁 Conteneur = boîte qui contient tout

Ex :

- MP4
- MKV
- MOV
- AVI

💡 **Un MP4 peut contenir du H.264, HEVC, ou même AV1.**

---

## 1.5 Pourquoi réencoder ? 🔄

Je réencode une vidéo quand :

- son codec n’est pas compatible MP4,
- j’ai besoin de faire un hardsub,
- je veux réduire la taille,
- j’ai du EAC3/DTS incompatible,
- je veux accélérer avec QSV/NVENC/AMF.

---

## 1.6 CPU vs GPU ⚡

| Tâche                | CPU 💻       | GPU 🎮                      |
| --------------------- | ------------ | --------------------------- |
| Décodage vidéo      | ✔️         | ✔️ (très rapide)         |
| Filtres (ASS, crop…) | ✔️         | ❌ (quasi jamais)           |
| Encodage vidéo       | ✔️ libx264 | ✔️ h264_qsv / nvenc / amf |
| Audio                 | ✔️         | ❌                          |

💡 **Les filtres ASS sont presque toujours traités par le CPU**
→ d’où l’étape **hwdownload → format=nv12 → ass=**.

---


# 2. Installation & Configuration de FFmpeg

Cette section regroupe toutes les étapes nécessaires pour installer FFmpeg correctement, et surtout le configurer dans le PATH, car sans cela FFmpeg ne peut pas être utilisé directement dans PowerShell.

---

## 2.1 Télécharger et installer FFmpeg

1. Aller sur le site officiel ou un build fiable (Gyan, BtbN…)
2. Télécharger la version *Static Build*
3. Extraire l’archive dans un dossier simple (ex : `C:\ffmpeg`)
4. Le fichier important se trouve ici :

   `C:\ffmpeg\bin\ffmpeg.exe`

---

## 2.2 Ajouter FFmpeg au PATH (Windows)

### Pourquoi ?

Pour pouvoir taper simplement `ffmpeg` dans PowerShell, sans écrire son emplacement complet.

### Étape 1 : Ouvrir les variables d'environnement

* Menu Démarrer
* Chercher : « variables d’environnement »
* Cliquer : « Modifier les variables d’environnement pour votre compte »

### Étape 2 : Ajouter dans *Variables utilisateur*

1. Dans « Variables d’utilisateur pour `<user>` »
2. Sélectionner « Path »
3. Cliquer sur « Modifier »
4. Cliquer sur « Nouveau »
5. Ajouter : `C:\ffmpeg\bin`

### Étape 3 : Ajouter dans *Variables système*

1. Aller dans « Variables système »
2. Cliquer sur « Nouveau »
3. Ajouter : `C:\ffmpeg\bin`

💡 Le mettre dans utilisateur + système évite des bugs avec certains logiciels.

### Étape 4 : Vérifier l’installation

Dans un nouveau PowerShell :

`ffmpeg -version`

Si les infos FFmpeg s’affichent → installation OK.

---

## 2.3 Vérifier les encodeurs disponibles

Lister tous les encodeurs :

`ffmpeg -encoders`

Lister uniquement le matériel Intel QSV :

`ffmpeg -encoders | Select-String qsv`

Tu dois voir :

* `h264_qsv`
* `hevc_qsv`

---

## 2.4 Comprendre les accélérations matérielles

`-hwaccel` accélère le  **décodage** , pas l’encodage.

| Option           | GPU                   |
| ---------------- | --------------------- |
| -hwaccel qsv     | Intel                 |
| -hwaccel cuda    | NVIDIA                |
| -hwaccel dxva2   | AMD / Intel (Windows) |
| -hwaccel d3d11va | AMD / Intel           |
| -hwaccel vaapi   | Linux                 |

Pour encoder réellement avec le GPU, il faut un codec matériel :

* Intel → `h264_qsv`
* NVIDIA → `h264_nvenc`
* AMD → `h264_amf`

---

# 3. Commandes essentielles FFmpeg

## Structure générale

`ffmpeg [options] -i input [filtres] [codecs] output`

## Options importantes

* `-i` fichier d’entrée
* `-vf` filtres vidéo
* `-c:v` codec vidéo
* `-c:a` codec audio
* `-map` sélection de flux
* `-preset` vitesse/qualité
* `-crf` qualité (libx264)
* `-b:v` bitrate vidéo
* `-c:a copy` copie audio sans réencodage

---

## 3.3 Copier sans réencoder

`ffmpeg -i input.mkv -c copy output.mp4`

Limitations MP4 :

* H.264 ✔
* HEVC parfois ✔
* AAC ✔
* EAC3 ⚠
* DTS ❌ incompatible

---

## 3.4 Conversion MKV → MP4 sans réencodage

`ffmpeg -i input.mkv -c copy output.mp4`

Si le fichier est illisible → audio incompatible.

---

## 3.5 Quand “copy” échoue

Convertir l’audio :

`-c:a aac -b:a 192k`

---

# 4. Encodage CPU libx264 (universel)

## Quand l'utiliser ?

* Format source incompatible avec QSV/NVENC/AMF
* Recherche de qualité maximale
* Beaucoup de filtres (subtitles, scale…)
* Compression cohérente et stable

## Valeurs CRF recommandées

* 18 : haute qualité
* 20–23 : excellent équilibre
* 24–28 : taille réduite

## Presets libx264

| Preset    | Vitesse      | Qualité         | Taille          |
| --------- | ------------ | ---------------- | --------------- |
| ultrafast | très rapide | faible           | énorme         |
| veryfast  | rapide       | bonne            | grande          |
| medium    | équilibré  | excellente       | petite          |
| slow      | lent         | encore meilleure | plus petite     |
| veryslow  | très lent   | qualité max     | taille minimale |

## Exemple basique

`ffmpeg -i input.mkv -c:v libx264 -preset medium -crf 23 -c:a copy output.mp4`

## Avec réencodage audio

`ffmpeg -i input.mkv -c:v libx264 -preset slow -crf 23 -c:a aac -b:a 192k output.mp4`

---

# Pourquoi libx264 peut être plus rapide que QSV ?

Parce que :

* les filtres (ASS) obligent QSV à faire **GPU → CPU → GPU**
* libx264 travaille tout en CPU
* QSV se bloque sur les sources en **10 bits**

# 2. Installation & Configuration de FFmpeg

Cette section regroupe toutes les étapes nécessaires pour installer FFmpeg correctement, et surtout le configurer dans le PATH, car sans cela FFmpeg ne peut pas être utilisé directement dans PowerShell.

---

## 2.1 Télécharger et installer FFmpeg

1. Aller sur le site officiel ou un build fiable (Gyan, BtbN…)
2. Télécharger la version *Static Build*
3. Extraire l’archive dans un dossier simple (ex : `C:\ffmpeg`)
4. Le fichier important se trouve ici :

   `C:\ffmpeg\bin\ffmpeg.exe`

---

## 2.2 Ajouter FFmpeg au PATH (Windows)

### Pourquoi ?

Pour pouvoir taper simplement `ffmpeg` dans PowerShell, sans écrire son emplacement complet.

### Étape 1 : Ouvrir les variables d'environnement

* Menu Démarrer
* Chercher : « variables d’environnement »
* Cliquer : « Modifier les variables d’environnement pour votre compte »

### Étape 2 : Ajouter dans *Variables utilisateur*

1. Dans « Variables d’utilisateur pour `<user>` »
2. Sélectionner « Path »
3. Cliquer sur « Modifier »
4. Cliquer sur « Nouveau »
5. Ajouter : `C:\ffmpeg\bin`

### Étape 3 : Ajouter dans *Variables système*

1. Aller dans « Variables système »
2. Cliquer sur « Nouveau »
3. Ajouter : `C:\ffmpeg\bin`

💡 Le mettre dans utilisateur + système évite des bugs avec certains logiciels.

### Étape 4 : Vérifier l’installation

Dans un nouveau PowerShell :

`ffmpeg -version`

Si les infos FFmpeg s’affichent → installation OK.

---

## 2.3 Vérifier les encodeurs disponibles

Lister tous les encodeurs :

`ffmpeg -encoders`

Lister uniquement le matériel Intel QSV :

`ffmpeg -encoders | Select-String qsv`

Tu dois voir :

* `h264_qsv`
* `hevc_qsv`

---

## 2.4 Comprendre les accélérations matérielles

`-hwaccel` accélère le  **décodage** , pas l’encodage.

| Option           | GPU                   |
| ---------------- | --------------------- |
| -hwaccel qsv     | Intel                 |
| -hwaccel cuda    | NVIDIA                |
| -hwaccel dxva2   | AMD / Intel (Windows) |
| -hwaccel d3d11va | AMD / Intel           |
| -hwaccel vaapi   | Linux                 |

Pour encoder réellement avec le GPU, il faut un codec matériel :

* Intel → `h264_qsv`
* NVIDIA → `h264_nvenc`
* AMD → `h264_amf`

---

# 3. Commandes essentielles FFmpeg

## Structure générale

`ffmpeg [options] -i input [filtres] [codecs] output`

## Options importantes

* `-i` fichier d’entrée
* `-vf` filtres vidéo
* `-c:v` codec vidéo
* `-c:a` codec audio
* `-map` sélection de flux
* `-preset` vitesse/qualité
* `-crf` qualité (libx264)
* `-b:v` bitrate vidéo
* `-c:a copy` copie audio sans réencodage

---

## 3.3 Copier sans réencoder

`ffmpeg -i input.mkv -c copy output.mp4`

Limitations MP4 :

* H.264 ✔
* HEVC parfois ✔
* AAC ✔
* EAC3 ⚠
* DTS ❌ incompatible

---

## 3.4 Conversion MKV → MP4 sans réencodage

`ffmpeg -i input.mkv -c copy output.mp4`

Si le fichier est illisible → audio incompatible.

---

## 3.5 Quand “copy” échoue

Convertir l’audio :

`-c:a aac -b:a 192k`

---

# 4. Encodage CPU libx264 (universel)

## Quand l'utiliser ?

* Format source incompatible avec QSV/NVENC/AMF
* Recherche de qualité maximale
* Beaucoup de filtres (subtitles, scale…)
* Compression cohérente et stable

## Valeurs CRF recommandées

* 18 : haute qualité
* 20–23 : excellent équilibre
* 24–28 : taille réduite

## Presets libx264

| Preset    | Vitesse      | Qualité         | Taille          |
| --------- | ------------ | ---------------- | --------------- |
| ultrafast | très rapide | faible           | énorme         |
| veryfast  | rapide       | bonne            | grande          |
| medium    | équilibré  | excellente       | petite          |
| slow      | lent         | encore meilleure | plus petite     |
| veryslow  | très lent   | qualité max     | taille minimale |

## Exemple basique

`ffmpeg -i input.mkv -c:v libx264 -preset medium -crf 23 -c:a copy output.mp4`

## Avec réencodage audio

`ffmpeg -i input.mkv -c:v libx264 -preset slow -crf 23 -c:a aac -b:a 192k output.mp4`

---

# Pourquoi libx264 peut être plus rapide que QSV ?

Parce que :

* les filtres (ASS) obligent QSV à faire **GPU → CPU → GPU**
* libx264 travaille tout en CPU
* QSV se bloque sur les sources en **10 bits**

# 2. Installation & Configuration de FFmpeg

Cette section regroupe toutes les étapes nécessaires pour installer FFmpeg correctement, et surtout le configurer dans le PATH, car sans cela FFmpeg ne peut pas être utilisé directement dans PowerShell.

---

## 2.1 Télécharger et installer FFmpeg

1. Aller sur le site officiel ou un build fiable (Gyan, BtbN…)
2. Télécharger la version *Static Build*
3. Extraire l’archive dans un dossier simple (ex : `C:\ffmpeg`)
4. Le fichier important se trouve ici :

   `C:\ffmpeg\bin\ffmpeg.exe`

---

## 2.2 Ajouter FFmpeg au PATH (Windows)

### Pourquoi ?

Pour pouvoir taper simplement `ffmpeg` dans PowerShell, sans écrire son emplacement complet.

### Étape 1 : Ouvrir les variables d'environnement

* Menu Démarrer
* Chercher : « variables d’environnement »
* Cliquer : « Modifier les variables d’environnement pour votre compte »

### Étape 2 : Ajouter dans *Variables utilisateur*

1. Dans « Variables d’utilisateur pour `<user>` »
2. Sélectionner « Path »
3. Cliquer sur « Modifier »
4. Cliquer sur « Nouveau »
5. Ajouter : `C:\ffmpeg\bin`

### Étape 3 : Ajouter dans *Variables système*

1. Aller dans « Variables système »
2. Cliquer sur « Nouveau »
3. Ajouter : `C:\ffmpeg\bin`

💡 Le mettre dans utilisateur + système évite des bugs avec certains logiciels.

### Étape 4 : Vérifier l’installation

Dans un nouveau PowerShell :

`ffmpeg -version`

Si les infos FFmpeg s’affichent → installation OK.

---

## 2.3 Vérifier les encodeurs disponibles

Lister tous les encodeurs :

`ffmpeg -encoders`

Lister uniquement le matériel Intel QSV :

`ffmpeg -encoders | Select-String qsv`

Tu dois voir :

* `h264_qsv`
* `hevc_qsv`

---

## 2.4 Comprendre les accélérations matérielles

`-hwaccel` accélère le  **décodage** , pas l’encodage.

| Option           | GPU                   |
| ---------------- | --------------------- |
| -hwaccel qsv     | Intel                 |
| -hwaccel cuda    | NVIDIA                |
| -hwaccel dxva2   | AMD / Intel (Windows) |
| -hwaccel d3d11va | AMD / Intel           |
| -hwaccel vaapi   | Linux                 |

Pour encoder réellement avec le GPU, il faut un codec matériel :

* Intel → `h264_qsv`
* NVIDIA → `h264_nvenc`
* AMD → `h264_amf`

---

# 3. Commandes essentielles FFmpeg

## Structure générale

`ffmpeg [options] -i input [filtres] [codecs] output`

## Options importantes

* `-i` fichier d’entrée
* `-vf` filtres vidéo
* `-c:v` codec vidéo
* `-c:a` codec audio
* `-map` sélection de flux
* `-preset` vitesse/qualité
* `-crf` qualité (libx264)
* `-b:v` bitrate vidéo
* `-c:a copy` copie audio sans réencodage

---

## 3.3 Copier sans réencoder

`ffmpeg -i input.mkv -c copy output.mp4`

Limitations MP4 :

* H.264 ✔
* HEVC parfois ✔
* AAC ✔
* EAC3 ⚠
* DTS ❌ incompatible

---

## 3.4 Conversion MKV → MP4 sans réencodage

`ffmpeg -i input.mkv -c copy output.mp4`

Si le fichier est illisible → audio incompatible.

---

## 3.5 Quand “copy” échoue

Convertir l’audio :

`-c:a aac -b:a 192k`

---

# 4. Encodage CPU libx264 (universel)

## Quand l'utiliser ?

* Format source incompatible avec QSV/NVENC/AMF
* Recherche de qualité maximale
* Beaucoup de filtres (subtitles, scale…)
* Compression cohérente et stable

## Valeurs CRF recommandées

* 18 : haute qualité
* 20–23 : excellent équilibre
* 24–28 : taille réduite

## Presets libx264

| Preset    | Vitesse      | Qualité         | Taille          |
| --------- | ------------ | ---------------- | --------------- |
| ultrafast | très rapide | faible           | énorme         |
| veryfast  | rapide       | bonne            | grande          |
| medium    | équilibré  | excellente       | petite          |
| slow      | lent         | encore meilleure | plus petite     |
| veryslow  | très lent   | qualité max     | taille minimale |

## Exemple basique

`ffmpeg -i input.mkv -c:v libx264 -preset medium -crf 23 -c:a copy output.mp4`

## Avec réencodage audio

`ffmpeg -i input.mkv -c:v libx264 -preset slow -crf 23 -c:a aac -b:a 192k output.mp4`

---

# Pourquoi libx264 peut être plus rapide que QSV ?

Parce que :

* les filtres (ASS) obligent QSV à faire **GPU → CPU → GPU**
* libx264 travaille tout en CPU
* QSV se bloque sur les sources en **10 bits**



# 5. ⚡ Encodage matériel Intel Quick Sync Video (QSV)

QSV = ton matériel principal !

C’est l’accélération matérielle intégrée à ton CPU Intel, très utile pour HEVC → H.264 et pour le décodage rapide.

---

## 5.1 🔍 Vérifier que QSV est activé

Commande :

ffmpeg -encoders | Select-String qsv

Tu dois voir 🟦 :

* **h264_qsv**
* **hevc_qsv**

Si rien → ton build FFmpeg n’a pas QSV → télécharger un build compatible.

---

## 5.2 🚀 Décodage matériel QSV (rapide)

Décoder = lire la vidéo.

Pour activer le décodage HEVC via QSV :

* ffmpeg -c:v hevc_qsv -i input.mkv

  ou
* ffmpeg -hwaccel qsv -i input.mkv

Résultat :

✔ Charge CPU réduite

✔ Lecture + extraction plus fluide

---

## 5.3 🎥 Encodage matériel QSV (h264_qsv)

Ta commande de base :

ffmpeg -i input.mkv -c:v h264_qsv -preset veryfast -c:a copy out.mp4

Avantages :

* 🏎 Très rapide
* 🔋 Faible charge CPU
* 🧼 Parfait pour conversions simples

---

## 5.4 🟦 Deux catégories QSV

### 🔵 A. Décodage logiciel + encodage QSV

ffmpeg -i input.mkv -c:v h264_qsv -preset veryfast -c:a copy out.mp4

Caractéristiques :

* Décodage logiciel
* Encodage GPU Intel
* Vitesse correcte

---

### 🟦 B. Décodage matériel QSV + encodage QSV (LE MEILLEUR)

ffmpeg -c:v hevc_qsv -i input.mkv -c:v h264_qsv -preset veryfast -b:v 4M -c:a copy out.mp4

Avantages :

* ⚡ Plus rapide
* 🎯 Meilleur contrôle de taille (bitrate fixe)
* 💻 Optimisé pour ton CPU Intel HD Graphics 520

---

## 5.5 ❌ Erreur classique : « Current pixel format is unsupported »

Cause principale :

* Vidéo HEVC en **10 bits**
* Format : **yuv420p10le**

Mais **h264_qsv = 8 bits uniquement**

→ donc crash.

---

## 5.6 ✔ Solution : forcer NV12 (8 bits)

### 🌟 Version simple

ffmpeg -c:v hevc_qsv -i input.mkv -vf format=nv12 -c:v h264_qsv -b:v 4M -c:a copy out.mp4

### 🌟 Version pro, stable, recommandée

ffmpeg -init_hw_device qsv=hw -filter_hw_device hw -c:v hevc_qsv -i input.mkv -vf format=nv12,hwupload -c:v h264_qsv -preset veryfast -b:v 4M -c:a copy out.mp4

Explications :

* init_hw_device → prépare le GPU Intel
* hwupload → remonte la frame sur le GPU
* format=nv12 → conversion en 8 bits

---

## 5.7 🎨 Pourquoi NV12 ?

Parce que QSV :

* accepte NV12 ✔
* refuse le 10-bit ❌
* refuse yuv420p10le ❌

Donc conversion  **obligatoire** .

---

## 5.8 🧠 Option avancée : look_ahead

* look_ahead 1 → meilleure qualité mais + lent
* look_ahead 0 → plus rapide, faible latence

Pour la vitesse :

-look_ahead 0

---

## 5.9 ⭐ Commandes QSV recommandées pour TOI

### 🔥 HEVC 10 bits → H.264 (ultra fiable)

ffmpeg -init_hw_device qsv=hw -filter_hw_device hw -c:v hevc_qsv -i input.mkv -vf format=nv12,hwupload -c:v h264_qsv -preset veryfast -b:v 4M -c:a copy out.mp4

### 🔥 Conversion rapide sans réencoder l’audio

ffmpeg -c:v hevc_qsv -i input.mkv -vf format=nv12 -c:v h264_qsv -preset veryfast -c:a copy out.mp4

### 🔥 Hardsub en QSV (obligé de repasser via CPU pour le filtre ASS)

ffmpeg -hwaccel qsv -c:v h264_qsv -i video.mp4 -vf hwdownload,format=nv12,ass=sub.ass -c:v h264_qsv -preset fast -c:a copy out.mp4

---

# 6. 🟩 Encodage NVIDIA NVENC

Même si ce n’est pas ton matériel, tu veux la doc complète.

### ⚡ Conversion rapide

ffmpeg -hwaccel cuda -i input.mkv -c:v h264_nvenc -preset fast -cq 23 -c:a copy output.mp4

CQ = Constant Quality

* plus bas = meilleure qualité
* 23 = standard

NVENC = excellent pour :

* ⚡ vitesse
* 🎥 streaming

Moins bon pour :

* compression optimale (x264 meilleur)

---

# 7. 🟥 Encodage AMD AMF/VCE

### 🔥 Encodage rapide

ffmpeg -hwaccel dxva2 -i video.mp4 -c:v h264_amf -quality speed -c:a copy out.mp4

### 🎯 Contrôle de qualité CQP

ffmpeg -hwaccel dxva2 -i video.mp4 -c:v h264_amf -quality speed -rc cqp -qp_i 22 -qp_p 25 -qp_b 27 -c:a copy out.mp4

### ⚠ Si vidéo source en 10 bits → risque d’erreur

Solution :

ffmpeg -hwaccel d3d11va -i input.mp4 -pix_fmt yuv420p -c:v h264_amf -c:a aac -b:a 192k out.mp4

dxva2 = décodage matériel Windows

d3d11va = plus stable

h264_amf = encodeur AMD



# 8. 🔥 Hardsub (Sous-titres incrustés) avec FFmpeg

Le *hardsub* = les sous-titres sont  **gravés dans la vidéo** , impossibles à désactiver.

C’est utile pour :

* envoyer sur téléphone
* TikTok, Instagram
* lecteurs incompatibles avec les fichiers ASS
* partage universel

---

## 8.1 🔍 Vérifier les pistes de sous-titres dans un fichier MKV

Commande de base (toujours la même) :

ffmpeg -i fichier.mkv

Tu verras les pistes comme :

* Stream #0:0 → vidéo
* Stream #0:1 → audio
* Stream #0:2 → sous-titres (ENG)
* Stream #0:3 → sous-titres (POR)
* Stream #0:4 → sous-titres (SPA)

Exemple réel (ton fichier IP17) :

* #0:2 = ass anglais
* #0:3 = ass portugais
* #0:4 = ass espagnol

Tu choisis la piste avec **si=** (Subtitle Index).

Exemple : tableau interne s = [eng, por, spa]

→ anglais = si=0

---

# 8.2 🟦 Hardsub en CPU (libx264) — stable et universel

Version simple :

ffmpeg -i input.mkv -vf "subtitles=input.mkv:si=0" -c:v libx264 -preset fast -b:v 4M -c:a copy output.mp4

Avantages :

* Très fiable
* Compatible partout
* Fonctionne même sur HEVC 10 bits

Inconvénient :

* Plus lent que QSV/NVENC

---

# 8.3 🟩 Hardsub en Intel QSV (partie complexe)

⚠ QSV  **ne peut pas appliquer un filtre ASS directement sur le GPU** .

Il faut donc faire :

1️⃣ décodage matériel QSV

2️⃣ hwdownload = ramener les frames GPU → CPU

3️⃣ format=nv12 = conversion 8 bits

4️⃣ ass=sub.ass = filtre appliqué

5️⃣ ré-upload sur le GPU si tu veux réencoder en QSV

### 🔵 Commande validée (ta meilleure version)

ffmpeg -hwaccel qsv -c:v h264_qsv -i video.mp4 -vf "hwdownload,format=nv12,ass=sub.ass" -c:v h264_qsv -preset fast -c:a copy output.mp4

Explications :

* hwdownload → sortie GPU → RAM
* format=nv12 → conversion 8 bits lisible par les filtres
* ass=sub.ass → hardsub CPU
* h264_qsv → réencodage rapide

---

# 8.4 🟦 Hardsub en Intel QSV + HEVC décodé matériellement

Pour HEVC 10 bits → hardsub → H.264 QSV :

ffmpeg -init_hw_device qsv=hw -filter_hw_device hw -c:v hevc_qsv -i input.mkv -vf "format=nv12,hwupload,ass=sub.ass" -c:v h264_qsv -preset fast -c:a copy out.mp4

⚠️ Souvent hwupload + ass provoquent des erreurs → préférer la version CPU (8.3).

---

# 8.5 🟥 Hardsub AMD (h264_amf)

### Version basique AMD :

ffmpeg -hwaccel dxva2 -i video.mp4 -vf "ass=sub.ass" -c:v h264_amf -quality speed -c:a copy out.mp4

### Version avec CQP :

ffmpeg -hwaccel dxva2 -i video.mp4 -vf "ass=sub.ass" -c:v h264_amf -quality speed -rc cqp -qp_i 22 -qp_p 25 -qp_b 27 -c:a copy out.mp4

---

# 8.6 🟩 Hardsub NVIDIA NVENC

Si NVIDIA disponible :

ffmpeg -i video.mp4 -vf "subtitles=sub.srt" -c:v h264_nvenc -preset fast -c:a copy out.mp4

Rapide, mais qualité un peu inférieure à x264.

---

# 9. 🎯 Sélection d'une piste précise de sous-titres (si=)

### Pour incruster dans une vidéo MKV multi-sous-titres :

ffmpeg -i input.mkv -vf "subtitles=input.mkv:si=2" -c:v libx264 -preset fast -c:a copy output.mp4

Éléments importants :

* subtitles=« input.mkv » → lit directement dans le conteneur
* si=2 → sélectionne la piste #0:2
* fonctionne avec .ass et .srt
* ne fonctionne PAS avec PGS (image)

---

# 10. ⏱ Mesurer le temps d’encodage FFmpeg

## 10.1 🟦 Méthode PowerShell (Measure-Command)

Measure-Command { ffmpeg … }

Affiche :

* Days
* Hours
* Minutes
* Seconds
* Milliseconds

Exemple (réel dans ton cas) :

Temps = **12 minutes 52 secondes**

---

## 10.2 🟩 Sous Linux/macOS/Git Bash

Utilise :

time ffmpeg …

Affiche :

* real = temps réel
* user = charge CPU utilisateur
* sys = charge CPU système

---

# 11. 🎛 Scripts automatiques de conversion

## 11.1 🔄 Script PowerShell : convertir tous les MKV du dossier → MP4 QSV

Get-ChildItem *.mkv | ForEach-Object {

$input = $ *.FullName

$output = $* .BaseName + ".mp4"

ffmpeg -hwaccel qsv -c:v h264_qsv -i "$input" -c:v h264_qsv -c:a aac -b:a 192k "$output"

}

Avantages :

* conversion de masse automatique
* très rapide avec QSV
* parfait pour des gros dossiers d’anime

---

## 11.2 🟦 Script Linux (.sh)

for file in *.mkv; do

output="${file%.mkv}.mp4"

ffmpeg -hwaccel qsv -c:v h264_qsv -i "$file" -c:v h264_qsv -c:a aac -b:a 192k "$output"

done

chmod +x convert.sh

./convert.sh

---

# 12. 🎥 Différence : MP4 ≠ Codec vidéo

Rappel très important (pour t’aider à t’éviter des erreurs) :

* MP4 = conteneur 📦
* H.264 / HEVC = codecs vidéo 🎞
* AAC / MP3 / AC3 = codecs audio 🔊

Donc :

* un fichier .mp4 peut contenir HEVC
* un fichier .mkv peut contenir H.264
* la compatibilité dépend des lecteurs
