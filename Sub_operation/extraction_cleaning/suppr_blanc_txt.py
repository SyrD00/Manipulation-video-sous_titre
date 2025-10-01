# Ouvre le fichier d'origine en lecture
with open("C:/Users/babak/Videos/PSO/Episode/PSO23.txt", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Supprime les lignes vides
non_empty_lines = [line for line in lines if line.strip() != ""]

# Écrit le résultat dans un nouveau fichier
with open("C:/Users/babak/Videos/PSO/Episode/PSO23v2.txt", "w", encoding="utf-8") as f:
    f.writelines(non_empty_lines)
