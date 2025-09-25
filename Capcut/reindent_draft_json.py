import json

# Ouvrir le fichier d'origine
with open("draft_content.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Réécriture du JSON avec indentation
with open("draft_content_pretty.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print("✅ Fichier reformatté : draft_content_pretty.json")
