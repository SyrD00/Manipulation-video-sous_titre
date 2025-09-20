# -*- coding: utf-8 -*-
import pysubs2
from collections import defaultdict

def extract_songs(input_path: str, output_path: str):
    """
    Extrait les sous-titres de chansons d'un fichier ASS et les sauvegarde dans un nouveau fichier.
    """
    try:
        # Charger le fichier de sous-titres
        subs = pysubs2.load(input_path, encoding="utf-8")
        
        # Définir les styles de chansons que nous voulons conserver
        song_styles = {"Rom Fight Might Me", "Eng Fight Might Me", "Eng Callisto", "Rom Callisto", "English Multi", "Romanji Multi"}
       
        # Liste temporaire pour stocker les lignes de chansons filtrées
        filtered_lines = []
        
        # Ensemble pour collecter les noms de styles réellement utilisés
        used_style_names = set()

        # Filtrer les lignes et collecter les styles
        
        for line in subs:
            # Critère unique et précis:
            if "♬" in line.text or line.style in song_styles:
                filtered_lines.append(line)
                used_style_names.add(line.style)

        # Créer un nouvel objet SSAFile pour le résultat
        song_subs = pysubs2.SSAFile()
        
        # Copier les informations du fichier d'origine
        song_subs.info = subs.info

        # Copier SEULEMENT les styles utilisés
        for style_name, style_obj in subs.styles.items():
            if style_name in used_style_names:
                song_subs.styles[style_name] = style_obj

        # Ajouter les lignes filtrées au nouveau fichier
        for line in filtered_lines:
            song_subs.append(line)

        # Sauvegarder le nouveau fichier
        song_subs.save(output_path, encoding="utf-8")
        print(f"Extraction réussie ! Les chansons ont été sauvegardées dans : {output_path}")

    except FileNotFoundError:
        print(f"Erreur : Le fichier {input_path} n'a pas été trouvé.")
    except Exception as e:
        print(f"Une erreur est survenue : {e}")

if __name__ == "__main__":
    # Définissez vos chemins de fichiers ici
    file_path = "C:/Users/babak/Videos/PSO/PSO22_rom.ass"  # Remplacez par le chemin de votre fichier ASS
    output_file_path = "C:/Users/babak/Videos/PSO/PSO22_dial.ass"
    
    # Exécutez la fonction
    extract_songs(file_path, output_file_path)