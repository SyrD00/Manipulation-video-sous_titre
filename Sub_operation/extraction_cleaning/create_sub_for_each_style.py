# -*- coding: utf-8 -*-
import pysubs2
import os

def extract_styles_separately(input_path: str, output_folder: str, target_styles: list):
    """
    Pour chaque style dans target_styles, crée un fichier ASS contenant uniquement
    les sous-titres appartenant à ce style.
    """
    try:
        subs = pysubs2.load(input_path, encoding="utf-8")

        # Crée le dossier de sortie s’il n’existe pas
        os.makedirs(output_folder, exist_ok=True)

        # Pour chaque style demandé
        for style_name in target_styles:
            # Filtrer les lignes correspondant à ce style
            filtered_lines = [line for line in subs if line.style == style_name]

            if not filtered_lines:
                print(f"⚠️ Aucun sous-titre trouvé pour le style : {style_name}")
                continue

            # Créer un nouveau fichier ASS ne contenant que ce style
            output_subs = pysubs2.SSAFile()
            output_subs.info = subs.info

            # Ajouter uniquement le style concerné
            if style_name in subs.styles:
                output_subs.styles[style_name] = subs.styles[style_name]
            else:
                print(f"⚠️ Style non trouvé dans le fichier : {style_name}")
                continue

            # Ajouter les lignes correspondantes
            for line in filtered_lines:
                output_subs.append(line)

            # Nom du fichier de sortie
            safe_name = style_name.replace(" ", "_").replace(",", "")
            #output_path = os.path.join(output_folder, f"{safe_name}.ass")
            output_path=os.path.join(output_folder, f"{safe_name}.srt")

            # Sauvegarde du fichier
            output_subs.save(output_path, encoding="utf-8")
            print(f"✅ Fichier généré : {output_path}")

        print("\nExtraction terminée pour tous les styles demandés !")

    except FileNotFoundError:
        print(f"❌ Erreur : le fichier {input_path} n'a pas été trouvé.")
    except Exception as e:
        print(f"❌ Une erreur est survenue : {e}")

if __name__ == "__main__":
    # Fichier d'entrée
    input_file = "C:/Users/babak/Videos/PSO/Video/op.ass"

    # Dossier où enregistrer les fichiers créés
    output_folder = "C:/Users/babak/Videos/PSO/Video/"

    # Liste des styles à extraire
    styles_to_extract = ["color", "ripple", "zeal", "meteor"]

    extract_styles_separately(input_file, output_folder, styles_to_extract)
