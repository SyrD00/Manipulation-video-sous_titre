import re
from tkinter import Tk, filedialog
import os

Tk().withdraw()
input = filedialog.askopenfilename(title="Sélectionne ton fichier .ass", filetypes=[("ASS files", "*.ass")])
if not input:
    print("Aucun fichier sélectionné.")
    exit()

output = os.path.splitext(input)[0] + "_sansbalise.ass"

with open(input, "r", encoding="utf-8") as infile, open(output, "w", encoding="utf-8") as outfile:
    for line in infile:
        newline = re.sub(r'\{[^}]*\}', '', line)
        outfile.write(newline)