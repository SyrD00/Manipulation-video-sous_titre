# -*- coding: utf-8 -*-
import pysubs2
from collections import defaultdict

def extract_multiple_styles(input_path: str, output_path: str, target_styles: list):
    """
    Extrait les sous-titres d'un fichier ASS qui correspondent à un ou plusieurs
    styles spécifiques et les sauvegarde dans un nouveau fichier.
    """
    try:
        subs = pysubs2.load(input_path, encoding="utf-8")
        
        filtered_lines = []
        used_style_names = set()

        for line in subs:
            # La condition est modifiée pour vérifier si le style est dans la liste
            if line.style in target_styles:
                filtered_lines.append(line)
                used_style_names.add(line.style)

        if not filtered_lines:
            print(f"Aucune ligne de sous-titre trouvée pour les styles : {', '.join(target_styles)}")
            return

        output_subs = pysubs2.SSAFile()
        output_subs.info = subs.info

        for style_name, style_obj in subs.styles.items():
            if style_name in used_style_names:
                output_subs.styles[style_name] = style_obj

        for line in filtered_lines:
            output_subs.append(line)

        output_subs.save(output_path, encoding="utf-8")
        print(f"Extraction réussie ! Les lignes des styles {', '.join(target_styles)} ont été sauvegardées dans : {output_path}")

    except FileNotFoundError:
        print(f"Erreur : Le fichier {input_path} n'a pas été trouvé.")
    except Exception as e:
        print(f"Une erreur est survenue : {e}")

if __name__ == "__main__":
    file_path = "C:/Users/babak/Videos/PSO/PSO22_rom.ass"
    output_file_path = "C:/Users/babak/Videos/PSO/PSO22_dial.ass"
    
    # Définissez une liste de styles à extraire
    styles_to_extract = ["dialog during song"]
    
    extract_multiple_styles(file_path, output_file_path, styles_to_extract)