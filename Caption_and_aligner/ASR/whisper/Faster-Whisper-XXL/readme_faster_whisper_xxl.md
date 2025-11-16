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

1. **Télécharge** la dernière version (ex : `Whisper_Advanced_r245.4.zip`).
2. **Décompresse** le dossier et repère `Faster-Whisper-XXL.exe` puis place le dans C:\Program Files\Whisper\
3. (Optionnel) Ajoute tes modèles Whisper (`medium`, `large-v3`, etc.) dans :
   ```
   Whisper\Purfview-Whisper-Faster\_models\
   ```
4. Assure-toi que le dossier de sortie existe (ex : `C:\Anime\Subs`).

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
import subprocess
import os

# ===============================
# ⚙️ CONFIGURATION UTILISATEUR
# ===============================
input_file = r"C:\Anime\Episodes\episode.mkv"
output_dir = r"C:\Anime\Subs"
whisper_exe = r"C:\Program Files\Whisper\Faster-Whisper-XXL.exe"

# Vérifications
if not os.path.exists(input_file):
    raise FileNotFoundError(f"❌ Fichier introuvable : {input_file}")
if not os.path.exists(whisper_exe):
    raise FileNotFoundError(f"❌ Exécutable introuvable : {whisper_exe}")
os.makedirs(output_dir, exist_ok=True)

# Commande complète
cmd = [
    whisper_exe,
    input_file,
    "--task", "translate",
    "--language", "ja",
    "--output_format", "srt",
    "--output_dir", output_dir,
    "--compute_type", "float16",
    "--temperature", "0",
    "--beam_size", "5",
    "--no_repeat_ngram_size", "3",
    "--condition_on_previous_text", "True",
    "--standard_asia",
    "--vad_filter", "True",
    "--vad_method", "silero_v5_fw",
    "--vad_threshold", "0.35",
    "--vad_min_silence_duration_ms", "100",
    "--vad_speech_pad_ms", "300",
    "--ff_rnndn_xiph",
    "--ff_lowhighpass",
    "--ff_speechnorm",
    "--ff_silence_suppress", "-50", "0.1",
    "--beep_off"
]

print("🚀 Lancement de Faster-Whisper-XXL...\n")
process = subprocess.run(cmd, shell=True)

if process.returncode == 0:
    print(f"✅ Transcription terminée !\n➡️ Sous-titres dans : {output_dir}")
else:
    print(f"⚠️ Erreur (code {process.returncode}) pendant l’exécution.")
```

---

## 📖 5. Liste complète des arguments (classée par thème)

### ⚙️ 1. Configuration générale

Si tu veux télécharger des models :https://huggingface.co/openai/whisper-large-v3#model-details

et ceux de faster whisper: https://huggingface.co/collections/Systran/faster-whisper

| Argument            | Description                                                                                | Défaut                     |
| ------------------- | ------------------------------------------------------------------------------------------ | --------------------------- |
| `--model`         | Choisit le modèle Whisper (`tiny`, `base`, `small`, `medium`, `large-v3`, etc.) | `medium`                  |
| `--model_dir`     | Dossier des modèles                                                                       | `_models`                 |
| `--device`        | Cible d’exécution (`cpu`, `cuda`, etc.)                                              | auto                        |
| `--output_dir`    | Dossier de sortie                                                                          | même dossier que le média |
| `--output_format` | Format du sous-titre (`srt`, `vtt`, `txt`, etc.)                                     | `srt`                     |
| `--compute_type`  | Quantization (`float16`, `int8`, etc.)                                                 | auto                        |
| `--threads`       | Nombre de threads CPU                                                                      | auto (4 max)                |
| `--verbose`       | Affiche logs détaillés                                                                   | `False`                   |
| `--beep_off`      | Désactive le bip final                                                                    | `False`                   |

### 🧠 2. Tâches & langues

| Argument                           | Description                                        | Défaut        |
| ---------------------------------- | -------------------------------------------------- | -------------- |
| `--task`                         | `transcribe` (X→X) / `translate` (X→Anglais) | `transcribe` |
| `--language`                     | Code ISO (`ja`, `en`, `fr`, etc.)            | auto           |
| `--language_detection_threshold` | Confiance min détection                           | `0.5`        |
| `--initial_prompt`               | Prompt initial pour contexte                       | `auto`       |
| `--condition_on_previous_text`   | Cohérence inter-segments                          | `True`       |

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

### 🎧 4. VAD – Voice Activity Detection

| Argument                          | Description                                          | Défaut          |
| --------------------------------- | ---------------------------------------------------- | ---------------- |
| `--vad_filter`                  | Active détection voix                               | `True`         |
| `--vad_method`                  | `silero_v4_fw`, `silero_v5_fw`, `webrtc`, etc. | `silero_v4_fw` |
| `--vad_threshold`               | Sensibilité (0–1)                                  | `0.45`         |
| `--vad_min_speech_duration_ms`  | Ignorer segments trop courts                         | `250`          |
| `--vad_min_silence_duration_ms` | Silence min avant coupure                            | `3000`         |
| `--vad_speech_pad_ms`           | Marge autour voix                                    | `900`          |
| `--vad_window_size_samples`     | Taille fenêtre audio                                | `1536`         |

### 🧹 5. Filtres audio (pré-traitement)

| Argument                  | Description                  | Défaut     |
| ------------------------- | ---------------------------- | ----------- |
| `--ff_rnndn_xiph`       | Denoise léger               | `False`   |
| `--ff_rnndn_sh`         | Denoise fort                 | `False`   |
| `--ff_lowhighpass`      | Passe-bande 50–7800 Hz      | `False`   |
| `--ff_speechnorm`       | Amplifie voix                | `False`   |
| `--ff_loudnorm`         | Normalise volume             | `False`   |
| `--ff_gate`             | Réduit bruit faible         | `False`   |
| `--ff_silence_suppress` | Supprime silence (dB,durée) | `[0,3.0]` |
| `--ff_vocal_extract`    | Sépare voix du fond         | `None`    |

### ✂️ 6. Segmentation & affichage texte

| Argument              | Description              | Défaut   |
| --------------------- | ------------------------ | --------- |
| `--sentence`        | Coupe par phrase         | `False` |
| `--standard`        | Mode standard occidental | `False` |
| `--standard_asia`   | Mode asiatique (JA/ZH)   | `False` |
| `--max_line_width`  | Nb max caractères       | `1000`  |
| `--max_line_count`  | Nb lignes max            | `1`     |
| `--highlight_words` | Mode karaoké            | `False` |
| `--word_timestamps` | Mots horodatés          | `True`  |

### 👥 7. Diarization (multi-locuteurs)

| Argument                | Description                     | Défaut     |
| ----------------------- | ------------------------------- | ----------- |
| `--diarize`           | Active détection locuteurs     | `None`    |
| `--num_speakers`      | Nb fixe de locuteurs            | `None`    |
| `--speaker`           | Nom custom au lieu de "SPEAKER" | `SPEAKER` |
| `--diarize_dump`      | Sauve résultats diarization    | `False`   |
| `--return_embeddings` | Sauve vecteurs vocaux           | `False`   |

### 🧪 8. Fonctions avancées

| Argument                              | Description                                           | Défaut   |
| ------------------------------------- | ----------------------------------------------------- | --------- |
| `--batch_recursive`                 | Analyse dossier complet                               | `False` |
| `--skip`                            | Ignore fichiers déjà traités                       | `False` |
| `--hotwords`                        | Mots-clés prioritaires                               | `None`  |
| `--japanese`                        | Style de sortie japonais (`blend`, `kanji`, etc.) | `blend` |
| `--hallucination_silence_threshold` | Anti-hallucination                                    | `None`  |

### 🗂️ 9. Formats & sortie

| Argument                 | Description                                  | Défaut   |
| ------------------------ | -------------------------------------------- | --------- |
| `--output_format`      | `srt`, `vtt`, `txt`, `json`, `all` | `srt`   |
| `--without_timestamps` | Supprime timecodes                           | `False` |
| `--print_progress`     | Affiche progression                          | `False` |
| `--check_files`        | Vérifie erreurs entrée                     | `False` |
