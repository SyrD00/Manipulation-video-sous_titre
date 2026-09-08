# 🎥 Conversion Vidéo Automatisée 16:9 ➔ 9:16 (FFmpeg Intel QSV)

Ce projet contient un script PowerShell permettant de convertir automatiquement un dossier entier de vidéos horizontales (16:9) au format vertical (9:16) pour Shorts, Reels et TikTok, tout en conservant la vidéo originale centrée sur un arrière-plan flouté.

---

## 🚀 Prérequis

1. **FFmpeg** installé et accessible dans le PATH du système.
2. Un processeur Intel avec **Intel QuickSync Video (QSV)** activé pour l'accélération matérielle.
3. **PowerShell** (intégré par défaut sous Windows).

---

## 📁 Installation & Utilisation

1. Placez le fichier `convert_qsv.ps1` directement dans le dossier contenant les vidéos `.mp4` à traiter.
2. Ouvrez une fenêtre PowerShell dans ce dossier.
3. *(Si c'est la première fois)* Autorisez l'exécution des scripts locaux :
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
   ```
4. Exécutez le script :
   ```powershell
   .\convert_qsv.ps1
   ```

---

## 📜 Code du Script (`convert_qsv.ps1`)

```powershell
# Script PowerShell de traitement vidéo par lot avec Intel QSV et chronométrage

# 1. Sélection de toutes les vidéos .mp4 ne commençant pas déjà par "out_"
$videos = Get-ChildItem *.mp4 | Where-Object { $_.Name -notlike "out_*" }

if ($videos.Count -eq 0) {
    Write-Host "Aucune vidéo à traiter dans ce dossier." -ForegroundColor Yellow
    exit
}

Write-Host "Trouvé $($videos.Count) vidéo(s) à traiter avec Intel QSV." -ForegroundColor Cyan
Write-Host "--------------------------------------------------------"

# 2. Chronométrage global du traitement
$tempsTotal = Measure-Command {
    foreach ($video in $videos) {
        $fichierSortie = "out_qsv_$($video.Name)"
        Write-Host "Traitement en cours : $($video.Name) -> $fichierSortie" -ForegroundColor Green

        # Exécution de la commande FFmpeg QSV
        ffmpeg -threads 0 -i $video.FullName -filter_complex "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=20[bg];[0:v]scale=1080:-1[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2" -c:v h264_qsv -preset 7 -global_quality 23 -c:a copy $fichierSortie -y
    }
}

# 3. Affichage des résultats du chronomètre
Write-Host "--------------------------------------------------------"
Write-Host "Traitement terminé !" -ForegroundColor Cyan
Write-Host "Temps total d'exécution : $($tempsTotal.TotalSeconds) secondes ($($tempsTotal.Minutes) min $($tempsTotal.Seconds) s)" -ForegroundColor Yellow
```

---

## 📖 Explication détaillée du script PowerShell étape par étape

**1. Recherche et filtrage des fichiers**

```powershell
$videos = Get-ChildItem *.mp4 | Where-Object { $_.Name -notlike "out_*" }
```

* `Get-ChildItem *.mp4` : Récupère tous les fichiers ayant l'extension `.mp4` présents dans le dossier courant.
* `| Where-Object { $_.Name -notlike "out_*" }` : Filtre les résultats pour ignorer les vidéos qui commencent déjà par `out_`. Cela évite d'encoder en boucle des vidéos qui ont déjà été traitées lors d'un passage précédent.

---

**2. Vérification de sécurité**

```powershell
if ($videos.Count -eq 0) {
    Write-Host "Aucune vidéo à traiter dans ce dossier." -ForegroundColor Yellow
    exit
}
```

* Vérifie si le dossier contient des vidéos à traiter. Si la liste est vide, le script affiche un message d'avertissement en jaune et s'arrête immédiatement (`exit`).

---

**3. Mesure du temps d'exécution (Chronomètre)**

```powershell
$tempsTotal = Measure-Command { ... }
```

* `Measure-Command { ... }` : Englobe tout le bloc de traitement. Il mesure précisément le temps écoulé (en millisecondes) entre le début et la fin de l'exécution de l'ensemble des conversions, puis stocke le résultat dans la variable `$tempsTotal`.

---

**4. Boucle de traitement (`foreach`)**

```powershell
foreach ($video in $videos) {
    $fichierSortie = "out_qsv_$($video.Name)"
    ...
}
```

* Prend chaque vidéo trouvée une par une.
* `$fichierSortie = "out_qsv_$($video.Name)"` : Construit automatiquement le nom du fichier de sortie en ajoutant le préfixe `out_qsv_` devant le nom d'origine (exemple : `eclair.mp4` devient `out_qsv_eclair.mp4`).

---

**5. La commande FFmpeg avec Intel QSV**

```powershell
ffmpeg -threads 0 -i $video.FullName -filter_complex "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=20[bg];[0:v]scale=1080:-1[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2" -c:v h264_qsv -preset 7 -global_quality 23 -c:a copy $fichierSortie -y
```

* `-threads 0` : Utilise tous les cœurs du processeur disponibles.
* `-i $video.FullName` : Spécifie le chemin d'accès complet de la vidéo source à traiter.
* `-filter_complex "..."` :
  * **Arrière-plan (`[bg]`)** : Agrandit la vidéo pour couvrir la zone 1080×1920, recadre au format 9:16 exact et applique un flou gaussien (`gblur=sigma=20`).
  * **Premier plan (`[fg]`)** : Redimensionne la largeur à 1080 px tout en conservant le ratio d'origine de la vidéo.
  * **Overlay** : Superpose le premier plan net au centre précis de l'arrière-plan flouté avec la formule `(W-w)/2:(H-h)/2`.
* `-c:v h264_qsv` : Utilise l'encodeur matériel **Intel QuickSync Video (iGPU)** au lieu du processeur principal.
* `-preset 7` : Règle le niveau de qualité/vitesse d'Intel QSV (`7` correspond à la meilleure qualité d'encodage).
* `-global_quality 23` : Définit la qualité visuelle constante (équivalent du CRF pour QSV).
* `-c:a copy` : Duplique la piste audio originale sans réencodage.
* `$fichierSortie -y` : Définit le nom du fichier généré et force le remplacement s'il existe déjà.

---

**6. Affichage du bilan chronométré**

```powershell
Write-Host "Temps total d'exécution : $($tempsTotal.TotalSeconds) secondes ($($tempsTotal.Minutes) min $($tempsTotal.Seconds) s)" -ForegroundColor Yellow
```

* Une fois toutes les vidéos converties, le script extrait la durée mesurée par `Measure-Command` et affiche le temps exact écoulé en secondes et en minutes.
