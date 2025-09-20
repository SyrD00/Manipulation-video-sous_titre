import re
import sys

def extract_times(input_file, output_file):
    # détecter si c'est un .srt ou un .ass
    if input_file.lower().endswith(".srt"):
        with open(input_file, encoding="utf-8") as f, open(output_file, "w", encoding="utf-8") as out:
            block = 1
            for line in f:
                # repérer une ligne de timecode
                if "-->" in line:
                    out.write(f"{block}\n")
                    out.write(line.strip() + "\n")
                    out.write("\n")
                    block += 1

    elif input_file.lower().endswith(".ass"):
        time_pattern = re.compile(r"Dialogue:[^,]*,([^,]*),([^,]*),")
        with open(input_file, encoding="utf-8") as f, open(output_file, "w", encoding="utf-8") as out:
            out.write("[Script Info]\n")
            out.write("Title: Timestamps only\n")
            out.write("ScriptType: v4.00+\n\n")
            out.write("[Events]\n")
            out.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
            for i, line in enumerate(f, 1):
                m = time_pattern.match(line)
                if m:
                    start, end = m.groups()
                    out.write(f"Dialogue: 0,{start},{end},Default,,0,0,0,,\n")

    else:
        print("Format non supporté (seulement .srt ou .ass)")


if __name__ == "__main__":
    # Définissez vos noms de fichiers ici 👇
    input_file = "C:/Users/babak/Videos/PSO/PSO22_rom_sans_song.ass" 
    output_file = "C:/Users/babak/Videos/PSO/PSO22_horodatages.ass"

    # Appelez la fonction avec les noms de fichiers spécifiés
    extract_times(input_file, output_file)

"""

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python extract_times.py fichier_entree.srt fichier_sortie.srt")
    else:
        extract_times(sys.argv[1], sys.argv[2])
"""