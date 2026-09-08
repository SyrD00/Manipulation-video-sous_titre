# Guide Complet & Benchmark FFmpeg : Conversion 16:9 vers 9:16 avec Arrière-Plan Flou

Ce guide documente en détail la conversion automatique d'une vidéo horizontal (16:9) vers un format vertical (9:16 - Short / Reel / TikTok) avec un arrière-plan flouté, en expliquant la structure des filtres, l'optimisation des performances (CPU vs GPU QSV / NVENC), et les résultats de benchmark.

---

## 📑 Table des Matières
1. [Vue d'ensemble & Structure de la commande](#1-vue-densemble--structure-de-la-commande)
2. [Explication ultra simple (L'analogie du sandwich)](#2-explication-ultra-simple-lanalogie-du-sandwich)
3. [Compréhension des Mathématiques & Variables (W, H vs w, h)](#3-compréhension-des-mathématiques--variables-w-h-vs-w-h)
4. [Optimisation de la vitesse & Méthodes d'encodage](#4-optimisation-de-la-vitesse--méthodes-dencodage)
5. [Ajustement de l'intensité du Flou](#5-ajustement-de-lintensité-du-flou)
6. [Benchmark & Comparatif de Performance (CPU vs Intel QSV vs NVENC)](#6-benchmark--comparatif-de-performance-cpu-vs-intel-qsv-vs-nvenc)

---

## 1. Vue d'ensemble & Structure de la commande

La commande principale permet d'adapter une vidéo paysage en vertical 1080x1920 sans bandes noires, en remplissant le fond par une version agrandie et floutée de la vidéo source.

```bash
ffmpeg -i "eclair tac.mp4" -filter_complex "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=30:15[bg];[0:v]scale=1080:-1[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2" -c:a copy "out_eclair_tac.mp4"
```

### Décomposition des éléments de base :
- `ffmpeg` : Lance l'exécutable FFmpeg.
- `-i "eclair tac.mp4"` : Fichier d'entrée (*input*).
- `-filter_complex "..."` : Chaîne de filtres complexes exécutés en parallèle.
- `-c:a copy` : Copie le flux audio original tel quel (pas de réencodage audio = vitesse maximale et aucune perte de qualité).
- `"out_eclair_tac.mp4"` : Nom du fichier vidéo généré.

---

## 2. Explication ultra simple (L'analogie du sandwich)

En résumé, on demande à FFmpeg d'effectuer 3 étapes :
1. **Étape 1 : Le fond flou (`[bg]`)** -> On étire la vidéo pour remplir le canvas 1080x1920 (`scale`), on découpe ce qui dépasse (`crop`), et on applique un flou (`boxblur` ou `gblur`).
2. **Étape 2 : La vidéo centrale (`[fg]`)** -> On adapte la largeur de la vidéo à 1080 pixels (`scale=1080:-1`) tout en laissant FFmpeg calculer la hauteur automatique pour garder le ratio 16:9 sans déformation.
3. **Étape 3 : L'assemblage (`overlay`)** -> On pose la vidéo nette (`[fg]`) par-dessus le fond flou (`[bg]`), centrée au milieu.

### Abréviations courantes
| Abréviation | Terme complet | Description |
| :--- | :--- | :--- |
| `-i` | Input | Fichier source |
| `[0:v]` | First Stream Video | Le premier flux vidéo du fichier source (index 0) |
| `[bg]` | Background | Arrière-plan flou |
| `[fg]` | Foreground | Premier plan (vidéo nette au centre) |
| `W`, `H` | Main Width / Height | Largeur et Hauteur du canvas de fond (1080 x 1920) |
| `w`, `h` | Overlay Width / Height | Largeur et Hauteur de la vidéo centrale nette |

---

## 3. Compréhension des Mathématiques & Variables (W, H vs w, h)

Lors de la superposition (`overlay`), FFmpeg utilise des variables pour positionner précisément la vidéo :
- **Majuscules (`W`, `H`)** = Taille de la grande image de fond ($W = 1080$, $H = 1920$).
- **Minuscules (`w`, `h`)** = Taille de la vidéo du milieu ($w = 1080$, $h pprox 607$ pour du 16:9).

### Formules de centrage :
- **Axe Horizontal ($X$)** : `(W - w) / 2`  
  $ightarrow (1080 - 1080) / 2 = 0$ (La vidéo s'aligne exactement sur les bords latéraux).
- **Axe Vertical ($Y$)** : `(H - h) / 2`  
  $ightarrow (1920 - 607) / 2 = 656.5$ (FFmpeg décale la vidéo de 656.5 pixels vers le bas pour la placer exactement au centre vertical).

---

## 4. Optimisation de la vitesse & Méthodes d'encodage

Pour accélérer l'exécution de la commande au maximum :

1. **Activer le multi-threading CPU** : Ajouter `-threads 0` pour utiliser 100% des cœurs processeur disponibles.
2. **Utiliser un preset x264 ultra rapide** : Utiliser `-preset superfast` ou `-preset ultrafast`.
3. **Remplacer `boxblur` par `gblur`** : Le filtre gaussien optimisé (`gblur=sigma=20`) est nettement plus rapide à calculer sur les CPU récents.

### Commande Optimisée CPU (Recommandée)
```powershell
ffmpeg -threads 0 -i "eclair tac.mp4" -filter_complex "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=20[bg];[0:v]scale=1080:-1[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2" -c:v libx264 -preset superfast -crf 23 -c:a copy "out_eclair_tac.mp4" -y
```

---

## 5. Ajustement de l'intensité du Flou

### Avec le filtre `gblur` (Recommandé) :
Contrôlé par le paramètre `sigma` (`gblur=sigma=X`) :
- **`sigma=10`** : Flou léger (silhouette arrière-plan bien lisible).
- **`sigma=20`** : Flou standard (équilibre visuel idéal).
- **`sigma=45`** : Flou intense (fond très diffus/abstrait).

### Avec le filtre `boxblur` :
Contrôlé par le rayon (`boxblur=X:15`) :
- **`boxblur=10:15`** : Léger
- **`boxblur=30:15`** : Standard
- **`boxblur=60:15`** : Fort

---

## 6. Benchmark & Comparatif de Performance

Voici les mesures d'exécution obtenues avec `Measure-Command` dans PowerShell sur un extrait de test :

### Commandes de Benchmark
- **Mode CPU (libx264)** :
  ```powershell
  Measure-Command { ffmpeg -threads 0 -i "eclair tac.mp4" -filter_complex "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=20[bg];[0:v]scale=1080:-1[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2" -c:v libx264 -preset superfast -crf 23 -c:a copy "out_cpu.mp4" -y }
  ```
- **Mode Intel QuickSync (h264_qsv)** :
  ```powershell
  Measure-Command { ffmpeg -threads 0 -i "eclair tac.mp4" -filter_complex "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=20[bg];[0:v]scale=1080:-1[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2" -c:v h264_qsv -preset 7 -global_quality 23 -c:a copy "out_qsv.mp4" -y }
  ```
- **Mode Nvidia NVENC (h264_nvenc)** :
  ```powershell
  Measure-Command { ffmpeg -threads 0 -i "eclair tac.mp4" -filter_complex "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=20[bg];[0:v]scale=1080:-1[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2" -c:v h264_nvenc -preset p1 -cq 23 -c:a copy "out_nvenc.mp4" -y }
  ```

### Table Comparative des Résultats

| Mode d'encodage | Preset / Option | Temps d'exécution | Débit (Speed) | Remarques & Usage recommandé |
| :--- | :--- | :--- | :--- | :--- |
| **CPU (`libx264`)** | `-preset superfast` | **1,13 s** | **0.563x** | **Le plus rapide sur les courts clips.** Évite les transferts mémoire RAM CPU $ightarrow$ VRAM GPU. |
| **Intel QSV (`h264_qsv`)** | `-preset 7` | **2,45 s** | **0.202x** | Recommandé pour les **longs traitements** afin de décharger le CPU et éviter la surchauffe. |
| **Intel QSV (`h264_qsv`)** | `-preset veryfast` | **2,69 s** | **0.183x** | Surcoût d'initialisation de l'API matériel QSV sur les très petits fichiers. |
| **Nvidia NVENC (`h264_nvenc`)**| `-preset p1` | *Variable* | *N/A* | Nécessite un GPU Nvidia dédié et le pilote CUDA (`nvcuda.dll`). |

### Synthèse & Conclusion
1. **Pour la vitesse pure sur de courts clips** : Le mode **CPU (`libx264 -preset superfast`)** est l'option la plus performante car il n'impose aucun transfert aller-retour entre la RAM système et le processeur graphique.
2. **Pour les traitements par lots ou les vidéos longues** : L'accélération matérielle **Intel QSV** ou **Nvidia NVENC** permet d'encoder sans faire chauffer le processeur principal.
