import os
import pysubs2

def extract_music_and_text(text):
    """Retourne (musique, texte) ou None si pas de 🎶"""
    if "🎶" not in text:
        return None

    text_only = text.replace("🎶", "").strip()
    spacing = " " * max(4, len(text_only) // 2)
    music_only = f"🎶{spacing}🎶"
    return music_only, text_only


def split_subs(input_path):
    # Chargement auto (ASS, SRT, etc.)
    subs = pysubs2.load(input_path, encoding="utf-8-sig")
    base, ext = os.path.splitext(input_path)

    subs_text = pysubs2.SSAFile()
    subs_music = pysubs2.SSAFile()

    # Copier les styles et metadata si ASS
    subs_text.styles = subs.styles.copy()
    subs_music.styles = subs.styles.copy()
    subs_text.info = subs.info.copy()
    subs_music.info = subs.info.copy()

    for event in subs:
        result = extract_music_and_text(event.text)
        if result:
            music, pure_text = result

            e_text = event.copy()
            e_text.text = pure_text
            subs_text.append(e_text)

            e_music = event.copy()
            e_music.text = music
            subs_music.append(e_music)
        else:
            subs_text.append(event.copy())
            subs_music.append(event.copy())

    # Sauvegarde
    text_out = base + "_TEXT" + ext
    music_out = base + "_MUSIC" + ext
    subs_text.save(text_out, encoding="utf-8")
    subs_music.save(music_out, encoding="utf-8")

    print(f"✅ Fichiers générés :\n→ {text_out}\n→ {music_out}")


if __name__ == "__main__":
    # 👉 Mets ici le chemin de ton fichier
    input_file = r"C:\Users\babak\Videos\PSO\Episode\Video\Eng\Rom_Super_Higher.srt"
    split_subs(input_file)
