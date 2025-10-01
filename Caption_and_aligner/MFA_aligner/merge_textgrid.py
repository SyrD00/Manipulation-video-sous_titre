import os
from textgrid import TextGrid

# Répertoires
input_dir = "C:/Users/babak/Videos/PSO/Episode/output_align/"
output_file = "C:/Users/babak/Videos/PSO/Episode/merged_output/mergedF.TextGrid"

# Créer le dossier de sortie si il n'existe pas
os.makedirs(os.path.dirname(output_file), exist_ok=True)

# Lister tous les fichiers TextGrid
textgrid_files = [f for f in os.listdir(input_dir) if f.endswith('.TextGrid')]

# Liste pour stocker tous les TextGrid
all_tgs = []

# Lire tous les TextGrid
for tg_file in textgrid_files:
    tg_path = os.path.join(input_dir, tg_file)
    tg = TextGrid()
    tg.read(tg_path)
    all_tgs.append(tg)

# Fusionner les TextGrid
merged_tg = TextGrid()
time_offset = 0.0  # Pour décaler les intervalles

for tg in all_tgs:
    for tier in tg.tiers:
        # Vérifier si la tier existe déjà dans merged_tg
        merged_tier = next((t for t in merged_tg.tiers if t.name == tier.name), None)
        if not merged_tier:
            # Créer une nouvelle tier
            merged_tier = type(tier)(name=tier.name)
            merged_tg.append(merged_tier)
        
        # Ajouter les intervalles ou points avec décalage
        for interval in getattr(tier, 'intervals', getattr(tier, 'points', [])):
            if hasattr(interval, 'mark'):  # IntervalTier
                merged_tier.add(interval.minTime + time_offset, interval.maxTime + time_offset, interval.mark)
            else:  # PointTier
                merged_tier.add(interval.time + time_offset, interval.mark)
    
    # Mettre à jour le décalage pour le prochain TextGrid
    tg_end_time = tg.maxTime
    time_offset += tg_end_time

# Sauvegarder le TextGrid fusionné
merged_tg.write(output_file)
print(f"✅ TextGrid fusionné créé ici : {output_file}")
