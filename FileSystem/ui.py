import sys
from PyQt5.QtWidgets import *
from FAT32 import Fat32, TXTReaderThread
from GetDisks import getDiskType, getDisks


class TreeFileWidget(QWidget):
    def __init__(self):
        super(TreeFileWidget, self).__init__()
        self.setWindowTitle('File Management ^^')
        self.fields = ['Name', 'Status', 'Sectors', 'Clusters', 'Size', 'Created Time', 'Created Date',
                       'Latest Access', 'Latest Modified Time', 'Latest Modified Day', 'Path']
        self.readDiskThreads = {}
        self.disks = getDisks()
        self.listFile = {}  # {'diskName': {}}
        self.setMinimumHeight(720)
        self.setMinimumWidth(1080)
        self.listWidget = QListWidget()
        operatorLayout = QHBoxLayout()
        addBtn = QPushButton("Add Node")
        updateBtn = QPushButton("Modify Node")
        delBtn = QPushButton("Delete Node")

        # operatorLayout.addWidget(addBtn)
        # operatorLayout.addWidget(updateBtn)
        # operatorLayout.addWidget(delBtn)
        # button signal slot connection
        addBtn.clicked.connect(self.addTreeNodeBtn)
        updateBtn.clicked.connect(self.updateTreeNodeBtn)
        delBtn.clicked.connect(self.delTreeNodeBtn)

        self.tree = QTreeWidget(self)
        # self.tree.setColumnCount(2)

        self.tree.setHeaderLabels(l for l in self.fields)

        self.tree.clicked.connect(self.onTreeClicked)
        self.tree.doubleClicked.connect(self.onTreeDoubleCLicked)

        self.textBox = QPlainTextEdit('Double click file txt -> Show here')
        self.bottomLayout = QHBoxLayout()
        self.bottomLayout.addWidget(self.listWidget)
        self.bottomLayout.addWidget(self.textBox)

        mainLayout = QVBoxLayout(self)
        mainLayout.addLayout(operatorLayout)
        mainLayout.addWidget(self.tree)
        mainLayout.addLayout(self.bottomLayout)

        self.setLayout(mainLayout)

        for disk in self.disks:
            if getDiskType(disk) == 'FAT32':
                fat32Thread = Fat32(disk)
                fat32Thread.rootSignal.connect(self.addRoot)
                fat32Thread.fileSignal.connect(self.addNode)
                fat32Thread.diskSignal.connect(self.showDiskInfo)
                self.readDiskThreads[disk] = fat32Thread
                self.listFile[disk] = {}
                fat32Thread.start()

        self.txtThreads = []

    def showTextFile(self, text):
        self.textBox.setPlainText(text)

    def onTreeDoubleCLicked(self):
        item = self.tree.currentItem()
        if item.text(0).strip('\x00')[-4:].lower() != '.txt':
            return
        # sector_start, sector_end = item.text(2).split('->')
        sectors = item.text(2).strip('[]').split(', ')
        sectors = [int(x) for x in sectors]
        print(sectors)
        diskName = item.text(10)[0]
        t = TXTReaderThread(diskName, sectors, self.readDiskThreads[diskName].bytesPerSector)
        t.finish.connect(self.showTextFile)
        self.txtThreads.append(t)
        t.start()

    def showDiskInfo(self, data):
        bootSector, diskName = data[0], data[1]
        self.listWidget.addItem('DRIVE {} Boot Sector Info'.format(diskName))
        for name in bootSector:
            self.listWidget.addItem('\t{}:{}'.format(name, bootSector[name]))
        self.listWidget.addItem('\n\n')

    # Node click event

    def onTreeClicked(self, qmodelindex):
        item = self.tree.currentItem()
        print("key={} ,value={}".format(item.text(0), item.text(1)))

    # Add node
    def addTreeNodeBtn(self):
        print('--- addTreeNodeBtn ---')
        item = self.tree.currentItem()

        node = QTreeWidgetItem(item)
        node.setText(0, 'newNode')
        node.setText(1, '10')

    def addRoot(self, info):
        root = QTreeWidgetItem(self.tree)
        root.setText(0, '{} ({})'.format(info[0], info[1]))
        self.tree.addTopLevelItem(root)
        self.listFile[info[0]]['root'] = root

    def addNode(self, info):
        rootIndex = info['rootIndex']
        diskFile = self.listFile[info['Disk']]
        if rootIndex not in diskFile:
            node = QTreeWidgetItem(diskFile['root'])
        else:
            node = QTreeWidgetItem(diskFile[rootIndex])
        self.listFile[info['Disk']][info['index']] = node

        # info['Sectors'] = '{}->{}'.format(info['Sectors'][0], info['Sectors'][1])
        # info['Clusters'] = '{}->{}'.format(str(info['Clusters'][0]), str(info['Clusters'][-1]))
        # info['Sectors'] = '{}->{}'.format(str(info['Sectors'][0]), str(info['Sectors'][-1]))

        for i, field in enumerate(self.fields):
            node.setText(i, str(info[field]))

    # Node update
    def updateTreeNodeBtn(self):
        print('--- updateTreeNodeBtn ---')
        item = self.tree.currentItem()
        item.setText(0, 'updateNode')
        item.setText(1, '20')

    # Delete node
    def delTreeNodeBtn(self):
        print('--- delTreeNodeBtn ---')
        item = self.tree.currentItem()
        root = self.tree.invisibleRootItem()
        for item in self.tree.selectedItems():
            (item.parent() or root).removeChild(item)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    tree = TreeFileWidget()
    tree.show()
    sys.exit(app.exec_())
