# ============================================================
# SUPPRIMER LES VIDEOS DE list_video_common.txt DU TELEPHONE
# OPTIMISE AVEC SUPPRESSION PAR LOTS (TRES RAPIDE)
# ============================================================

$ErrorActionPreference = "Stop"

# ============================================================
# ENCODAGE CONSOLE (CRUCIAL POUR LES NOMS DE FICHIERS)
# ============================================================
try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
}
catch {}

Clear-Host

Write-Host ""
Write-Host "============================================================"
Write-Host "   SUPPRESSION DES VIDEOS PRESENTES DANS list_video_common"
Write-Host "============================================================"
Write-Host ""

# ============================================================
# DEMANDER LE FICHIER list_video_common.txt (VIA FENETRE)
# ============================================================
Write-Host "Ouverture de la fenetre de selection..." -ForegroundColor Cyan

Add-Type -AssemblyName System.Windows.Forms
$dialog = New-Object System.Windows.Forms.OpenFileDialog
$dialog.Title = "Sélectionne le fichier list_video_common.txt"
$dialog.Filter = "Fichiers texte (*.txt)|*.txt|Tous les fichiers (*.*)|*.*"
$dialog.ShowHelp = $true

$result = $dialog.ShowDialog()

if ($result -eq 'OK') {
    $liste = $dialog.FileName
} else {
    Write-Host ""
    Write-Host "ERREUR : Aucun fichier selectionne. Annulation." -ForegroundColor Red
    Write-Host ""
    exit
}

Write-Host ""
Write-Host "Liste trouvee :" -ForegroundColor Green
Write-Host $liste
Write-Host ""

# ============================================================
# RECHERCHE AUTOMATIQUE DE ADB
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

if (-not $adb) {
    try {
        $adbCommande = Get-Command adb -ErrorAction Stop
        $adb = $adbCommande.Source
    }
    catch {
        Write-Host "ADB non trouve. Installation automatique..." -ForegroundColor Yellow

        $dossierAndroid = Join-Path $env:LOCALAPPDATA "Android"
        $zipADB = Join-Path $env:TEMP "platform-tools-latest-windows.zip"

        if (-not (Test-Path $dossierAndroid)) {
            New-Item -ItemType Directory -Path $dossierAndroid -Force | Out-Null
        }

        Invoke-WebRequest -Uri "https://dl.google.com/android/repository/platform-tools-latest-windows.zip" -OutFile $zipADB
        Expand-Archive -Path $zipADB -DestinationPath $dossierAndroid -Force

        $adb = Join-Path $dossierAndroid "platform-tools\adb.exe"

        if (-not (Test-Path $adb)) {
            throw "Impossible de trouver adb.exe apres l'installation."
        }

        Write-Host "ADB installe." -ForegroundColor Green
    }
} else {
    Write-Host "ADB trouve : $adb" -ForegroundColor Green
}

Write-Host ""

# ============================================================
# DEMARRAGE ADB
# ============================================================

Write-Host "Demarrage du serveur ADB..."
& $adb start-server | Out-Null
Write-Host ""

# ============================================================
# DETECTION DU TELEPHONE
# ============================================================

Write-Host "Recherche du telephone..."

$devices = @(
    & $adb devices |
    Select-Object -Skip 1 |
    Where-Object {
        $_ -match "^\S+\s+device"
    }
)

if ($devices.Count -eq 0) {
    Write-Host ""
    Write-Host "ERREUR : aucun telephone ADB detecte." -ForegroundColor Red
    Write-Host ""
    Write-Host "Verifie :"
    Write-Host "  1. Le telephone est connecte en USB."
    Write-Host "  2. Le debogage USB est active."
    Write-Host "  3. L'autorisation RSA a ete acceptee."
    Write-Host ""
    exit
}

$deviceId = ($devices[0] -split "\s+")[0]

Write-Host ""
Write-Host "Telephone detecte :" -ForegroundColor Green
Write-Host $deviceId
Write-Host ""

# ============================================================
# INFORMATIONS DU TELEPHONE
# ============================================================

$model = (& $adb -s $deviceId shell getprop ro.product.model).Trim()
$manufacturer = (& $adb -s $deviceId shell getprop ro.product.manufacturer).Trim()
$android = (& $adb -s $deviceId shell getprop ro.build.version.release).Trim()

Write-Host "------------------------------------------------------------"
Write-Host "Telephone"
Write-Host "------------------------------------------------------------"
Write-Host "Fabricant : $manufacturer"
Write-Host "Modele    : $model"
Write-Host "Android   : $android"
Write-Host "------------------------------------------------------------"
Write-Host ""

# ============================================================
# LIRE list_video_common.txt
# ============================================================

Write-Host "Lecture de la liste..."

$noms = @(
    Get-Content -LiteralPath $liste -Encoding UTF8 |
    ForEach-Object { $_.Trim() } |
    Where-Object { -not [string]::IsNullOrWhiteSpace($_) } |
    Sort-Object -Unique
)

$totalListe = $noms.Count

if ($totalListe -eq 0) {
    Write-Host ""
    Write-Host "ERREUR : Le fichier de liste est vide." -ForegroundColor Red
    exit
}

Write-Host ""
Write-Host "Nombre de videos dans la liste : $totalListe" -ForegroundColor Green
Write-Host ""

# ============================================================
# INTERROGER MEDIASTORE DU TELEPHONE
# ============================================================

Write-Host "Recherche des videos sur le telephone via MediaStore..."
Write-Host ""

$uri = "content://media/external/video/media"
$projection = "_id:_display_name:_data:_size:date_added:date_modified:datetaken:duration:width:height"

$raw = @(
    & $adb -s $deviceId shell content query --uri $uri --projection $projection 2>&1
)

# ============================================================
# FONCTION EXTRACTION
# ============================================================

function Get-FieldValue {
    param(
        [string]$Text,
        [string]$Field
    )

    $escapedField = [regex]::Escape($Field)
    $pattern = "(?:^|,\s*)" + $escapedField + "=" + "(.*?)" + "(?=,\s*[A-Za-z_][A-Za-z0-9_]*=|$)"

    $match = [regex]::Match($Text, $pattern, [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)

    if ($match.Success) {
        return $match.Groups[1].Value.Trim()
    }
    return $null
}

# ============================================================
# CREER LA LISTE DES VIDEOS DU TELEPHONE
# ============================================================

$videosTelephone = New-Object System.Collections.Generic.List[object]

foreach ($ligneObject in $raw) {
    $ligne = $ligneObject.ToString().Trim()

    if ([string]::IsNullOrWhiteSpace($ligne) -or $ligne -notmatch "Row:") {
        continue
    }

    $ligne = $ligne -replace "^Row:\s*\d+\s*", ""

    $id = Get-FieldValue $ligne "_id"
    $nom = Get-FieldValue $ligne "_display_name"
    $chemin = Get-FieldValue $ligne "_data"

    if ([string]::IsNullOrWhiteSpace($id) -or [string]::IsNullOrWhiteSpace($nom)) {
        continue
    }

    $videosTelephone.Add(
        [PSCustomObject]@{
            ID     = $id
            Nom    = $nom
            Chemin = $chemin
        }
    )
}

Write-Host "Videos trouvees dans MediaStore : $($videosTelephone.Count)"

# ============================================================
# DIAGNOSTIC EN CAS DE ZERO VIDEOS
# ============================================================
if ($videosTelephone.Count -eq 0) {
    Write-Host ""
    Write-Host "ERREUR : MediaStore n'a retourne aucune video exploitable." -ForegroundColor Red
    exit
}

Write-Host ""

# ============================================================
# COMPARER LA LISTE AVEC LE TELEPHONE
# ============================================================

$videosASupprimer = @()
$introuvables = New-Object System.Collections.Generic.List[string]

foreach ($nomRecherche in $noms) {
    $trouve = $false

    foreach ($video in $videosTelephone) {
        if ($video.Nom -eq $nomRecherche) {
            $videosASupprimer += $video
            $trouve = $true
            break
        }
    }

    if (-not $trouve) {
        $introuvables.Add($nomRecherche)
    }
}

# ============================================================
# AFFICHER LES CORRESPONDANCES
# ============================================================

if ($videosASupprimer.Count -eq 0) {
    Write-Host "Aucune video de la liste n'a ete trouvee sur le telephone." -ForegroundColor Yellow
    exit
}

Write-Host "Nombre de videos pretes a etre supprimees : $($videosASupprimer.Count)" -ForegroundColor Yellow
Write-Host ""

# ============================================================
# CONFIRMATION VIA FENETRE POP-UP
# ============================================================

Write-Host "Attente de la confirmation via la fenetre pop-up..." -ForegroundColor Cyan

$titreMsg = "Confirmation de suppression"
$texteMsg = "Attention : $($videosASupprimer.Count) vidéos vont être définitivement supprimées de ton téléphone.`n`nVeux-tu vraiment continuer ?"
$boutons = [System.Windows.Forms.MessageBoxButtons]::YesNo
$icone = [System.Windows.Forms.MessageBoxIcon]::Warning

$choix = [System.Windows.Forms.MessageBox]::Show($texteMsg, $titreMsg, $boutons, $icone)

if ($choix -ne [System.Windows.Forms.DialogResult]::Yes) {
    Write-Host ""
    Write-Host "Suppression annulee." -ForegroundColor Yellow
    exit
}

# ============================================================
# SUPPRESSION PAR LOTS (RAPIDE)
# ============================================================

Write-Host ""
Write-Host "Suppression en cours par lots de 50..."
Write-Host ""

$nbSupprimees = 0
$nbEchecs = 0
$tailleLot = 50
$totalASupprimer = $videosASupprimer.Count

for ($i = 0; $i -lt $totalASupprimer; $i += $tailleLot) {
    
    $lotActuel = $videosASupprimer | Select-Object -Skip $i -First $tailleLot
    $ids = ($lotActuel | ForEach-Object { $_.ID }) -join ","
    
    # LA SOLUTION EST ICI : on utilise de simples apostrophes (')
    # pour protéger les parenthèses de la ligne de commande Android.
    $whereClause = "'_id IN ($ids)'"

    $numLot = [math]::Floor($i / $tailleLot) + 1
    Write-Host "Traitement du lot $numLot (Contient $($lotActuel.Count) videos) : " -NoNewline

    # On suspend l'arrêt automatique de PowerShell sur erreur pour voir ce qu'ADB nous dit vraiment
    $oldEA = $ErrorActionPreference
    $ErrorActionPreference = "Continue"

    try {
        $resultat = @( & $adb -s $deviceId shell content delete --uri $uri --where $whereClause 2>&1 )
        $retour = ($resultat | Out-String).Trim()

        if ($retour -match "Error|Exception|Failed|No such file|bad |unrecognized|Syntax|unexpected") {
            Write-Host "[ ECHEC ]" -ForegroundColor Red
            Write-Host "  -> Raison : $retour" -ForegroundColor DarkGray
            $nbEchecs += $lotActuel.Count
        }
        else {
            Write-Host "[ OK - SUPPRIMEES ]" -ForegroundColor Green
            $nbSupprimees += $lotActuel.Count
        }
    }
    catch {
        Write-Host "[ ERREUR ]" -ForegroundColor Red
        Write-Host "  -> PowerShell dit : $_" -ForegroundColor DarkGray
        $nbEchecs += $lotActuel.Count
    }
    finally {
        # On remet la sécurité de PowerShell
        $ErrorActionPreference = $oldEA
    }
}

# ============================================================
# RESULTAT FINAL
# ============================================================

Write-Host ""
Write-Host "============================================================"
Write-Host "                    RESULTAT FINAL"
Write-Host "============================================================"
Write-Host ""

Write-Host "Telephone : $manufacturer $model"
Write-Host ""
Write-Host "Videos dans la liste  : $totalListe"
Write-Host "Trouvees sur le phone : $totalASupprimer"
Write-Host ""
Write-Host "Supprimees   : $nbSupprimees" -ForegroundColor Green
Write-Host "Echecs       : $nbEchecs" -ForegroundColor $(if ($nbEchecs -gt 0) { "Red" } else { "Green" })
Write-Host "Introuvables : $($introuvables.Count)" -ForegroundColor $(if ($introuvables.Count -gt 0) { "Yellow" } else { "Green" })
Write-Host ""
Write-Host "============================================================"
Write-Host "                         TERMINE"
Write-Host "============================================================"
Write-Host ""

# SAUVEGARDE DES INTROUVABLES SUR LE BUREAU
if ($introuvables.Count -gt 0) {
    $bureau = [Environment]::GetFolderPath("Desktop")
    $fichierRapport = Join-Path $bureau "Rapport_Introuvables.txt"
    $introuvables | Out-File -FilePath $fichierRapport -Encoding UTF8
    Write-Host "Un fichier 'Rapport_Introuvables.txt' a ete cree sur ton Bureau avec les noms des 168 videos." -ForegroundColor Cyan
    Write-Host ""
}