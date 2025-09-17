"""
Exemple
📝 Progression:   0%|                                    | 2.88/1430.08 [01:49<15:07:45, 38.16s/sec]

1️⃣ 📝 Progression: 0%|

👉 C’est le titre de la barre (desc="📝 Progression") + l’état actuel.
Ici ça dit : 0% de la vidéo est transcrite.

2️⃣ 2.88/1430.08

2.88 = nombre de secondes d’audio déjà transcrites.

1430.08 = durée totale de la vidéo en secondes (≈ 23 min 50).

Donc tu as transcrit 2,88 secondes sur 1430 secondes → d’où le 0%.

3️⃣ [01:49<15:07:45, 38.16s/sec]

Ça ce sont les stats calculées par tqdm :

01:49 → temps déjà écoulé (1 min 49 s).

<15:07:45 → estimation du temps restant (ici 15h 😅, mais c’est faux car tu viens de commencer, tqdm 
extrapole mal au début).

38.16s/sec → vitesse estimée = combien de secondes d’audio transcrites par seconde de calcul.

Ici : tu traites 38 secondes d’audio en 1 seconde de CPU (c’est un ratio, pas du temps réel).

Comme au début le modèle est lent à charger, ça paraît énorme et faussé. Après quelques minutes, ça se 
stabilise.

🚨 Conclusion

Ton modèle large + CPU est en train de galérer :

23 minutes d’audio à 38x temps réel = environ 15 heures de transcription 🤯.

C’est exactement ce que l’ETA affiche (15:07:45).

"""
import argparse
import os
import time
from tqdm import tqdm
from faster_whisper import WhisperModel

def format_timestamp(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = seconds % 60
    milliseconds = int((seconds - int(seconds)) * 1000)
    return f"{hours:02}:{minutes:02}:{int(seconds):02},{milliseconds:03}"

def diagnostic_vitesse(speed: float) -> str:
    """Donne une recommandation selon la vitesse de traitement."""
    if speed < 1:
        return "🐌 Très lent → Conseil: utilisez un modèle plus petit (base/small) ou activez GPU si dispo."
    elif speed < 2:
        return "⚠️ Correct mais lent → Conseil: vous pouvez réduire la taille du modèle ou fermer d'autres applis."
    elif speed < 5:
        return "✅ Bon débit → Conseil: continuez comme ça, le modèle choisi est adapté."
    else:
        return "🚀 Excellent débit → Conseil: vous pouvez utiliser un modèle plus grand (ex: large) pour plus de précision."

def transcribe_with_progress(audio_path: str, model_size="medium", language=None, task="transcribe"):
    print(f"🚀 Chargement du modèle '{model_size}' optimisé AVX2...")
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    print("✅ Modèle chargé.\n")

    print(f"🎧 Transcription de : {audio_path}\n")
    start_time = time.time()

    segments_generator, info = model.transcribe(
        audio_path,
        language=language,
        task=task,
        beam_size=5,
    )
    if language is None:
        print(f"🌍 Langue détectée automatiquement : {info.language} (confiance {info.language_probability:.2f})")

    total_duration = info.duration
    srt_path = os.path.splitext(audio_path)[0] + ".srt"

    diagnostic_affiche = False  # variable pour afficher le diagnostic seulement 1 fois si lent

    with open(srt_path, "w", encoding="utf-8") as srt_file:
        progress_bar = tqdm(total=total_duration, desc="📝 Progression", unit="sec", ncols=100)
        current_time = 0.0

        for i, segment in enumerate(segments_generator):
            start = format_timestamp(segment.start)
            end = format_timestamp(segment.end)
            text = segment.text.strip()
            srt_file.write(f"{i+1}\n{start} --> {end}\n{text}\n\n")

            # Mise à jour de la barre
            progress_bar.update(segment.end - current_time)
            current_time = segment.end

            # Calcul de vitesse
            elapsed = time.time() - start_time
            speed = current_time / elapsed if elapsed > 0 else 0

            # Afficher diagnostic **une seule fois si vitesse lente (<1x)**
            if not diagnostic_affiche and speed < 1:
                print(f"\n⚡ Vitesse: {speed:.2f}x temps réel ({current_time/60:.1f} min audio en {elapsed/60:.1f} min réelles)")
                print("💡 " + diagnostic_vitesse(speed))
                diagnostic_affiche = True

        progress_bar.close()

    elapsed = time.time() - start_time
    print(f"\n✅ Transcription terminée en {elapsed/60:.1f} minutes réelles")
    print(f"📄 Fichier SRT généré : {srt_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Transcrire un fichier audio en SRT avec Faster-Whisper (AVX2 optimisé).")
    parser.add_argument("input_file", help="Chemin du fichier audio à transcrire")
    parser.add_argument("--model_size", default="medium", help="Taille du modèle : tiny, base, small, medium, large")
    parser.add_argument("--language", default=None, help="Langue de l'audio, ex: ('auto', 'fr', 'en', ou 'ja'). Laisse vide pour auto-détection")
    parser.add_argument("--task", default="transcribe", choices=["transcribe", "translate"], help="Tâche : transcrire ou traduire")
    args = parser.parse_args()

    transcribe_with_progress(args.input_file, args.model_size, args.language, args.task)

