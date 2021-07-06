# from rawdisk.plugins.filesystems.ntfs.ntfs_volume import NtfsVolume
from NTFSFunctions import *


class NTFS:
    bootSectorStructure = {  # { offset: (name, unpack string) }
        0x00: ('JumpInstruction', '3s'),
        0x03: ('OemID', '8s'),
        0x0B: ('BytesPerSector', '<H'),
        0x0D: ('SectorsPerCluster', 'B'),
        0x0E: ('ReservedSectors', '<H'),
        0x10: ('Reserved 1', 'BBBBB'),
        # 0x10: ('Always 0', 'BBB'),
        # 0x13: ('Not used by NTFS 1', '<H'),
        0x15: ('MediaDescriptor', 'B'),
        0x16: ('Reserved 2', '<H'),
        0x18: ('Not used or checked by NTSF', '<Q'),
        # 0x1A: ('Heads', '<H'),
        # 0x1C: ('HiddenSectors', '<I'),
        0x20: ('Reserved', '<Q'),
        0x28: ('TotalSectors', '<Q'),
        0x30: ('LogicalClusterNumber$MFT', '<Q'),
        0x38: ('LogicalClusterNumber$MFTMirror', '<Q'),
        0x40: ('Clusters Per File Record Segment', '<I'),
        0x44: ('Clusters Per Index Buffer', 'B'),
        0x45: ('Not used by NTFS', 'BBB'),
        0x48: ('Volume Serial Number', '<Q'),
        0x50: ('CheckSum', '<I'),
        # 0x54: ('Bootstrap Code', '426s'),
        0x01FE: ('End of Sector Marker', '<H')
    }

    def __init__(self, diskName):
        self.diskPath = r'\\.\{}:'.format(diskName)
        self.diskName = diskName
        self.bootSector = {}  # { name: value}
        self.size = 0
        self.MFT_start = 0
        # self.read_boot_sector(self.diskPath)

    def read_boot_sector(self, diskPath):
        with open(diskPath, 'rb') as fp:
            boot_sector = fp.read(512)
        bootSectorStructure = list(self.bootSectorStructure.items())
        for i, (start_offset, info) in enumerate(bootSectorStructure):
            if start_offset == 0x50:
                end_offset = 0x54
            elif start_offset == 0x1FE:
                end_offset = 513
            else:
                end_offset = bootSectorStructure[i + 1][0]

            # print(info)
            self.bootSector[info[0]] = unpack(info[1], boot_sector[start_offset:end_offset])[0]

        total_sectors = self.bootSector['TotalSectors']
        bytes_per_sectors = self.bootSector['BytesPerSector']
        self.bootSector['Size'] = '{} gb'.format(float(total_sectors * bytes_per_sectors / (2.0 ** 30)))
        self.bootSector['Disk'] = self.diskName
        self.MFT_start = int(
            self.bootSector['BytesPerSector'] * self.bootSector['SectorsPerCluster']
            * self.bootSector['LogicalClusterNumber$MFT'])

    def show_info(self):
        for name_offset in self.bootSector:
            print('{}: {}'.format(name_offset, self.bootSector[name_offset]))



if __name__ == '__main__':
    drive = "D"
    # c = NtfsVolume()
    # c.load(drive, 0)
    # c.dump_volume()
    # print(float(c.mft_zone_size) /
    #                 c.bootsector.volume_size * 100)

    b = NTFS(drive)
    b.show_info()
    b.Read_MFT()

    # print(c.mft_table)
    # print(c.mft_table_offset + 1024*12)
    # b.show_info()
    # b.read_rdet()
