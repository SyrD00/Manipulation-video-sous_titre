#Capcut/Clipchamp parfois fusionne des mots entre eux(surtout en japoanis).Ceci permet de les dissocier
#C'est utile d ele faire pour mfa align pour eviter d'avoir des mots inconnus(unk)

#pip install fugashi unidic-lite
import fugashi
"""
version arguments en ligne de commande
if len(sys.argv) < 3:
    print("Usage: python clean_txt_jp.py input.txt output.txt")
    sys.exit(1)

input_file = sys.argv[1]
output_file = sys.argv[2]
"""
r"""
NB: Pour l'instant mamba install -c conda-forge fugashi unidic-lite ne marche pas
avec python 3.13 ,utilise 3.9 -> 3.11
cd C:\Users\babak\Documents\GitHub\Manipulation-video-sous_titre\Caption_and_aligner\MFA_aligner
    -mamba create -n mfa_dict_jp python=3.10 #creation d'un environnement vide(python 3.10)
        ou tu pourras lancer ton script de génération du dictionnaire japonais.

    -mamba activate mfa_dict_jp #ça bascule ton terminal dans cet environnement (execute ca dans anaconda prompt)
            (séparé de ton (base) ou de MFA_aligner).

    -pip install fugashi unidic-lite



        
"""
import os
import fugashi

# 📂 Dossier contenant tes fichiers txt
folder = "C:/Users/babak/Videos/PSO/Episode/temp/"

tagger = fugashi.Tagger()

for filename in os.listdir(folder):
    if filename.endswith(".txt"):
        file_path = os.path.join(folder, filename)

        # 1️⃣ Lire tout le fichier
        with open(file_path, "r", encoding="utf-8") as fin:
            lines = fin.readlines()

        # 2️⃣ Nettoyer
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if not line:
                cleaned_lines.append("\n")
                continue
            words = [word.surface for word in tagger(line)]
            cleaned_lines.append(" ".join(words) + "\n")

        # 3️⃣ Réécrire par-dessus le fichier
        with open(file_path, "w", encoding="utf-8") as fout:
            fout.writelines(cleaned_lines)

        print(f"✅ Nettoyage terminé (fichier écrasé) : {filename}")


"""

#version ne pas ecraser le fichier d'origine et créer un nouveau fichier avec ajout suffixe _clean.txt
import fugashi

# 📂 Dossier contenant tes fichiers txt
folder = "C:/Users/babak/Videos/PSO/Episode/Split_txt_aud/PSO23"

tagger = fugashi.Tagger()

for filename in os.listdir(folder):
    if filename.endswith(".txt") and not filename.endswith("_clean.txt"):
        input_file = os.path.join(folder, filename)
        output_file = os.path.join(folder, filename.replace(".txt", "_clean.txt"))

        with open(input_file, "r", encoding="utf-8") as fin, \
             open(output_file, "w", encoding="utf-8") as fout:
            for line in fin:
                line = line.strip()
                if not line:
                    fout.write("\n") # Utilise \n pour un saut de ligne
                    continue
                words = [word.surface for word in tagger(line)]
                fout.write(" ".join(words) + "\n") # Utilise \n pour un saut de ligne

        print(f"✅ Nettoyage terminé : {output_file}")



"""

"""
Version 1 fichier unique
import fugashi

# 🔧 Mets ici ton fichier en entrée et sortie :
input_file = "C:/Users/babak/Videos/PSO/Episode/temp/PSO23.txt"
output_file = "C:/Users/babak/Videos/PSO/Episode/temp/PSO23_clean.txt" #nb si t'avias mis le meme nom que input,l'output sera vide a la fin de la generation

tagger = fugashi.Tagger()

with open(input_file, "r", encoding="utf-8") as fin, \
     open(output_file, "w", encoding="utf-8") as fout:
    for line in fin:
        line = line.strip()
        if not line:
            fout.write("\n")  
            continue
        words = [word.surface for word in tagger(line)]
        fout.write(" ".join(words) + "\n")  

print(f"✅ Nettoyage terminé : {output_file}")


"""