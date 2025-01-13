import re
from datetime import datetime, timedelta

def parse_srt(file_path):
    """Parse an SRT file into a list of subtitle entries line by line."""
    subtitles = []
    with open(file_path, 'r', encoding='utf-8-sig') as file:
        block = []
        for line in file:
            if line.strip():
                block.append(line.strip())
            else:
                if block:
                    index = int(block[0])
                    start, end = block[1].split(' --> ')
                    text = '\n'.join(block[2:])
                    subtitles.append({'index': index, 'start': start, 'end': end, 'text': text})
                    block = []
        # Handle the last block
        if block:
            index = int(block[0])
            start, end = block[1].split(' --> ')
            text = '\n'.join(block[2:])
            subtitles.append({'index': index, 'start': start, 'end': end, 'text': text})
    return subtitles

def format_srt(subtitles):
    """Format a list of subtitle entries into SRT format."""
    srt_content = ""
    for sub in subtitles:
        srt_content += f"{sub['index']}\n{sub['start']} --> {sub['end']}\n{sub['text']}\n\n"
    return srt_content





def parse_time(time_str):

    """Convertit un horodatage SRT en objet datetime."""

    return datetime.strptime(time_str, "%H:%M:%S,%f")



def format_time(time_obj):

    """Convertit un objet datetime en horodatage SRT."""

    return time_obj.strftime("%H:%M:%S,%f")[:-3]



def parse_time(time_str):

    """Convertit un horodatage SRT en objet datetime."""

    return datetime.strptime(time_str, "%H:%M:%S,%f")



def format_time(time_obj):

    """Convertit un objet datetime en horodatage SRT."""

    return time_obj.strftime("%H:%M:%S,%f")[:-3]



def merge_srt(eng_subs, fr_subs):

    """Fusionne les sous-titres anglais et français sans chevauchement."""

    merged_subs = []

    fr_index = 0  # Index pour parcourir les sous-titres français

    prev_end_time = None  # Pour vérifier les chevauchements



    for eng in eng_subs:

        eng_start = parse_time(eng['start'])

        eng_end = parse_time(eng['end'])

        eng_text = eng['text']



        # Ajuster le début si chevauchement avec le sous-titre précédent

        if prev_end_time and eng_start < prev_end_time:

            eng_start = prev_end_time + timedelta(milliseconds=1)



        # Chercher un sous-titre FR qui chevauche avec le EN

        merged_text = eng_text

        while fr_index < len(fr_subs):

            fr_sub = fr_subs[fr_index]

            fr_start = parse_time(fr_sub['start'])

            fr_end = parse_time(fr_sub['end'])

            fr_text = fr_sub['text']



            # Si le sous-titre FR commence après le sous-titre EN, on arrête de chercher

            if fr_start > eng_end:

                break



            # S'il y a un chevauchement, on fusionne les textes

            if fr_end >= eng_start:

                merged_text += f"\n{fr_text}"

                eng_end = max(eng_end, fr_end)  # Étendre la fin si nécessaire



            fr_index += 1  # Passer au sous-titre FR suivant



        # Ajouter le sous-titre fusionné

        merged_subs.append({

            'index': len(merged_subs) + 1,

            'start': format_time(eng_start),

            'end': format_time(eng_end),

            'text': merged_text

        })



        prev_end_time = eng_end  # Mettre à jour la fin du dernier sous-titre



    return merged_subs

def save_srt(file_path, subtitles):
    """Save subtitles to an SRT file."""
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(format_srt(subtitles))

# File paths
eng_path = "C:/Users/mamou/Downloads/SoloLeveling_S02E01_ENGSUB.srt"
fr_path = "C:/Users/mamou/Downloads/SoloLeveling_S02E01_FR.srt"
output_path = "C:/Users/mamou/Downloads/merged_subtitles.srt"

# Parse subtitles
eng_subs = parse_srt(eng_path)
fr_subs = parse_srt(fr_path)

# Merge subtitles
merged_subs = merge_srt(eng_subs, fr_subs)


# Save merged subtitles
save_srt(output_path, merged_subs)

output_path
