from FAT32Functions import *
from FAT32STRUCTURE import *
from PyQt5.QtCore import QThread, pyqtSignal


fileOrder = 1

NUMBER_THREAD = 4


def read_main_entry(entry):
    mainEntryData = list(mainEntryStructure.items())
    data = {}
    for i, (start_offset, (name, formatType)) in enumerate(mainEntryData):
        if i == len(mainEntryData) - 1:
            end_offset = 0x20
        else:
            end_offset = mainEntryData[i + 1][0]
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
    data['Name'] = data['Name']
    return data


def read_subEntry(entry):
    extendedName = ''
    data = {}
    layout = list(subEntryStructure.items())
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


class TXTReaderThread(QThread):
    finish = pyqtSignal(object)

    def __init__(self, disk, sectors, bytesPerSector):
        super(TXTReaderThread, self).__init__()
        self.sectors = sectors
        self.bytesPerSector = bytesPerSector
        self.diskPath = r'\\.\{}:'.format(disk)

    def run(self):
        fp = open(self.diskPath, 'rb')
        # print(self.sectors)
        file = []
        for sector in self.sectors:
            fp.seekable()
            fp.seek(sector*self.bytesPerSector)
            file.append(fp.read(self.bytesPerSector))

        file = b''.join(file)
        try:
            file = file[:file.index(b'\x00')].decode('utf-8')
        except:
            file = file.decode('utf-8')

        fp.close()
        # print(file)
        self.finish.emit(file)


class DFSThread(QThread):
    finish = pyqtSignal(object)
    fileSignal = pyqtSignal(object)

    def __init__(self, diskPath, FATTable, sectorStartRDET, clusterStartRDET, rootFolder, bytesPerSector, sectorPerCluster):
        super(DFSThread, self).__init__()
        self.diskPath = diskPath
        self.diskName = diskPath.strip(r'\\.\:')
        self.rootFolder = rootFolder
        self.maxSector = 0
        self.bytesPerSector = bytesPerSector
        self.clusterStartRDET = clusterStartRDET
        self.sectorStartRDET = sectorStartRDET
        self.sectorPerCluster = sectorPerCluster
        self.FATTable = FATTable

    def DFS_SDET(self, rootData, sector_start, sector_end, space=0):
        fp = open(self.diskPath, 'rb')
        fp.seekable()
        fp.seek(sector_start * self.bytesPerSector)
        fp.read(64)

        space += 10
        n = int((sector_end - sector_start + 1) * self.bytesPerSector/32)

        for i in range(n):
            entry = fp.read(32)
            status = unpack('B', entry[0:1])[0]
            if status == 229:
                continue
            elif status == 0:
                break

            status = unpack('B', entry[0x0B:0x0C])[0]

            if status != 15:
                if not isValidFile(status):
                    continue
                mainEntry = read_main_entry(entry)

                name = mainEntry['Name']
                extendedName = mainEntry['Extension name']
                if isFile(mainEntry['Status']):
                    mainEntry['Name'] = name.decode('utf-8').strip(' ') + '.' + extendedName.decode('utf-8').strip(
                        ' ').strip('\x00')
                else:
                    mainEntry['Name'] = (name + extendedName).decode('utf-8').strip('\x00')
            else:
                extendedName = ''
                extendedName = read_subEntry(entry) + extendedName.strip('\x00')
                entry = fp.read(32)

                isSubEntry = unpack('B', entry[0x0B:0x0C])[0] == 15
                while isSubEntry:
                    extendedName = read_subEntry(entry) + extendedName.strip('\x00')
                    entry = fp.read(32)
                    isSubEntry = unpack('B', entry[0x0B:0x0C])[0] == 15

                status_1 = unpack('B', entry[0:1])[0]
                if status_1 == 0 or status_1 == 229:
                    continue
                mainEntry = read_main_entry(entry)

                if not isValidFile(mainEntry['Status']):
                    continue
                mainEntry['Name'] = extendedName.strip('\x00')

                mainEntry.pop('Extension name')

                # for atb in mainEntry:
                #     print('{}: {}'.format(atb, mainEntry[atb]), end='\t')
                # print()

            print(' ' * space, end='')
            print(mainEntry['Name'])
            start_cluster = getStartCluster(mainEntry['Start Cluster Low'], mainEntry['Start Cluster High'])
            clusters = getClusterFromFAT(start_cluster, self.FATTable)
            subFileSectors = getSectors(self.clusterStartRDET, self.sectorStartRDET,
                                                  self.sectorPerCluster, clusters)

            mainEntry['Name'] = mainEntry['Name'].strip()
            mainEntry['Sectors'] = subFileSectors
            mainEntry['Clusters'] = clusters
            mainEntry['rootIndex'] = rootData['index']
            mainEntry['Disk'] = self.diskName
            mainEntry['Path'] = rootData['Path'] + '\\' + mainEntry['Name']

            global fileOrder
            mainEntry['index'] = fileOrder
            fileOrder += 1

            self.fileSignal.emit(mainEntry.copy())

            if mainEntry['Status'] == 16:
                self.DFS_SDET(mainEntry, subFileSectors[0], subFileSectors[-1], space)

    def run(self):
        start_sector, end_sector = int(self.rootFolder['Sectors'][0]), int(self.rootFolder['Sectors'][-1])

        self.DFS_SDET(self.rootFolder, start_sector, end_sector)
        self.finish.emit(True)


class Fat32(QThread):
    fileSignal = pyqtSignal(object)
    rootSignal = pyqtSignal(object)
    diskSignal = pyqtSignal(object)
    threads = []

    def __init__(self, diskName):
        super(Fat32, self).__init__()
        self.diskPath = r'\\.\{}:'.format(diskName)
        self.diskName = diskName
        self.volumeName = ''
        self.bootSector = {}  # { name: offset}
        self.size = 0
        self.sectorStartRDET = None
        self.sectorPerCluster = None
        self.bytesPerSector = None
        self.FATTable = b''
        self.rootFolder = []
        self.treeFiles = [[], []]
        self.maxSector = 0
        self.clusterStartRDET = None
        self.fileOrder = 1
        self.index = 0
        # self.read_boot_sector(self.diskPath)

    def finish(self, res):
        if self.index < len(self.rootFolder):
            # fp = self.getRDETPointer()
            t = DFSThread(self.diskPath, self.FATTable, self.sectorStartRDET, self.clusterStartRDET, self.rootFolder[self.index], self.bytesPerSector, self.sectorPerCluster)
            self.index += 1
            t.fileSignal.connect(self.updateFile)
            self.threads.append(t)
            t.start()

    def updateFile(self, file):
        self.fileSignal.emit(file)

    def run(self):
        self.read_boot_sector()
        self.rootSignal.emit((self.diskName, 'FAT32'))
        self.diskSignal.emit(self.bootSector)
        self.show_info()
        self.read_rdet()

        n = len(self.rootFolder)
        # while self.index < n and self.index < NUMBER_THREAD:
        folder = self.rootFolder[self.index]
        print(folder['Name'])
        t = DFSThread(self.diskPath, self.FATTable, self.sectorStartRDET, self.clusterStartRDET, folder, self.bytesPerSector, self.sectorPerCluster)
        t.finish.connect(self.finish)
        t.fileSignal.connect(self.updateFile)
        self.threads.append(t)
        self.index += 1
        t.start()

    def read_boot_sector(self):
        with open(self.diskPath, 'rb') as fp:
            boot_sector = fp.read(512)
        fp.close()
        layout = list(bootSectorStructure.items())
        for i, (start_offset, info) in enumerate(layout):
            if start_offset == 0x52:
                end_offset = 0x5A
            elif start_offset == 0x1FE:
                end_offset = 513
            else:
                end_offset = layout[i + 1][0]

            self.bootSector[info[0]] = unpack(info[1], boot_sector[start_offset:end_offset])[0]

        total_sectors = self.bootSector['TotalLogicalSectors']
        self.bytesPerSector = self.bootSector['BytesPerSector']
        self.size = float(total_sectors * self.bytesPerSector / (2.0 ** 30))
        self.sectorPerCluster = self.bootSector['SectorsPerCluster']
        self.clusterStartRDET = self.bootSector['RootCluster']
        self.volumeName = self.bootSector['VolumeLabel'].decode('utf-8')
        self.bootSector['Size'] = '{} gb'.format(self.size)
        self.bootSector['Disk'] = self.diskName

    def show_info(self):
        for name_offset, data in list(self.bootSector.items()):
            print('{}: {}'.format(name_offset, data))
        print('Total size: {} gb'.format(self.size))

    def read_rdet(self):
        SF = self.bootSector['SectorsPerFAT']
        sectorStart = self.bootSector['SectorsOfBootSector']
        bytesPerSector = self.bootSector['BytesPerSector']
        self.sectorStartRDET = SF * 2 + sectorStart

        with open(self.diskPath, 'rb') as fp:
            fp.seekable()
            fp.seek(sectorStart*bytesPerSector)
            tmp = []

            for i in range(SF):
                tmp.append(fp.read(bytesPerSector))
            self.FATTable = b''.join(tmp)

            fp.seekable()
            fp.seek(sectorStart*bytesPerSector+2*SF*bytesPerSector)

            clusters = getClusterFromFAT(self.clusterStartRDET, self.FATTable)
            sectors = getSectors(self.clusterStartRDET, self.sectorStartRDET, self.sectorPerCluster, clusters)
            # print(sectors)
            n = (sectors[-1] - sectors[0]) * int((self.bytesPerSector / 32)) - 2
            for i in range(n):
                entry = fp.read(32)
                status_1 = unpack('B', entry[0:1])[0]
                if status_1 == 229:
                    continue
                status = unpack('B', entry[0x0B:0x0C])[0]
                if status == 0:
                    continue

                if status != 15:
                    if status_1 == 0:
                        break
                    if not isValidFile(status):
                        continue
                    mainEntry = read_main_entry(entry)
                    mainEntry['Name'] = mainEntry['Name'].decode('utf-8').strip(' ')
                    extendedName = mainEntry['Extension name'].decode('utf-8').strip(' ').strip('\x00')
                    if isFile(mainEntry['Status']):
                        mainEntry['Name'] += '.' + extendedName
                    else:
                        mainEntry['Name'] += ' ' + extendedName

                else:
                    extendedName = ''
                    extendedName = read_subEntry(entry) + extendedName.strip('\x00')
                    entry = fp.read(32)
                    isSubEntry = unpack('B', entry[0x0B:0x0C])[0] == 15
                    while isSubEntry:
                        extendedName = read_subEntry(entry) + extendedName.strip('\x00')
                        entry = fp.read(32)
                        isSubEntry = unpack('B', entry[0x0B:0x0C])[0] == 15

                    status_1 = unpack('B', entry[0:1])[0]
                    if status_1 == 0 or status_1 == 229:
                        continue
                    mainEntry = read_main_entry(entry)

                    if not isValidFile(mainEntry['Status']):
                        continue
                    mainEntry['Name'] = extendedName
                mainEntry.pop('Extension name')

                checkName = mainEntry['Name'].split()[0]
                if checkName == '.' or checkName == '..':
                    continue

                for atb in mainEntry:
                    print('{}: {}'.format(atb, mainEntry[atb]), end='\t')
                print()

                global fileOrder
                mainEntry['index'] = fileOrder
                fileOrder += 1

                mainEntry['rootIndex'] = 0
                start_cluster = getStartCluster(mainEntry['Start Cluster Low'], mainEntry['Start Cluster High'])
                subFileclusters = getClusterFromFAT(start_cluster, self.FATTable)
                subFileSectors = getSectors(self.clusterStartRDET, self.sectorStartRDET,
                                                      self.sectorPerCluster, subFileclusters)
                mainEntry['Name'] = mainEntry['Name'].strip()
                mainEntry['Sectors'] = subFileSectors
                mainEntry['Clusters'] = subFileclusters
                mainEntry['Disk'] = self.diskName
                mainEntry['Path'] = self.diskName + ':\\' + mainEntry['Name']
                self.fileSignal.emit(mainEntry.copy())
                if mainEntry['Status'] == 16:
                    self.rootFolder.append(mainEntry)
                elif mainEntry['Status'] == 32:
                    self.treeFiles[0].append(mainEntry)

        fp.close()








