def extract_text_from_srt(srt_path, txt_path):
    with open(srt_path, "r", encoding="utf-8") as srt, open(txt_path, "w", encoding="utf-8") as txt:
        for line in srt:
            line = line.strip()
            # Ignorer lignes vides, numéros et timestamps
            if line == "" or line.isdigit() or "-->" in line:
                continue
            txt.write(line + " ")

extract_text_from_srt("C:/Users/babak/Videos/PSO/PSO8.srt", "C:/Users/babak/Videos/PSO/PSO8_text.txt")
