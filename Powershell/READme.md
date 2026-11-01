a commande **`winget install --id Microsoft.Powershell --source winget`** permet d'installer automatiquement **PowerShell 7 (pwsh)** sur votre système Windows via **Windows Package Manager** (winget).

Voici le détail de chaque partie de la commande :

* **`winget install`** : Indique au gestionnaire de paquets de Windows de télécharger et d'installer un logiciel.
* **`--id Microsoft.Powershell`** : Spécifie l'identifiant exact du paquet à installer (ici, la version moderne de PowerShell 7).
* **`--source winget`** : Indique de rechercher ce paquet directement dans le dépôt officiel de Microsoft Winget (pour s'assurer de récupérer la source officielle).

### Quelle est la différence après l'installation ?

* **PowerShell 5.1 (déjà sur votre PC)** : C'est la version historique intégrée à Windows (`powershell.exe`).
* $PSVersionTable.PSVersion

Major  Minor  Build  Revision

---

5      1      19041  7725

**PowerShell 7 (installé via cette commande)** : C'est la version moderne, multiplateforme et plus rapide (`pwsh.exe`). C'est **cette version** qui débloque la fonctionnalité de traitement parallèle (`ForEach-Object -Parallel`) dans vos scripts.


### Configurer VS Code pour exécuter toujours PowerShell 7 par défaut

Pour que le bouton **Run** / Code Runner lance automatiquement PowerShell 7 au lieu de la version 5.1 :

1. Ouvrez les paramètres de VS Code (`Ctrl + ,`).
2. Tapez **`Code-runner: Executor Map`** dans la barre de recherche.
3. Cliquez sur  **Modifier dans settings.json** .
4. Modifiez la ligne `"powershell"` pour qu'elle utilise `pwsh` au lieu de `powershell` :
