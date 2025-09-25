
"""
pour l'instant code donne mauvais horodqtage srt un jour je m'en occuperais quand j'aurais le temps.
De toute facon whisper x n'est pas precis(regarde le json et regarde a peu pres ta video =tu verras 
c'est pas precis)
"""
import whisperx
import gc
import srt
import re
from datetime import timedelta

# 1️⃣ Configuration du modèle
device = "cpu"  # "cuda" si GPU
model_size = "large-v2"
compute_type = "float32"  # "float16" si GPU
batch_size = 32

print(f"Chargement du modèle '{model_size}' sur '{device}'...")
model = whisperx.load_model(model_size, device, compute_type=compute_type)

# 2️⃣ Transcription de l'audio
audio_file = "C:/Users/babak/Videos/PSO/Episode/Audio/chibi_12half.wav"
print(f"Transcription de l'audio: {audio_file}...")

result = model.transcribe(
    audio_file,
    batch_size=batch_size,
    language="ja"
)

# Libérer le modèle de transcription
del model
gc.collect()


# 3️⃣ Alignement précis mot par mot
print("Alignement précis des mots...")
model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device)

# Appel avec arguments POSITIONNELS uniquement
result = whisperx.align(
    result["segments"],   # segments
    model_a,              # modèle d'alignement
    metadata,             # align_model_metadata
    audio_file,           # chemin audio
    device,               # cpu/gpu
    return_char_alignments=True  # <- nécessaire pour mot par mot
)



# 4️⃣ Construire les phrases avec mots - Version Vraiment Finale
subs = []
sub_index = 1

for segment in result["segments"]:
    # 1. Texte brut du segment tel que transcrit (raw_text)
    raw_text = segment['text']
    current_words = segment.get('word_segments', [])
    
    # 2. Nettoyage du texte pour l'INDEXATION et le DÉCOUPAGE
    # Remplacer TOUT espace (y compris espace, tab, newline) par RIEN
    cleaned_text_for_index = re.sub(r'\s+', '', raw_text) 
    
    # AJOUT DE SÉCURITÉ : Point de fin dans le texte nettoyé
    if cleaned_text_for_index and cleaned_text_for_index[-1] not in ('。', '！', '!', '？', '?'):
        cleaned_text_for_index += '。'

    # Découpage du segment en phrases japonaises sur le texte nettoyé
    sentences = re.split(r'(?<=。|！|!|？|\?)', cleaned_text_for_index)
    sentences = [s.strip() for s in sentences if s.strip()]
    if not sentences:
        sentences = [cleaned_text_for_index.rstrip('。')] # Cas de repli

    # Initialisation des pointeurs pour l'attribution des mots
    word_ptr = 0 
    current_char_offset = 0 # Pointeur de début de recherche dans cleaned_text_for_index

    # Pour chaque phrase découpée :
    for sentence in sentences:
        if not sentence: continue

        words_in_sentence = []
        
        # 🚨 ÉTAPE CLÉ 1 : Trouver la plage de caractères (start, end)
        # On cherche la phrase DÉCOUPÉE (sentence) dans le texte NETTOYÉ (cleaned_text_for_index).
        start_in_cleaned_index = cleaned_text_for_index.find(sentence, current_char_offset)
        
        if start_in_cleaned_index != -1:
            end_in_cleaned_index = start_in_cleaned_index + len(sentence)
            current_char_offset = end_in_cleaned_index
            
            # 🚨 ÉTAPE CLÉ 2 : Attribution des mots
            # Le 'char_start' des mots alignés correspond à l'index dans la version nettoyée !
            while word_ptr < len(current_words):
                word = current_words[word_ptr]
                
                # Récupérer l'index de caractère du mot
                # ATTENTION: Si 'char_start' n'existe pas, votre alignement est corrompu ou incomplet.
                char_pos = word.get('char_start') 
                
                if char_pos is None:
                    # Gérer le cas où char_start n'est pas là (très rare avec whisperx.align)
                    print(f"Erreur fatale: 'char_start' manquant pour le mot {word['word']}")
                    break

                # ⚠️ L'erreur est là: char_pos doit être comparé à la plage du texte nettoyé.
                if char_pos >= start_in_cleaned_index and char_pos < end_in_cleaned_index:
                    words_in_sentence.append(word)
                    word_ptr += 1
                elif char_pos >= end_in_cleaned_index:
                    # Le mot est après la fin de la phrase
                    break
                else:
                    # Le mot est avant le début (logique de pointeur)
                    word_ptr += 1


        # 3. CRÉATION DU SOUS-TITRE
        if words_in_sentence:
            # 🥳 SUCCÈS : Timing précis
            start = words_in_sentence[0]['start']
            end = words_in_sentence[-1]['end']
            sentence_text = sentence.rstrip('。')
        else:
            # 😫 ÉCHEC : Cas de repli (ce qui se passe actuellement)
            print(f"ATTENTION: Mots non trouvés pour la phrase: '{sentence}'. Utilisation du timing de segment.")
            start = segment['start']
            end = segment['end']
            sentence_text = sentence.rstrip('。')


        # Ajouter au SRT
        subs.append(srt.Subtitle(
            index=sub_index,
            start=timedelta(seconds=start),
            end=timedelta(seconds=end),
            content=sentence_text
        ))
        sub_index += 1

# 5️⃣ Sauvegarder le SRT
output_srt_path = "C:/Users/babak/Videos/PSO/Episode/sous_titres_phrases.srt"
with open(output_srt_path, "w", encoding="utf-8") as f:
    f.write(srt.compose(subs))

print(f"Fichier SRT généré avec phrases et mots: {output_srt_path}")
