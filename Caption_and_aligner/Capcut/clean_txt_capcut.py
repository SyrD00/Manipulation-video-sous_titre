#Capcut parfois fusionne des mots entre eux(surtout en japoanis).Ceci permet de les dissocier
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

    -mamba activate mfa_dict_jp #ça bascule ton terminal dans cet environnement 
            (séparé de ton (base) ou de MFA_aligner).

    -pip install fugashi unidic-lite



        
"""
import fugashi

# 🔧 Mets ici ton fichier en entrée et sortie :
input_file = "C:/Users/babak/Videos/PSO/Episode/chibi_12half.txt"
output_file = "C:/Users/babak/Videos/PSO/Episode/chibi_12half_cleaned.txt"

tagger = fugashi.Tagger()

with open(input_file, "r", encoding="utf-8") as fin, \
     open(output_file, "w", encoding="utf-8") as fout:
    for line in fin:
        line = line.strip()
        if not line:
            fout.write("\n")  # Utilise \n pour un saut de ligne
            continue
        words = [word.surface for word in tagger(line)]
        fout.write(" ".join(words) + "\n")  # Utilise \n pour un saut de ligne

print(f"✅ Nettoyage terminé : {output_file}")

