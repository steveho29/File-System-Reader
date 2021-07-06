bootSectorStructure = {  # { offset: (name, unpack string) }
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

mainEntryStructure = {
        0x00: ('Name', '8s'),
        0x08: ('Extension name', '3s'),
        0x0B: ('Status', 'B'),
        0x0C: ('For', 'B'),
        0x0D: ('Created Time', '<I'),
        0x10: ('Created Date', '<H'),
        0x12: ('Latest Access', '<H'),
        0x14: ('Start Cluster High', '<H'),
        0x16: ('Latest Modified Time', '<H'),
        0x18: ('Latest Modified Day', '<H'),
        0x1A: ('Start Cluster Low', '<H'),
        0x1C: ('Size', '<I'),
    }

subEntryStructure = {
        0x00: ('Order Number', 'B'),
        0x01: ('5 chars Unicode', '10s'),
        0xB: ('SubEntry Signature', 'B'),
        0xE: ('6 next chars', '12s'),
        0x1C: ('2 next chars', '4s')

    }