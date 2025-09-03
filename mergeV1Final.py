
import pysubs2

def merge_subtitles(eng_file, fr_file, output_file):
    """Fusionne les sous-titres anglais et français en leur attribuant les mêmes horodatages."""
    
    # Chargement des fichiers de sous-titres
    subs_eng = pysubs2.load(eng_file, encoding="utf-8")
    subs_fr = pysubs2.load(fr_file, encoding="utf-8")
    
    merged_subs = pysubs2.SSAFile()
    merged_subs.styles.update(subs_eng.styles)
    
    eng_dict = {s.start: s for s in subs_eng}  
    fr_dict = {s.start: s for s in subs_fr}

    used_eng_subs = set()
    used_fr_subs = set()

    # Fusion des sous-titres
    for start_time, eng_sub in eng_dict.items():
        closest_fr = min(
            fr_dict.values(),
            key=lambda s: abs(s.start - eng_sub.start),
            default=None
        )
        
        # Si une correspondance a été trouvée, on met à jour le texte français avec les mêmes timestamps
        if closest_fr:
            # On ajuste la fin du sous-titre français pour correspondre à celui de l'anglais
            end_time_fr = min(eng_sub.end, closest_fr.end)  # Empêche le chevauchement
            fr_sub = pysubs2.SSAEvent(
                start=eng_sub.start, end=end_time_fr, text=closest_fr.text
            )

            merged_subs.append(fr_sub)
            used_fr_subs.add(closest_fr.start)
        
        # Toujours ajouter le sous-titre anglais
        merged_subs.append(eng_sub)
        used_eng_subs.add(eng_sub.start)
    
    # Ajouter les sous-titres français non utilisés (ceux qui n'ont pas trouvé de correspondance)
    for fr_sub in subs_fr:
        if fr_sub.start not in used_fr_subs:
            # Si le sous-titre français n'a pas trouvé de correspondance, on l'ajoute avec les timestamps exacts
            merged_subs.append(fr_sub)
    
    # Tri des événements par start_time pour avoir un fichier de sous-titres correctement ordonné
    merged_subs.events.sort(key=lambda e: e.start)
    
    # Sauvegarder le fichier fusionné
    merged_subs.save(output_file, encoding="utf-8")

# Utilisation
merge_subtitles(
     "C:/Users/mamou/Videos/1/SL/SL6FR.ass",
    "C:/Users/mamou/Videos/1/SL/SL6ENG.ass",
    "C:/Users/mamou/Videos/1/SL/FUSION.ass"
)
