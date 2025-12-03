# 🎙️ Faster-Whisper-XXL – Manuel complet

## 🧭 Sommaire

* [1️⃣ Introduction et contexte]()
* [2️⃣ Installation &amp; configuration]()
* [3️⃣ Commande parfaite (usage anime japonais)]()
* [4️⃣ Script Python automatisé]()
* [5️⃣ Liste complète des arguments (classée par thème)]()
  * [⚙️ Configuration générale]()
  * [🧠 Tâches &amp; langues]()
  * [🔍 Décodage &amp; génération]()
  * [🎧 VAD – Voice Activity Detection]()
  * [🧹 Filtres audio (pré-traitement)]()
  * [✂️ Segmentation &amp; affichage texte]()
  * [👥 Diarization (multi-locuteurs)]()
  * [🧪 Fonctions avancées]()
  * [🗂️ Formats &amp; sorti]()

---

## 🎬 1. Introduction

**Faster-Whisper-XXL** (r245.4) est une version optimisée de *Whisper* pour Windows, développée par **Purfview (Const-me)**. Elle inclut :

- des améliorations de vitesse (CUDA / CPU optimisé)
- des filtres audio internes (nettoyage, amplification, coupe silencieuse)
- un VAD intégré pour détection automatique de la parole
- un support multi-langue et traduction directe (ex: japonais → anglais)

GitHub officiel : [https://github.com/Purfview/whisper-standalone-win](https://github.com/Purfview/whisper-standalone-win)

Releases : [https://github.com/Purfview/whisper-standalone-win/releases](https://github.com/Purfview/whisper-standalone-win/releases)

---

## ⚙️ 2. Installation & Configuration

![1764701139503](image/readme_faster_whisper_xxl/1764701139503.png)

puis redémarre l'ordu

1. **Télécharge** la dernière version dans **github.com/Purfview/whisper-standalone-win/releases**
2. **Va dans** C:\Program Files\Whisper\Faster-Whisper-XXL
3. Télécharger tes modèles Whisper (`medium`, `large-v3`, etc.) dans : **Whisper\Purfview-Whisper-Faster_models\**
4. Où les télécharger:**huggingface.co/Systran(**faster whisper**)**
5. Assure-toi que le dossier de sortie existe (ex : `C:\Anime\Subs`).

---

## 💡 3. Commande parfaite pour ton usage

```bash
Faster-Whisper-XXL.exe "episode.mkv" ^
--task translate ^
--language ja ^
--output_format srt ^
--output_dir "C:\Anime\Subs" ^
--compute_type float16 ^
--temperature 0 ^
--beam_size 5 ^
--no_repeat_ngram_size 3 ^
--condition_on_previous_text True ^
--standard_asia ^
--vad_filter True ^
--vad_method silero_v5_fw ^
--vad_threshold 0.35 ^
--vad_min_silence_duration_ms 100 ^
--vad_speech_pad_ms 300 ^
--ff_rnndn_xiph ^
--ff_lowhighpass ^
--ff_speechnorm ^
--ff_silence_suppress -50 0.1 ^
--beep_off
```

Cette commande est optimisée pour :

- 🎙️ **traduction japonaise** → anglais
- ✂️ **coupure si pause > 0.10 s**
- 🧹 **nettoyage & amplification audio**
- 💬 **sortie claire (.srt)**
- 💫 **meilleure précision et synchronisation**

---

## 🐍 4. Script Python automatisé

```python
voir fwxxl.py
```

---

## 📖 5. Liste complète des arguments

## 🟢Accélérer commande


Sur  **CPU Intel** , donc le batch size va dépendre de  **ta puissance CPU et du nombre de cœurs réels disponibles** . Voici comment raisonner :

---

## **1. Vérifier tes cœurs**

* Sur Windows, ouvre le  **Gestionnaire des tâches → Performance → CPU** .
* Note le **nombre de cœurs physiques** (pas les threads logiques).
* Exemple : un i7 avec 8 threads = 4 cœurs physiques, 8 logiques.

---

## **2. Batch size recommandé sur CPU**

* Le batch size correspond au  **nombre de segments VAD traités en parallèle** .
* Sur CPU : **batch_size ≈ nombre de cœurs physiques** → c’est le maximum conseillé.
  * Trop petit → pas d’accélération.
  * Trop grand → surcharge, ralentissement.

Exemple :

| Cœurs physiques | batch_size conseillé                     |
| ---------------- | ----------------------------------------- |
| 2                | 2                                         |
| 4                | 4                                         |
| 6                | 6                                         |
| 8                | 8 (mais à tester, parfois 6 plus stable) |

> Note : Les threads logiques (Hyperthreading) ne doublent pas toujours la vitesse pour ce type de calcul intensif.

---

## **3. Astuce pratique**

* Commence par `--batch_size = cœurs physiques`.
* Observe l’utilisation CPU dans le gestionnaire des tâches.
  * Si utilisation < 80% → tu peux augmenter légèrement.
  * Si 100% → réduire pour éviter que le système rame.

---

## **4. Autres options pour CPU**

* Active `--threads` pour limiter le nombre de threads par batch.
  <pre class="overflow-visible!" data-start="1460" data-end="1502"><div class="contain-inline-size rounded-2xl corner-superellipse/1.1 relative bg-token-sidebar-surface-primary"><div class="sticky top-9"><div class="absolute end-0 bottom-0 flex h-9 items-center pe-2"><div class="bg-token-bg-elevated-secondary text-token-text-secondary flex items-center gap-4 rounded-sm px-2 font-sans text-xs"></div></div></div><div class="overflow-y-auto p-4" dir="ltr"><code class="whitespace-pre! language-bash"><span><span>--threads 4 --batch_size 4</span></span></code></div></div></pre>



### ⚙️ 1. Configuration générale

Si tu veux télécharger des models :[https://huggingface.co/openai/whisper-large-v3#model-details](https://huggingface.co/openai/whisper-large-v3#model-details)

et ceux de faster whisper: [https://huggingface.co/collections/Systran/faster-whisper](https://huggingface.co/collections/Systran/faster-whisper)

| Argument            | Description                                                                            | Défaut                     |
| ------------------- | -------------------------------------------------------------------------------------- | --------------------------- |
| `audio`           | **Le ou les fichiers audio/vidéo à transcrire (argument positionnel)**         | -                           |
| `--model`         | Choisit le modèle Whisper (`tiny`,`base`,`small`,`medium`,`large-v3`, etc.) | `medium`                  |
| `--model_dir`     | Dossier des modèles                                                                   | `_models`                 |
| `--device`        | Cible d’exécution (`cpu`,`cuda`, etc.)                                           | auto                        |
| `--output_dir`    | Dossier de sortie                                                                      | même dossier que le média |
| `--output_format` | Format du sous-titre (`srt`,`vtt`,`txt`, etc.)                                   | `srt`                     |
| `--compute_type`  | Quantization (`float16`,`int8`, etc.)                                              | auto                        |
| `--threads`       | Nombre de threads CPU                                                                  | auto (4 max)                |
| `--verbose`       | Affiche logs détaillés                                                               | `False`                   |
| `--beep_off`      | Désactive le bip final                                                                | `False`                   |

Exporter vers Sheets

---

### 🧠 2. Tâches & langues

| Argument                           | Description                                     | Défaut        |
| ---------------------------------- | ----------------------------------------------- | -------------- |
| `--task`                         | `transcribe`(X→X) /`translate`(X→Anglais) | `transcribe` |
| `--language`                     | Code ISO (`ja`,`en`,`fr`, etc.)           | auto           |
| `--multilingual`                 | **Détecte la langue à chaque segment**  | `False`      |
| `--language_detection_threshold` | Confiance min détection                        | `0.5`        |
| `--initial_prompt`               | Prompt initial pour contexte                    | `auto`       |
| `--condition_on_previous_text`   | Cohérence inter-segments                       | `True`       |

Exporter vers Sheets

---

### 🔍 3. Décodage & génération

| Argument                   | Description            | Défaut  |
| -------------------------- | ---------------------- | -------- |
| `--temperature`          | Contrôle créativité | `0`    |
| `--beam_size`            | Largeur recherche      | `5`    |
| `--best_of`              | Nb candidats si temp>0 | `5`    |
| `--patience`             | Tolérance beam search | `2.0`  |
| `--length_penalty`       | Pénalise longueur     | `1.0`  |
| `--repetition_penalty`   | Répétition max       | `1.0`  |
| `--no_repeat_ngram_size` | Supprime répétitions | `0`    |
| `--logprob_threshold`    | Score min confiance    | `-1.0` |
| `--no_speech_threshold`  | Silence                | `0.6`  |

Exporter vers Sheets

---

### 🎧 4. VAD – Voice Activity Detection

| Argument                          | Description                                              | Défaut          |
| --------------------------------- | -------------------------------------------------------- | ---------------- |
| `--vad_filter`                  | Active détection voix                                   | `True`         |
| `--vad_method`                  | `silero_v4_fw`,`silero_v5_fw`,`webrtc`, etc.       | `silero_v4_fw` |
| `--vad_threshold`               | Sensibilité (0–1)                                      | `0.45`         |
| `--vad_min_speech_duration_ms`  | Ignorer segments trop courts                             | `250`          |
| `--vad_max_speech_duration_s`   | **Durée maximale d’un segment (en secondes)**    | `None`         |
| `--vad_min_silence_duration_ms` | Silence min avant coupure                                | `3000`         |
| `--vad_speech_pad_ms`           | Marge autour voix                                        | `900`          |
| `--vad_window_size_samples`     | Taille fenêtre audio                                    | `1536`         |
| `--vad_device`                  | **Matériel utilisé pour VAD (`cpu`,`cuda`)** | `cpu`          |

Exporter vers Sheets

---

### 🧹 5. Filtres audio (pré-traitement)

| Argument                  | Description                                          | Défaut     |
| ------------------------- | ---------------------------------------------------- | ----------- |
| `--ff_track`            | **Choisir la piste audio si plusieurs**        | `1`       |
| `--ff_rnndn_xiph`       | **Denoise léger (Supprime bruit et musique)** | `False`   |
| `--ff_rnndn_sh`         | Denoise fort                                         | `False`   |
| `--ff_fftdn`            | **Denoise FFT (réduit bruit)**                | `None`    |
| `--ff_lowhighpass`      | Passe-bande 50–7800 Hz                              | `False`   |
| `--ff_speechnorm`       | Amplifie voix                                        | `False`   |
| `--ff_loudnorm`         | Normalise volume                                     | `False`   |
| `--ff_gate`             | Réduit bruit faible                                 | `False`   |
| `--ff_silence_suppress` | Supprime silence (dB,durée)                         | `[0,3.0]` |
| `--ff_vocal_extract`    | Sépare voix du fond                                 | `None`    |
| `--ff_tempo`            | **Change vitesse audio**                       | `1.0`     |

Exporter vers Sheets

---

### ✂️ 6. Segmentation & affichage texte

| Argument                    | Description                                                | Défaut    |
| --------------------------- | ---------------------------------------------------------- | ---------- |
| `--sentence`              | Coupe par phrase                                           | `False`  |
| `--standard`              | Mode standard occidental                                   | `False`  |
| `--standard_asia`         | Mode asiatique (JA/ZH)                                     | `False`  |
| `--max_line_width`        | Nb max caractères                                         | `1000`   |
| `--max_line_count`        | Nb lignes max                                              | `1`      |
| `--max_comma`             | **Quand couper après une virgule**                  | `250`    |
| `--max_gap`               | **Gap en secondes > ça devient un nouveau segment** | `3.0`    |
| `--prepend_punctuations`  | **Fusionne ponctuation avec le mot suivant**         | `'“¿([{' |
| `--append_punctuations`   | **Fusionne ponctuation avec le mot précédent**     | `.,!?)`  |
| `--max_initial_timestamp` | **Décalage max du 1er timestamp (en secondes)**     | `None`   |
| `--timestamps_format`     | **Format des timestamps**                            | `format` |
| `--timestamps_threshold`  | **Sensibilité pour les timestamps**                 | `float`  |
| `--highlight_words`       | Mode karaoké                                              | `False`  |
| `--word_timestamps`       | Mots horodatés                                            | `True`   |

Exporter vers Sheets

---

### 👥 7. Diarization (multi-locuteurs)

| Argument                | Description                              | Défaut     |
| ----------------------- | ---------------------------------------- | ----------- |
| `--diarize`           | Active détection locuteurs              | `None`    |
| `--num_speakers`      | Nb fixe de locuteurs                     | `None`    |
| `--min_speakers`      | **Nombre minimum de locuteurs**    | `None`    |
| `--max_speakers`      | **Nombre maximum de locuteurs**    | `None`    |
| `--speaker`           | Nom custom au lieu de "SPEAKER"          | `SPEAKER` |
| `--diarize_dump`      | Sauve résultats diarization             | `False`   |
| `--diarize_only`      | **Sort uniquement la diarisation** | `False`   |
| `--return_embeddings` | Sauve vecteurs vocaux                    | `False`   |

Exporter vers Sheets

---

### 🧪 8. Fonctions avancées

| Argument                              | Description                                                   | Défaut   |
| ------------------------------------- | ------------------------------------------------------------- | --------- |
| `--batch_recursive`                 | Analyse dossier complet                                       | `False` |
| `--skip`                            | Ignore fichiers déjà traités                               | `False` |
| `--hotwords`                        | Mots-clés prioritaires                                       | `None`  |
| `--prefix`                          | **Préfixe imposé pour le début de la transcription** | `None`  |
| `--postfix`                         | **Postfix imposé pour la fin de la transcription**     | `None`  |
| `--ignore_dupe_prompt`              | **Ignore les prompts répétés**                       | `None`  |
| `--reprompt`                        | **Répète prompt si bloc incohérent**                 | `False` |
| `--one_word`                        | **Force la sortie en un seul mot (pour japonais)**      | `0`     |
| `--japanese`                        | Style de sortie japonais (`blend`,`kanji`, etc.)          | `blend` |
| `--hallucination_silence_threshold` | **Anti-hallucination (seuil de silence en secondes)**   | `None`  |
| `--v3_offsets_off`                  | **Désactive certaines corrections pour large-v3**      | `False` |

Exporter vers Sheets

---

### 🗂️ 9. Formats & sortie

| Argument                 | Description                                                   | Défaut   |
| ------------------------ | ------------------------------------------------------------- | --------- |
| `--output_format`      | `srt`,`vtt`,`txt`,`json`,`all`                      | `srt`   |
| `--postfix`            | **Ajouter la langue en suffixe dans le nom du fichier** | `False` |
| `--without_timestamps` | Supprime timecodes                                            | `False` |
| `--print_progress`     | Affiche progression                                           | `False` |
| `--check_files`        | Vérifie erreurs entrée                                      | `False` |

Exporter vers Sheets

---

### 10. Ordre d’exécution recommandé

Voici l'ordre recommandé pour appliquer les options (tiré de `README2`):

1. **Prétraitement audio** → options `--ff_*`
2. **Segmentation audio (VAD)** → options `--vad_*`
3. **Transcription / traduction** → options `--model`, `--task`, `--language`
4. **Post-traitement texte** → options `--word_timestamps`, `--sentence`, `--max_line_width`
5. **Sortie / sous-titres** → options `--output_format`, `--output_dir`

---

## 🟢Argments donnés par le help de faster-whisper-xxl.exe

# 🧠  Paramètres essentiels

| Option          | Valeur         | Description                                          |
| --------------- | -------------- | ---------------------------------------------------- |
| `--model`     | nom du modèle | Modèle Whisper à utiliser (ex :`large-v3-turbo`) |
| `--model_dir` | chemin         | Utilise un dossier local contenant déjà un modèle |
| `audio`       | fichier        | Le fichier audio/vidéo à transcrire                |

Exporter vers Sheets

---

# 📤 3. Options de sortie

| Option                   | Valeur possible          | Description                                              |
| ------------------------ | ------------------------ | -------------------------------------------------------- |
| `--output_dir`         | dossier                  | Dossier où seront enregistrés les fichiers SRT/VTT/TXT |
| `--output_format`      | srt, vtt, txt, json, all | Format(s) de sortie désiré(s)                          |
| `--verbose`            | 0/1/2                    | Niveau de détails dans les logs                         |
| `--task`               | transcribe / translate   | Transcription ou traduction directe                      |
| `--timestamps`         | —                       | Affiche les timestamps (par défaut)                     |
| `--without_timestamps` | —                       | Désactive les timestamps                                |

Exporter vers Sheets

---

# 🌍 4. Langue

| Option         | Valeur      | Description                               |
| -------------- | ----------- | ----------------------------------------- |
| `--language` | code langue | Force la langue (ex :`ja`pour japonais) |
| `--lang`     | 1/2         | Mode langue avancé (Purfview)            |

Exporter vers Sheets

---

# ⚙️ 5. Matrice de calcul / vitesse

| Option             | Valeur                        | Description                             |
| ------------------ | ----------------------------- | --------------------------------------- |
| `--compute_type` | float32, int8, auto, bfloat16 | Précision et vitesse                   |
| `--threads`      | nombre                        | Nombre de threads CPU                   |
| `--beam_size`    | nombre                        | Augmente précision mais ralentit       |
| `--best_of`      | nombre                        | Teste plusieurs propositions de phrases |

Exporter vers Sheets

---

# 🔊 6. VAD (Détection de voix)

| Option                            | Valeur                                                          | Description                                          |
| --------------------------------- | --------------------------------------------------------------- | ---------------------------------------------------- |
| `--vad_method`                  | silero_v4, silero_v5, silero_v5_fw, webrtc, auditok, pyanote_v3 | Choix du moteur VAD (silero_v5_fw = le plus récent) |
| `--vad_filter`                  | —                                                              | Active le filtrage par VAD                           |
| `--vad_threshold`               | 0 → 1                                                          | Sensibilité (bas = plus sensible)                   |
| `--vad_min_speech_duration_ms`  | ms                                                              | Durée minimale d’un segment vocal                  |
| `--vad_max_speech_duration_s`   | sec                                                             | Durée maximale d’un segment                        |
| `--vad_min_silence_duration_ms` | ms                                                              | Silence minimal pour couper                          |
| `--vad_speech_pad_ms`           | ms                                                              | Padding avant/après un segment                      |
| `--vad_window_size_samples`     | taille                                                          | Longueur de la fenêtre d’analyse                   |
| `--vad_device`                  | cpu / cuda                                                      | Matériel utilisé pour VAD                          |

Exporter vers Sheets

---

# 🎵 7. Options audio avancées

| Option              | Description                          |
| ------------------- | ------------------------------------ |
| `--ffmpeg`        | Utilise ffmpeg interne               |
| `--audio_filters` | Filtres audio FFmpeg                 |
| `--ff_dump`       | Enregistre les segments extraits     |
| `--ff-cuda`       | Accélération CUDA FFmpeg           |
| `--ff`            | Mode audio FFmpeg spécial           |
| `--f-crop`        | Coupe automatique les silences/bords |

Exporter vers Sheets

---

# 📝 8. Prompting / contrôle du texte

| Option                   | Description                                   |
| ------------------------ | --------------------------------------------- |
| `--initial_prompt`     | Ajoute un prompt pour guider la transcription |
| `--prefix`             | Préfixe imposé                              |
| `--postfix`            | Postfix imposé                               |
| `--ignore_dupe_prompt` | Ignore les prompts répétés                 |
| `--reprompt`           | Répète prompt si bloc incohérent           |

Exporter vers Sheets

---

# 🕒 9. Gestion des timestamps

| Option                      | Valeur | Description                      |
| --------------------------- | ------ | -------------------------------- |
| `--max_initial_timestamp` | s      | Décalage max du 1er timestamp   |
| `--timestamps_format`     | format | Format des timestamps            |
| `--timestamps_threshold`  | float  | Sensibilité pour les timestamps |
| `--word_timestamps`       | —     | Timestamps par mot               |
| `--highlight_words`       | —     | Coloration mot par mot           |

Exporter vers Sheets

---

# 🧩 10. Japonais (options Purfview)

| Option         | Valeur                               | Description                         |
| -------------- | ------------------------------------ | ----------------------------------- |
| `--japanese` | blend / kanji / hira / hira+katakana | Méthode de transcription japonaise |
| `--one_word` | 0/1/2                                | Force la sortie en un seul mot      |
| `--sentence` | 0/1                                  | Découpe par phrase                 |
| `--standard` | —                                   | Mode standard japonais              |

Exporter vers Sheets

---

# 🗣️ 11. Diarisation (séparation des voix)

| Option                  | Description                                    |
| ----------------------- | ---------------------------------------------- |
| `--diarize`           | Active la diarisation (pyannote, reverb, etc.) |
| `--num_speakers`      | Force un nombre de locuteurs                   |
| `--min_speakers`      | Minimum                                        |
| `--max_speakers`      | Maximum                                        |
| `--diarize_only`      | Sort uniquement la diarisation                 |
| `--return_embeddings` | Retourne les embeddings vocaux                 |
