#pip install py-cpuinfo
#avx permet d'accélérer les calculs en virgule flottante nécessaires pour les modèles de deep learning comme Whisper.  


"""
 la lib faster-whisper → elle repose sur CTranslate2 (le moteur d’inférence).

CTranslate2 a été compilé en plusieurs variantes (avec AVX, AVX2, AVX512, CUDA, etc.).

Quand tu installes faster-whisper via pip, il télécharge un binaire de CTranslate2 précompilé optimisé 
pour AVX2 (si ta machine supporte ces instructions).
"""
import cpuinfo
flags = cpuinfo.get_cpu_info()['flags']
print("AVX présent :", 'avx' in flags)
print("AVX2 présent :", 'avx2' in flags)
