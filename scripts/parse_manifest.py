import zipfile
import struct

def parse_axml_strings(data):
    # Header: magic (4), file_size (4), string_pool_tag (4), string_pool_size (4), string_count (4), style_count (4)
    magic, file_size, chunk_type, chunk_size, string_count, style_count, flags, strings_start, styles_start = struct.unpack('<IIIIIIIII', data[:36])
    print(f'Magic: {hex(magic)}, Strings: {string_count}, Start: {strings_start}')
    is_utf8 = bool(flags & (1 << 8))
    
    offsets = struct.unpack(f'<{string_count}I', data[36:36 + 4 * string_count])
    strings = []
    pool_data = data[36 + 4 * string_count:] # from end of offset table
    
    # Actually strings start from 8 + strings_start
    pool_base = 8 + strings_start
    for off in offsets:
        cur = pool_base + off
        if is_utf8:
            # UTF8 format: len in bytes
            u8len = data[cur + 1]
            s = data[cur + 2:cur + 2 + u8len].decode('utf-8', errors='ignore')
        else:
            # UTF16 format: len in chars
            u16len = struct.unpack('<H', data[cur:cur+2])[0]
            s = data[cur + 2:cur + 2 + u16len * 2].decode('utf-16le', errors='ignore')
        strings.append(s)
    return strings

with zipfile.ZipFile('static/Hermes_Apex_Trading_Terminal.apk', 'r') as z:
    manifest = z.read('AndroidManifest.xml')
    strs = parse_axml_strings(manifest)
    print('Strings in Manifest:')
    for s in strs:
        if s and not s.startswith('android.') and len(s) > 2:
            print('  ->', s)
