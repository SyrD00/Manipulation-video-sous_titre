# 🎥 FFmpeg – Conversion & Ré-encodage rapide (CPU / GPU)

Un guide complet et pratique pour convertir, ré-encoder ou incruster des sous-titres dans des vidéos en utilisant **FFmpeg**, avec ou sans accélération matérielle (Intel, NVIDIA, AMD).

---

## 📖 Sommaire
- [⚡ Conversion simple (sans ré-encodage)](#-conversion-simple-sans-ré-encodage)
- [🧠 Ré-encodage CPU (libx264)](#-ré-encodage-cpu-libx264)
- [💽 Ré-encodage matériel Intel (Quick Sync Video – QSV)](#-ré-encodage-matériel-intel-quick-sync-video--qsv)
  - [Vérifier la compatibilité QSV](#-vérifier-la-compatibilité-qsv)
  - [Commandes QSV de base](#-commandes-qsv-de-base)
  - [Conversion 10 bits → 8 bits (NV12)](#-conversion-10-bits--8-bits-nv12)
  - [Look-Ahead (optimisation qualité)](#-look-ahead-optimisation-qualité)
- [🈶 Incrustation de sous-titres (hardsub)](#-incrustation-de-sous-titres-hardsub)
- [⏱️ Mesurer le temps d’exécution](#️-mesurer-le-temps-dexécution)
- [🧩 Autres GPU : NVIDIA / AMD](#-autres-gpu--nvidia--amd)
- [🧰 Conversion en lot (Batch)](#-conversion-en-lot-batch)
- [✅ Résumé rapide](#-résumé-rapide)

---

## ⚡ Conversion simple (sans ré-encodage)

```bash
ffmpeg -i IP17.mkv -c copy IP17s.mp4
```

### 🧩 Détails
- `-i input.mkv` : fichier source  
- `-c copy` : copie vidéo et audio sans ré-encodage  
- ⚠️ Ne fonctionne que si les codecs sont compatibles MP4 (H.264 + AAC par ex.)

---

## 🧠 Ré-encodage CPU (libx264)

```bash
ffmpeg -i IP17.mkv -c:v libx264 -preset ultrafast -crf 23 -c:a copy IP17s.mp4
```

### 🔍 Explications
| Option | Description |
|--------|--------------|
| `-c:v libx264` | encodeur H.264 universel (CPU) |
| `-crf 23` | qualité constante (18–28, plus bas = meilleure qualité) |
| `-preset ultrafast` | vitesse max, taille plus grande |
| `-c:a copy` | copie audio sans perte |

### 📊 Comparatif de presets
| Preset | Vitesse | Qualité | Taille |
|--------|----------|----------|--------|
| ultrafast | 🚀 Très rapide | 😐 Moyenne | 📦 Grande |
| medium | ⚖️ Moyenne | 😊 Bonne | 📦 Moyenne |
| slow | 🐢 Lent | 😍 Excellente | 📦 Petite |

💡 Recommandé : `-preset slow -crf 22` (excellent compromis)

---

## 💽 Ré-encodage matériel Intel (Quick Sync Video – QSV)

### 🔎 Vérifier la compatibilité QSV
**Linux**
```bash
ffmpeg -encoders | grep qsv
```
**Windows**
```powershell
ffmpeg -encoders | Select-String qsv
```

Doit afficher :
```
V..... h264_qsv   Intel Quick Sync H.264 encoder
V..... hevc_qsv   Intel Quick Sync HEVC encoder
```

---

### 🔧 Commandes QSV de base

#### A. Encodage matériel H.264 (audio copié)
```bash
ffmpeg -i IP17.mkv -c:v h264_qsv -preset veryfast -c:a copy IP17s.mp4
```

#### B. Décodage + encodage matériel (HEVC → H.264)
```bash
ffmpeg -c:v hevc_qsv -i IP17.mkv -c:v h264_qsv -preset veryfast -b:v 4M -c:a copy IP17s2.mp4
```

#### B2. Version plus stable (conversion NV12)
```bash
ffmpeg -c:v hevc_qsv -i IP17.mkv -vf format=nv12 -c:v h264_qsv -preset veryfast -b:v 4M -c:a copy IP17s2.mp4
```

| Option | Sans `-vf format=nv12` | Avec `-vf format=nv12` |
|---------|------------------------|--------------------------|
| Compatibilité | variable | ✅ très stable |
| Performances | identiques | légèrement plus robustes |

---

### 🔧 Conversion 10 bits → 8 bits (NV12)
Pour les sources HEVC 10 bits, QuickSync requiert un passage en NV12 :

```bash
ffmpeg -init_hw_device qsv=hw -filter_hw_device hw \
-c:v hevc_qsv -i IP17.mkv \
-vf "format=nv12,hwupload" \
-c:v h264_qsv -preset veryfast -b:v 4M -c:a copy IP17_fixed.mp4
```

🧠 Pipeline :
- Décodage matériel HEVC  
- Conversion en 8 bits (NV12)  
- Upload GPU  
- Encodage H.264 matériel  
- Audio copié  

---

### ⚙️ Look-Ahead (optimisation qualité)

| Mode | Description |
|------|--------------|
| `-look_ahead 1` | meilleure qualité, plus lent |
| `-look_ahead 0` | plus rapide, moins précis |

---

## 🈶 Incrustation de sous-titres (hardsub)

### 1️⃣ Identifier la piste
```bash
ffmpeg -i IP17.mkv
```
➡️ Note le numéro `Stream #0:x` du sous-titre voulu.

### 2️⃣ Graver le sous-titre

#### CPU (libx264)
```bash
ffmpeg -i IP17.mkv -vf "subtitles=IP17.mkv:si=0" -c:v libx264 -preset fast -b:v 4M -c:a copy IP17_hardsub.mp4
```

#### GPU Intel (QSV)
```bash
ffmpeg -i IP17.mkv -map 0:v -map 0:a -vf "subtitles=IP17.mkv:si=2" -c:v h264_qsv -preset veryfast -c:a aac IP17_hardsub.mp4
```

---

## ⏱️ Mesurer le temps d’exécution

### Windows PowerShell
```powershell
Measure-Command { ffmpeg -i IP17.mkv -c:v h264_qsv -b:v 4M -c:a copy out.mp4 }
```

### Linux/macOS
```bash
time ffmpeg -i IP17.mkv -c:v h264_qsv -b:v 4M -c:a copy out.mp4
```

---

## 🧩 Autres GPU : NVIDIA / AMD

### 🟩 NVIDIA (NVENC)
```bash
ffmpeg -hwaccel cuda -i IP17.mkv -c:v h264_nvenc -preset fast -cq 23 -c:a copy IP17s.mp4
```

### 🟥 AMD (AMF)
```bash
ffmpeg -hwaccel dxva2 -i IP17.mkv -c:v h264_amf -quality speed -c:a copy IP17s.mp4
```

| GPU | Accélération | Encodeur | OS |
|------|--------------|-----------|----|
| Intel | `qsv` | `h264_qsv` | ✅ Windows / Linux |
| NVIDIA | `cuda` | `h264_nvenc` | ✅ Windows / Linux |
| AMD | `dxva2` | `h264_amf` | ⚙️ Windows |

---

## 🧰 Conversion en lot (Batch)

### 🪟 PowerShell
```powershell
Get-ChildItem *.mkv | ForEach-Object {
  $input = $_.FullName
  $output = $_.BaseName + ".mp4"
  ffmpeg -hwaccel qsv -c:v h264_qsv -i "$input" -c:v h264_qsv -c:a aac -b:a 192k "$output"
}
```

### 🐧 Bash
```bash
#!/bin/bash
for file in *.mkv; do
  output="${file%.mkv}.mp4"
  ffmpeg -hwaccel qsv -c:v h264_qsv -i "$file" -c:v h264_qsv -c:a aac -b:a 192k "$output"
done
```

---

## ✅ Résumé rapide

| Objectif | Commande recommandée |
|-----------|----------------------|
| Conversion rapide sans ré-encodage | `ffmpeg -i in.mkv -c copy out.mp4` |
| Ré-encodage CPU universel | `ffmpeg -i in.mkv -c:v libx264 -crf 23 -preset slow -c:a aac out.mp4` |
| Accélération Intel QSV | `ffmpeg -c:v hevc_qsv -i in.mkv -vf format=nv12 -c:v h264_qsv -b:v 4M -c:a copy out.mp4` |
| NVIDIA NVENC | `ffmpeg -hwaccel cuda -i in.mkv -c:v h264_nvenc -preset fast -cq 23 -c:a copy out.mp4` |
| AMD AMF | `ffmpeg -hwaccel dxva2 -i in.mkv -c:v h264_amf -quality speed -c:a copy out.mp4` |

---

💡 **Conseil final :**
> Pour un équilibre optimal sur PC Intel :  
> `ffmpeg -c:v hevc_qsv -i input.mkv -vf format=nv12 -c:v h264_qsv -b:v 4M -preset veryfast -c:a copy output.mp4`

---
🧾 Auteur : Sebastien Tallman  
🔗 Licence : Libre utilisation / partage (crédit apprécié)
