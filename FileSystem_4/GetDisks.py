import os
from struct import unpack


def getDisks():
    l = [x.strip(':\\') for x in os.popen("fsutil fsinfo drives").read().split()]
    # l = [r'\\.\{}:'.format(x) for x in l if len(x) == 1 and x.isalpha()]
    l = [x for x in l if len(x) == 1 and x.isalpha()]
    print(l)
    return l


def getDiskType(diskName):
    diskPath = r'\\.\{}:'.format(diskName)
    with open(diskPath, 'rb') as f:
        f.read(3)
        if not 'NTFS' in unpack('8s', f.read(8))[0].decode('utf-8').split()[0].upper():
            f.seek(0)
            f.read(0x52)
            if 'FAT32' in unpack('8s', f.read(8))[0].decode('utf-8').split()[0].upper():
                return 'FAT32'
        else:
            return 'NTFS'

    return 'NULL'


