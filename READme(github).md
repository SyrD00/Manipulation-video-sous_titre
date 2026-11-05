Ne jamais commit truc >100mo

si vscode n'arrive pas a synchroniser

![1762108367463](image/READme(github)/1762108367463.png)

fais

git fetch origin main
git reset --soft origin/main


---

**« Récupérer » (Fetch) sert à préparer la synchronisation sans modifier tes fichiers locaux.**

Je t'explique avec un exemple concret.

### Imaginons cette situation

Tu as un fichier `script.ps1` sur ton PC et sur GitHub.

1. Sur ton PC, ton fichier contient la version A.
2. Tu vas sur GitHub et tu modifies le fichier : il passe à la version B.
3. Tu retournes sur VS Code.

Voici ce qui se passe selon la commande \:

| Commande                      | Ce qu'elle fait                                                                                                            |
| ----------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| **Récupérer (Fetch)** | Télécharge les informations sur les changements et te permet de voir ce qui a changé. Ne modifie pas ton fichier local. |
| **Tirer (Pull)**        | Récupère les changements ET les applique à tes fichiers locaux.                                                         |
| **Push**                | Envoie tes modifications locales vers GitHub.                                                                              |

### Alors, à quoi sert Fetch ?

Imagine que tu travailles sur un projet important.

Tu veux vérifier si quelqu'un a modifié des fichiers sur GitHub avant de mettre à jour ton PC.

Tu fais **Fetch** \:

- Git vérifie les nouveautés sur GitHub.
- Il actualise les références de la branche distante (`origin/main`, par exemple).
- Tu peux comparer les changements avec ta version locale.
- Tu décides ensuite si tu veux faire un Pull.

### Mon conseil pour ton utilisation

Si tu es le seul à modifier ton dépôt et que tu fais des changements directement sur GitHub depuis le navigateur \:

**Tu peux simplement utiliser « Tirer (pull) » à chaque fois que tu veux mettre à jour ton PC.**

Tu n'as pas besoin de faire Fetch avant chaque Pull.
