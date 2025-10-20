import re
import os

def split_music_and_text_generic(text):
    """
    Sépare les symboles 🎶 et le texte d'une ligne.
    Retourne (ligne_musique, ligne_texte) ou None si inutile.
    """
    if "🎶" not in text:
        return None

    core_text = text.replace("🎶", "").strip()
    if core_text:
        spacing = " " * max(4, len(core_text) // 2)
    else:
        spacing = "     "

    return (f"🎶{spacing}🎶", core_text)


def process_ass(input_path, output_path):
    with open(input_path, "r", encoding="utf-8-sig") as f:
        lines = f.readlines()

    output = []
    in_events = False

    for line in lines:
        if line.strip().startswith("[Events]"):
            in_events = True
            output.append(line)
            continue

        if in_events and line.startswith("Dialogue:"):
            parts = line.split(",,")
            if len(parts) < 2:
                output.append(line)
                continue
            header = ",,".join(parts[:-1]) + ",,"
            text = parts[-1].strip()
            result = split_music_and_text_generic(text)
            if result:
                music, text_only = result
                output.append(f"{header}{music}\n")
                output.append(f"{header}{text_only}\n")
            else:
                output.append(line)
        else:
            output.append(line)

    with open(output_path, "w", encoding="utf-8") as f:
        f.writelines(output)

    print(f"✅ Fichier ASS traité : {output_path}")


def process_srt(input_path, output_path):
    with open(input_path, "r", encoding="utf-8-sig") as f:
        lines = f.read().splitlines()

    output = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Si c’est un numéro de sous-titre
        if line.isdigit():
            output.append(line)
            i += 1
            if i >= len(lines): break

            # Ligne de temps
            output.append(lines[i])
            i += 1

            # Texte
            text_lines = []
            while i < len(lines) and lines[i].strip() != "":
                text_lines.append(lines[i])
                i += 1

            full_text = " ".join(text_lines).strip()
            result = split_music_and_text_generic(full_text)
            if result:
                music, text_only = result
                output.append(music)
                output.append(text_only)
            else:
                output.append(full_text)
            output.append("")  # ligne vide
        else:
            i += 1

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(output))

    print(f"✅ Fichier SRT traité : {output_path}")


def process_subtitle_file(input_path):
    ext = os.path.splitext(input_path)[1].lower()
    base, _ = os.path.splitext(input_path)
    output_path = base + "_split" + ext

    if ext == ".ass":
        process_ass(input_path, output_path)
    elif ext == ".srt":
        process_srt(input_path, output_path)
    else:
        print("❌ Format non supporté (seuls .ass et .srt sont pris en charge).")


# ============================
# 🔧 CONFIGURATION ICI :
# ============================
if __name__ == "__main__":
    # Mets ici le chemin vers ton fichier (ass OU srt)
    input_file = r"C:\Users\babak\Videos\PSO\Episode\triad_force_paires.ass"

    process_subtitle_file(input_file)


'''  
===Exemple d’utilisation ===
if __name__ == "__main__":
    input_file = "input.ass"   # ton fichier d’entrée
    output_file = "output_split.ass"  # fichier résultat
    process_ass_file(input_file, output_file)
'''