import re
import os

# ---------------- CONFIG ----------------
input_file = r"C:/Users/babak/Videos/PSO/Episode/A.srt"
main_font = "Tahoma "
fallback_font = "Segoe UI Symbol"  # sans Bold
text_size = 50
output_dir = r"C:/Users/babak/Videos/PSO/Episode/TextPlus_Settings"
output_file = os.path.join(output_dir, "TextPlus_Composite.comp")

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# ---------------- LECTURE DU TEXTE ----------------
def read_text(file_path):
    """Lit le texte SRT et nettoie les numéros, timecodes et BOM"""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    lines = []
    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
        # Ignore numéro de sous-titre
        if re.match(r"^\d+$", line):
            continue
        # Ignore timecodes SRT
        if re.match(r"\d{2}:\d{2}:\d{2}[,\.]\d{3}", line):
            continue
        # Supprime BOM invisible
        line = line.replace("\ufeff", "")
        lines.append(line)
    return "\n".join(lines).strip()

# ---------------- SÉPARATION TEXTE / FALLBACK ----------------
def separate_text(text):
    """Sépare le texte normal et les glyphes spéciaux (Unicode > 127)"""
    normal_text = ""
    fallback_text = ""
    for c in text:
        if ord(c) > 127:  # caractères spéciaux (🎶, emojis, etc.)
            normal_text += " "
            fallback_text += c
        else:
            normal_text += c
            fallback_text += " "
    return normal_text, fallback_text

# ---------------- GÉNÉRATION DU FICHIER .COMP ----------------
def create_fusion_comp(normal_text, fallback_text):
    # Style = 0 → Normal, 1 = Bold, 2 = Italic...
    return f"""Composition {{
   CurrentTime = 0,
   Tools = {{
      Text_Main = TextPlus {{
         CtrlWZoom = false,
         Inputs = {{
            StyledText = Input {{ Value = [[{normal_text}]] }},
            Font = Input {{ Value = "{main_font}" }},
            Size = Input {{ Value = {text_size} }},
            Style = Input {{ Value = 0 }},
         }},
         ViewInfo = OperatorInfo {{ Pos = {{0, 0}} }},
      }},
      Text_Fallback = TextPlus {{
         CtrlWZoom = false,
         Inputs = {{
            StyledText = Input {{ Value = [[{fallback_text}]] }},
            Font = Input {{ Value = "{fallback_font}" }},
            Size = Input {{ Value = {text_size} }},
            Style = Input {{ Value = 0 }},
         }},
         ViewInfo = OperatorInfo {{ Pos = {{0, -1}} }},
      }},
      Merge1 = Merge {{
         CtrlWZoom = false,
         Inputs = {{
            Background = Input {{ SourceOp = "Text_Main", Source = "Output" }},
            Foreground = Input {{ SourceOp = "Text_Fallback", Source = "Output" }},
         }},
         ViewInfo = OperatorInfo {{ Pos = {{1, 0}} }},
      }},
      MediaOut1 = MediaOut {{
         CtrlWZoom = false,
         Inputs = {{
            Input = Input {{ SourceOp = "Merge1", Source = "Output" }},
         }},
         ViewInfo = OperatorInfo {{ Pos = {{2, 0}} }},
      }},
   }}
}}
"""

# ---------------- MAIN ----------------
full_text = read_text(input_file)
normal_text, fallback_text = separate_text(full_text)
comp_content = create_fusion_comp(normal_text, fallback_text)

# Sauvegarde du .comp
with open(output_file, "w", encoding="utf-8") as f:
    f.write(comp_content)

print("\n✅ Composition Fusion générée !")
print(f"→ {output_file}")
print("1️⃣ Crée une Fusion Composition vide dans Montage ou Edit.")
print("2️⃣ Ouvre-la dans Fusion et importe ce fichier (.comp).")
print("3️⃣ Text_Main + Text_Fallback apparaissent superposés, 🎶 en Segoe UI Symbol sans Bold.")
