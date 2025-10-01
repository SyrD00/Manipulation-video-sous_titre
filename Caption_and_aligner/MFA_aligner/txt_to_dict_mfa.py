r"""
NB: Pour l'instant mamba install -c conda-forge fugashi unidic-lite ne marche pas
avec python 3.13 ,utilise 3.9 -> 3.11
cd C:\Users\babak\Documents\GitHub\Manipulation-video-sous_titre\Caption_and_aligner\MFA_aligner
    -mamba create -n mfa_dict_jp python=3.10 #creation d'un environnement vide(python 3.10)
        ou tu pourras lancer ton script de génération du dictionnaire japonais.

    -mamba activate mfa_dict_jp #ça bascule ton terminal dans cet environnement 
            (séparé de ton (base) ou de MFA_aligner).

    -pip install fugashi unidic-lite


Ensuite activer l'environnement mfa_dict_jp (Anaconda Prompt)
    mamba activate mfa_dict_jp
        Ce script convertit une transcription brute en un dictionnaire au format MFA pour le japonais.

            si tu veux supprimer : mamba env remove -n mfa_dict_jp

        
"""
import fugashi

tagger = fugashi.Tagger()

input_file = "C:/Users/babak/Videos/PSO/Episode/chibi_12half.txt"
output_dict = "C:/Users/babak/Videos/PSO/Episode/chibi_12half.dict"

with open(input_file, "r", encoding="utf-8") as fin, open(output_dict, "w", encoding="utf-8") as fout:
    for line in fin:
        line = line.strip()
        if not line:
            continue
        words = tagger(line)
        for word in words:
            surface = word.surface
            # Pour Unidic-lite :
            # word.feature.pos1, pos2, base_form, reading, pronunciation, etc.
            reading = getattr(word.feature, "pronunciation", None) or getattr(word.feature, "reading", None) or surface
            fout.write(f"{surface}\t{reading}\n")

print(f"✅ Dictionnaire MFA généré : {output_dict}")


"""
le code produira :
 Colonne 1 : forme de surface (mot tel qu'il apparaît dans le texte)
 Colonne 2 : lecture en kana (ou prononciation)

Par exemple, p
    Exemple 1: "私は学生です。 (romaji: Watashi wa gakusei desu.)"
    Le dictionnaire contiendra :
        私    ワタシ      (watashi)
        は    ハ          (wa)
        学生  ガクセイ     (Gakusei)
        です  デス         (desu)
        。    。

NB:
Pour beaucoup de mots simples ou déjà en hiragana/katakana, les deux colonnes seront
 identiques, mais pour des kanji ou combinaisons complexes, la lecture peut être
 très différente.



"""