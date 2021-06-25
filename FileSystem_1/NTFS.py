from struct import unpack


class NTFSPartitionBoot:
    layout = {  # { offset: (name, unpack string) }
        0x00: ('JumpInstruction', '3s'),
        0x03: ('OemID', '8s'),
        0x0B: ('BytesPerSector', '<H'),
        0x0D: ('SectorsPerCluster', 'B'),
        0x0E: ('ReservedSectors', '<H'),
        0x10: ('Always 0', 'BBB'),
        0x13: ('Not used by NTFS 1', '<H'),
        0x15: ('MediaDescriptor', 'B'),
        0x16: ('Always 0', '<H'),
        0x18: ('SectorsPerTrack', '<H'),
        0x1A: ('Heads', '<H'),
        0x1C: ('HiddenSectors', '<I'),
        0x20: ('Not used by NTFS 2', '<I'),
        0x24: ('Not used by NTFS 3', '<I'),
        0x28: ('TotalSectors', '<Q'),
        0x30: ('Logical Cluster Number for the file $MFT', '<Q'),
        0x38: ('Logical Cluster Number for the file $MFTMirrd', '<Q'),
        0x40: ('Clusters Per File Record Segment', '<I'),
        0x44: ('Clusters Per Index Buffer', 'B'),
        0x45: ('Not used by NTFS 4', 'BBB'),
        0x48: ('Volume Serial Number', '<Q'),
        0x50: ('CheckSum', '<I'),
        # 0x54: ('Bootstrap Code', '426s'),
        0x01FE: ('End of Sector Marker', '<H')
    }  # Size = 0x200 (512 byte)

    def __init__(self, disk_path):
        self.diskPath = disk_path
        self.offset_name = {}  # { name: offset}
        self.size = 0

        self.read_boot_sector(self.diskPath)

    def get_boot_sector(self, diskPath):
        with open(diskPath, 'rb') as fp:
            boot_sector = fp.read(512)
        fp.close()
        return boot_sector

    def read_boot_sector(self, diskPath):
        boot_sector = self.get_boot_sector(diskPath)
        layout = list(self.layout.copy().items())
        for i, (start_offset, info) in enumerate(layout):
            if start_offset == 0x50:
                end_offset = 0x54
            elif start_offset == 0x1FE:
                end_offset = 513
            else:
                end_offset = layout[i + 1][0]

            # print(info)
            self.offset_name[info[0]] = unpack(info[1], boot_sector[start_offset:end_offset])[0]

        total_sectors = self.offset_name['TotalSectors']
        bytes_per_sectors = self.offset_name['BytesPerSector']
        self.size = float(total_sectors * bytes_per_sectors / (2.0 ** 30))

    def show_info(self):
        for name_offset, data in list(self.offset_name.items()):
            print('{}: {}'.format(name_offset, data))
        print('Total size: {} gb'.format(self.size))

    def read_rdet(self):
        numberSector = (self.offset_name['RootCluster']) * self.offset_name['SectorsPerCluster']
        print(numberSector)
        bytePerSector = self.offset_name['BytesPerSector']
        start_offset = numberSector * bytePerSector
        start_offset = 1 * bytePerSector
        print(start_offset)

        with open(self.diskPath, 'rb') as fp:
            fp.seek(start_offset)
            boot_sector = fp.read(512)

        fp.close()

        print(boot_sector)

drive = r"\\.\C:"
b = NTFSPartitionBoot(drive)
b.show_info()
# b.read_rdet()
