import json

def try_parse_json_string(value):
    """Essaie de parser une chaîne comme JSON, sinon renvoie l'original."""
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value

def deep_parse(obj):
    """Parcourt récursivement dict/liste pour reparser les sous-JSON encodés en texte."""
    if isinstance(obj, dict):
        return {k: deep_parse(try_parse_json_string(v)) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [deep_parse(try_parse_json_string(v)) for v in obj]
    else:
        return obj

# Lire le JSON brut
with open("C:/Users/babak/AppData/Local/CapCut/User Data/Projects/com.lveditor.draft/0925/draft_content.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Reparser les sous-JSON stockés comme chaînes
data = deep_parse(data)

# Réécrire joliment
with open("draft2_content_pretty.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print("✅ Fichier reformatté : draft_content_pretty.json")
