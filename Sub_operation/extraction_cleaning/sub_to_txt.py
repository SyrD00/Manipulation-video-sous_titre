
"""""
def extract_text_from_srt(srt_path, txt_path):
    with open(srt_path, "r", encoding="utf-8") as srt, open(txt_path, "w", encoding="utf-8") as txt:
        for line in srt:
            line = line.strip()
            # Ignorer lignes vides, numéros et timestamps
            if line == "" or line.isdigit() or "-->" in line:
                continue
            txt.write(line + " ")

extract_text_from_srt("C:/Users/babak/Videos/PSO/TRIAD_FORCE.ass", "C:/Users/babak/Videos/PSO/TRIAD_FORCE.txt")
"""
import os
import pysubs2

def extract_text_from_subtitle_file_pysubs2(subtitle_path, txt_path):
    """
    Extrait le texte de sous-titres (SRT, ASS, VTT, etc.) vers un fichier TXT,
    en assurant un saut de ligne entre chaque réplique.
    Nécessite 'pip install pysubs2'.
    """
    try:
        # 1. Charger le fichier de sous-titres
        subs = pysubs2.load(subtitle_path)

        # 2. Ouvrir le fichier de destination en écriture
        with open(txt_path, "w", encoding="utf-8") as txt:
            # 3. Écrire le texte de chaque ligne de sous-titre
            for line in subs:
                # Le texte est déjà nettoyé des balises de formatage par pysubs2
                clean_text = line.text
                
                # Remplacement de l'espace par '\n' pour un saut de ligne
                txt.write(clean_text + "\n") # <-- LA MODIFICATION EST ICI

        print(f"✅ Texte extrait avec succès de '{subtitle_path}' vers '{txt_path}'.")

    except FileNotFoundError:
        print(f"❌ Erreur: Le fichier '{subtitle_path}' est introuvable.")
    except Exception as e:
        print(f"❌ Erreur lors de l'extraction: {e}")


# --- Exemple d'utilisation (inchangé) ---
subtitle_file = "C:/Users/babak/Videos/PSO/Episode/PSO24_cleaned.srt" 
output_text_file = "C:/Users/babak/Videos/PSO/Episode/PSO24.txt"

extract_text_from_subtitle_file_pysubs2(subtitle_file, output_text_file)