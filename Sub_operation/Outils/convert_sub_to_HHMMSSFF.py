import re
import os

# ==============================
# ⚙️ CONFIGURATION UTILISATEUR
# ==============================

# ➜ Indique ici le chemin complet de ton fichier .srt ou .ass :
input_path = "C:/Users/babak/Videos/PSO/Episode/Video/Eng/seg10_multicolor.ass"

# ➜ Indique ici le nombre d'images par seconde :
fps = 30

# ==============================
# 🚀 CODE PRINCIPAL
# ==============================

def convert_time_to_frames(time_str, fps):
    """
    Convertit un timecode HH:MM:SS,mmm ou HH:MM:SS.mmm → HH:MM:SS:FF
    """
    time_str = time_str.replace(',', '.')
    h, m, s = time_str.split(':')
    if '.' in s:
        s, ms = s.split('.')
        ms = int(ms.ljust(3, '0'))  # normalise à 3 chiffres
    else:
        ms = 0
    h, m, s = int(h), int(m), int(s)
    frames = round(ms / 1000 * fps)
    return f"{h:02}:{m:02}:{s:02}:{frames:02}"

def convert_file(input_path, fps=30):
    if not os.path.exists(input_path):
        print(f"❌ Fichier introuvable : {input_path}")
        return

    with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Motif général pour les timecodes SRT ou ASS
    # (exemples : 00:01:23,456  |  00:01:23.456)
    pattern = re.compile(r"(\d{2}:\d{2}:\d{2}[,\.]\d{1,3})")

    def repl(match):
        return convert_time_to_frames(match.group(1), fps)

    new_content = pattern.sub(repl, content)

    base, ext = os.path.splitext(input_path)
    output_path = f"{base}_HHMMSSFF{ext}"

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"✅ Conversion terminée avec succès !")
    print(f"📄 Fichier généré : {output_path}")

# Lancement automatique
convert_file(input_path, fps)


'''
# --- Exemple d’utilisation ---
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage : python convert_timecodes.py fichier.srt [fps]")
    else:
        fichier = sys.argv[1]
        fps = float(sys.argv[2]) if len(sys.argv) > 2 else 30
        convert_file(fichier, fps)
'''