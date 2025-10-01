## décu mfa resultat mauvais capcut et clipchamp mieux ,peut etre a retester un jour



https://montreal-forced-aligner.readthedocs.io/en/latest/installation.html

    https://github.com/MontrealCorpusTools/Montreal-Forced-Aligner/releases/tag/v3.3.4

    Intaller Conda

1. Download and install Miniconda from https://www.anaconda.com/download/success
   Je te conseille d'installer
   Anaconda Distribution
   -Très gros package (3–4 Go).
   -Installe Python + des centaines de librairies scientifiques (numpy, pandas, etc.) d’un coup.
   -Idéal si tu veux un environnement prêt à l’emploi, mais lourd.

   Miniconda

   -Version légère (quelques centaines de Mo).
   -Installe seulement Python + conda.
   -Ensuite, tu ajoutes seulement les librairies dont tu as besoin.
   Plus flexible et recommandé si tu n’as pas besoin de tout Anaconda.
2. Ouvrir un terminal (Anaconda Prompt sous Windows)
   NB: Ne pas ajouter Anaconda/Miniconda au PATH lors de l’installation.
   Utiliser Anaconda Prompt pour éviter les conflits de version de Python.

3.Utiler mamba plutotôt que conda (optionnel mais recommandé)
    -Mamba est un remplaçant rapide de conda.
    -Compatible avec tous les environnements Conda.
    -Beaucoup + rapide pour créer, installer et mettre à jour des packages que conda classique.

    Tu l’installes dans l’environnement base de Conda.
       -conda activate base
       -conda install -c conda-forge mamba

4..Installer MFA Aligner
   -mamba create -n aligner -c conda-forge montreal-forced-aligner # cree un environnement "aligner" avec MFA
   -conda activate aligner # active l’environnement "aligner" où MFA est installé

5.Mettre à jour Montreal Forced Aligner(MFA)
    mamba update -c conda-forge montreal-forced-aligner kalpy "kaldi=*=cpu*"

6.Installer SpeechBrain
    CPU: conda install pytorch torchvision torchaudio cpuonly -c pytorch
    GPU: conda install pytorch torchvision torchaudio pytorch-cuda=11.7 -c pytorch -c nvidia

    C'est quoi CPU et GPU?
            CPU: Central Processing Unit (Processeur central)
            GPU: Graphics Processing Unit (Processeur graphique)
            -Le CPU est le cerveau principal de l’ordinateur, gérant les tâches
            générales.
            -Le GPU est spécialisé dans le traitement parallèle, idéal pour les calculs
            graphiques et les tâches intensives comme l’apprentissage automatique.
                Pour les tâches d’apprentissage automatique, un GPU puissant peut accélérer
                considérablement les calculs par rapport à un CPU seul.

    Quand savoir si ton ordi peut utiliser ?
            -Si tu as une carte graphique NVIDIA récente, tu peux utiliser le GPU.
            -Sinon, tu peux toujours utiliser le CPU, mais ce sera plus lent pour les tâches lourdes.

7.Dans le dossier dans lequel tu veux travailler:
     a/ Créer un environnement local dans ton projet (passe par Anaconda Prompt)
       mamba create -p ./env -c conda-forge montreal-forced-aligner

    -p ./env → crée un dossier env dans MFA_aligner.

    conda env export > environment.yml # sauvegarde les dépendances dans environment.yml
             -Tu peux partager environment.yml avec d’autres personnes pour qu’elles puissent recréer le
                même environnement.

    Un fichier environment.yml est un fichier texte qui contient une liste de toutes les dépendances
        de votre projet, y compris les versions spécifiques des bibliothèques Python et du programme mfa.
         Il sert de "recette" pour recréer l'environnement.

    b/ Activer l’environnement local
         conda activate ./env

    A quoi ça sert?
        -Tu peux avoir plusieurs environnements Conda sur ton ordi.
        -Chaque environnement peut avoir des versions différentes de Python et des librairies.
        -L’environnement local dans ton projet garantit que tu utilises les bonnes versions spécifiques
         à ce projet.
        -Tu évites les conflits entre projets.

LAngues dans MFA:
    -french
    -english
    -spanish
    -japanese
    ...

8/Télécharger les modèles japonais(ou peut importe celui que tu veux)

    Toujours depuis ton environnement activé ((env) devant ton prompt) :

    mfa model download acoustic japanese_mfa
        mfa model download dictionary japanese_mfa
        mfa model download g2p japanese_mfa

    ⚠️ Ces deux modèles sont nécessaires :

    acoustic model = reconnaissance des sons de la langue

    dictionary model = prononciations pour mapper texte → phonèmes

    Mais en plus, pour le japonais, MFA a besoin de segmenter correctement le texte avant l’alignement.
    C’est là qu’intervient le tokenizer.
        -Pour les langues comme l’anglais ou le français, tout est souvent inclus dans le modèle et le
        dictionnaire.

    Pour le japonais, MFA ne peut pas segmenter le texte correctement sans les paquets Spacy + Sudachi.

    Donc même si tu as téléchargé le dictionnaire et le modèle acoustique, tu dois installer :

    conda install -c conda-forge spacy sudachipy sudachidict-core

    Sinon, MFA ne peut pas lire le texte japonais et va lever cette erreur.
