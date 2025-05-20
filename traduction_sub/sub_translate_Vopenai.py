import os
import time
import openai
import pysrt
import ass
from openai import OpenAI

# Configure ton API key OpenAI
client = OpenAI(api_key="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")  # Remplace "ta_clé_openai" par ta vraie clé

# Traduction via OpenAI Chat API
def traduire(texte):
    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Ou "gpt-4" si tu l’as
            messages=[
                {"role": "system", "content": "Tu es un traducteur professionnel d’anime japonais vers le français. Garde un ton naturel et fluide."},
                {"role": "user", "content": f"Traduis ce texte japonais en français :\n{texte}"}
            ]
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"Erreur : {e}")
        return texte

# Traduction de SRT
def traiter_srt(fichier):
    subs = pysrt.open(fichier, encoding='utf-8-sig')
    total = len(subs)
    for i, sub in enumerate(subs):
        print(f"[{i+1}/{total}] {sub.text}")
        traduction = traduire(sub.text)
        sub.text = f"{sub.text}\n{traduction}"
        time.sleep(1.5)
    nom_fichier = os.path.splitext(fichier)[0] + "_traduit.srt"
    subs.save(nom_fichier, encoding='utf-8')
    print(f"✅ Fichier traduit enregistré ici : {nom_fichier}")

# Traduction de ASS
def traiter_ass(fichier):
    with open(fichier, encoding="utf-8-sig") as f:
        doc = ass.parse(f)
        total = len([e for e in doc.events if isinstance(e, ass.Dialogue)])

        count = 0
        for event in doc.events:
            if isinstance(event, ass.Dialogue):
                texte_original = event.text
                print(f"[{count+1}/{total}] {texte_original}")
                traduction = traduire(texte_original)
                event.text = f"{texte_original}\\N{traduction}"
                count += 1
                time.sleep(1.5)

    nom_fichier = os.path.splitext(fichier)[0] + "_traduit.ass"
    with open(nom_fichier, "w", encoding="utf-8") as f:
        f.write(str(doc))
    print(f"✅ Fichier traduit enregistré ici : {nom_fichier}")

# Point d’entrée
if __name__ == "__main__":
    chemin_fichier = "C:/Users/mamou/Videos/1/PSO/PSO.ass"  # Remplace avec le vrai nom

    if chemin_fichier.endswith(".srt"):
        traiter_srt(chemin_fichier)
    elif chemin_fichier.endswith(".ass"):
        traiter_ass(chemin_fichier)
    else:
        print("❌ Format non pris en charge. Utilise .srt ou .ass uniquement.")
