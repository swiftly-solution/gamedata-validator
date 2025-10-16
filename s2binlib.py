import ctypes as C
from ctypes import *

PatternScanCallback = CFUNCTYPE(
    c_bool,
    c_size_t,
    c_void_p, 
    c_void_p
)

dll = None

def initialize(game_path, game_name, os):
    global dll
    dll = C.cdll.LoadLibrary("./s2binlib.dll")
    ret = dll.s2binlib_initialize_with_os(game_path.encode(), game_name.encode(), os.encode())
    if ret != 0:
        raise Exception(f"Failed to initialize, error code {ret}")

def find_vtable_va(class_binary_name, class_name):
    buffer = C.c_uint64(0)
    ret = dll.s2binlib_find_vtable_va(class_binary_name.encode(), class_name.encode(), C.byref(buffer))
    if ret != 0:
        raise Exception(f"Failed to find vtable, error code {ret}")
    return buffer.value

def get_vfunc_count(class_binary_name, class_name):
    buffer = C.c_uint64(0)
    ret = dll.s2binlib_get_vtable_vfunc_count(class_binary_name.encode(), class_name.encode(), C.byref(buffer))
    if ret != 0:
        raise Exception(f"Failed to find vtable, error code {ret}")
    return buffer.value

def pattern_scan(class_binary_name, pattern):
    buffer = C.c_uint64(0)
    match = 0
    count = 0
    
    def callback(index, address, user_data):
        nonlocal count
        nonlocal match
        count += 1
        match = address
        return False
    cb = PatternScanCallback(callback)
    ret = dll.s2binlib_pattern_scan_all_va(class_binary_name.encode(), pattern.encode(), cb, 0)
    if ret != 0 and ret != -4:
        raise Exception(f"Failed to find pattern, error code {ret}")
    return (match, count)