# 🎬 Guide FFmpeg Personnel – Encodage GPU/CPU, Hardsub & Conversion Vidéo

*📘 Documentation personnelle complète pour maîtriser FFmpeg, l’encodage matériel (Intel QSV, AMD AMF, NVIDIA NVENC), la conversion HEVC→H.264, les hardsubs ASS/SRT, les formats de pixel, les scripts automatisés et toutes les subtilités du workflow vidéo.*

---


# ⭐ SOMMAIRE


# 🌟 Table des Matières (Sommaire Cliquable)

## 1. 🎯 Introduction générale

- [✨ 1.1 Pourquoi j’ai créé ce guide](#11-pourquoi-jai-cree-ce-guide)
- [🧰 1.2 FFmpeg : ce que ça permet vraiment](#12-ffmpeg--ce-que-ca-permet-vraiment)
- [🖥️ 1.3 Mon matériel principal](#13-mon-materiel-principal)
- [📦 1.4 Codec vs Conteneur](#14-codec-vs-conteneur)
- [🔄 1.5 Pourquoi réencoder ?](#15-pourquoi-reencoder-)
- [⚡ 1.6 CPU vs GPU](#16-cpu-vs-gpu)

## 2. 🛠️ Installation & Configuration de FFmpeg

- [⬇️ 2.1 Téléchargement](#21-telechargement)
- [🧩 2.2 Ajouter FFmpeg au PATH (Windows)](#22-ajouter-ffmpeg-au-path-windows)
  - [👤 2.2.1 Variables d’environnement utilisateur](#221-variables-denvironnement-utilisateur)
  - [🖥️ 2.2.2 Variables système](#222-variables-systeme)
  - [🔍 2.2.3 Vérification](#223-verification)
- [🧪 2.3 Vérifier les encodeurs (CPU/GPU)](#23-verifier-les-encodeurs-cpugpu)
- [🔧 2.4 Vérifier les accélérations matérielles](#24-verifier-les-accelerations-materielles)
- [⚙️ 2.5 Comprendre -hwaccel](#25-comprendre--hwaccel)

## 3. 📘 Commandes FFmpeg essentielles

- [🧱 3.1 Structure de base](#31-structure-de-base)
- [🎛️ 3.2 Options fondamentales](#32-options-fondamentales)
- [📄 3.3 Copier un flux sans réencodage](#33-copier-un-flux-sans-reencodage)
- [🔄 3.4 MKV → MP4 sans réencodage](#34-mkv--mp4-sans-reencodage)
- [🚫 3.5 Quand le copy échoue](#35-quand-le-copy-echoue)

## 4. 🧠 Encodage CPU avec libx264

- [❗ 4.1 Pourquoi choisir le CPU ?](#41-pourquoi-choisir-le-cpu-)
- [🎚️ 4.2 CRF](#42-crf)
- [📈 4.3 Presets libx264](#43-presets-libx264)
- [📦 4.4 Commandes pratiques](#44-commandes-utiles-libx264)
- [🎵 4.5 Réencodage audio AAC](#45-reencodage-audio-aac)

## 5. 💠 Encodage matériel Intel Quick Sync (QSV)

- [💡 5.1 Introduction à QSV](#51-introduction-a-qsv)
- [🔍 5.2 Décodage matériel vs logiciel](#52-decodage-materiel-vs-logiciel)
- [📹 5.3 Encodage h264_qsv](#53-encodage-h264_qsv)
- [🎞️ 5.4 Décodage hevc_qsv](#54-decodage-hevc_qsv)
- [🔗 5.5 Pipeline HEVC 10 bits → H.264 8 bits](#55-pipeline-hevc-10-bits--h264-8-bits)
- [🎨 5.6 Importance du format NV12](#56-importance-du-format-nv12)
- [↕️ 5.7 hwupload / hwdownload](#57-hwupload--hwdownload)
- [⚡ 5.8 Commandes QSV rapides](#58-commandes-qsv-rapides)
- [🧠 5.9 look_ahead](#59-look_ahead)
- [🛑 5.10 Erreurs QSV](#510-erreurs-qsv)

## 6. 🟩 Encodage NVIDIA NVENC

- [💡 6.1 Principes](#61-principes)
- [🎚️ 6.2 Contrôle CQ](#62-controle-cq)
- [⚙️ 6.3 Presets NVENC](#63-presets-nvenc)
- [🚀 6.4 Commandes rapides](#64-commandes-rapides)

## 7. 🟥 Encodage matériel AMD AMF/VCE

- [💬 7.1 Présentation](#71-presentation)
- [⚡ 7.2 d3d11va vs dxva2](#72-d3d11va-vs-dxva2)
- [🎛️ 7.3 Mode CQP](#73-mode-cqp)
- [🎯 7.4 Paramètres QP_I/P/B](#74-parametres-qp_ipb)
- [🎚️ 7.5 Compatibilité 8/10 bits](#75-compatibilite-810-bits)
- [🛠️ 7.6 Commandes AMD](#76-commandes-amd)

## 8. ✨ Hardsub — Sous-titres incrustés

- [📜 8.1 ASS vs SRT](#81-ass-vs-srt)
- [📊 8.2 Lire les pistes d’un MKV](#82-lire-les-pistes-dun-mkv)
- [🎯 8.3 Identifier la piste](#83-identifier-la-piste)
- [📝 8.4 Hardsub fichier ASS externe](#84-hardsub-fichier-ass)
- [🎞️ 8.5 Hardsub depuis MKV](#85-hardsub-depuis-mkv)
- [⚙️ 8.6 Pipeline QSV hardsub](#86-pipeline-qsv-hardsub)
- [🔥 8.7 Hardsub AMD](#87-hardsub-amd)
- [💚 8.8 Hardsub NVENC](#88-hardsub-nvenc)
- [🔽 8.9 Intel : hwdownload obligatoire](#89-intel-hwdownload-obligatoire)
- [🛑 8.10 Erreurs courantes](#810-erreurs-courantes)

## 9. 🎞️ Conversion vidéo complète

- [🔄 9.1 Conversion HEVC → H.264](#91-conversion-hevc--h264)
- [🎧 9.2 Conversion audio AAC](#92-conversion-audio-aac)
- [📉 9.3 Bitrate &amp; qualité](#93-bitrate--qualite)
- [🎛️ 9.4 Exemples selon GPU](#94-exemples-selon-gpu)

## 10. 🧾 Scripts utiles

- [📌 10.1 PowerShell — Hardsub AMD](#101-powershell--hardsub-amd)
- [📁 10.2 PowerShell — Conversion QSV (lot de MKV)](#102-powershell--conversion-qsv-lot-de-mkv)
- [🐧 10.3 Bash Linux — Conversion massive](#103-bash-linux--conversion-massive)
- [⏱️ 10.4 Mesurer le temps FFmpeg](#104-mesurer-le-temps-ffmpeg)

## 11. 🎨 Formats de Pixel

- [🎛️ 11.1 yuv420p](#111-yuv420p)
- [🎛️ 11.2 yuv420p10le](#112-yuv420p10le)
- [🎨 11.3 NV12](#113-nv12)
- [📦 11.4 Compatibilité encodeurs](#114-compatibilite-encodeurs)
- [🤔 11.5 Pourquoi convertir ?](#115-pourquoi-convertir-)

## 12. 📊 Rate Control

- [🎚️ 12.1 CRF](#121-crf)
- [🎚️ 12.2 CQP](#122-cqp)
- [🎯 12.3 QP I / P / B](#123-qp-i--p--b)
- [📶 12.4 Bitrate CBR/VBR](#124-bitrate-cbrvbr)
- [🧠 12.5 look_ahead](#125-look_ahead)

## 13. 🛑 Troubleshooting Général

- [🟥 13.1 Pixel format unsupported](#131-pixel-format-unsupported)
- [🟥 13.2 Error opening encoder](#132-error-opening-encoder)
- [🟥 13.3 Décodage matériel non utilisé](#133-decodage-materiel-non-utilise)
- [🟥 13.4 Cas HEVC 10 bits](#134-cas-hevc-10-bits)
- [🟥 13.5 Hardsub ne s’applique pas](#135-hardsub-ne-sapplique-pas)
- [🟥 13.6 Problèmes audio](#136-problemes-audio)
- [🟥 13.7 MP4 non compatible](#137-mp4-non-compatible)

## 14. 📚 Annexes

- [📊 14.1 Comparatif GPU](#141-comparatif-gpu)
- [🎧 14.2 Codecs audio MP4](#142-codecs-audio-mp4)
- [⚡ 14.3 Raccourcis FFmpeg](#143-raccourcis-ffmpeg)
- [📝 14.4 Notes personnelles](#144-notes-personnelles)
- [📖 14.5 Glossaire](#145-glossaire)


Ce document est mon **guide personnel ultime** pour FFmpeg.Il regroupe :

## 1.🎯 Introduction générale

## 1.1 Pourquoi j’ai créé ce guide ✍️

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

# 2. 🛠️ Installation & Configuration de FFmpeg

## 2.1 ⬇️ Téléchargement

1. Télécharge FFmpeg (build statique Windows).
2. Extrait le dossier, ex :
   C:\ffmpeg\
3. Vérifie que dans \bin\ il y a :
   - ffmpeg.exe
   - ffprobe.exe
   - ffplay.exe

---

## 2.2 🧩 Ajouter FFmpeg au PATH (Windows)

### 2.2.1 👤 Variables d’environnement utilisateur

1. Menu Démarrer → tape **variables d’environnement**.
2. Clique sur **Modifier les variables d'environnement pour votre compte**.
3. Dans **Path** → Modifier → Nouveau.
4. Ajoute :
   C:\ffmpeg\bin

### 2.2.2 🖥️ Variables système

1. Dans **Variables système**, clique sur **Nouveau**.
2. Nom : FFmpeg
   Valeur : C:\ffmpeg\bin

### 2.2.3 🔍 Vérification

Commande :
ffmpeg -version

---

## 2.3 🧪 Vérifier les encodeurs (CPU/GPU)

ffmpeg -encoders

### Intel QSV :

ffmpeg -encoders | Select-String qsv✔️ Cherche :

- h264_qsv
- hevc_qsv

### NVIDIA NVENC :

ffmpeg -encoders | Select-String nvenc

### AMD AMF :

ffmpeg -encoders | Select-String amf

---

## 2.4 🔧 Vérifier les accélérations matérielles

ffmpeg -hwaccels

Pour Intel HD 520 tu dois voir :

- qsv
- dxva2
- d3d11va

---

## 2.5 ⚙️ Comprendre -hwaccel (accélération matérielle)

| Accélération | GPU     | Utilité            |
| -------------- | ------- | ------------------- |
| qsv            | Intel   | décodage matériel |
| cuda           | NVIDIA  | décodage GPU       |
| dxva2          | Windows | décodage Intel/AMD |
| d3d11va        | Windows | décodage moderne   |
| vaapi          | Linux   | décodage/encodage  |

Encodage contrôlé par :

- `-c:v h264_qsv` (Intel)
- `-c:v h264_nvenc` (NVIDIA)
- `-c:v h264_amf` (AMD)
- `-c:v libx264` (CPU)

---

# 3. 📘 Commandes FFmpeg essentielles

## 3.1 🧱 Structure de base

ffmpeg [options] -i input [filtres] [codecs] output

## 3.2 🎛️ Options fondamentales

- **-i** : entrée
- **-c:v** : codec vidéo
- **-c:a** : codec audio
- **-vf** : filtres vidéo
- **-map** : sélectionner des flux

---

## 3.3 📄 Copier un flux sans réencodage

ffmpeg -i input.mkv -c copy output.mp4

---

## 3.4 🔄 MKV → MP4 sans réencodage

ffmpeg -i IP17.mkv -c copy IP17s.mp4

⚠️ Fonctionne uniquement si :

- vidéo = **H.264**
- audio = **AAC / MP3 / AC3**

---

## 3.5 🚫 Quand le copy échoue (DTS/EAC3/FLAC)

Formats **non compatibles** MP4 :

- ❌ DTS
- ❌ EAC3
- ❌ FLAC
- ❌ Vorbis

Solution :
ffmpeg -i input.mkv -c:v copy -c:a aac -b:a 192k output.mp4

---

# 4. 🧠 Encodage CPU avec libx264

## 4.1 ❗ Pourquoi choisir le CPU ?

- meilleure qualité globale
- filtres ASS/SRT = CPU only
- compatible tout format
- utile si GPU ne gère pas 10-bit

---

## 4.2 🎚️ CRF (qualité)

- 18–20 ⭐ qualité très haute
- 23 🙂 qualité normale
- 26–28 📦 fichier plus petit

---

## 4.3 📈 Presets libx264 (vitesse ↔ qualité)

| Preset    | Vitesse | Qualité  | Taille  |
| --------- | ------- | --------- | ------- |
| ultrafast | 🚀      | 😐 faible | énorme |
| veryfast  | ⚡      | 🙂 ok     | moyen   |
| slow      | 🐢      | 😊 haute  | petit   |
| veryslow  | 🐌      | 🤩 max    | min     |

---

## 4.4 📦 Commandes utiles libx264

### Conversion HEVC → H.264 très rapide

ffmpeg -i IP17.mkv -c:v libx264 -preset ultrafast -crf 23 -c:a copy IP17s.mp4

### Encodage vidéo + audio AAC

ffmpeg -i IP17.mkv -c:v libx264 -preset slow -crf 23 -c:a aac -b:a 192k output.mp4

---

## 4.5 🎵 Réencodage audio AAC

ffmpeg -i input.mkv -c:a aac -b:a 192k output.mp4

# 5. 💠 Encodage matériel Intel Quick Sync (QSV)

## 5.1 💡 Introduction à QSV

Intel Quick Sync Video (QSV) est l’accélération matérielle Intel permettant :

- décodage rapide (hevc_qsv, h264_qsv),
- encodage rapide (h264_qsv),
- faible consommation CPU,
- utile pour gros fichiers HEVC 10-bits (anime, films, raw).

Ton PC (Intel HD 520) **supporte QSV**.

---

## 5.2 🔍 Décodage matériel vs logiciel

### Décodage logiciel :

- FFmpeg utilise ton CPU pour décoder HEVC → lent.
- Bon fallback quand QSV échoue.

### Décodage matériel QSV :

# 5. 💠 Encodage matériel Intel Quick Sync (QSV)

## 5.1 💡 Introduction à QSV

Intel Quick Sync Video (QSV) est l’accélération matérielle Intel qui permet :

- le décodage rapide (`hevc_qsv`, `h264_qsv`),
- l’encodage rapide (`h264_qsv`),
- une consommation CPU faible,
- très utile pour les vidéos HEVC 10 bits (anime, films, raws).

Ton PC (Intel HD 520) **supporte QSV**.

---

## 5.2 🔍 Décodage matériel vs logiciel

### Décodage logiciel (CPU)

- le CPU décode toute la vidéo,
- lent sur les gros HEVC 10 bits,
- utile si QSV n’est pas disponible ou plante.

### Décodage matériel QSV

Option principale : `-c:v hevc_qsv`

Avantages :

- très rapide,
- libère beaucoup le CPU,
- recommandé pour toutes les sources HEVC 10 bits.

---

## 5.3 📹 Encodage `h264_qsv`

Encodage matériel Intel : `-c:v h264_qsv`

Caractéristiques de `h264_qsv` :

- encode uniquement en **8 bits**,
- exige un format de pixel compatible, typiquement **NV12**,
- très rapide,
- parfait pour convertir HEVC → H.264 tout en profitant du GPU Intel.

---

## 5.4 🎞️ Décodage `hevc_qsv`

Décodage matériel HEVC/H.265 : `-c:v hevc_qsv`

À utiliser pour :

- HEVC 1080p 10 bits,
- sources Amazon/Netflix / Blu-ray compressées en HEVC,
- releases fansub type Erai-raws en 10 bits.

---

## 5.5 🔗 Pipeline complet : HEVC 10 bits → H.264 8 bits

Objectif :

- décoder le HEVC 10 bits avec QSV,
- convertir le format de pixel en 8 bits NV12,
- uploader les frames sur le GPU,
- encoder en H.264 avec QSV.

Pipeline complet robuste (idée) :

- `-init_hw_device qsv=hw` → préparation du périphérique QSV
- `-filter_hw_device hw` → les filtres matériels utilisent ce périphérique
- `-c:v hevc_qsv` → décodage matériel HEVC
- `-vf "format=nv12,hwupload"` → conversion en NV12 + upload GPU
- `-c:v h264_qsv` → encodage matériel H.264
- `-b:v 4M` → bitrate vidéo cible (exemple)
- `-c:a copy` → copie audio

---

## 5.6 🎨 Importance du format NV12

Problème classique :

- Les sources HEVC 10 bits utilisent souvent `yuv420p10le` ou formats similaires.
- Le codec `h264_qsv` n’accepte pas ces formats 10 bits.

Solution :

- Forcer la conversion vers `NV12` (8 bits, YUV 4:2:0).

Concept :

- `format=nv12` convertit l’image dans un format 8 bits compatible QSV.
- Sans cette conversion, tu peux obtenir : “Current pixel format is unsupported”.

---

## 5.7 ↕️ `hwupload` / `hwdownload` — Quand et pourquoi ?

- `hwdownload` : récupère les frames de la mémoire GPU vers la mémoire CPU.
- `hwupload` : envoie les frames de la mémoire CPU vers le GPU.

Pourquoi ?

- Les filtres comme `ass=` (hardsub) sont **logiciels** → ils s’appliquent sur des frames gérées par le CPU.
- Après ce filtrage, si tu veux réencoder avec QSV, tu dois renvoyer les frames vers le GPU avec `hwupload`.

Schéma typique (idée de chaîne) :

- décodage matériel QSV → `hwdownload` → `format=nv12` → filtre `ass` → `hwupload` → encodage QSV.

---

## 5.8 ⚡ Commandes QSV rapides (A, B1, B2)

### 🟣 A — Décodage logiciel + encodage QSV

- Décodage : logiciel (CPU)
- Encodage : `h264_qsv`
- Avantage : simple, compatible
- Inconvénient : décodage HEVC lent si grosse source

Idée de commande A :

- `ffmpeg -i input.mkv -c:v h264_qsv -preset veryfast -c:a copy A.mp4`

---

### 🔵 B1 — Full matériel : décodage HEVC + encodage H.264

- Décodage : `hevc_qsv`
- Encodage : `h264_qsv`
- Bitrate fixé (ex : `-b:v 4M`)
- Audio copié

Idée B1 :

- `ffmpeg -c:v hevc_qsv -i input.mkv -c:v h264_qsv -preset veryfast -b:v 4M -c:a copy B1.mp4`

Avantages :

- très rapide,
- presque tout le travail est fait par le GPU.

Limite :

- peut échouer si la conversion de format de pixel n’est pas gérée correctement (cas 10 bits).

---

### 🔵 B2 — Version optimisée avec conversion NV12 (recommandée)

- Ajout de `-vf format=nv12`
- Assure que l’entrée de `h264_qsv` est en NV12 8 bits.

Idée B2 :

- `ffmpeg -c:v hevc_qsv -i input.mkv -vf format=nv12 -c:v h264_qsv -preset veryfast -b:v 4M -c:a copy B2.mp4`

Comparaison B1 vs B2 :

- Sans `format=nv12` (B1) : FFmpeg décide automatiquement du format → peut échouer selon pilotes.
- Avec `format=nv12` (B2) : format forcé → plus stable et plus compatible.

---

## 5.9 🧠 `look_ahead` — optimisation ou latence ?

`-look_ahead` contrôle la fonction de "look-ahead" du codeur QSV.

- `-look_ahead 1` (activé) :

  - le codeur regarde quelques images à l’avance,
  - meilleure qualité visuelle à débit égal,
  - meilleure compression sur mouvements complexes,
  - plus de ressources et plus de latence (pas bon pour du live).
- `-look_ahead 0` (désactivé) :

  - moins de pré-analyse,
  - plus rapide,
  - moins de latence,
  - qualité potentiellement un peu moins optimisée.

Remarque :

- certains presets (ex : très rapides) désactivent `look_ahead` par défaut,
- certains modes de contrôle de débit peuvent l’activer automatiquement.

---

## 5.10 🛑 Erreurs courantes QSV et corrections

### Erreur : `Current pixel format is unsupported`

Cause :

- la vidéo d’entrée est en 10 bits (`yuv420p10le`) alors que `h264_qsv` attend du 8 bits (NV12).

Correction :

- forcer le format :
  - `-vf format=nv12`

---

### Erreur : `Error while opening encoder - maybe incorrect parameters`

Causes possibles :

- résolution non supportée,
- format de pixel incompatible,
- pipeline matériel mal initialisé (manque `init_hw_device` / `filter_hw_device` / `hwupload`).

Correction :

- ajouter :
  - `-init_hw_device qsv=hw`
  - `-filter_hw_device hw`
  - `-vf "format=nv12,hwupload"`

---

# 6. 🟩 Encodage NVIDIA NVENC

## 6.1 💡 Principes

NVENC est le moteur d’encodage matériel NVIDIA.Il permet :

- un encodage H.264 très rapide,
- une bonne qualité,
- une charge CPU très faible.

Codec utilisé : `-c:v h264_nvenc`.

---

## 6.2 🎚️ Contrôle CQ (vs CRF)

Avec NVENC, on utilise généralement `-cq` (Constant Quality) plutôt que CRF.

- Valeurs typiques : 15–28
- `-cq 23` ≈ qualité moyenne correcte
- plus la valeur est basse → meilleure qualité, mais fichier plus gros

---

## 6.3 ⚙️ Presets NVENC

Quelques presets communs :

- `-preset fast`
- `-preset medium`
- `-preset slow`

Plus le preset est lent, meilleure est la compression (donc meilleurs ratio qualité/taille) mais plus l’encodage est long.

---

## 6.4 🚀 Commandes NVENC rapides

Exemple type :

- `ffmpeg -hwaccel cuda -i input.mkv -c:v h264_nvenc -preset fast -cq 23 -c:a copy nvenc.mp4`

Explications rapides :

- `-hwaccel cuda` : utilise le GPU NVIDIA pour décoder,
- `-c:v h264_nvenc` : encode en H.264 via NVENC,
- `-preset fast` : vise la rapidité,
- `-cq 23` : qualité constante,
- `-c:a copy` : audio copié sans réencodage.

---

# 7. 🟥 Encodage matériel AMD AMF/VCE

## 7.1 💬 Présentation

AMF (Advanced Media Framework) est l’API d’encodage matériel pour les GPU AMD (souvent appelé VCE/VCN).

Codec :

- `-c:v h264_amf` pour l’encodage H.264 matériel.

Utilité :

- encodage plus rapide que le CPU,
- moins de charge processeur,
- bonne solution sur PC avec carte AMD.

---

## 7.2 ⚡ d3d11va vs dxva2

Pour le décodage matériel sur Windows avec AMD :

- `-hwaccel dxva2` :

  - API plus ancienne,
  - fonctionne sur beaucoup de cartes.
- `-hwaccel d3d11va` :

  - API plus moderne,
  - souvent plus stable et plus performante,
  - recommandé si ta carte supporte bien Direct3D 11.

Exemple :

- `ffmpeg -hwaccel d3d11va -i input.mkv ...`

---

## 7.3 🎛️ Mode CQP (Constant Quantization Parameter)

Avec AMD AMF, on peut utiliser un contrôle du débit basé sur la quantification constante :

- `-rc cqp` : active le mode CQP.
- Puis on règle les QP :
  - `-qp_i` : QP pour les images I (keyframes),
  - `-qp_p` : QP pour les images P (prédictives),
  - `-qp_b` : QP pour les images B (bidirectionnelles).

---

## 7.4 🎯 Paramètres `qp_i` / `qp_p` / `qp_b`

Exemple de valeurs équilibrées :

- `-qp_i 22` : qualité relativement haute sur les keyframes,
- `-qp_p 25` : un peu plus compressé pour les P-frames,
- `-qp_b 27` : le plus compressé pour les B-frames.

Idée :

- plus la valeur est haute → plus la compression est forte → plus la qualité baisse (mais fichiers plus légers).

---

## 7.5 🎚️ Compatibilité 8/10 bits

Sur beaucoup de GPU AMD :

- l’encodage 10 bits peut être limité/non supporté,
- le décodage HEVC 10 bits via `d3d11va` peut fonctionner, mais l’encodage `h264_amf` attend souvent du 8 bits.

Solution :

- forcer le format 8 bits avec :
  - `-pix_fmt yuv420p`

Cette option convertit la vidéo en 8 bits avant encodage.

---

## 7.6 🛠️ Commandes AMD pratiques

### Encodage AMD avec hardsub ASS

Exemple logique :

- décodage matériel (`-hwaccel dxva2`),
- filtre ASS (`-vf "ass=F.ass"`),
- encodage H.264 AMF,
- CQP + QP réglés,
- audio copié.

Idée de chaîne :

- `ffmpeg -hwaccel dxva2 -i "video.mp4" -vf "ass=subs.ass" -c:v h264_amf -quality speed -rc cqp -qp_i 22 -qp_p 25 -qp_b 27 -c:a copy output.mp4`

---

### Conversion H.265 → H.264 avec AMD + conversion 8 bits

- `ffmpeg -hwaccel d3d11va -i FF.mp4 -pix_fmt yuv420p -c:v h264_amf -c:a aac -b:a 192k FF1sub.mp4`

Explications :

- `-hwaccel d3d11va` : décodage matériel Direct3D 11,
- `-pix_fmt yuv420p` : conversion forcée en 8 bits,
- `-c:v h264_amf` : encodage matériel AMD H.264,
- `-c:a aac -b:a 192k` : audio AAC compatible MP4.

## 8. ✨ Hardsub — Sous-titres incrustés

### 8.1 📜 ASS vs SRT

#### Format ASS

- styles avancés
- positionnement fin
- bordures / contours / animations
- parfait pour fansubs & karaokés

Limite : filtrage logiciel (via `ass=`) ⇒ plus lent.

#### Format SRT

- simple
- universel
- hyper compatible

Limite : pas de styling avancé.

---

### 8.2 📊 Lire les pistes d’un MKV

Commande :

```
ffmpeg -i input.mkv
```

Exemple de résultat :

```
Stream #0:0: Video: hevc (Main 10)
Stream #0:1: Audio: eac3
Stream #0:2: Subtitle: ass
Stream #0:3: Subtitle: ass
Stream #0:4: Subtitle: srt
```

---

### 8.3 🎯 Identifier la piste (si)

FFmpeg utilise `si=` pour sélectionner une piste sous-titres.

Correspondances typiques :

- piste 0:2 → si=0
- piste 0:3 → si=1
- piste 0:4 → si=2

---

### 8.4 📝 Hardsub d’un fichier ASS externe

#### CPU (libx264)

```
ffmpeg -i video.mp4 -vf "ass=subs.ass" -c:v libx264 -preset fast -c:a copy out.mp4
```

#### Intel QSV (nécessite hwdownload)

```
ffmpeg -hwaccel qsv -i video.mp4 \
-vf "hwdownload,format=nv12,ass=subs.ass,hwupload" \
-c:v h264_qsv -preset fast -c:a copy out.mp4
```

---

### 8.5 🎞️ Hardsub à partir des sous-titres internes MKV

#### CPU (libx264)

```
ffmpeg -i input.mkv -vf "subtitles=input.mkv:si=0" \
-c:v libx264 -preset fast -b:v 4M -c:a copy hardsub.mp4
```

#### Intel QSV

```
ffmpeg -i input.mkv -map 0:v -map 0:a \
-vf "subtitles=input.mkv:si=0" \
-c:v h264_qsv -preset veryfast -c:a aac hardsub_qsv.mp4
```

---

### 8.6 ⚙️ Pipeline complet Hardsub Intel QSV (HEVC 10 bits → H.264)

```
ffmpeg -init_hw_device qsv=hw -filter_hw_device hw \
-c:v hevc_qsv -i input.mkv \
-vf "hwdownload,format=nv12,ass=subs.ass,hwupload" \
-c:v h264_qsv -preset fast -c:a copy out.mp4
```

Étapes internes :

1. Décodage matériel HEVC (QSV)
2. hwdownload → passage GPU → CPU
3. format=nv12 → conversion vers un format logiciel
4. ass=subs.ass
5. hwupload → retour GPU
6. Encodage matériel QSV

---

### 8.7 🔥 Hardsub AMD (AMF)

```
ffmpeg -hwaccel dxva2 -i input.mp4 -vf "ass=subs.ass" \
-c:v h264_amf -quality speed -rc cqp \
-qp_i 22 -qp_p 25 -qp_b 27 -c:a copy out_amf.mp4
```

---

### 8.8 💚 Hardsub NVIDIA NVENC

```
ffmpeg -hwaccel cuda -i input.mkv \
-vf "subtitles=input.mkv:si=0" \
-c:v h264_nvenc -preset fast -cq 23 -c:a copy hardsub_nvenc.mp4
```

---

### 8.9 🔽 Intel — Cas où hwdownload + format=nv12 sont obligatoires

Pourquoi ?

Parce que :

- les filtres comme `ass=` doivent être appliqués sur des frames **CPU**,
- QSV décode en format **GPU** → incompatible,
- il faut donc redescendre les frames.

Pipeline à respecter :

```
hwdownload → format=nv12 → ass → hwupload
```

Exemple :

```
ffmpeg -hwaccel qsv -c:v hevc_qsv -i input.mkv \
-vf "hwdownload,format=nv12,ass=subs.ass,hwupload" \
-c:v h264_qsv -preset fast out.mp4
```

---

### 8.10 🛑 Erreurs courantes & solutions

#### ❌ “Current pixel format is unsupported”

Cause : la vidéo entrée est en 10 bits, QSV n’accepte que NV12 8 bits.

Fix :

```
-vf format=nv12
```

#### ❌ “Filter ass requires software frames”

Cause : filtre appliqué sur images GPU.

Fix :

```
hwdownload,format=nv12,ass=...,hwupload
```

#### ❌ Sous-titre incorrect

Fix :

```
ffmpeg -i input.mkv
```

---

# 9. 🎞️ Conversion vidéo complète

## 9.1 🔄 Conversion HEVC → H.264

### CPU (libx264)

```
ffmpeg -i input.mkv -c:v libx264 -preset fast -crf 23 -c:a copy out.mp4
```

### Intel QSV

```
ffmpeg -c:v hevc_qsv -i input.mkv -vf format=nv12 \
-c:v h264_qsv -preset veryfast -b:v 4M -c:a copy qsv.mp4
```

### AMD

```
ffmpeg -hwaccel d3d11va -i input.mkv -pix_fmt yuv420p \
-c:v h264_amf -c:a aac -b:a 192k amd.mp4
```

### NVIDIA NVENC

```
ffmpeg -hwaccel cuda -i input.mkv \
-c:v h264_nvenc -preset fast -cq 23 -c:a copy nvenc.mp4
```

---

## 9.2 🎧 Conversion audio EAC3/DTS → AAC

```
ffmpeg -i input.mkv -c:v copy -c:a aac -b:a 192k fixed.mp4
```

---

## 9.3 📉 Bitrate & qualité

### Bitrate constant (CBR)

```
-b:v 4M
```

### Qualité constante (CRF – libx264)

- 18–20 : haute qualité
- 23 : normal
- 26–28 : léger

### NVENC (Qualité constante)

```
-cq 23
```

### QSV

```
-b:v 4M
```

---

## 9.4 🎛️ Exemples selon GPU

### Intel QSV

```
ffmpeg -c:v hevc_qsv -i input.mkv -vf format=nv12 \
-c:v h264_qsv -preset veryfast -b:v 4M -c:a copy intel.mp4
```

### AMD

```
ffmpeg -hwaccel dxva2 -i input.mp4 -pix_fmt yuv420p \
-c:v h264_amf -quality speed -c:a aac amd_out.mp4
```

### NVIDIA

```
ffmpeg -hwaccel cuda -i input.mkv \
-c:v h264_nvenc -preset fast -cq 23 -c:a copy nvenc.mp4
```

---

# 10. 🧾 Scripts utiles

## 10.1 PowerShell — Hardsub AMD

```
ffmpeg -hwaccel dxva2 -i "SL8.mp4" -vf "ass=F.ass" \
-c:v h264_amf -quality speed -rc cqp \
-qp_i 22 -qp_p 25 -qp_b 27 -c:a copy "SL8sub.mp4"
```

---

## 10.2 PowerShell — Conversion QSV (lot de MKV)

```
Get-ChildItem *.mkv | ForEach-Object {
    $input = $_.FullName
    $output = $_.BaseName + ".mp4"
    ffmpeg -hwaccel qsv -c:v h264_qsv -i "$input" \
    -c:v h264_qsv -c:a aac -b:a 192k "$output"
}
```

---

## 10.3 Bash Linux — Conversion massive

```
#!/bin/bash
for file in *.mkv; do
    output="${file%.mkv}.mp4"
    ffmpeg -hwaccel qsv -c:v h264_qsv -i "$file" \
    -c:v h264_qsv -c:a aac -b:a 192k "$output"
done
```

---

## 10.4 ⏱️ Mesurer le temps FFmpeg

### PowerShell

```
Measure-Command { ffmpeg -i input.mkv -c:v libx264 out.mp4 }
```

### Linux / Mac / Git Bash

```
time ffmpeg -i input.mkv -c:v libx264 out.mp4
```

## 11. 🎨 Formats de Pixel (Pixel Format)

Les formats de pixel définissent comment les couleurs sont stockées dans la mémoire.
FFmpeg les utilise constamment, et les encodeurs matériels (QSV, NVENC, AMF) ont des exigences strictes.

---

### 11.1 🎛️ yuv420p (8 bits)

- format vidéo standard
- totalement compatible avec :
  - libx264
  - NVENC
  - AMF
  - QSV (encodage)
- idéal pour H.264 / MP4
- utilisé par 95% des vidéos internet

---

### 11.2 🎛️ yuv420p10le (10 bits)

- utilisé pour HEVC 10 bits
- non compatible avec :
  - h264_qsv
  - h264_amf (selon GPU)
  - h264_nvenc (sauf cartes récentes)
- nécessite conversion → yuv420p ou NV12

---

### 11.3 🎨 NV12 (8 bits)

- format préféré des encodeurs matériels
- mémoire optimisée pour GPU
- QSV : **obligatoire**
- NVENC / AMF : recommandé

Conversion :

```
-vf format=nv12
```

---

### 11.4 📦 Compatibilité des encodeurs

| Format      | libx264 | h264_qsv | h264_nvenc | h264_amf |
| ----------- | ------- | -------- | ---------- | -------- |
| yuv420p     | ✔️    | ✔️     | ✔️       | ✔️     |
| yuv420p10le | ✔️    | ❌       | ⚠️*      | ⚠️*    |
| NV12        | ✔️    | ✔️**   | ✔️       | ✔️     |

Notes :

- ❌ QSV refuse le 10 bits pour H.264
- ⚠️ NVENC/AMF acceptent le 10 bits surtout avec HEVC
- ✔️ NV12 = format magique pour tout matériel

---

### 11.5 🤔 Pourquoi convertir ?

Conversion obligatoire si :

- la source est en 10 bits,
- l’encodeur exige du 8 bits (QSV H.264),
- un filtre vidéo CPU doit être appliqué (ex : hardsub ASS).

Pipeline typique Intel :

```
hwdownload → format=nv12 → ass → hwupload
```

---

# 12. 📊 Rate Control (Gestion du débit vidéo)

Les méthodes de contrôle de qualité / taille.

---

### 12.1 🎚️ CRF (Constant Rate Factor)

Pour libx264 :

- 18–20 → haute qualité
- 23 → valeur défaut
- 26–28 → petit fichier

Commande :

```
-crf 23
```

---

### 12.2 🎚️ CQP (Constant Quantization Parameter)

Utilisé par :

- h264_amf
- h264_nvenc (mode cq)
- h264_qsv (mode CQP)

Paramètres :

- QP I : images I (plus important)
- QP P : images P
- QP B : images B

Exemple AMF :

```
-rc cqp -qp_i 22 -qp_p 25 -qp_b 27
```

---

### 12.3 🎯 QP I / P / B

Résumé :

- QP bas = meilleure qualité
- QP haut = fichier plus léger

Importance :

- QP_I > QP_P > QP_B
  (I doit être le plus propre)

---

### 12.4 📶 Bitrate CBR/VBR

#### CBR (débit constant)

```
-b:v 4M
```

- parfait pour compatibilité streaming
- taille prévisible

#### VBR (variable)

- meilleure qualité
- taille plus efficace

---

### 12.5 🧠 look_ahead (en détail)

- permet d’analyser les images futures
- améliore la compression
- augmente la latence
- consomme plus de GPU

Pour activer :

```
-look_ahead 1
```

Pour désactiver :

```
-look_ahead 0
```

---

# 13. 🛑 Troubleshooting Général

---

### 13.1 🟥 Current pixel format is unsupported

Cause :

- source en 10 bits incompatible

Fix :

```
-vf format=nv12
```

---

### 13.2 🟥 Error opening encoder

Causes :

- résolution non supportée
- bitrate invalide
- pixel format non supporté

Checklist :

- vérifier `ffmpeg -encoders`
- ajouter `-pix_fmt yuv420p` ou `format=nv12`

---

### 13.3 🟥 Décodage matériel non utilisé

Fix :

```
-hwaccel qsv
-hwaccel cuda
-hwaccel dxva2
-hwaccel d3d11va
```

---

### 13.4 🟥 Cas HEVC 10 bits → H.264 QSV

QSV refuse :

- 10 bits
- yuv420p10le

Pipeline obligatoire :

```
ffmpeg -c:v hevc_qsv -i input.mkv \
-vf "format=nv12" \
-c:v h264_qsv out.mp4
```

---

### 13.5 🟥 Hardsub ne s’applique pas

Cause :

- filtre `ass=` ne fonctionne que sur frames CPU.

Fix :

```
hwdownload,format=nv12,ass=...,hwupload
```

---

### 13.6 🟥 Problèmes audio EAC3 / DTS

MP4 incompatible.

Fix :

```
-c:a aac -b:a 192k
```

---

### 13.7 🟥 MP4 non compatible (erreur lecteur)

Fix :

```
-pix_fmt yuv420p
```

---

# 14. 📚 Annexes — Tableaux récapitulatifs

---

### 14.1 📊 Tableau comparatif GPU (Intel / AMD / NVIDIA)

| Fonction               | Intel QSV      | NVIDIA NVENC | AMD AMF  |
| ---------------------- | -------------- | ------------ | -------- |
| Décodage HEVC 10 bits | ✔️           | ✔️         | ✔️     |
| Encodage H.264 8 bits  | ✔️           | ✔️         | ✔️     |
| Encodage H.264 10 bits | ❌             | ⚠️         | ⚠️     |
| Format préféré      | NV12           | NV12         | NV12     |
| Hardsub sur GPU        | ❌             | ✔️         | ✔️     |
| Rapidité              | Très élevée | Élevée     | Élevée |

---

### 14.2 🎧 Codecs audio compatibles MP4

#### Compatibles

- AAC ✔️
- MP3 ✔️
- ALAC ✔️
- AC3 ⚠️
- Opus ⚠️

#### Incompatibles

- EAC3 ❌
- DTS ❌
- FLAC ❌
- Vorbis ❌

---

### 14.3 ⚡ Raccourcis FFmpeg

- copier sans réencoder :
  ```
  -c copy
  ```
- choisir piste sous-titres :
  ```
  -vf "subtitles=input.mkv:si=0"
  ```
- forcer 8 bits :
  ```
  -pix_fmt yuv420p
  ```
- forcer NV12 :
  ```
  -vf format=nv12
  ```

---

### 14.4 📝 Notes personnelles

- Toujours vérifier codecs via :
  ```
  ffmpeg -i input.mkv
  ```
- Si problème → forcer NV12.
- Si hardsub + GPU Intel → pipeline hwdownload / hwupload.

---

### 14.5 📖 Glossaire

- **QSV** : Quick Sync Video (Intel)
- **NVENC** : encodeur matériel NVIDIA
- **AMF** : encodeur matériel AMD
- **CRF** : qualité constante CPU
- **CQP** : qualité constante GPU
- **NV12** : format idéal GPU
- **10 bits** : HEVC HDR, incompatible H.264 QSV
