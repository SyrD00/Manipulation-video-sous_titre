#pip install py-cpuinfo

import cpuinfo
flags = cpuinfo.get_cpu_info()['flags']
print("AVX présent :", 'avx' in flags)
print("AVX2 présent :", 'avx2' in flags)
