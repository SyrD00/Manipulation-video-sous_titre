import os

# === CONFIGURATION ===
input_path = "C:/Users/babak/Downloads/Rain Song .ass"
output_path = "C:/Users/babak/Downloads/1 rain.ass"
"""
Le système de fichiers NTFS (utilisé par Windows) est par défaut insensible à la casse (case-insensitive).

Pour Windows, le nom de fichier Triad_Force.ass et triad_force.ass sont techniquement le même fichier sur le disque.
"""

rom_lines = []
eng_lines = []
header_lines = []

print(f"Lecture du fichier : {input_path}")
if not os.path.exists(input_path):
    print("ERREUR : Le fichier d'entrée n'existe pas !")
    exit(1)

# 1. Lire et séparer l'en-tête et les dialogues
with open(input_path, encoding='utf-8') as f:
    in_events = False
    for line in f:
        if not in_events:
            header_lines.append(line.rstrip('\n'))
            if line.strip().startswith('[Events]'):
                in_events = True
        else:
            if line.strip().startswith('Format:'):
                header_lines.append(line.rstrip('\n'))
                continue
            if line.startswith("Dialogue:"):
                parts = line.strip().split(',', 9)
                if len(parts) < 10:
                    continue
                style = parts[3]
                #A personnaliser selon le style que t'as dans le ass
                if style.startswith('Rom Fight_Might_Me'):
                    rom_lines.append(line.strip())
                elif style.startswith('Eng Fight_Might_Me'):
                    eng_lines.append(line.strip())

print(f"Nombre de lignes Rom trouvées : {len(rom_lines)}")
print(f"Nombre de lignes Eng trouvées : {len(eng_lines)}")

nb_paires = min(len(rom_lines), len(eng_lines))
print(f"Nombre de paires à écrire : {nb_paires}")

# 2. Écrire l'en-tête et toutes les paires + restes dans le fichier de sortie
with open(output_path, 'w', encoding='utf-8') as out:
    for h in header_lines:
        out.write(h + '\n')
    out.write('\n')
    # Paires
    for i in range(nb_paires):
        out.write(rom_lines[i] + '\n')
        out.write(eng_lines[i] + '\n\n')
    # Reste Rom
    if len(rom_lines) > nb_paires:
        out.write("; Lignes Rom non appariées :\n")
        for i in range(nb_paires, len(rom_lines)):
            out.write(rom_lines[i] + '\n')
    # Reste Eng
    if len(eng_lines) > nb_paires:
        out.write("; Lignes Eng non appariées :\n")
        for i in range(nb_paires, len(eng_lines)):
            out.write(eng_lines[i] + '\n')

print(f"Paires écrites dans le fichier : {nb_paires}")
print(f"Lignes Rom non appariées : {len(rom_lines) - nb_paires}")
print(f"Lignes Eng non appariées : {len(eng_lines) - nb_paires}")
print("Traitement terminé.")

if os.path.exists(output_path):
    print(f"Fichier généré : {output_path}")
else:
    print("ERREUR : Le fichier de sortie n'a pas été créé !")


    