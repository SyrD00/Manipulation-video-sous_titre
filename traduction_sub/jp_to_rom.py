import re
import warnings
from pykakasi import kakasi

# Masquer les DeprecationWarning
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Fichiers
input_file = "C:/Users/babak/Videos/PSO/PSO22.srt"
output_file = "C:/Users/babak/Videos/PSO/PSO22_rom.srt"

# Lire le SRT
with open(input_file, "r", encoding="utf-8") as f:
    srt_content = f.read()

# Séparer en blocs
blocks = re.split(r"\n\n+", srt_content.strip())

# Configurer pykakasi (ancienne API v2)
kks = kakasi()
kks.setMode("H", "a")  # Hiragana -> romaji
kks.setMode("K", "a")  # Katakana -> romaji
kks.setMode("J", "a")  # Kanji -> romaji
kks.setMode("r", "Hepburn")  # Utiliser Hepburn
kks.setMode("s", True)  # Séparer les mots
converter = kks.getConverter()

romaji_blocks = []

for block in blocks:
    lines = block.split("\n")
    if len(lines) >= 3:
        num = lines[0]
        timecode = lines[1]
        text_lines = lines[2:]
        
        # Traiter chaque ligne pour garder ponctuation et sauter des lignes correctement
        converted_lines = []
        for line in text_lines:
            line = line.strip()
            if line:
                romaji_line = converter.do(line)
                
                # Optionnel : nettoyer les espaces inutiles autour de la ponctuation
                romaji_line = re.sub(r'\s+([,.!?;:])', r'\1', romaji_line)
                
                converted_lines.append(romaji_line)
        
        romaji_text = "\n".join(converted_lines)
        romaji_blocks.append(f"{num}\n{timecode}\n{romaji_text}")
    else:
        romaji_blocks.append(block)

# Écrire le SRT converti
with open(output_file, "w", encoding="utf-8") as f:
    f.write("\n\n".join(romaji_blocks))

print(f"✅ Conversion terminée ! Fichier généré : {output_file}")



r"""
pip install pykakasi pour la conversion en romaji

WARNING: Skipping pykakasi as it is not installed.
PS C:\Users\babak\Documents\GitHub\Manipulation-video-sous_titre\traduction_sub> pip install --upgrade pykakasi --pre
>> 
Collecting pykakasi
  Using cached pykakasi-2.3.0-py3-none-any.whl.metadata (5.9 kB)
Requirement already satisfied: jaconv in c:\users\babak\appdata\local\programs\python\python313\lib\site-packages (from pykakasi) (0.4.0)
Requirement already satisfied: deprecated in c:\users\babak\appdata\local\programs\python\python313\lib\site-packages (from pykakasi) (1.2.18)Requirement already satisfied: wrapt<2,>=1.10 in c:\users\babak\appdata\local\programs\python\python313\lib\site-packages (from deprecated->pykakasi) (1.17.3)
Using cached pykakasi-2.3.0-py3-none-any.whl (2.4 MB)
Installing collected packages: pykakasi
Successfully installed pykakasi-2.3.0


La version 3 n’est pas encore officiellement publiée sur PyPI

Actuellement, la dernière version stable disponible est 2.3.0 (celle que tu as installée).

La v3 est encore en pré-release / développement, donc elle n’est pas accessible avec un pip install pykakasi
 classique.

Option --pre n’a pas trouvé de pré-release

Même en mettant --pre, PyPI n’avait pas de version v3 publiée.

Le package “pré-release” n’existe pas encore pour Python 3.13 ou pour Windows, donc pip a installé la 
dernière stable (v2.3.0).

comme je n'ai pas encore la v3 il yaura des warning





rōmaji (ローマ字) = “écriture en lettres latines du japonais”.
Mais il existe plusieurs systèmes de transcription.

Les principaux systèmes :

Hepburn (ヘボン式ローマ字, Hebon-shiki)

C’est le plus utilisé dans le monde (manuels de japonais, panneaux, passeports, animes fansub, etc.).

Il essaie de se rapprocher de la prononciation réelle pour les étrangers.

Exemple :

し = shi (pas si)

ち = chi (pas ti)

つ = tsu (pas tu)

Kunrei-shiki (訓令式ローマ字)

Officiel au Japon dans certains contextes (éducation, gouvernement).

Plus “logique” pour comprendre la grammaire japonaise, mais moins naturel pour prononcer.

Exemple :

し = si

ち = ti

つ = tu

Nihon-shiki (日本式ローマ字)

Ancien système, encore plus “technique”, utilisé pour des études linguistiques.

Exemple :

じ = zi (au lieu de ji)
"""                                                                                                                                                           