from struct import unpack
from FAT32Functions import *
from FAT32STRUCTURE import *



class Fat32:

    def __init__(self, disk_path):
        self.diskPath = disk_path
        self.bootSector = {}  # { name: offset}
        self.size = 0
        self.sectorStartRDET = None
        self.sectorPerCluster = None
        self.bytesPerSector = None
        self.FATTable = b''
        self.rootFolder = []
        self.treeFiles = [[], []]
        self.diskName = ''
        self.maxSector = 0
        self.clusterStartRDET = None

        self.read_boot_sector(self.diskPath)

    def get_boot_sector(self, diskPath):
        with open(diskPath, 'rb') as fp:
            boot_sector = fp.read(512)
        fp.close()
        return boot_sector

    def read_boot_sector(self, diskPath):
        boot_sector = self.get_boot_sector(diskPath)
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

    def show_info(self):
        for name_offset, data in list(self.bootSector.items()):
            print('{}: {}'.format(name_offset, data))
        print('Total size: {} gb'.format(self.size))

    def read_subEntry(self, entry):
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

    def read_main_entry(self, entry):
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

    def readSDET(self, startSector, endSector, fp):
        for i in range(startSector - self.sectorStartRDET):
            fp.read(self.bytesPerSector)

        # print(self.bytesPerSector)
        # print(startSector, endSector)
        n = (endSector - startSector) * int((self.bytesPerSector / 32)) - 2
        # print(n)
        files = []
        folders = []
        # x = fp.tell()
        fp.read(64)  # skip 2 first entry in SDET

        for i in range(n):
            entry = fp.read(32)
            status = unpack('B', entry[0:1])[0]
            if status == 229:
                continue
            elif status == 0:
                break

            status = unpack('B', entry[0x0B:0x0C])[0]

            if status != 15:
                if not isValidFile(status) or isHiddened(status):
                    continue
                mainEntry = self.read_main_entry(entry)

                # print(mainEntry)
                name = mainEntry['Name']
                extendedName = mainEntry['Extension name']
                if isFile(mainEntry['Status']):
                    mainEntry['Name'] = name.decode('utf-8').strip(' ') + '.' + extendedName.decode('utf-8').strip(' ')
                else:
                    mainEntry['Name'] = (name + extendedName).decode('utf-8').strip(' ')
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
                if not isValidFile(mainEntry['Status']) or isHiddened(mainEntry['Status']):
                    continue
                mainEntry['Name'] = extendedName
                mainEntry.pop('Extension name')

                # for atb in mainEntry:
                #     print('{}: {}'.format(atb, mainEntry[atb]), end='\t')
                # print()

            if mainEntry['Status'] == 16:
                folders.append(mainEntry)
            elif mainEntry['Status'] == 32:
                files.append(mainEntry)

        fp.close()
        return files, folders

    def DFS_SDET(self, rootSector, startSector, endSector, fp, space=0):
        rootFp = fp.tell()
        p = (startSector - rootSector)
        if endSector <= self.maxSector:
            # print(startSector*self.bytesPerSector)
            fp.seek(startSector*self.bytesPerSector)
        else:
            fp.read(self.bytesPerSector*p)
            self.maxSector = endSector

        subFp = fp.tell()
        fp.read(64)
        n = (endSector - startSector) * int((self.bytesPerSector / 32)) - 2
        space += 10
        x1 = fp.tell()
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
                mainEntry = self.read_main_entry(entry)

                # print(mainEntry)
                name = mainEntry['Name']
                extendedName = mainEntry['Extension name']
                if isFile(mainEntry['Status']):
                    mainEntry['Name'] = name.decode('utf-8').strip(' ') + '.' + extendedName.decode('utf-8').strip(' ')
                else:
                    mainEntry['Name'] = (name + extendedName).decode('utf-8').strip(' ')
                    # mainEntry['Name'] = name.decode('utf-8').strip(' ') + ' ' + extendedName.decode('utf-8').strip(' ')
            else:
                extendedName = ''
                extendedName = self.read_subEntry(entry) + extendedName
                entry = fp.read(32)

                isSubEntry = unpack('B', entry[0x0B:0x0C])[0] == 15
                while isSubEntry:
                    extendedName = self.read_subEntry(entry) + extendedName
                    entry = fp.read(32)
                    isSubEntry = unpack('B', entry[0x0B:0x0C])[0] == 15
                # c += 1

                mainEntry = self.read_main_entry(entry)
                if not isValidFile(mainEntry['Status']):
                    continue
                mainEntry['Name'] = extendedName
                mainEntry.pop('Extension name')

                # for atb in mainEntry:
                #     print('{}: {}'.format(atb, mainEntry[atb]), end='\t')
                # print()

            print(' ' * space, end='')
            print(mainEntry['Name'])
            if mainEntry['Status'] == 16:
                start_cluster = getStartCluster(mainEntry['Start Cluster Low'], mainEntry['Start Cluster High'])
                clusters = getClusterFromFAT(start_cluster, self.FATTable)
                start_sector, end_sector = getSectors(self.clusterStartRDET, self.sectorStartRDET, self.sectorPerCluster, clusters)

                x = fp.tell()
                # print(x1)
                # fp.seekable()
                # fp.seek(x1)
                fp.seekable()
                fp.seek(subFp)
                self.DFS_SDET(startSector, start_sector, end_sector, fp, space)
                fp.seekable()
                fp.seek(subFp)
                fp.read(64)
                fp.seekable()
                fp.seek(x)

        fp.seekable()
        fp.seek(subFp)
        fp.seekable()
        fp.seek(rootFp)

    def read_rdet(self):
        SF = self.bootSector['SectorsPerFAT']
        sectorStart = self.bootSector['SectorsOfBootSector']
        bytesPerSector = self.bootSector['BytesPerSector']
        self.sectorStartRDET = SF * 2 + sectorStart

        with open(self.diskPath, 'rb') as fp:
            for i in range(sectorStart):
                fp.read(bytesPerSector)

            tmp = []
            for i in range(SF):
                tmp.append(fp.read(bytesPerSector))
            self.FATTable = b''.join(tmp)

            for i in range(SF):
                fp.read(bytesPerSector)

            clusters = getClusterFromFAT(self.clusterStartRDET, self.FATTable)
            # print(clusters)
            startSector, endSector = getSectors(self.clusterStartRDET, self.sectorStartRDET, self.sectorPerCluster, clusters)
            # print(startSector, endSector)
            n = (endSector - startSector) * int((self.bytesPerSector / 32)) - 2

            for i in range(n):
                entry = fp.read(32)
                status_1 = unpack('B', entry[0:1])[0]
                if status_1 == 229:
                    continue
                status = unpack('B', entry[0x0B:0x0C])[0]
                # print(status)
                if status == 0:
                    continue

                if status != 15:
                    if status_1 == 0:
                        break
                    if not isValidFile(status):
                        continue
                    mainEntry = self.read_main_entry(entry)
                    mainEntry['Name'] = mainEntry['Name'].decode('utf-8').strip(' ')
                    extendedName = mainEntry['Extension name'].decode('utf-8').strip(' ')
                    if isFile(mainEntry['Status']):
                        mainEntry['Name'] += '.' + extendedName
                    else:
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

                    status_1 = unpack('B', entry[0:1])[0]
                    if status_1 == 0 or status_1 == 229:
                        continue
                    mainEntry = self.read_main_entry(entry)

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

                if mainEntry['Status'] == 16:
                    self.rootFolder.append(mainEntry)
                elif mainEntry['Status'] == 32:
                    self.treeFiles[0].append(mainEntry)

        fp.close()

    def getFolderTree(self):
        # print(self.rootFolder)
        fp = self.getRDETPointer()
        for file in self.treeFiles[0]:
            print(file['Name'])

        self.rootFolder.reverse()
        for folder in self.rootFolder:
            # print(folder)
            # continue
            print(folder['Name'])
            start_cluster = getStartCluster(folder['Start Cluster Low'], folder['Start Cluster High'])
            clusters = getClusterFromFAT(start_cluster, self.FATTable)
            start_sector, end_sector = getSectors(self.clusterStartRDET, self.sectorStartRDET, self.sectorPerCluster, clusters)

            self.DFS_SDET(self.sectorStartRDET, start_sector, end_sector, fp)
            # self.readFolder_2(data)
            # self.treeFiles[1].append(self.readFolder(data))
        fp.close()

        #
        # for folder in self.treeFiles[1]:
        #     self.printFolderTree(folder)

    def printFolderTree(self, folders, space=0):
        # tree = {root: (folderInfo, files, [])}

        for root in folders:
            data = folders[root]
            print(' ' * space, end='')
            print(data[0]['Name'])
            space += 10
            for file in data[1]:
                print(' ' * space, end='')
                print(file['Name'])
            for subFolder in data[2]:
                self.printFolderTree(subFolder, space)

    def getRDETPointer(self):
        # SF = self.bootSector['SectorsPerFAT']
        # sectorStart = self.bootSector['SectorsOfBootSector']
        # bytesPerSector = self.bootSector['BytesPerSector']
        fp = open(self.diskPath, 'rb')
        fp.seekable()
        fp.seek(self.sectorStartRDET*self.bytesPerSector)
        # for i in range(sectorStart):
        #     fp.read(bytesPerSector)
        # for i in range(SF * 2):
        #     fp.read(bytesPerSector)
        return fp

    def readFolder(self, folder):
        fp = self.getRDETPointer()
        # print(folder['Name'])
        # print(folder['Start Cluster Low'])
        start_cluster = getStartCluster(folder['Start Cluster Low'], folder['Start Cluster High'])
        # print(start_cluster)
        clusters = getClusterFromFAT(start_cluster, self.FATTable)
        # print(clusters)
        # print(self.sectorStartRDET)
        start_sector, end_sector = getSectors(2, self.sectorStartRDET, self.sectorPerCluster, clusters)
        files, folders = self.readSDET(start_sector, end_sector, fp)

        root = folder['Name'].strip('\x00')
        # tree = {root: (folder, files, [{str(f['Name'].strip('\x00')): (f, [], []) for f in folders}])}
        tree = {root: (folder, files, [])}
        # print(tree[root])
        if folders:
            for i, f in enumerate(folders):
                tree[root][2].append(self.readFolder(f))
        return tree

    def readFolder_2(self, folder, space=0):
        fp = self.getRDETPointer()
        start_cluster = getStartCluster(folder['Start Cluster Low'], folder['Start Cluster High'])
        clusters = getClusterFromFAT(start_cluster, self.FATTable)
        start_sector, end_sector = getSectors(2, self.sectorStartRDET, self.sectorPerCluster, clusters)
        files, folders = self.readSDET(start_sector, end_sector, fp)
        print(' ' * space, end='')
        space += 5
        print(folder['Name'])
        for file in files:
            print(' ' * space, end='')
            print(file['Name'])

        for i, f in enumerate(folders):
            self.readFolder_2(f, space)


drive = r"\\.\E:"

b = Fat32(drive)
b.show_info()
b.read_rdet()
b.getFolderTree()


