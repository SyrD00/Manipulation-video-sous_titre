import os

# Dossier contenant les fichiers SRT
folder = "C:/Users/babak/Videos/PSO/Episode/Split_txt_aud/PSO23"

# Parcours des fichiers du dossier
for filename in os.listdir(folder):
    if filename.endswith(".srt"):
        srt_path = os.path.join(folder, filename)
        txt_path = os.path.join(folder, filename.replace(".srt", ".txt"))
        
        # Lire contenu du .srt
        with open(srt_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        
        # Nettoyer le contenu : supprimer numéros et timecodes
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            # Ignore lignes vides, numéros, timecodes
            if line.isdigit():
                continue
            if "-->" in line:
                continue
            if line:
                cleaned_lines.append(line)
        
        # Sauvegarder en .txt
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("/n".join(cleaned_lines))
        
        # Supprimer le .srt original
        os.remove(srt_path)
        print(f"Converti et supprimé : {filename}")
