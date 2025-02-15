import pysubs2

def merge_subtitles(fr_file, eng_file, output_file):
    """Fusionne les sous-titres tout en évitant les chevauchements et en gardant les styles anglais."""

    # Chargement des fichiers
    subs_fr = pysubs2.load(fr_file, encoding="utf-8")  
    subs_eng = pysubs2.load(eng_file, encoding="utf-8")

    merged_subs = pysubs2.SSAFile()
    merged_subs.styles.update(subs_eng.styles)  # Garde les styles anglais

    fr_list = list(subs_fr)
    eng_list = list(subs_eng)

    merged_events = []
    last_fr_text, last_eng_text = "", ""
    i, j = 0, 0  # Indices de parcours

    while i < len(fr_list) or j < len(eng_list):
        fr_sub = fr_list[i] if i < len(fr_list) else None
        eng_sub = eng_list[j] if j < len(eng_list) else None

        if fr_sub and eng_sub:
            if abs(fr_sub.start - eng_sub.start) <= 500:
                # Définir la fin pour éviter le chevauchement
                end_time = min(fr_sub.end, eng_sub.end)

                merged_text = f"{fr_sub.text.strip()}\\N{eng_sub.text.strip()}"
                merged_events.append(
                    pysubs2.SSAEvent(start=fr_sub.start, end=end_time, text=merged_text, style=eng_sub.style)
                )
                last_fr_text, last_eng_text = fr_sub.text, eng_sub.text
                i += 1
                j += 1

            elif fr_sub.start < eng_sub.start:
                # Phrase FR seule, mais on ajuste la fin
                adjusted_end = min(fr_sub.end, eng_sub.start - 10)  # Empêche chevauchement
                merged_text = f"{fr_sub.text.strip()}\\N{last_eng_text.strip()}" if last_eng_text else fr_sub.text
                merged_events.append(
                    pysubs2.SSAEvent(start=fr_sub.start, end=adjusted_end, text=merged_text, style=eng_sub.style)
                )
                last_fr_text = fr_sub.text
                i += 1

            else:
                # Phrase ENG seule, mais on ajuste la fin
                adjusted_end = min(eng_sub.end, fr_sub.start - 10)  # Empêche chevauchement
                merged_text = f"{last_fr_text.strip()}\\N{eng_sub.text.strip()}" if last_fr_text else eng_sub.text
                merged_events.append(
                    pysubs2.SSAEvent(start=eng_sub.start, end=adjusted_end, text=merged_text, style=eng_sub.style)
                )
                last_eng_text = eng_sub.text
                j += 1

        elif fr_sub:
            # Cas où il ne reste que des sous-titres FR
            merged_events.append(
                pysubs2.SSAEvent(start=fr_sub.start, end=fr_sub.end, text=fr_sub.text, style=eng_sub.style if eng_sub else "Default")
            )
            i += 1

        elif eng_sub:
            # Cas où il ne reste que des sous-titres ENG
            merged_events.append(
                pysubs2.SSAEvent(start=eng_sub.start, end=eng_sub.end, text=eng_sub.text, style=eng_sub.style)
            )
            j += 1

    # Sauvegarde du fichier fusionné
    merged_subs.events = merged_events
    merged_subs.events.sort(key=lambda e: e.start)
    merged_subs.save(output_file, encoding="utf-8")

# Utilisation
merge_subtitles(
    "C:/Users/mamou/Videos/1/SL/SL6FR.ass",  
    "C:/Users/mamou/Videos/1/SL/SL6ENG.ass",  
    "C:/Users/mamou/Videos/1/SL/FUSION.ass"
)
