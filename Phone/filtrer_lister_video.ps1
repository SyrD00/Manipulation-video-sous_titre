# ============================================================
# SCAN VIDEOS TELEPHONE - ADB + MEDIASTORE
# ============================================================

$ErrorActionPreference = "Stop"

# ============================================================
# DOSSIER DU SCRIPT
# ============================================================

$dossierScript = Split-Path -Parent $MyInvocation.MyCommand.Path

if ([string]::IsNullOrWhiteSpace($dossierScript)) {
    $dossierScript = (Get-Location).Path
}

# ============================================================
# DOSSIER DE RESULTATS
# ============================================================

$dossierResultats = Join-Path `
    $dossierScript `
    "Resultats_Videos_19-06-2026"

if (-not (Test-Path $dossierResultats)) {

    New-Item `
        -ItemType Directory `
        -Path $dossierResultats `
        -Force |
        Out-Null
}

# ============================================================
# DATE LIMITE
# ============================================================

$dateLimite = Get-Date "2026-06-19 23:59:59"

# ============================================================
# FICHIERS DE SORTIE
# ============================================================

$csvComplet = Join-Path `
    $dossierResultats `
    "videos_telephone.csv"

$csvFiltre = Join-Path `
    $dossierResultats `
    "videos_avant_19_06_2026.csv"

$listeNoms = Join-Path `
    $dossierResultats `
    "videos_avant_19_06_2026_noms.txt"

$listeDetails = Join-Path `
    $dossierResultats `
    "videos_avant_19_06_2026_details.txt"

$analyse = Join-Path `
    $dossierResultats `
    "analyse_dates_videos.txt"

# ============================================================
# FICHIER TEMPORAIRE
# ============================================================

$fichierTemp = Join-Path `
    $dossierResultats `
    "TEMP_MEDIastore_raw.txt"

# ============================================================
# ENCODAGE CONSOLE
# ============================================================

try {
    [Console]::OutputEncoding =
        [System.Text.Encoding]::UTF8
}
catch {}

# ============================================================
# CHRONOMETRE GLOBAL
# ============================================================

$chronoGlobal =
    [System.Diagnostics.Stopwatch]::StartNew()

# ============================================================
# TITRE
# ============================================================

Clear-Host

Write-Host ""
Write-Host "============================================================"
Write-Host "       SCAN VIDEOS TELEPHONE - ADB + MEDIASTORE"
Write-Host "============================================================"
Write-Host ""

Write-Host "Dossier du script :"
Write-Host $dossierScript

Write-Host ""

Write-Host "Dossier des résultats :"
Write-Host $dossierResultats

Write-Host ""

# ============================================================
# RECHERCHE ADB
# ============================================================

Write-Host "Recherche de ADB sur le PC..."
Write-Host ""

$adb = $null

$adbPossibles = @(
    "$env:LOCALAPPDATA\Android\platform-tools\adb.exe",
    "$env:USERPROFILE\AppData\Local\Android\platform-tools\adb.exe",
    "C:\Android\platform-tools\adb.exe"
)

foreach ($chemin in $adbPossibles) {

    if (Test-Path $chemin) {

        $adb = $chemin

        break
    }
}

# ============================================================
# RECHERCHE ADB DANS PATH
# ============================================================

if (-not $adb) {

    try {

        $adbCommande =
            Get-Command adb -ErrorAction Stop

        $adb = $adbCommande.Source
    }
    catch {

        Write-Host ""
        Write-Host "ADB n'est pas installé." `
            -ForegroundColor Yellow

        Write-Host ""
        Write-Host "Installation automatique..."
        Write-Host ""

        $dossierAndroid =
            Join-Path `
                $env:LOCALAPPDATA `
                "Android"

        $zipADB =
            Join-Path `
                $env:TEMP `
                "platform-tools-latest-windows.zip"

        if (-not (Test-Path $dossierAndroid)) {

            New-Item `
                -ItemType Directory `
                -Path $dossierAndroid `
                -Force |
                Out-Null
        }

        Invoke-WebRequest `
            -Uri "https://dl.google.com/android/repository/platform-tools-latest-windows.zip" `
            -OutFile $zipADB

        Expand-Archive `
            -Path $zipADB `
            -DestinationPath $dossierAndroid `
            -Force

        $adb =
            Join-Path `
                $dossierAndroid `
                "platform-tools\adb.exe"

        if (-not (Test-Path $adb)) {

            throw "Impossible de trouver adb.exe après l'installation."
        }

        Write-Host "ADB installé." `
            -ForegroundColor Green
    }
}
else {

    Write-Host "ADB déjà installé :" `
        -ForegroundColor Green

    Write-Host $adb
}

Write-Host ""

# ============================================================
# DEMARRAGE ADB
# ============================================================

Write-Host "Démarrage du serveur ADB..."

& $adb start-server | Out-Null

Write-Host "ADB opérationnel." `
    -ForegroundColor Green

Write-Host ""

# ============================================================
# DETECTION TELEPHONE
# ============================================================

Write-Host "Recherche du téléphone..."
Write-Host ""

$devices = @(
    & $adb devices |
    Select-Object -Skip 1 |
    Where-Object {
        $_ -match "^\S+\s+device"
    }
)

if ($devices.Count -eq 0) {

    Write-Host ""
    Write-Host "Aucun téléphone ADB détecté." `
        -ForegroundColor Red

    Write-Host ""
    Write-Host "Vérifie :"
    Write-Host "  1. Téléphone connecté en USB"
    Write-Host "  2. Débogage USB activé"
    Write-Host "  3. Autorisation RSA acceptée"
    Write-Host ""

    exit
}

$deviceId =
    ($devices[0] -split "\s+")[0]

Write-Host "Téléphone détecté :" `
    -ForegroundColor Green

Write-Host $deviceId
Write-Host ""

# ============================================================
# INFORMATIONS TELEPHONE
# ============================================================

$model = (
    & $adb `
        -s $deviceId `
        shell getprop ro.product.model
).Trim()

$manufacturer = (
    & $adb `
        -s $deviceId `
        shell getprop ro.product.manufacturer
).Trim()

$android = (
    & $adb `
        -s $deviceId `
        shell getprop ro.build.version.release
).Trim()

Write-Host "------------------------------------------------------------"
Write-Host "Téléphone"
Write-Host "------------------------------------------------------------"

Write-Host "Fabricant : $manufacturer"
Write-Host "Modèle    : $model"
Write-Host "Android   : $android"

Write-Host "------------------------------------------------------------"
Write-Host ""

# ============================================================
# MEDIASTORE
# ============================================================

Write-Host "Vérification de MediaStore..."
Write-Host ""

$uri =
    "content://media/external/video/media"

$projection =
    "_id:_display_name:_data:_size:date_added:date_modified:datetaken:duration:width:height"

Write-Host "Interrogation de MediaStore..."
Write-Host ""

# ============================================================
# CHRONOMETRE MEDIASTORE
# ============================================================

$chronoMediaStore =
    [System.Diagnostics.Stopwatch]::StartNew()

# ============================================================
# REQUETE MEDIASTORE
# ============================================================

$raw = @(
    & $adb `
        -s $deviceId `
        shell content query `
        --uri $uri `
        --projection $projection `
        2>&1
)

$chronoMediaStore.Stop()

# ============================================================
# STOCKAGE TEMPORAIRE
# ============================================================

try {

    $raw |
        ForEach-Object {
            $_.ToString()
        } |
        Set-Content `
            -Path $fichierTemp `
            -Encoding UTF8
}
catch {}

# ============================================================
# FONCTION EXTRACTION
# ============================================================

function Get-FieldValue {

    param(
        [string]$Text,
        [string]$Field
    )

    $escapedField =
        [regex]::Escape($Field)

    $pattern =
        "(?:^|,\s*)" +
        "$escapedField=" +
        "(.*?)" +
        "(?=,\s*[A-Za-z_][A-Za-z0-9_]*=|$)"

    $match =
        [regex]::Match(
            $Text,
            $pattern,
            [System.Text.RegularExpressions.RegexOptions]::IgnoreCase
        )

    if ($match.Success) {

        return $match.Groups[1].Value.Trim()
    }

    return $null
}

# ============================================================
# CONVERSION UNIX SECONDES
# ============================================================

function Convert-UnixSecondsToDate {

    param(
        [string]$Value
    )

    if ([string]::IsNullOrWhiteSpace($Value)) {
        return $null
    }

    [long]$number = 0

    if (-not [long]::TryParse(
        $Value,
        [ref]$number
    )) {
        return $null
    }

    if ($number -le 0) {
        return $null
    }

    try {

        return (
            [DateTimeOffset]::FromUnixTimeSeconds(
                $number
            ).LocalDateTime
        )
    }
    catch {

        return $null
    }
}

# ============================================================
# CONVERSION UNIX MILLISECONDES
# ============================================================

function Convert-UnixMillisecondsToDate {

    param(
        [string]$Value
    )

    if ([string]::IsNullOrWhiteSpace($Value)) {
        return $null
    }

    [long]$number = 0

    if (-not [long]::TryParse(
        $Value,
        [ref]$number
    )) {
        return $null
    }

    if ($number -le 0) {
        return $null
    }

    try {

        return (
            [DateTimeOffset]::FromUnixTimeMilliseconds(
                $number
            ).LocalDateTime
        )
    }
    catch {

        return $null
    }
}

# ============================================================
# LISTE VIDEOS
# ============================================================

$videos =
    New-Object System.Collections.Generic.List[object]

# ============================================================
# ANALYSE MEDIASTORE
# ============================================================

foreach ($lineObject in $raw) {

    $line =
        $lineObject.ToString().Trim()

    if ([string]::IsNullOrWhiteSpace($line)) {
        continue
    }

    if ($line -notmatch "Row:") {
        continue
    }

    # --------------------------------------------------------
    # EXTRACTION DES INFORMATIONS
    # --------------------------------------------------------

    $id =
        Get-FieldValue $line "_id"

    $nom =
        Get-FieldValue $line "_display_name"

    $chemin =
        Get-FieldValue $line "_data"

    $taille =
        Get-FieldValue $line "_size"

    $dateAddedRaw =
        Get-FieldValue $line "date_added"

    $dateModifiedRaw =
        Get-FieldValue $line "date_modified"

    $dateTakenRaw =
        Get-FieldValue $line "datetaken"

    $duree =
        Get-FieldValue $line "duration"

    $largeur =
        Get-FieldValue $line "width"

    $hauteur =
        Get-FieldValue $line "height"

    # --------------------------------------------------------
    # CONVERSION DES DATES
    # --------------------------------------------------------

    $dateAdded =
        Convert-UnixSecondsToDate $dateAddedRaw

    $dateModified =
        Convert-UnixSecondsToDate $dateModifiedRaw

    $dateTaken =
        Convert-UnixMillisecondsToDate $dateTakenRaw

    # --------------------------------------------------------
    # FILTRE
    #
    # DATE_ADDED uniquement
    # --------------------------------------------------------

    $avantDateLimite = $false

    if (
        $dateAdded -and
        $dateAdded -le $dateLimite
    ) {

        $avantDateLimite = $true
    }

    # --------------------------------------------------------
    # OBJET
    # --------------------------------------------------------

    $video = [PSCustomObject]@{

        ID =
            $id

        Nom =
            $nom

        Chemin =
            $chemin

        TailleOctets =
            $taille

        DateAdded =
            if ($dateAdded) {
                $dateAdded.ToString(
                    "yyyy-MM-dd HH:mm:ss"
                )
            }
            else {
                ""
            }

        DateModified =
            if ($dateModified) {
                $dateModified.ToString(
                    "yyyy-MM-dd HH:mm:ss"
                )
            }
            else {
                ""
            }

        DateTaken =
            if ($dateTaken) {
                $dateTaken.ToString(
                    "yyyy-MM-dd HH:mm:ss"
                )
            }
            else {
                ""
            }

        DureeMs =
            $duree

        Largeur =
            $largeur

        Hauteur =
            $hauteur

        AvantDateLimite =
            $avantDateLimite
    }

    $videos.Add($video)
}

# ============================================================
# TABLEAU
# ============================================================

$videosArray =
    $videos.ToArray()

# ============================================================
# VERIFICATION
# ============================================================

if ($videosArray.Count -eq 0) {

    Write-Host ""
    Write-Host "ERREUR : aucune vidéo analysée." `
        -ForegroundColor Red

    Write-Host ""

    $premiereLigne =
        $raw |
        Where-Object {
            $_.ToString() -match "Row:"
        } |
        Select-Object -First 1

    if ($premiereLigne) {

        Write-Host "Première ligne MediaStore :"
        Write-Host ""
        Write-Host $premiereLigne
    }

    if (Test-Path $fichierTemp) {

        Remove-Item `
            $fichierTemp `
            -Force `
            -ErrorAction SilentlyContinue
    }

    exit
}

# ============================================================
# STATISTIQUES
# ============================================================

$total =
    $videosArray.Count

$avecDateAdded = @(
    $videosArray |
    Where-Object {
        $_.DateAdded -ne ""
    }
).Count

$avecDateModified = @(
    $videosArray |
    Where-Object {
        $_.DateModified -ne ""
    }
).Count

$avecDateTaken = @(
    $videosArray |
    Where-Object {
        $_.DateTaken -ne ""
    }
).Count

# ============================================================
# VIDEOS FILTREES
# ============================================================

$videosFiltrees = @(
    $videosArray |
    Where-Object {
        $_.AvantDateLimite -eq $true
    }
)

$totalFiltrees =
    $videosFiltrees.Count

# ============================================================
# COMPTAGE DATE_ADDED
# ============================================================

$countAdded = @(
    $videosArray |
    Where-Object {

        $_.DateAdded -ne "" -and

        (
            [DateTime]$_.DateAdded
        ) -le $dateLimite
    }
).Count

# ============================================================
# COMPTAGE DATE_MODIFIED
# ============================================================

$countModified = @(
    $videosArray |
    Where-Object {

        $_.DateModified -ne "" -and

        (
            [DateTime]$_.DateModified
        ) -le $dateLimite
    }
).Count

# ============================================================
# COMPTAGE DATE_TAKEN
# ============================================================

$countTaken = @(
    $videosArray |
    Where-Object {

        $_.DateTaken -ne "" -and

        (
            [DateTime]$_.DateTaken
        ) -le $dateLimite
    }
).Count

# ============================================================
# CSV COMPLET
# ============================================================

$videosArray |
    Export-Csv `
        -Path $csvComplet `
        -NoTypeInformation `
        -Encoding UTF8

# ============================================================
# CSV FILTRE
# ============================================================

$videosFiltrees |
    Export-Csv `
        -Path $csvFiltre `
        -NoTypeInformation `
        -Encoding UTF8

# ============================================================
# LISTE NOMS UNIQUEMENT
# ============================================================

$videosFiltrees |
    ForEach-Object {
        $_.Nom
    } |
    Where-Object {
        -not [string]::IsNullOrWhiteSpace($_)
    } |
    Set-Content `
        -Path $listeNoms `
        -Encoding UTF8

# ============================================================
# LISTE DETAILLEE
# ============================================================

$texteListe =
    New-Object System.Collections.Generic.List[string]

$texteListe.Add(
    "VIDEOS AJOUTEES AU TELEPHONE / MEDIASTORE <= 19/06/2026"
)

$texteListe.Add(
    "Date limite : 19/06/2026 23:59:59"
)

$texteListe.Add(
    "Total : $totalFiltrees"
)

$texteListe.Add("")

$texteListe.Add(
    "============================================================"
)

$texteListe.Add("")

foreach ($video in $videosFiltrees) {

    $texteListe.Add(
        "Nom : $($video.Nom)"
    )

    $texteListe.Add(
        "Chemin : $($video.Chemin)"
    )

    $texteListe.Add(
        "DATE_ADDED    : $($video.DateAdded)"
    )

    $texteListe.Add(
        "DATE_MODIFIED : $($video.DateModified)"
    )

    $texteListe.Add(
        "DATE_TAKEN    : $($video.DateTaken)"
    )

    $texteListe.Add("")

    $texteListe.Add(
        "------------------------------------------------------------"
    )

    $texteListe.Add("")
}

$texteListe |
    Set-Content `
        -Path $listeDetails `
        -Encoding UTF8

# ============================================================
# ANALYSE
# ============================================================

$analyseTexte = @"

============================================================
ANALYSE DES VIDEOS DU TELEPHONE
============================================================

Téléphone :
$manufacturer $model

Android :
$android

Nombre total de vidéos :
$total

------------------------------------------------------------
DATES DISPONIBLES
------------------------------------------------------------

DATE_ADDED :
$avecDateAdded / $total

DATE_MODIFIED :
$avecDateModified / $total

DATE_TAKEN :
$avecDateTaken / $total

------------------------------------------------------------
DATE LIMITE
------------------------------------------------------------

19/06/2026 23:59:59

------------------------------------------------------------
RESULTATS
------------------------------------------------------------

DATE_ADDED <= 19/06/2026 :
$countAdded

DATE_MODIFIED <= 19/06/2026 :
$countModified

DATE_TAKEN <= 19/06/2026 :
$countTaken

------------------------------------------------------------
FILTRE UTILISE
------------------------------------------------------------

DATE_ADDED

------------------------------------------------------------
VIDEOS FILTREES
------------------------------------------------------------

$totalFiltrees

------------------------------------------------------------
INTERPRETATION
------------------------------------------------------------

Le filtre utilise DATE_ADDED.

DATE_ADDED correspond à la date d'ajout du média
dans MediaStore.

DATE_MODIFIED correspond à la dernière modification
du fichier.

DATE_TAKEN correspond à la date de prise de vue
lorsqu'elle est disponible.

DATE_TAKEN n'est pas utilisée pour le filtre.

============================================================

"@

$analyseTexte |
    Set-Content `
        -Path $analyse `
        -Encoding UTF8

# ============================================================
# SUPPRESSION DU TEMPORAIRE
# ============================================================

if (Test-Path $fichierTemp) {

    Remove-Item `
        $fichierTemp `
        -Force `
        -ErrorAction SilentlyContinue
}

# ============================================================
# FIN CHRONOMETRES
# ============================================================

$chronoGlobal.Stop()

# ============================================================
# RESULTAT FINAL
# ============================================================

Write-Host ""
Write-Host ""
Write-Host "============================================================"
Write-Host "                    RESULTAT FINAL"
Write-Host "============================================================"
Write-Host ""

Write-Host "Téléphone : $manufacturer $model"
Write-Host "Android   : $android"

Write-Host ""

Write-Host "VIDEOS TROUVEES : $total" `
    -ForegroundColor Green

Write-Host ""

Write-Host "DATE_MODIFIED disponibles : $avecDateModified"
Write-Host "DATE_ADDED disponibles    : $avecDateAdded"
Write-Host "DATE_TAKEN disponibles    : $avecDateTaken"

Write-Host ""

Write-Host "------------------------------------------------------------"
Write-Host "VIDEOS <= 19/06/2026"
Write-Host "------------------------------------------------------------"
Write-Host ""

Write-Host "DATE_ADDED    : $countAdded"
Write-Host "DATE_MODIFIED : $countModified"
Write-Host "DATE_TAKEN    : $countTaken"

Write-Host ""

Write-Host "------------------------------------------------------------"
Write-Host "FILTRE UTILISE : DATE_ADDED"
Write-Host "------------------------------------------------------------"
Write-Host ""

Write-Host "VIDEOS FILTREES : $totalFiltrees" `
    -ForegroundColor Green

Write-Host ""

Write-Host "------------------------------------------------------------"
Write-Host "DOSSIER DES RESULTATS"
Write-Host "------------------------------------------------------------"
Write-Host ""

Write-Host $dossierResultats

Write-Host ""

Write-Host "Fichiers créés :"
Write-Host ""

Write-Host "  - videos_telephone.csv"
Write-Host "  - videos_avant_19_06_2026.csv"
Write-Host "  - videos_avant_19_06_2026_noms.txt"
Write-Host "  - videos_avant_19_06_2026_details.txt"
Write-Host "  - analyse_dates_videos.txt"

Write-Host ""

Write-Host "------------------------------------------------------------"
Write-Host "TEMPS"
Write-Host "------------------------------------------------------------"
Write-Host ""

Write-Host "Temps MediaStore : $($chronoMediaStore.Elapsed.TotalSeconds) secondes"

Write-Host "Temps total      : $($chronoGlobal.Elapsed.TotalSeconds) secondes"

Write-Host ""

Write-Host "============================================================"
Write-Host "                         TERMINE"
Write-Host "============================================================"
Write-Host ""