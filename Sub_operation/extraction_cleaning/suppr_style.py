# -*- coding: utf-8 -*-
import pysubs2

def remove_specific_lines_and_styles_guaranteed(input_path: str, output_path: str, styles_to_remove: list):
    """
    Supprime de manière forcée :
    1. Toutes les lignes de sous-titres utilisant un style dans 'styles_to_remove'.
    2. La définition de TOUS les styles nommés dans 'styles_to_remove' de [V4+ Styles],
       même s'ils ne sont pas utilisés.
    """
    try:
        subs = pysubs2.load(input_path, encoding="utf-8")
        
        # Styles originaux dans le fichier
        original_styles = set(subs.styles.keys())
        
        # --- 1️⃣ Supprimer les lignes avec les styles à retirer ---
        # On ne garde que les lignes dont le style N'EST PAS dans la liste à supprimer.
        kept_lines = [line for line in subs if line.style not in styles_to_remove]

        # --- 2️⃣ Créer un nouveau fichier ASS ---
        output_subs = pysubs2.SSAFile()
        output_subs.info = subs.info

        # --- 3️⃣ Garder TOUS les styles sauf ceux à retirer (LA VRAIE CLE) ---
        # On force la suppression en ne copiant que les styles DONT LE NOM n'est PAS 
        # dans la liste à supprimer, peu importe s'ils sont utilisés ou non.
        for style_name, style_obj in subs.styles.items():
            if style_name not in styles_to_remove:
                output_subs.styles[style_name] = style_obj
                
        # --- 4️⃣ Ajouter les lignes gardées ---
        for line in kept_lines:
            output_subs.append(line)
            
        # --- 5️⃣ Sauvegarder le résultat ---
        output_subs.save(output_path, encoding="utf-8")

        # Vérification des styles qui étaient présents et qui ont été supprimés
        removed_styles = original_styles.intersection(set(styles_to_remove))
        
        print(f"✅ Opération terminée avec suppression forcée.")
        print(f"✅ Styles listés et supprimés : {', '.join(removed_styles)}")
        
        # Afficher ceux qui étaient dans la liste mais peut-être pas dans le fichier d'origine
        not_found = set(styles_to_remove) - original_styles
        if not_found:
             print(f"ℹ️ Styles listés mais absents du fichier d'origine : {', '.join(not_found)}")
             
        print(f"➡️ Nouveau fichier sauvegardé : {output_path}")

    except FileNotFoundError:
        print(f"❌ Erreur : le fichier {input_path} n'a pas été trouvé.")
    except Exception as e:
        print(f"❌ Une erreur est survenue : {e}")

if __name__ == "__main__":
    file_path = "C:/Users/babak/Videos/PSO/Episode/Video/PSO23eng_clean.ass"
    output_file_path = "C:/Users/babak/Videos/PSO/Episode/Video/PSO23english.ass"

    # Liste des styles dont les lignes et la définition doivent être supprimées
    # Y compris "Rom Triad Force" et "Eng Triad Force", même s'ils sont inutilisés.
    styles_to_remove = ["Rom Multi", "Eng Multi", "Rom Triad Force", "Eng Triad Force","Rom Super Higher","Eng Super Higher"]

    # Exécution de la nouvelle fonction
    remove_specific_lines_and_styles_guaranteed(file_path, output_file_path, styles_to_remove)



