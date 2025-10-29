import pysubs2
import re

# Charger le fichier SRT original
input_file = "C:/Users/babak/Downloads/14.srt"
output_file ="C:/Users/babak//Downloads/14_split.srt"
subs = pysubs2.load(input_file, encoding="utf-8")

new_subs = pysubs2.SSAFile()

# Expression régulière universelle :
# Coupe après tout signe de ponctuation fort (.,!?,。！？、)
split_pattern = r'(?<=[\.\!\?。！？、,])'

for line in subs:
    parts = re.split(split_pattern, line.text)
    parts = [p.strip() for p in parts if p.strip()]

    if not parts:
        continue

    # Répartit le temps sur les sous-phrases
    t_step = (line.end - line.start) / len(parts)

    for i, p in enumerate(parts):
        new_line = line.copy()
        new_line.text = p
        new_line.start = line.start + i * t_step
        new_line.end = line.start + (i + 1) * t_step
        new_subs.append(new_line)

new_subs.save(output_file, encoding="utf-8")
print("✅ Fichier généré :", output_file)
