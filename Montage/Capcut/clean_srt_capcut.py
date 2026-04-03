import re
from typing import List, Tuple, Dict

# Constantes pour le format SRT
SRT_TIME_FORMAT = "%H:%M:%S,%f"

# =====================
# Fonctions utilitaires
# =====================

def srt_time_to_seconds(time_str: str) -> float:
    """Convertit une chaîne de temps SRT (HH:MM:SS,mmm) en secondes (float)."""
    try:
        # Remplace la virgule par le point pour le parsing des millisecondes
        time_str = time_str.replace(',', '.')
        
        # Le format doit correspondre à HH:MM:SS.mmm
        parts = time_str.split(':')
        hours = float(parts[0])
        minutes = float(parts[1])
        seconds = float(parts[2])
        
        return (hours * 3600) + (minutes * 60) + seconds
    except Exception as e:
        print(f"Erreur de parsing temporel pour '{time_str}': {e}")
        return 0.0

def seconds_to_srt_time(seconds: float) -> str:
    """Convertit un temps en secondes (float) au format SRT HH:MM:SS,mmm."""
    seconds = max(0, seconds) # Assure que le temps n'est pas négatif
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    # Calcule les millisecondes à partir de la partie décimale
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"

# =====================
# Logique de Fusion SRT
# =====================

def parse_srt(srt_path: str) -> List[Dict]:
    """Lit un fichier SRT et retourne une liste d'objets (start, end, text).
    
    Le fichier SRT est un simple fichier texte, mais il a une structure stricte. 
    La fonction parse_srt a pour rôle de lire le fichier SRT brut et de le convertir en une liste d'objets Python 
    (un dictionnaire pour chaque sous-titre) contenant uniquement les informations numériques exploitables : 
    le temps de début, le temps de fin, et le texte.

    1. Lire la structure du SRT
     Un fichier SRT classique est structuré en blocs séparés par des lignes vides :
            1
        00:00:05,000 --> 00:00:06,200
        Texte de la première ligne

        2
        00:00:06,500 --> 00:00:07,800
        Texte de la deuxième ligne
    
    2. Extraire les informations
       La fonction parse_srt utilise une expression régulière (re.compile) très puissante pour parcourir tout le contenu du fichier
       et capturer ces trois éléments pour chaque bloc :
        -L'index (ex: 1, 2).
        -Le temps de début (ex: 00:00:05,000).
        -Le temps de fin (ex: 00:00:06,200).
        -Le texte associé.

    La fonction parse_srt retourne une Liste de Dictionnaires où chaque dictionnaire représente un sous-titre, comme ceci :
        [
            {
                "start": 5.0,     # Le temps de début en secondes
                "end": 6.2,       # Le temps de fin en secondes
                "text": "Texte de la première ligne" 
            },
            {
                "start": 6.5,     # Le temps de début en secondes
                "end": 7.8,       # Le temps de fin en secondes
                "text": "Texte de la deuxième ligne"
            }
            # ... et ainsi de suite pour tous les sous-titres
       ]

    """
    
    # Regex pour capturer l'index, les temps et le texte
    pattern = re.compile(
        r"(\d+)\n"  # Index du sous-titre
        r"(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n"  # Temps
        r"([\s\S]*?)(?=\n\d+\n|\Z)",  # Texte (non gourmand, s'arrête avant le prochain index)
        re.MULTILINE | re.DOTALL
    )
    
    with open(srt_path, 'r', encoding='utf-8') as f:
        content = f.read().strip()
    
    blocks = []
    
    for match in pattern.finditer(content):# Parcourt chaque bloc capturé
        # Index, temps de début, temps de fin, texte
        _, start_str, end_str, text_block = match.groups()
        
        blocks.append({
            "start": srt_time_to_seconds(start_str),
            "end": srt_time_to_seconds(end_str),
            "text": text_block.strip()
        })
        
    return blocks

def merge_srt_subtitles(input_srt_path: str, output_srt_path: str, pause_threshold: float):
    """
    Fusionne les lignes SRT consécutives où la pause est inférieure
    au seuil spécifié.
    """
    
    # 1. Charger et parser les blocs SRT
    subtitles = parse_srt(input_srt_path)
    if not subtitles:
        print("Erreur: Aucun sous-titre trouvé ou fichier SRT invalide.")
        return

    merged_subs = []
    current_sub = None
    
    for next_sub in subtitles:
        if current_sub is None:
            # Démarrer le premier sous-titre
            current_sub = next_sub
            continue

        # Calculer la pause entre la fin du sous-titre actuel et le début du suivant
        pause = next_sub['start'] - current_sub['end']
        
        # Logique de fusion:
        # Si la pause est courte (inférieure au seuil)
        if pause < pause_threshold:
            # Fusionner le texte et étendre le temps de fin
            current_sub['text'] += "\n" + next_sub['text']
            current_sub['end'] = next_sub['end']
        else:
            # Si la pause est longue, enregistrer le sous-titre actuel et démarrer le suivant
            merged_subs.append(current_sub)
            current_sub = next_sub
            
    # Ajouter le dernier sous-titre s'il existe
    if current_sub is not None:
        merged_subs.append(current_sub)

    # 2. Écrire le nouveau fichier SRT
    with open(output_srt_path, 'w', encoding='utf-8') as f:
        for idx, sub in enumerate(merged_subs, 1):
            f.write(f"{idx}\n")
            f.write(f"{seconds_to_srt_time(sub['start'])} --> {seconds_to_srt_time(sub['end'])}\n")
            f.write(f"{sub['text']}\n\n")

    print(f"Fusion réussie. Nouveaux sous-titres enregistrés dans: {output_srt_path}")
    print(f"Sous-titres originaux: {len(subtitles)}, Sous-titres fusionnés: {len(merged_subs)}")


# =====================
# Exécution principale
# =====================

if __name__ == "__main__":
    # --- Modifiez ces chemins ---
    
    # Le chemin vers le fichier SRT d'origine (celui de CapCut)
    INPUT_SRT_FILE = "C:/Users/babak/Videos/PSO/Sub/PSO27_capcut.srt"
    
    # Le chemin vers le nouveau fichier SRT nettoyé
    OUTPUT_SRT_FILE = "C:/Users/babak/Videos/PSO/Sub/PSO27_cleaned.srt"
    
    # --- Seuil de Pause ---
    # Si le silence entre deux lignes SRT est inférieur à ce seuil (en secondes), 
    # les deux lignes seront fusionnées.
    # 0.1 est un bon point de départ, car les pauses de respiration sont généralement plus longues.
    PAUSE_THRESHOLD = 0.15
    
    print(f"Démarrage de la fusion SRT avec un seuil de pause de {PAUSE_THRESHOLD} secondes.")
    merge_srt_subtitles(INPUT_SRT_FILE, OUTPUT_SRT_FILE, PAUSE_THRESHOLD)
