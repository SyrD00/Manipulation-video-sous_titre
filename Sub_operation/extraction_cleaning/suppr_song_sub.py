# -*- coding: utf-8 -*-
import pysubs2
from collections import defaultdict

def remove_songs(input_path: str, output_path: str):
    """
    Supprime les sous-titres de chansons d'un fichier ASS et sauvegarde le résultat.
    Les critères de suppression sont :
    1. La présence de l'emoji '♬' dans le texte.
    2. Un style de sous-titre qui correspond à une chanson.
    """
    try:
        # Charger le fichier de sous-titres
        subs = pysubs2.load(input_path, encoding="utf-8")
        
        # Définir les styles de chansons que nous voulons supprimer
        song_styles = {"Rom-Fight Might Me", "Eng-Fight Might Me", "Rom Callisto" ,"Eng Callisto" , "Romanji Multi", "English Multi" }
        
        # Liste temporaire pour stocker les lignes non-chansons
        filtered_lines = []
        
        # Ensemble pour collecter les noms de styles réellement utilisés dans le fichier de sortie
        used_style_names = set()

        # Parcourir les lignes et filtrer celles qui ne sont PAS des chansons
        for line in subs:
            is_song = False
            # Critère 1: Vérifier si le texte contient l'emoji de musique
            if "♬" in line.text:
                is_song = True
            # Critère 2: Vérifier si le style de la ligne est dans notre liste de styles à supprimer
            elif line.style in song_styles:
                is_song = True
            
            # Si ce n'est PAS une chanson, on la garde
            if not is_song:
                filtered_lines.append(line)
                used_style_names.add(line.style)

        # Créer un nouvel objet SSAFile pour le résultat
        dialog_subs = pysubs2.SSAFile()
        
        # Copier les informations du fichier d'origine
        dialog_subs.info = subs.info

        # Copier SEULEMENT les styles des lignes conservées
        for style_name, style_obj in subs.styles.items():
            if style_name in used_style_names:
                dialog_subs.styles[style_name] = style_obj

        # Ajouter les lignes filtrées au nouveau fichier
        for line in filtered_lines:
            dialog_subs.append(line)

        # Sauvegarder le nouveau fichier
        dialog_subs.save(output_path, encoding="utf-8")
        print(f"Suppression des chansons réussie ! Le résultat a été sauvegardé dans : {output_path}")

    except FileNotFoundError:
        print(f"Erreur : Le fichier {input_path} n'a pas été trouvé.")
    except Exception as e:
        print(f"Une erreur est survenue : {e}")

if __name__ == "__main__":
    # Définissez vos chemins de fichiers ici
    file_path = "C:/Users/babak/Videos/PSO/PSO22_rom.ass"  # Remplacez par le chemin de votre fichier ASS
    output_file_path = "C:/Users/babak/Videos/PSO/PSO22_rom_sans_song.ass"
    
    # Exécutez la fonction
    remove_songs(file_path, output_file_path)