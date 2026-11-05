#Pour eviter affichage caractere bizarre exemple: période, vidéos,Téléphone ...
#appuie sur UTF-8 en bas de vscode puis enregistrer avec l'encodage puis UTF-8 with BOM
#date_added=  timestamp (en secondes) du moment exact où le fichier a été enregistré et indexé dans la base de données multimédia du téléphone.

# ============================================================
# TRANSFERT DES VIDEOS DU TELEPHONE VERS LE PC
# ADB + MEDIASTORE (AVEC INTERFACES GRAPHIQUES CORRIGÉES)
# ============================================================

$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# ============================================================
# 0. FONCTIONS
# ============================================================

function Show-Confirmation {
    param(
        [string]$Titre,
        [string]$Message,
        [string]$TexteOui = "Oui",
        [string]$TexteNon = "Non"
    )

    $form = New-Object System.Windows.Forms.Form
    $form.Text = $Titre
    $form.Size = New-Object System.Drawing.Size(560, 270) # Fenêtre élargie
    $form.StartPosition = "CenterScreen"
    $form.FormBorderStyle = "FixedDialog"
    $form.MaximizeBox = $false
    $form.MinimizeBox = $false
    $form.TopMost = $true

    $label = New-Object System.Windows.Forms.Label
    $label.Text = $Message
    $label.Location = New-Object System.Drawing.Point(20, 20)
    $label.Size = New-Object System.Drawing.Size(505, 140) # Espace étendu pour tout voir
    $label.Font = New-Object System.Drawing.Font("Segoe UI", 10)
    $form.Controls.Add($label)

    $oui = New-Object System.Windows.Forms.Button
    $oui.Text = $TexteOui
    $oui.Location = New-Object System.Drawing.Point(300, 175)
    $oui.Size = New-Object System.Drawing.Size(105, 32)
    $oui.DialogResult = [System.Windows.Forms.DialogResult]::Yes
    $form.Controls.Add($oui)

    $non = New-Object System.Windows.Forms.Button
    $non.Text = $TexteNon
    $non.Location = New-Object System.Drawing.Point(420, 175)
    $non.Size = New-Object System.Drawing.Size(105, 32)
    $non.DialogResult = [System.Windows.Forms.DialogResult]::No
    $form.Controls.Add($non)

    $form.AcceptButton = $oui
    $form.CancelButton = $non

    $resultat = $form.ShowDialog()
    $form.Dispose()

    return ($resultat -eq [System.Windows.Forms.DialogResult]::Yes)
}

function Show-DateSelector {
    $form = New-Object System.Windows.Forms.Form
    $form.Text = "Sélection de la période"
    $form.Size = New-Object System.Drawing.Size(420, 210)
    $form.StartPosition = "CenterScreen"
    $form.FormBorderStyle = "FixedDialog"
    $form.MaximizeBox = $false
    $form.MinimizeBox = $false
    $form.TopMost = $true

    $lblStart = New-Object System.Windows.Forms.Label
    $lblStart.Text = "Date de début :"
    $lblStart.Location = New-Object System.Drawing.Point(30, 25)
    $lblStart.Size = New-Object System.Drawing.Size(120, 20)
    $form.Controls.Add($lblStart)

    $dtpStart = New-Object System.Windows.Forms.DateTimePicker
    $dtpStart.Location = New-Object System.Drawing.Point(160, 22)
    $dtpStart.Size = New-Object System.Drawing.Size(200, 20)
    $dtpStart.Format = [System.Windows.Forms.DateTimePickerFormat]::Short
    $dtpStart.Value = [datetime]::new(2025, 8, 22)
    $form.Controls.Add($dtpStart)

    $lblEnd = New-Object System.Windows.Forms.Label
    $lblEnd.Text = "Date de fin (inclus) :"
    $lblEnd.Location = New-Object System.Drawing.Point(30, 70)
    $lblEnd.Size = New-Object System.Drawing.Size(130, 20)
    $form.Controls.Add($lblEnd)

    $dtpEnd = New-Object System.Windows.Forms.DateTimePicker
    $dtpEnd.Location = New-Object System.Drawing.Point(160, 67)
    $dtpEnd.Size = New-Object System.Drawing.Size(200, 20)
    $dtpEnd.Format = [System.Windows.Forms.DateTimePickerFormat]::Short
    $dtpEnd.Value = [datetime]::new(2026, 2, 11)
    $form.Controls.Add($dtpEnd)

    $btnOk = New-Object System.Windows.Forms.Button
    $btnOk.Text = "Valider"
    $btnOk.Location = New-Object System.Drawing.Point(255, 115)
    $btnOk.Size = New-Object System.Drawing.Size(105, 32)
    $btnOk.DialogResult = [System.Windows.Forms.DialogResult]::OK
    $form.AcceptButton = $btnOk
    $form.Controls.Add($btnOk)

    $result = $form.ShowDialog()
    
    if ($result -eq [System.Windows.Forms.DialogResult]::OK) {
        $start = $dtpStart.Value.Date
        $end = $dtpEnd.Value.Date.AddDays(1)
        $form.Dispose()
        return @($start, $end)
    }
    else {
        $form.Dispose()
        exit
    }
}

function New-ProgressWindow {
    param([string]$Title, [int]$Maximum)

    $form = New-Object System.Windows.Forms.Form
    $form.Text = $Title
    $form.Size = New-Object System.Drawing.Size(560, 210) # Hauteur et largeur augmentées pour éviter les coupures
    $form.StartPosition = "CenterScreen"
    $form.FormBorderStyle = "FixedDialog"
    $form.MaximizeBox = $false
    $form.MinimizeBox = $false
    $form.TopMost = $true

    $lblStatus = New-Object System.Windows.Forms.Label
    $lblStatus.Text = "Préparation du transfert..."
    $lblStatus.Location = New-Object System.Drawing.Point(20, 15)
    $lblStatus.Size = New-Object System.Drawing.Size(505, 70) # Espace suffisant pour le texte et la taille
    $lblStatus.Font = New-Object System.Drawing.Font("Segoe UI", 9.5)
    $form.Controls.Add($lblStatus)

    $progressBar = New-Object System.Windows.Forms.ProgressBar
    $progressBar.Location = New-Object System.Drawing.Point(20, 95) # Descendu pour laisser de la place au texte
    $progressBar.Size = New-Object System.Drawing.Size(505, 25)
    $progressBar.Minimum = 0
    $progressBar.Maximum = $Maximum
    $progressBar.Value = 0
    $form.Controls.Add($progressBar)

    $form.Show()
    [System.Windows.Forms.Application]::DoEvents()

    return [PSCustomObject]@{
        Form = $form
        Label = $lblStatus
        ProgressBar = $progressBar
    }
}

function Format-FileSize {
    param([long]$Bytes)

    if ($Bytes -ge 1GB) {
        return "{0:N2} Go" -f ($Bytes / 1GB)
    }
    elseif ($Bytes -ge 1MB) {
        return "{0:N2} Mo" -f ($Bytes / 1MB)
    }
    elseif ($Bytes -ge 1KB) {
        return "{0:N2} Ko" -f ($Bytes / 1KB)
    }
    else {
        return "$Bytes octets"
    }
}

function Get-FieldValue {
    param(
        [string]$Text,
        [string]$Field
    )

    $Text = $Text -replace '^Row:\s*\d+\s*', ''
    $escapedField = [regex]::Escape($Field)
    $pattern = "(?:^|,\s*)" + $escapedField + "=(.*?)" + "(?=,\s*[A-Za-z_][A-Za-z0-9_]*=|$)"

    $match = [regex]::Match(
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
# 1. CONFIGURATION ET CHOIX DES DATES
# ============================================================

$uri = "content://media/external/video/media"
$destination = Join-Path $env:USERPROFILE "Downloads\phone"

$datesChoisies = Show-DateSelector
$dateDebut = $datesChoisies[0]
$dateFinExclusive = $datesChoisies[1]

$debut = ([DateTimeOffset]$dateDebut).ToUnixTimeSeconds()
$finExclusive = ([DateTimeOffset]$dateFinExclusive).ToUnixTimeSeconds()

# ============================================================
# 2. ENCODAGE
# ============================================================

try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
}
catch {}

# ============================================================
# 3. TITRE
# ============================================================

Clear-Host

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "       TRANSFERT DES VIDEOS DU TELEPHONE VERS LE PC"
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$dateDebutAffichage = $dateDebut.ToString('dd/MM/yyyy')
$dateFinAffichage = $dateFinExclusive.AddDays(-1).ToString('dd/MM/yyyy')

Write-Host "Periode DATE_ADDED : $dateDebutAffichage au $dateFinAffichage inclus"
Write-Host "Destination : $destination"
Write-Host ""

$chronoGlobal = [System.Diagnostics.Stopwatch]::StartNew()

# ============================================================
# 4. RECHERCHE ADB
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
    if (Test-Path -LiteralPath $chemin) {
        $adb = $chemin
        break
    }
}

if (-not $adb) {
    try {
        $adbCommande = Get-Command adb -ErrorAction Stop
        $adb = $adbCommande.Source
    }
    catch {}
}

if (-not $adb) {
    Write-Host "ADB introuvable. Installation automatique..." -ForegroundColor Yellow

    $dossierAndroid = Join-Path $env:LOCALAPPDATA "Android"
    $zipADB = Join-Path $env:TEMP "platform-tools-latest-windows.zip"

    New-Item -ItemType Directory -Path $dossierAndroid -Force | Out-Null

    Invoke-WebRequest `
        -Uri "https://dl.google.com/android/repository/platform-tools-latest-windows.zip" `
        -OutFile $zipADB

    Expand-Archive -Path $zipADB -DestinationPath $dossierAndroid -Force

    $adb = Join-Path $dossierAndroid "platform-tools\adb.exe"

    if (-not (Test-Path -LiteralPath $adb)) {
        throw "Impossible de trouver adb.exe apres installation."
    }
}
else {
    Write-Host "ADB deja installe :" -ForegroundColor Green
    Write-Host $adb
}

Write-Host ""

# ============================================================
# 5. DEMARRAGE ADB
# ============================================================

Write-Host "Demarrage du serveur ADB..."
& $adb start-server | Out-Null

if ($LASTEXITCODE -ne 0) {
    throw "Impossible de demarrer ADB."
}

Write-Host "ADB operationnel." -ForegroundColor Green
Write-Host ""

# ============================================================
# 6. DETECTION DU TELEPHONE
# ============================================================

Write-Host "Recherche du telephone..."
Write-Host ""

$devices = @(
    & $adb devices |
    Select-Object -Skip 1 |
    Where-Object {
        $_ -match "^\S+\s+device$"
    }
)

if ($devices.Count -eq 0) {
    throw "Aucun telephone ADB autorise. Verifie le cable USB et le debogage USB."
}

if ($devices.Count -gt 1) {
    Write-Host "Plusieurs telephones sont connectes :" -ForegroundColor Yellow
    $devices | ForEach-Object { Write-Host $_ }
    throw "Laisse un seul telephone connecte puis relance le script."
}

$deviceId = ($devices[0] -split "\s+")[0]

Write-Host "Telephone detecte :" -ForegroundColor Green
Write-Host $deviceId
Write-Host ""

# ============================================================
# 7. INFORMATIONS TELEPHONE
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
# 8. CREATION DU DOSSIER DESTINATION
# ============================================================

New-Item -ItemType Directory -Path $destination -Force | Out-Null

Write-Host "Dossier de destination :"
Write-Host $destination -ForegroundColor Green
Write-Host ""

# ============================================================
# 9. INTERROGATION MEDIASTORE
# ============================================================

Write-Host "Interrogation de MediaStore..."
Write-Host ""

$chronoMediaStore = [System.Diagnostics.Stopwatch]::StartNew()
$projection = "_id:_display_name:_data:_size:date_added"

$raw = @(
    & $adb `
        -s $deviceId `
        shell content query `
        --uri $uri `
        --projection $projection `
        2>&1
)

$codeMediaStore = $LASTEXITCODE
$chronoMediaStore.Stop()

if ($codeMediaStore -ne 0) {
    $raw | ForEach-Object { Write-Host $_ }
    throw "Erreur pendant l'interrogation de MediaStore."
}

# ============================================================
# 10. ANALYSE ET FILTRAGE DES VIDEOS
# ============================================================

Write-Host ""
Write-Host "Analyse des videos MediaStore..." -ForegroundColor Cyan

$videos = New-Object System.Collections.Generic.List[object]

$compteurLignes = 0
$compteurID = 0
$compteurDates = 0
$compteurChemins = 0
$compteurHorsPeriode = 0
$compteurInvalides = 0

foreach ($ligneObject in $raw) {
    $ligne = $ligneObject.ToString()

    if ($ligne -notmatch '^Row:\s*\d+') {
        continue
    }

    $compteurLignes++

    $id = Get-FieldValue $ligne "_id"
    $nom = Get-FieldValue $ligne "_display_name"
    $chemin = Get-FieldValue $ligne "_data"
    $tailleRaw = Get-FieldValue $ligne "_size"
    $dateRaw = Get-FieldValue $ligne "date_added"

    $idNombre = 0L
    if (-not [long]::TryParse($id, [ref]$idNombre)) {
        $compteurInvalides++
        continue
    }
    $compteurID++

    $dateAdded = 0L
    if (-not [long]::TryParse($dateRaw, [ref]$dateAdded)) {
        $compteurInvalides++
        continue
    }
    $compteurDates++

    if ($dateAdded -lt $debut -or $dateAdded -ge $finExclusive) {
        $compteurHorsPeriode++
        continue
    }

    if ([string]::IsNullOrWhiteSpace($chemin) -or $chemin -eq "null") {
        $compteurInvalides++
        continue
    }
    $compteurChemins++

    if ([string]::IsNullOrWhiteSpace($nom) -or $nom -eq "null") {
        $compteurInvalides++
        continue
    }

    $taille = 0L
    if (-not [long]::TryParse($tailleRaw, [ref]$taille) -or $taille -lt 0) {
        $compteurInvalides++
        continue
    }

    $dateLisible = [DateTimeOffset]::FromUnixTimeSeconds($dateAdded).ToLocalTime().DateTime

    $videos.Add(
        [PSCustomObject]@{
            ID = $id
            Nom = $nom
            Chemin = $chemin
            Taille = $taille
            DateAdded = $dateLisible
            DateAddedUnix = $dateAdded
        }
    )
}

# ============================================================
# 11. TRI CHRONOLOGIQUE DES VIDEOS
# ============================================================

$videos = @(
    $videos | Sort-Object DateAddedUnix, ID
)

Write-Host ""
Write-Host "Tri chronologique termine." -ForegroundColor Green

# ============================================================
# 12. RESULTAT DU FILTRAGE
# ============================================================

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " RESULTAT DU FILTRAGE"
Write-Host "============================================================"
Write-Host ""

Write-Host "Lignes MediaStore analysees : $compteurLignes"
Write-Host "Identifiants recuperes      : $compteurID"
Write-Host "Dates recuperables          : $compteurDates"
Write-Host "Videos hors periode         : $compteurHorsPeriode"
Write-Host "Lignes invalides            : $compteurInvalides"
Write-Host ""

Write-Host "Videos trouvees : $($videos.Count)" -ForegroundColor Green

if ($videos.Count -eq 0) {
    Write-Host ""
    Write-Host "Aucune video ne correspond a la periode." -ForegroundColor Yellow
    Write-Host "Aucun fichier n'a ete copie ni supprime."
    exit
}

Write-Host ""
Write-Host "Quelques videos trouvees :"

$videos |
    Select-Object -First 15 Nom,
        @{Name="Taille"; Expression={ Format-FileSize $_.Taille }},
        DateAdded |
    Format-Table -AutoSize

$totalVideos = $videos.Count
$tailleTotale = ($videos | Measure-Object -Property Taille -Sum).Sum

Write-Host ""
Write-Host "Nombre total : $totalVideos"
Write-Host "Taille totale : $(Format-FileSize $tailleTotale)"
Write-Host "Destination : $destination"
Write-Host ""

$confirmation = Show-Confirmation `
    -Titre "Transfert des videos" `
    -Message "$totalVideos videos correspondent a la periode demandee.`n`nTaille totale : $(Format-FileSize $tailleTotale)`n`nDestination : $destination`n`nVoulez-vous commencer la copie ?"

if (-not $confirmation) {
    Write-Host "Operation annulee." -ForegroundColor Yellow
    exit
}

# ============================================================
# 13. COPIE ET VERIFICATION DES FICHIERS (AVEC POURCENTAGE)
# ============================================================

$copiesVerifiees = New-Object System.Collections.Generic.List[object]
$echecsCopie = New-Object System.Collections.Generic.List[object]

$compteur = 0
$tailleTransferee = 0L

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " COPIE DES VIDEOS VERS LE PC"
Write-Host "============================================================"
Write-Host ""

$progressWin = New-ProgressWindow -Title "Transfert des vidéos vers le PC..." -Maximum $totalVideos

foreach ($video in $videos) {
    $compteur++

    # Calcul du pourcentage exact (ex: 16/182 = 8,8%)
    $pourcentage = [math]::Round(($compteur / $totalVideos) * 100, 1)

    # Mise à jour de la fenêtre graphique avec le pourcentage
    $progressWin.Label.Text = "[$compteur/$totalVideos - $pourcentage%] $($video.Nom)`nTaille : $(Format-FileSize $video.Taille)"
    $progressWin.ProgressBar.Value = $compteur
    [System.Windows.Forms.Application]::DoEvents()

    Write-Host ""
    Write-Host "[$compteur/$totalVideos - $pourcentage%] $($video.Nom)" -ForegroundColor Cyan
    Write-Host "  Date : $($video.DateAdded.ToString('dd/MM/yyyy HH:mm:ss'))"
    Write-Host "  Taille : $(Format-FileSize $video.Taille)"

    $nomDestination = $video.Nom
    $cheminDestination = Join-Path $destination $nomDestination

    if (Test-Path -LiteralPath $cheminDestination) {
        $extension = [IO.Path]::GetExtension($video.Nom)
        $nomSansExtension = [IO.Path]::GetFileNameWithoutExtension($video.Nom)

        $nomDestination = "{0}_telephone_{1}{2}" -f `
            $nomSansExtension, $video.ID, $extension

        $cheminDestination = Join-Path $destination $nomDestination
    }

    if (Test-Path -LiteralPath $cheminDestination) {
        Write-Host "  ECHEC : un fichier portant deja ce nom existe." -ForegroundColor Red
        $echecsCopie.Add($video)
        continue
    }

    $anciennePreference = $ErrorActionPreference
    $anciennePreferenceNative = $null
    $nativePreferenceExiste = $false

    try {
        $ErrorActionPreference = "Continue"

        $nativeVariable = Get-Variable `
            -Name PSNativeCommandUseErrorActionPreference `
            -ErrorAction SilentlyContinue

        if ($null -ne $nativeVariable) {
            $nativePreferenceExiste = $true
            $anciennePreferenceNative = $nativeVariable.Value
            $PSNativeCommandUseErrorActionPreference = $false
        }

        & $adb -s $deviceId pull -p $video.Chemin $cheminDestination
        $pullExitCode = $LASTEXITCODE

        $ErrorActionPreference = $anciennePreference

        if ($nativePreferenceExiste) {
            $PSNativeCommandUseErrorActionPreference = $anciennePreferenceNative
        }

        if ($pullExitCode -ne 0) {
            throw "ADB a retourne le code $pullExitCode."
        }

        if (-not (Test-Path -LiteralPath $cheminDestination -PathType Leaf)) {
            throw "Le fichier est introuvable sur le PC apres le transfert."
        }

        $fichierPC = Get-Item -LiteralPath $cheminDestination -ErrorAction Stop

        if ($fichierPC.Length -ne $video.Taille) {
            throw "Taille differente : telephone=$(Format-FileSize $video.Taille), PC=$(Format-FileSize $fichierPC.Length)."
        }

        Write-Host "  COPIE VERIFIEE : $(Format-FileSize $fichierPC.Length)" -ForegroundColor Green

        $tailleTransferee += $fichierPC.Length

        $copiesVerifiees.Add(
            [PSCustomObject]@{
                ID = $video.ID
                Nom = $video.Nom
                CheminPC = $cheminDestination
                Taille = $video.Taille
                DateAdded = $video.DateAdded
                DateAddedUnix = $video.DateAddedUnix
            }
        )
    }
    catch {
        $ErrorActionPreference = $anciennePreference

        if ($nativePreferenceExiste) {
            $PSNativeCommandUseErrorActionPreference = $anciennePreferenceNative
        }

        Write-Host "  ECHEC : $($_.Exception.Message)" -ForegroundColor Red
        $echecsCopie.Add($video)

        if (Test-Path -LiteralPath $cheminDestination) {
            Remove-Item -LiteralPath $cheminDestination -Force -ErrorAction SilentlyContinue
        }
    }
    finally {
        $ErrorActionPreference = $anciennePreference

        if ($nativePreferenceExiste) {
            $PSNativeCommandUseErrorActionPreference = $anciennePreferenceNative
        }
    }
}

$progressWin.Form.Close()
$progressWin.Form.Dispose()

# ============================================================
# 14. BILAN DES COPIES
# ============================================================

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " BILAN DES COPIES"
Write-Host "============================================================"
Write-Host ""

Write-Host "Videos selectionnees : $($videos.Count)"
Write-Host "Copies verifiees     : $($copiesVerifiees.Count)" -ForegroundColor Green
Write-Host "Echecs de copie      : $($echecsCopie.Count)" -ForegroundColor Red
Write-Host "Volume verifie       : $(Format-FileSize $tailleTransferee)" -ForegroundColor Green

if ($copiesVerifiees.Count -eq 0) {
    Write-Host ""
    Write-Host "Aucune copie verifiee. Aucune video ne sera supprimee du telephone." -ForegroundColor Red
    exit
}

Write-Host ""
Write-Host "Les originaux des copies verifiees pourront etre supprimes."
Write-Host "La suppression sera effectuee en UNE SEULE COMMANDE ADB." -ForegroundColor Yellow
Write-Host ""

$confirmationSuppression = Show-Confirmation `
    -Titre "Suppression des originaux" `
    -Message "Copies verifiees : $($copiesVerifiees.Count)`nEchecs de copie : $($echecsCopie.Count)`nVolume copie : $(Format-FileSize $tailleTransferee)`n`nSeuls les originaux dont la copie a ete verifiee seront supprimes du telephone.`n`nConfirmer la suppression ?" `
    -TexteOui "Supprimer" `
    -TexteNon "Annuler"

if (-not $confirmationSuppression) {
    Write-Host ""
    Write-Host "Suppression annulee." -ForegroundColor Yellow
    Write-Host "Les copies restent sur le PC et les originaux restent sur le telephone."
    exit
}

# ============================================================
# 15. SUPPRESSION EN UNE SEULE COMMANDE
# ============================================================

Write-Host ""
Write-Host "Preparation de la suppression globale..." -ForegroundColor Cyan

$ids = ($copiesVerifiees | ForEach-Object { $_.ID }) -join ","
$whereClause = "'_id IN ($ids)'"

Write-Host "Nombre d'identifiants : $($copiesVerifiees.Count)"
Write-Host "Envoi de la commande unique..." -ForegroundColor Yellow

$anciennePreference = $ErrorActionPreference

try {
    $ErrorActionPreference = "Continue"

    $deleteOutput = @(
        & $adb `
            -s $deviceId `
            shell content delete `
            --uri $uri `
            --where $whereClause 2>&1
    )

    $deleteExitCode = $LASTEXITCODE
}
finally {
    $ErrorActionPreference = $anciennePreference
}

$deleteOutput | ForEach-Object {
    Write-Host $_
}

if ($deleteExitCode -ne 0) {
    Write-Host ""
    Write-Host "ERREUR : la commande de suppression a echoue." -ForegroundColor Red
    Write-Host "Les copies PC sont conservees."
    Write-Host "Les originaux ne sont pas declares supprimes."
    exit
}

# ============================================================
# 16. VERIFICATION MEDIASTORE
# ============================================================

Write-Host ""
Write-Host "Verification des videos restantes dans MediaStore..." -ForegroundColor Cyan

$anciennePreference = $ErrorActionPreference

try {
    $ErrorActionPreference = "Continue"

    $verifyOutput = @(
        & $adb `
            -s $deviceId `
            shell content query `
            --uri $uri `
            --projection "_id" `
            2>&1
    )

    $verifyExitCode = $LASTEXITCODE
}
finally {
    $ErrorActionPreference = $anciennePreference
}

if ($verifyExitCode -ne 0) {
    Write-Host "Impossible de verifier les identifiants restants." -ForegroundColor Yellow
    Write-Host "La commande de suppression a ete envoyee, mais son resultat reste a confirmer."
    exit
}

$idsRestants = @{}

foreach ($lineObject in $verifyOutput) {
    $line = $lineObject.ToString()

    if ($line -notmatch '^Row:\s*\d+') {
        continue
    }

    $idRestant = Get-FieldValue $line "_id"

    if ($idRestant) {
        $idsRestants[$idRestant] = $true
    }
}

$restants = @(
    $copiesVerifiees | Where-Object {
        $idsRestants.ContainsKey($_.ID)
    }
)

$supprimes = $copiesVerifiees.Count - $restants.Count

# ============================================================
# 17. RAPPORT
# ============================================================

$rapport = Join-Path $destination "Rapport_Transfert_Videos.txt"

$rapportLignes = @(
    "RAPPORT DE TRANSFERT DES VIDEOS"
    "================================"
    "Telephone : $deviceId"
    "Fabricant : $manufacturer"
    "Modele : $model"
    "Android : $android"
    "Periode DATE_ADDED : $dateDebutAffichage au $dateFinAffichage inclus"
    "Ordre : DATE_ADDED croissant"
    "Destination : $destination"
    ""
    "Videos selectionnees : $($videos.Count)"
    "Copies verifiees : $($copiesVerifiees.Count)"
    "Echecs de copie : $($echecsCopie.Count)"
    "Volume copie verifie : $(Format-FileSize $tailleTransferee)"
    "Originaux absents de MediaStore apres suppression : $supprimes"
    "Originaux encore presents dans MediaStore : $($restants.Count)"
    ""
    "LISTE DES COPIES VERIFIEES :"
)

foreach ($video in $copiesVerifiees) {
    $rapportLignes += "$($video.DateAdded.ToString('dd/MM/yyyy HH:mm:ss')) | $($video.Nom) | $(Format-FileSize $video.Taille) | ID $($video.ID)"
}

$rapportLignes += ""
$rapportLignes += "VIDEOS ENCORE PRESENTES DANS MEDIASTORE :"

foreach ($video in $restants) {
    $rapportLignes += "$($video.Nom) | ID $($video.ID)"
}

$rapportLignes += ""
$rapportLignes += "VIDEOS DONT LA COPIE A ECHOUE :"

foreach ($video in $echecsCopie) {
    $rapportLignes += "$($video.Nom) | ID $($video.ID)"
}

$rapportLignes | Set-Content -Path $rapport -Encoding UTF8

# ============================================================
# 18. RESULTAT FINAL
# ============================================================

$chronoGlobal.Stop()

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " RESULTAT FINAL"
Write-Host "============================================================"
Write-Host ""

Write-Host "Videos trouvees : $($videos.Count)"
Write-Host "Copies verifiees : $($copiesVerifiees.Count)" -ForegroundColor Green
Write-Host "Echecs de copie : $($echecsCopie.Count)" -ForegroundColor Red
Write-Host "Volume copie : $(Format-FileSize $tailleTransferee)" -ForegroundColor Green
Write-Host "Originaux absents de MediaStore : $supprimes" -ForegroundColor Green
Write-Host "Originaux encore presents : $($restants.Count)" -ForegroundColor Yellow

Write-Host ""
Write-Host "Dossier des videos :"
Write-Host $destination -ForegroundColor Green

Write-Host ""
Write-Host "Rapport :"
Write-Host $rapport -ForegroundColor Green

Write-Host ""
Write-Host "Temps MediaStore : $($chronoMediaStore.Elapsed.TotalSeconds) secondes"
Write-Host "Temps total : $($chronoGlobal.Elapsed.TotalSeconds) secondes"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " OPERATION TERMINEE"
Write-Host "============================================================"