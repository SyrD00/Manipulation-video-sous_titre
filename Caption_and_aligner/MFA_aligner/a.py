import torch

# Charger le modèle Silero VAD
model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad', model='silero_vad', force_reload=False)
(get_speech_timestamps, save_audio, read_audio, VADIterator, collect_chunks) = utils

# Charger un fichier audio (wav, mono, 16kHz)
wav = read_audio('mon_audio.wav', sampling_rate=16000)

# Détecter les segments de parole
speech_timestamps = get_speech_timestamps(wav, model)
print(speech_timestamps)