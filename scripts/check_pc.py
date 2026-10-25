import ctypes
import shutil
import subprocess

class MEM(ctypes.Structure):
    _fields_ = [
        ('dwLength', ctypes.c_ulong),
        ('dwMemoryLoad', ctypes.c_ulong),
        ('ullTotalPhys', ctypes.c_ulonglong),
        ('ullAvailPhys', ctypes.c_ulonglong),
        ('ullTotalPageFile', ctypes.c_ulonglong),
        ('ullAvailPageFile', ctypes.c_ulonglong),
        ('ullTotalVirtual', ctypes.c_ulonglong),
        ('ullAvailVirtual', ctypes.c_ulonglong),
        ('sullAvailExtendedVirtual', ctypes.c_ulonglong),
    ]

mem = MEM()
mem.dwLength = ctypes.sizeof(MEM)
ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(mem))

total_ram = round(mem.ullTotalPhys / (1024**3), 2)
avail_ram = round(mem.ullAvailPhys / (1024**3), 2)

total, used, free = shutil.disk_usage('C:')
free_disk = round(free / (1024**3), 2)

print(f"TOTAL_RAM: {total_ram} GB")
print(f"AVAIL_RAM: {avail_ram} GB")
print(f"FREE_DISK: {free_disk} GB")

try:
    cpu_info = subprocess.check_output('wmic cpu get name', shell=True).decode()
    for l in cpu_info.splitlines():
        if l.strip() and 'Name' not in l:
            print("CPU:", l.strip())
except Exception as e:
    print("CPU error:", e)

try:
    gpu_info = subprocess.check_output('wmic path win32_videocontroller get name', shell=True).decode()
    for l in gpu_info.splitlines():
        if l.strip() and 'Name' not in l:
            print("GPU:", l.strip())
except Exception as e:
    print("GPU error:", e)
