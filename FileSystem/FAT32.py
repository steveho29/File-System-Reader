from struct import unpack
from FAT32Functions import*


class BootFat32:
    bootSector = {  # { offset: (name, unpack string) }
        0x00: ('JumpInstruction', '3s'),
        0x03: ('OemID', '8s'),
        0x0B: ('BytesPerSector', '<H'),
        0x0D: ('SectorsPerCluster', 'B'),
        0x0E: ('SectorsOfBootSector', '<H'),
        0x10: ('FATCopies', 'B'),
        0x11: ('MaxRootEntries', '<H'),
        0x13: ('TotalSectors', '<H'),
        0x15: ('MediaDescriptor', 'B'),
        0x16: ('SectorsPerFAT', '<H'),  # not used, see 24h instead
        0x18: ('SectorsPerTrack', '<H'),
        0x1A: ('Heads', '<H'),
        0x1C: ('HiddenSectors', '<H'),
        0x1E: ('TotalHiddenSectors', '<H'),
        0x20: ('TotalLogicalSectors', '<I'),
        0x24: ('SectorsPerFAT', '<I'),
        0x28: ('MirroringFlags', '<H'),  # bits 0-3: active FAT, it bit 7 set; else: mirroring as usual
        0x2A: ('Version', '<H'),
        0x2C: ('RootCluster', '<I'),  # usually 2
        0x30: ('FSISector', '<H'),  # usually 1
        0x32: ('BootCopySector', '<H'),  # 0x0000 or 0xFFFF if unused, usually 6
        0x34: ('Reserved', '12s'),
        0x40: ('PhysDriveNumber', 'B'),
        0x41: ('Flags', 'B'),
        0x42: ('ExtBootSignature', 'B'),
        0x43: ('VolumeID', '<I'),
        0x47: ('VolumeLabel', '11s'),
        0x52: ('FSType', '8s'),
        # ~ 0x72: ('chBootstrapCode', '390s'),
        0x1FE: ('BootSignature', '<H')  # 55 AA
    }

    mainEntry = {
        0x00: ('Name', '8s'),
        0x08: ('Extension name', '3s'),
        0x0B: ('Status', 'B'),
        0x0C: ('For', 'B'),
        0x0D: ('Created Time', '<I'),
        0x10: ('Created Date', '<H'),
        0x12: ('Latest Access', '<H'),
        0x14: ('Start Cluster', '<H'),
        0x16: ('Latest Modified Time', '<H'),
        0x18: ('Latest Modified Day', '<H'),
        0x1A: ('Start Cluster Low', '<H'),
        0x1C: ('Size', '<I'),
    }

    subEntry = {
        0x00: ('Order Number', 'B'),
        0x01: ('5 chars Unicode', '10s'),
        0xB: ('SubEntry Signature', 'B'),
        0xE: ('6 next chars', '12s'),
        0x1C: ('2 next chars', '4s')

    }

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
        layout = list(self.bootSector.copy().items())
        for i, (start_offset, info) in enumerate(layout):
            if start_offset == 0x52:
                end_offset = 0x5A
            elif start_offset == 0x1FE:
                end_offset = 513
            else:
                end_offset = layout[i + 1][0]

            self.offset_name[info[0]] = unpack(info[1], boot_sector[start_offset:end_offset])[0]

        total_sectors = self.offset_name['TotalLogicalSectors']
        bytes_per_sectors = self.offset_name['BytesPerSector']
        self.size = float(total_sectors * bytes_per_sectors / (2.0 ** 30))

    def show_info(self):

        for name_offset, data in list(self.offset_name.items()):
            print('{}: {}'.format(name_offset, data))
        print('Total size: {} gb'.format(self.size))

    def read_subEntry(self, entry):
        extendedName = ''
        data = {}
        layout = list(self.subEntry.items())
        for i, (start_offset, (name, formatType)) in enumerate(layout):
            if start_offset == 0x1C:
                end_offset = 0x1C + 4
            elif start_offset == 0x01:
                end_offset = 0x01 + 10
            elif start_offset == 0xE:
                end_offset = 0xE + 12
            else:
                continue

            data[name] = unpack(formatType, entry[start_offset:end_offset])[0]
            extendedName += data[name].decode('UTF-16').strip('￿')
        # print(extendedName)
        return extendedName

    def read_main_entry(self, entry):
        mainEntry = list(self.mainEntry.items())
        data = {}
        for i, (start_offset, (name, formatType)) in enumerate(mainEntry):
            if i == len(mainEntry) - 1:
                end_offset = 0x20
            else:
                end_offset = mainEntry[i + 1][0]
            if name == 'Created Time':
                info = unpack(formatType, entry[start_offset:end_offset] + b'\x00')[0]

            else:
                info = unpack(formatType, entry[start_offset:end_offset])[0]

            if name == 'Created Date' or name == 'Latest Modified Day' or name == 'Latest Access':
                data[name] = getDate(info)
            elif name == 'Latest Modified Time':
                data[name] = getTime(info)
            elif name == 'Created Time':
                data[name] = getTimeCreated(info)

            else:
                data[name] = info

        return data

    def read_rdet(self):
        sectorStart = self.offset_name['SectorsOfBootSector']+2 * self.offset_name['SectorsPerFAT']
        with open(self.diskPath, 'rb') as fp:
            for i in range(sectorStart):
                fp.read(512)
            for i in range(512):
                entry = fp.read(32)
                status = unpack('B', entry[0:1])[0]
                if status == 0 or status == 229:
                    continue
                if unpack('B', entry[0x0B:0x0C])[0] != 15:
                    mainEntry = self.read_main_entry(entry)
                    mainEntry['Name'] = mainEntry['Name'].decode('utf-8').strip(' ')
                    extendedName = mainEntry['Extension name'].decode('utf-8').strip(' ')
                    if isFile(mainEntry['Status']):
                        mainEntry['Name'] += '.' + extendedName

                    mainEntry['Name'] += ' ' + extendedName

                else:
                    extendedName = ''
                    extendedName = self.read_subEntry(entry) + extendedName
                    entry = fp.read(32)
                    isSubEntry = unpack('B', entry[0x0B:0x0C])[0] == 15
                    while isSubEntry:
                        extendedName = self.read_subEntry(entry) + extendedName
                        entry = fp.read(32)
                        isSubEntry = unpack('B', entry[0x0B:0x0C])[0] == 15
                    mainEntry = self.read_main_entry(entry)
                    mainEntry['Name'] = extendedName
                mainEntry.pop('Extension name')

                for atb in mainEntry:
                    print('{}: {}'.format(atb, mainEntry[atb]), end='\t')
                print()
        fp.close()


drive = r"\\.\D:"
b = BootFat32(drive)
# b.show_info() 
b.read_rdet()
