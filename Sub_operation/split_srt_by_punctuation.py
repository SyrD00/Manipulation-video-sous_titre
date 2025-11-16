r'''
pip install pysubs2

j'ai teste code le 11 Novembre 2025 et j'avias la version 1.8 de pysub2 et ca marchait pas :
PS C:\Users\babak\Documents\GitHub\Manipulation-video-sous_titre\Sub_operation> python split_srt_by_punctuation.py
Traceback (most recent call last):
  File "C:\Users\babak\Documents\GitHub\Manipulation-video-sous_titre\Sub_operation\split_srt_by_punctuation.py", line 1, in <module>
    import pysubs2
  File "C:\Users\babak\AppData\Local\Programs\Python\Python313\Lib\site-packages\pysubs2\__init__.py", line 1, in <module>
    from .ssafile import SSAFile
  File "C:\Users\babak\AppData\Local\Programs\Python\Python313\Lib\site-packages\pysubs2\ssafile.py", line 584, in <module>
    from .formats import autodetect_format, get_format_class, get_format_identifier  # noqa: E402   
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\babak\AppData\Local\Programs\Python\Python313\Lib\site-packages\pysubs2\formats\__init__.py", line 13, in <module>
    from .whisper import WhisperJAXFormat
ModuleNotFoundError: No module named 'pysubs2.formats.whisper'                  pip install pysubs2
>> C:\Users\babak\Documents\GitHub\Manipulation-video-sous_titre\Sub_operation>
Requirement already satisfied: pysubs2 in c:\users\babak\appdata\local\programs\python\python313\lib\site-packages (1.8.0)
PS C:\Users\babak\Documents\GitHub\Manipulation-video-sous_titre\Sub_operation> python split_srt_by_punctuation.py
Traceback (most recent call last):
  File "C:\Users\babak\Documents\GitHub\Manipulation-video-sous_titre\Sub_operation\split_srt_by_punctuation.py", line 4, in <module>
    import pysubs2
  File "C:\Users\babak\AppData\Local\Programs\Python\Python313\Lib\site-packages\pysubs2\__init__.py", line 1, in <module>
    from .ssafile import SSAFile
  File "C:\Users\babak\AppData\Local\Programs\Python\Python313\Lib\site-packages\pysubs2\ssafile.py", line 584, in <module>
    from .formats import autodetect_format, get_format_class, get_format_identifier  # noqa: E402   
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\babak\AppData\Local\Programs\Python\Python313\Lib\site-packages\pysubs2\formats\__init__.py", line 13, in <module>
    from .whisper import WhisperJAXFormat
ModuleNotFoundError: No module named 'pysubs2.formats.whisper'



Solution :installer une version anterieur
pip uninstall pysubs2
pip install pysubs2==1.6.0

'''
import pysubs2
import re

# Charger le fichier SRT original
input_file = r"C:\Users\babak\Videos\Precure\Dancing star precure\DSP.srt"
output_file =r"C:\Users\babak\Videos\Precure\Dancing star precure\DSP_split.srt"
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
