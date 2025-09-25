    https://montreal-forced-aligner.readthedocs.io/en/v3.1.3/user_guide/workflows/alignment.html#pretrained-alignment

On active l'environment :
    conda activate aligner
Important pour pouvoir utiliser mfa dans le terminal sinon faut toujours mettre le chemin complet
python -m montreal_forced_aligner align ...

mfa align_one est une version simplifiée de mfa align conçue pour aligner un seul fichier audio avec sa
transcription.
Elle est + directe et ne nécessite pas de créer un dossier de corpus.
mfa align_one `<OPTIONS>` <AUDIO_FILE> <TRANSCRIPTION_FILE> <DICTIONARY_PATH> <ACOUSTIC_MODEL> <OUTPUT_DIRECTORY> [OPTIONS]
    Fichier audio : C:\Users\babak\Videos\PSO\Episode\chibi_12half.mp3

    Fichier texte : C:\Users\babak\Videos\PSO\Episode\chibi_12half.txt

    Dossier de sortie : C:\Users\babak\Videos\PSO\Episode\output_align

mfa align `<OPTIONS>` `<CORPUS>` <DICTIONARY_PATH> <ACOUSTIC_MODEL> <OUTPUT_DIRECTORY>

| Argument               | Description                                                          |
| ---------------------- | -------------------------------------------------------------------- |
| `<CORPUS>`           | Dossier contenant les fichiers audio à aligner (WAV mono 16 kHz).   |
| `<DICTIONARY_PATH>`  | Dictionnaire phonétique (ou dossier contenant des dictionnaires).   |
| `<ACOUSTIC_MODEL>`   | Modèle acoustique pour la langue (english, french, japanese, etc.). |
| `<OUTPUT_DIRECTORY>` | Dossier où MFA enregistrera les fichiers alignés (textgrid ).      |
| `[OPTIONS]`          | Options facultatives :                                               |

Faut toujours que le txt ait le meme nom que l'audio

I/OPTIONS
    A/Options de Configuration et de Fichier
        --config_path :
            Utilisez un fichier YAML pour configurer des paramètres complexes.
            fichier YAML? : Un fichier YAML est un format de fichier lisible par l'homme utilisé pour
            configurer des paramètres.

    mfa align -c my_config.yaml /chemin/vers/mon_corpus/ mon_dico_fr mon_modele_acoustique_fr /chemin/vers/mon_output/

    --speaker_characters :
            Si vos fichiers sont nommés locuteur1_fichier.wav, locuteur2_fichier.wav,
            vous pouvez dire à MFA d'utiliser les 9 premiers caractères pour identifier le locuteur.
            Il utilise les noms de fichiers pour identifier les locuteurs afin de pouvoir adapter le
             modèle acoustique à la voix de chaque personne.
            L'adaptation du locuteur (speaker adaptation) est une technique où MFA ajuste légèrement le
            modèle acoustique pour qu'il soit + précis pour la voix d'un locuteur particulier.
            Cela améliore considérablement la qualité de l'alignement.

    Exemple 1:
                    Si vos fichiers sont nommés comme ça : speaker01_sentence1.wav, speaker02_sentence2.wav
                    Vous pouvez utiliser --speaker_characters 9 pour que MFA reconnaisse "speaker01" et "speaker02"
                    comme des locuteurs distincts.

    Exemple 2: avec --speaker_characters 9 :

    locuteur1_discoursA.wav,locuteur1_discoursB.wav,locuteur2_discoursC.wav,locuteur2_discoursD.wav
                    MFA va identifier 2 groupes :
                    Le groupe "locuteur1" (basé sur les 9 premiers caractères locuteur1_).
                    Le groupe "locuteur2" (basé sur les 9 premiers caractères locuteur2_).

    Il va alors entraîner un modèle adapté pour "locuteur1" en utilisant tous ses fichiers
                    d'entraînement (discoursA et discoursB), et un autre modèle adapté pour "locuteur2"
                    en utilisant ses fichiers (discoursC et discoursD).

    mfa align --speaker_characters 9 /chemin/vers/mon_corpus/ ...

    --audio_directory :
            Si vos fichiers audio sont dans un dossier séparé de vos transcriptions.
            Par exemple, si vos fichiers audio sont dans /chemin/vers/audio/ et  vos transcriptions sont dans
            /chemin/vers/transcriptions/, vous pouvez utiliser cette option pour spécifier le dossier
            mfa align --audio_directory /chemin/vers/audio/ /chemin/vers/transcriptions/ mon_dico_fr ...

    --output_format : Pour obtenir les résultats en format JSON plutôt que le .TextGrid par défaut.
            Options
                long_textgrid | short_textgrid | json | csv
            mfa align --output_format json /chemin/vers/mon_corpus/ mon_dico_fr mon_modele_acoustique_fr /chemin/vers/mon_output/

    --g2p_model_path : Si vous avez un modèle G2P personnalisé pour gérer les mots inconnus.
         G2P? : G2P signifie "Grapheme-to-Phoneme".
                C'est un processus qui convertit les lettres (graphemes) d'un mot en sons (phonemes).
                Par exemple:
                 -Le mot anglais "cat" est converti en phonemes /k/ /æ/ /t/.
            Cela est particulièrement utile pour les mots qui ne sont pas dans le dictionnaire phonétique.

    mfa align --g2p_model_path /chemin/vers/mon_modele_g2p.zip /chemin/vers/mon_corpus/ ...

    --temporary_directory :
         Pour changer l'emplacement des fichiers temporaires (utile pour des raisons d'espace disque).
            mfa align -t /chemin/vers/dossier_temporaire/ /chemin/vers/mon_corpus/ ...

    --num_jobs : Pour accélérer le processus en utilisant plus de cœurs de votre processeur.
            mfa align -j 8 /chemin/vers/mon_corpus/ ...
            Par défaut, MFA utilise 3 cœurs

    Informations système :
                -Appuyez sur la touche Windows + R, puis tapez msinfo32 et appuyez sur Entrée.
                -Dans la fenêtre Résumé système, cherchez Processeur. Le nombre de cœurs y est indiqué.
                Par exemple, "Intel(R) Core(TM) i7-9700 CPU @ 3.00GHz, 8 Cœurs".
                         	  Intel(R) Core(TM) i5-6300U CPU @ 2.40GHz, 2501 MHz, 2 cœur(s), 4 processeur(s) logique(s)
                                -2 cœurs : Ce sont les cœurs physiques, les unités de traitement
                                réelles du processeur.

    -4 processeurs logiques : C'est le nombre de threads. Votre processeur
                                utilise la technologie Hyper-Threading, ce qui permet à chaque cœur
                                physique de gérer 2 threads.
                                Pour les applications gourmandes en ressources comme MFA, c'est le nombre de processeurs logiques qui importe.

    Pour tirer le meilleur parti de votre processeur avec MFA, vous devez définir l'option --num_jobs (ou -j) sur 4 dans votre ligne de commande.

    B/Options de Nettoyage et de Sortie
        --clean :
            Pour s'assurer que le dossier de sortie est vidé avant de commencer l'alignement.
                mfa align --clean /chemin/vers/mon_corpus/ mon_dico_fr mon_modele_acoustique_fr /chemin/vers/mon_output/

    --final_clean :
            Pour ne pas laisser de fichiers temporaires une fois le processus terminé.
                mfa align --final_clean /chemin/vers/mon_corpus/ ...

    --verbose :
            Pour afficher plus d'informations détaillées sur le déroulement de l'alignement.
            Il est très utile pour diagnostiquer les problèmes si l'alignement échoue ou pour surveiller
            la progression sur de grands corpus.
            Pour une utilisation de base, le mode par défaut est suffisant, mais si vous rencontrez des
            difficultés, --verbose est la première option à essayer.

    mfa align -v /chemin/vers/mon_corpus/ ...
            Par exemple:
                1/Détails sur l'environnement et la configuration
                    -Le chemin vers le corpus, le dictionnaire, et le modèle acoustique que MFA est en train
                    d'utiliser.

    -Les paramètres tels que le nombre de cœurs de processeur (num_jobs) utilisés.

    -Les chemins des dossiers temporaires et de sortie.

    2/Statut du corpus :
                    -Le nombre de fichiers audio et de transcriptions trouvés dans le corpus.
                    -Les noms des locuteurs identifiés par MFA.
                    -Un résumé des transcriptions :
                        le nombre de mots, le nombre de mots inconnus (Out-of-Vocabulary ou OOV) pour lesquels MFA a besoin d'une prédiction.

    3/Progression de chaque étape :
                    -Nettoyage :
                    Si vous utilisez --clean, MFA vous dira quels fichiers il est en train de supprimer.

    -Génération du dictionnaire :
                        MFA affichera la progression de la prédiction des prononciations pour les mots
                        inconnus. Vous verrez quels mots sont traités et combien de temps cela prend.

    -Acoustic Modeling (Modélisation acoustique) :
                        Cette étape est la plus longue. MFA vous montrera la progression de chaque itération
                        (l'étape d'entraînement).
                        Vous verrez des informations comme la log-likelihood (une mesure de la qualité du modèle), ce qui est utile pour les experts.

    -Alignment (Alignement) :
                        La progression de l'alignement pour chaque fichier. Vous verrez les noms des fichiers
                        audio au fur et à mesure qu'ils sont alignés.

    4/Messages d'avertissement et d'erreur (plus précis) :
                    -Si un fichier audio ne peut pas être lu, le mode verbose donnera plus de détails sur
                     la raison de l'échec.

    -Si un mot n'est pas dans le dictionnaire et ne peut pas être prédit, MFA le signalera.

    --quiet : Pour ne pas afficher d'informations du tout.
            mfa align -q /chemin/vers/mon_corpus/ ...

    --overwrite : Pour écraser les fichiers existants sans que MFA ne s'arrête.
            mfa align --overwrite /chemin/vers/mon_corpus/ ...

    C/Options de Performance
        --fine_tune :
         Pour une meilleure précision sur un corpus difficile.
            -mfa align --fine_tune /chemin/vers/mon_corpus/ ...

    --single_speaker :
            Si tout votre corpus provient du même locuteur.
                mfa align --single_speaker /chemin/vers/mon_corpus/ ...

    D/Options de Débogage et Post-traitement
        --debug : Pour la résolution de problèmes.
            mfa align -d /chemin/vers/mon_corpus/ ...

    --textgrid_cleanup :
            Pour améliorer la lisibilité des .TextGrid en regroupant des mots ou en gérant les silences.
            mfa align --textgrid_cleanup /chemin/vers/mon_corpus/ ...

II/Corpus:
    MFA fonctionne avec de nombreux types de fichiers audio et vidéo.
    Il utilise FFmpeg en arrière-plan pour gérer ces formats.

    A/Fichiers audio
            MFA est très robuste et peut gérer une grande variété de formats audio, incluant :

    .wav (le format le plus recommandé),.mp3,.flac,.m4a,.aiff,.ogg

    MFA convertira automatiquement ces fichiers en .wav (mono, 16 kHz) avant de les traiter.
        Cette conversion se fait en mémoire, vous n'avez pas besoin de le faire manuellement,

    B/Fichiers vidéo
           MFA peut également traiter les fichiers vidéo si FFmpeg est correctement installé et accessible
           sur votre système. MFA ne traite que la piste audio de la vidéo.

    Formats vidéo supportés : .mp4,.mkv,.avi,.mov,.wmv

III/Dictionnaire phonétique:
    Le dictionnaire phonétique est crucial pour l'alignement. Il mappe les mots aux séquences de phonèmes.
    Vous pouvez utiliser des dictionnaires préexistants ou en créer un personnalisé.

    A/Dictionnaires préexistants
            MFA fournit des dictionnaires(pré-entrainé) pour plusieurs langues courantes, incluant :
                -Anglais : english
                -Français : french
                -Japonais : japanese
                -Espagnol : spanish
                       ...

    B/Créer un dictionnaire personnalisé
            Si votre corpus contient des mots non présents dans les dictionnaires fournis,
            vous devrez créer un dictionnaire personnalisé.
            Le format du dictionnaire est simple : chaque ligne contient un mot suivi de ses phonèmes,
            séparés par des espaces.

    Exemple :
                hello HH AH0 L OW1
                world W ER1 L D

    C/Utiliser des outils pour générer des dictionnaires
            Pour les langues comme l'anglais, vous pouvez utiliser des outils comme le CMU Pronouncing Dictionary.
            Pour d'autres langues, vous pouvez utiliser des outils de text-to-phoneme (T2P) ou des services en ligne.

IV/Modèles acoustiques:
    MFA utilise des modèles acoustiques pour aligner les phonèmes aux segments audio.
    phonèmes? : Les phonèmes sont les unités de son distinctes dans une langue.
    Par exemple simple :
        -Le mot "cat" en anglais est composé de trois phonèmes : /k/, /æ/, /t/.
        -Le mot "chat" en français est composé de trois phonèmes : /ʃ/, /a/, /t/.
        -Le mot "犬" (inu) en japonais est composé de trois phonèmes : /i/, /n/, /u/.
        -Le mot "gato" en espagnol est composé de quatre phonèmes : /g/, /a/, /t/, /o/.

    Vous devez spécifier le modèle acoustique correspondant à la langue de votre corpus.

    A/Modèles préexistants
            MFA fournit des modèles acoustiques pour plusieurs langues courantes, incluant :
                -Anglais : english
                -Français : french
                -Japonais : japanese
                -Espagnol : spanish
                       ...

    B/Créer un modèle acoustique personnalisé
            Si vous travaillez avec une langue ou un dialecte non couvert par les modèles fournis,
            vous pouvez entraîner votre propre modèle acoustique en utilisant vos données annotées.
            Cela nécessite une quantité significative de données et une expertise en apprentissage automatique.

Difference entre Dictionnaire et Modèle acoustique:
    -Le dictionnaire phonétique mappe les mots aux phonèmes.
        Par exemple : "cat" → /k æ t/
    -Le modèle acoustique mappe les phonèmes aux caractéristiques audio.
        Par exemple 1: /k/ → caractéristiques audio spécifiques du son "k"

    -Les deux sont essentiels pour un alignement précis.

V/ Répertoire de sortie:
    Créez un dossier vide pour les résultats, par exemple C:/Users/babak/Videos/PSO/Episode/output_align/
    NB: mfa align_one ne créera automatiquement le dossier s'il n'existe pas.
    MFA enregistrera les fichiers alignés dans ce dossier.
        Attention:
            -Le dossier de sortie doit être vide avant d'exécuter MFA.
            Si le répertoire de sortie n'est pas vide, la commande mfa align affichera une erreur et
            s'arrêtera. Cette exigence est une mesure de sécurité pour éviter que MFA n'écrase
            accidentellement des données existantes.

    Si vous voulez réutiliser un répertoire qui contient des résultats d'une exécution précédente, vous avez
                2 options :

    1.Vider manuellement le répertoire avant de lancer la commande.

    2.Utiliser le drapeau --clean avec votre commande mfa align.

🔵Exemples pratiques

    mfa align_one ^
    C:/Users/babak/Videos/PSO/Episode/Audio/chibi_12half.wav ^
    C:/Users/babak/Videos/PSO/Episode/Txt/chibi_12half.txt ^
    japanese_mfa ^
    japanese_mfa ^
    C:/Users/babak/Videos/PSO/Episode/output_align ^
    --beam 40

    ou en une ligne

    mfa align_one -v C:/Users/babak/Videos/PSO/Episode/chibi_12half.wav C:/Users/babak/Videos/PSO/Episode/PSO24.txt japanese_mfa japanese_mfa C:/Users/babak/Videos/PSO/Episode/output_align --beam 40

    -Le dossier output_align est créé automatiquement s’il n’existe pas.
    -Le fichier de sortie sera chibi_12half.TextGrid dans output_align.

   NB:
   Si tu obtiens l'erreur:
    Could not align the file with the current beam size (10, please try increasing the beam size via `--beam X`)
    Tu peux ajouter l’option --beam 20 (ou 30, 40, etc.) à la fin de la commande.

    Alignement en ligne (online alignment) :
        MFA utilise un algorithme de « beam search » pour trouver la meilleure correspondance
        phonème ↔ audio.

    Beam size = 10 par défaut :
        ça limite le nombre de chemins considérés.
        Pour certains fichiers audio (longs, bruyants ou avec des mots rares),
        10 chemins c’est trop peu → MFA échoue.

    Le beam size est un hyperparamètre lié à la complexité de l’audio et à la longueur des phrases.

    MFA ne peut pas prédire à l’avance combien de chemins seront nécessaires.

    --retry beam
            Si MFA échoue avec le beam size , il te suggère d’augmenter cette valeur.
            MFA  refaitautomatiquement  l’alignement avec ce beam plus large avant d’abandonner.
            -Gain de temps : pas besoin de relancer manuellement.

- -Robustesse: certains fichiers difficiles passent avec un beam plus large.

  - retry beam= beam de secours, utilisé automatiquement si le beam principal échoue.
  - Sert à augmenter les chances de succès de l’alignement sans intervention manuelle.
  - Plus le retry beam est grand, plus l’alignement est tolérant, mais plus il est lent.

  💡 Voici quelques conseils pratiques pour le choisir :

  Commencer petit :

  --beam 10 (valeur par défaut) → rapide, mais risque d’échec si l’audio est long ou complexe.

  Augmenter progressivement si ça échoue : --beam 20 → 50 → 100

  Longueur de fichier :
  -Fichiers courts (< 1 min) → <=50 recommandé.

Si tout se passe bien,un fichier .Textgrid sera créé dans le dossier output_align.
    Si tu veux convertir le TextGrid en SRT, tu peux utiliser le script textgrid_to_srt.py
    (voir Caption_and_aligner/MFA_aligner/textgrid_to_srt.py).

    Si tu remarques qu'il des`<unk>` dans le TextGrid, c'est que MFA n'a pas trouvé la prononciation de certains mots.
    Il faut créer un lexique personnalisé (custom lexicon) pour ajouter les prononciations manquantes.
    Il faut alors utiliser la fonction g2p (grapheme-to-phoneme).
    Cette fonction permet à MFA de deviner la prononciation des mots qui ne sont pas dans son dictionnaire.

    Étapes pour corriger l'alignement avec G2P


        🟢Générer un dictionnaire temporaire


            Vous allez demander à MFA de créer un nouveau fichier de dictionnaire qui inclura la
            prononciation des mots inconnus dans votre texte.
            Le MFA va analyser votre fichier texte (chibi_12half.txt) et, pour tous les mots qui ne
            figurent pas dans son dictionnaire par défaut (japanese_mfa), il va prédire leur prononciation en phonèmes et les ajouter à un nouveau fichier.

    Ex: **mfa g2p C:/Users/babak/Videos/PSO/Episode/Txt/chibi_12half_cleaned.txt ^
                    C:/Users/babak/Documents/MFA/pretrained_models/g2p/japanese_mfa.zip ^
                    C:/Users/babak/Videos/PSO/Episode/custom_g2p_lexicon.txt**

    🔴Comment fonctionne mfa g2p?

    🔵Cas d'utilisation principaux
                    -Compléter un dictionnaire existant :
                        Vous pouvez lancer l'utilitaire de validation sur votre corpus pour identifier
                        tous les mots "hors-vocabulaire" (OOVs). Le MFA générera alors un fichier
                        oovs_found.txt que vous pouvez utiliser pour créer un dictionnaire qui ne contient
                        que les mots qui manquent.

    -Générer un dictionnaire à partir de zéro :
                        L'utilisation la + courante est de lui donner un fichier texte complet en entrée
                        (INPUT_PATH).
                        Le MFA traitera chaque mot et générera une prononciation pour ceux qui ne sont pas
                        reconnus.

    -Mode "pipe" (stdin/stdout) :
                        Pour un traitement + rapide, vous pouvez faire passer du texte en entrée (stdin)
                        et diriger le résultat directement vers la sortie standard (stdout)

    🔵Syntaxe
                mfa g2p [OPTIONS] INPUT_PATH G2P_MODEL_PATH OUTPUT_PATH
                -OPTIONS : pratiquement les mêmes que mfa align
                    1. Pour les données et les chemins

    -c, --config_path: Spécifie un fichier de configuration pour l'utilitaire G2P.
                            Permet d'utiliser un fichier de configuration spécial (.yaml) pour l'exécution.
                            Pourquoi l'utiliser :
                            Si vous avez un projet complexe avec de nombreux paramètres à ajuster,
                            il est plus pratique de les sauvegarder dans un fichier.
                                Exemple : mfa g2p -c ma_config.yaml

    -t, --temporary_directory:
                            Permet de spécifier où le MFA doit stocker ses fichiers de travail temporaires. Par défaut,
                            il utilise un dossier dans le répertoire utilisateur(C:\Users\babak\Documents\MFA\Temp)
                            Pourquoi l'utiliser :
                            Si vous manquez d'espace sur votre disque C ou si vous voulez utiliser un SSD pour accélérer le
                            processus.
                                Exemple : mfa g2p -t D:\temp **2. Pour optimiser la performance**
                        -J, --num_jobs:
                            Définit le nombre de cœurs de processeur que le MFA utilisera.Par défaut= 3.
                            Pourquoi l'utiliser : Pour accélérer le processus. L'augmentation du nombre de cœurs permet de diviser le travail et d'obtenir des résultats plus rapidement.
                                Exemple : mfa g2p -J 4 (utilise 4 cœurs).

    --use_mp, --use_threading:
                            Ces options gèrent la manière dont MFA utilise le processeur.
                            Le "multiprocessing" (--use_mp) est la méthode recommandée pour des performances
                            optimales.
                            Pourquoi les utiliser :
                            Pour ajuster la gestion des processus en fonction de la configuration de
                            votre machine et obtenir les meilleures performances possibles.
                                Exemple : mfa g2p --use_mp

    --single_speaker :
                            Mode locuteur unique. Le MFA est normalement conçu pour traiter plusieurs locuteurs.
                            Cette option lui indique de diviser les tâches par énoncé plutôt que par locuteur,
                            ce qui est utile si vous n'avez qu'une seule personne qui parle.
                            Pourquoi l'utiliser :
                            Pour les petits corpus, cela optimise la façon dont MFA gère les tâches de
                            traitement. C'est plus efficace que la méthode par défaut.

    Ex: mfa g2p --single_speaker ...

    **3. Pour gérer les fichiers et les erreurs**
                        --clean: Supprime les fichiers temporaires des exécutions précédentes.
                            Pourquoi l'utiliser :
                            Pour éviter les erreurs de type FileExistsError
    Exemple : mfa g2p --clean

    --final_clean:
                            Supprime les fichiers temporaires une fois que l'exécution est terminée
                            avec succès.
                            Pourquoi l'utiliser :
                            Pour s'assurer que le dossier temporaire soit toujours vide et que votre
                            espace disque ne soit pas encombré.

    Exemple : mfa g2p --final_clean

    --overwrite:
                            Permet d'écraser un fichier de sortie s'il existe déjà, sans demander de
                            confirmation.
                            Pourquoi l'utiliser :
                            Pour ne pas avoir à supprimer manuellement votre fichier de dictionnaire
                            personnalisé à chaque fois que vous relancez la génération.
                                Exemple : mfa g2p --overwrite

    **4. Pour la précision et les mots inconnus**
                        -n, --num_pronunciations:
                            Permet de générer plusieurs prononciations alternatives pour un seul mot.
                            Pourquoi l'utiliser :
                            Pour augmenter les chances que le MFA trouve la prononciation correcte si un
                            mot peut être prononcé de plusieurs manières.
                                Exemple : mfa g2p -n 3 (génère les 3 prononciations les plus probables).

    --DICTIONARY_PATH:
                            Permet de spécifier un dictionnaire existant.
                            MFA ne générera alors une prononciation que pour les mots qui ne s'y trouvent
                            pas déjà.
                            Pourquoi l'utiliser :
                            C'est utile pour "compléter" un dictionnaire existant au lieu de tout refaire
                            depuis le début.
                                Exemple : mfa g2p --DICTIONARY_PATH existant.dict

    --include_bracketed:
                        Permet de prendre en compte les mots qui sont entre parenthèses
                        ([...], (...), <...>) lors de l'analyse du texte.
                        Pourquoi l'utiliser :
                        Pour que le MFA ne les ignore pas. C'est utile si ces balises sont des mots
                        que vous voulez aligner, et non des bruits de fond.
                            Exemple : mfa g2p --include_bracketed

 **5. Options pour le débogage et le diagnostic**

    -v, --verbose :
                            Active les messages de débogage pour avoir plus d'informations sur ce que le
                            MFA est en train de faire. Par défaut, cette option est désactivée.
                            Pourquoi l'utiliser :
                            Pour le débogage. Si l'alignement échoue, l'option verbose permet de voir
                            les erreurs en détail et de comprendre pourquoi le programme a arrêté.

    -q, --quiet :
                        C'est l'inverse de l'option précédente. Elle masque tous les messages de sortie et
                        d'information. C'est utile si vous exécutez la commande en arrière-plan et que vous
                        ne voulez pas polluer la console.

    -h, --help :
                        Affiche un message d'aide sur la commande et ses options.
                        C'est la première chose à faire si vous avez des doutes sur la syntaxe.

    -INPUT_PATH : Le chemin vers votre fichier texte ou  pour l'entrée standard.
                -G2P_MODEL_PATH : Le chemin vers le modèle G2P que vous avez téléchargé (voir 8.)
                -OUTPUT_PATH : Le chemin où le dictionnaire de prononciation sera sauvegardé

    🟢**Lancer l'alignement avec le nouveau dictionnaire**
            Une fois que le dictionnaire est généré, vous pouvez relancer votre commande d'alignement.
            Cette fois, vous y ajoutez l'option --custom_dictionary pour que MFA utilise le fichier que
            vous venez de créer(custom_g2p_lexicon)

    **mfa align C:/Users/babak/Videos/PSO/Episode/temp/ ^
                C:/Users/babak/Videos/PSO/Episode/custom_g2p_lexicon.txt ^
                japanese_mfa ^
                C:/Users/babak/Videos/PSO/Episode/output_align/ ^
                --beam 40 --clean**

    Si tu as l'erreur:(Prochaine fois ajoute -clean)
                        FileExistsError: [WinError 183] Impossible de créer un fichier déjà existant:
                        'C:\\Users\\babak\\Documents\\MFA\\temp\\alignment\\phones.txt' ->
                        'C:\\Users\\babak\\Documents\\MFA\\temp\\dictionary\\phones\\phones.txt'

    solution:
                            supprimer manuellement le dossier temporaire de MFA avant de relancer la commande.

    Allez à cet emplacement sur votre disque dur :
                            C:\\Users\\babak\\Documents\\MFA\\temp\\.
