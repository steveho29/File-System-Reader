import sys

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import *
from FAT32Thread import Fat32, TXTReaderThread
from NTFSThread import NTFSThread
from GetDisks import getDiskType, getDisks
from threading import Thread
import os, subprocess


class TreeFileWidget(QWidget):
    def __init__(self):
        super(TreeFileWidget, self).__init__()
        self.setWindowTitle('File Management ^^')
        self.fields = ['Name', 'Status', 'Sectors', 'Clusters', 'Size', 'Created Time', 'Created Date',
                       'Latest Access', 'Latest Modified Time', 'Latest Modified Day', 'Path']
        self.Fat32TxtThreads = []
        self.openAppThreads = []
        self.readDiskThreads = {}
        self.disks = getDisks()
        self.dictNode = {}  # {'diskName': {}}
        self.setMinimumHeight(720)
        self.setMinimumWidth(1080)
        self.listWidget = QListWidget()
        self.setWindowIcon(QIcon('icon/disk.icon'))
        operatorLayout = QHBoxLayout()
        smallLayout = QHBoxLayout()
        self.comboBox = QComboBox()
        self.comboBox.setMaximumWidth(200)
        startButton = QPushButton('Start Read Disk')
        startButton.setMaximumWidth(150)
        startButton.clicked.connect(self.onClickStartButton)
        refreshButton = QPushButton('Refresh')
        refreshButton.setMaximumWidth(80)
        refreshButton.clicked.connect(self.onClickRefreshButton)
        for i, d in enumerate(self.disks):
            self.comboBox.addItem(d)
        smallLayout.addWidget(self.comboBox)
        smallLayout.addWidget(startButton)
        smallLayout.addWidget(refreshButton)
        operatorLayout.addLayout(smallLayout)

        # addBtn = QPushButton("Add Node")
        # updateBtn = QPushButton("Modify Node")
        # delBtn = QPushButton("Delete Node")
        # operatorLayout.addWidget(addBtn)
        # operatorLayout.addWidget(updateBtn)
        # operatorLayout.addWidget(delBtn)

        # button signal slot connection
        # addBtn.clicked.connect(self.addTreeNodeBtn)
        # updateBtn.clicked.connect(self.updateTreeNodeBtn)
        # delBtn.clicked.connect(self.delTreeNodeBtn)

        self.tree = QTreeWidget(self)
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

        # self.startReadDiskThread()

    def onClickRefreshButton(self):
        disks = getDisks()
        for disk in disks:
            if disk not in self.dictNode and disk not in self.disks:
                self.comboBox.addItem(disk)
                self.disks.append(disk)

    def onClickStartButton(self):
        i, disk = self.comboBox.currentIndex(), self.comboBox.currentText()
        if not disk:
            return
        self.comboBox.removeItem(i)
        self.startReadDiskThread(disk)

    def StartReadDisk(self, obj):
        pass

    def startReadDiskThread(self, diskName):
        typeDisk = getDiskType(diskName)
        if typeDisk == 'FAT32':
            thread = Fat32(diskName)
        elif typeDisk == 'NTFS':
            thread = NTFSThread(diskName)
        else:
            return

        thread.fileSignal.connect(self.addNode)
        thread.diskSignal.connect(self.showDiskInfo)
        thread.rootSignal.connect(self.addRoot)

        self.readDiskThreads[diskName] = thread
        self.dictNode[diskName] = {}
        thread.start()

    def showTextFile(self, text):
        self.textBox.setPlainText(text)

    def onTreeDoubleCLicked(self):
        item = self.tree.currentItem()
        if item.text(0).strip('\x00')[-4:].lower() != '.txt':
            path = item.text(len(self.fields)-1)
            try:
                os.startfile(path)
            except:
                pass
            return
        sectors = item.text(2).strip('[]').split(', ')

        # If NTFS -> read file
        if not sectors[0]:
            self.showTextFile(open(item.text(len(self.fields) - 1), 'rb').read().decode('utf-8'))
            return
        # If FAT32 -> Go to sectors and read
        sectors = [int(x) for x in sectors]
        diskName = item.text(10)[0]
        t = TXTReaderThread(diskName, sectors, self.readDiskThreads[diskName].bytesPerSector)
        t.finish.connect(self.showTextFile)
        self.Fat32TxtThreads.append(t)
        t.start()

    def showDiskInfo(self, bootSector):
        self.listWidget.addItem('DRIVE {} Boot Sector Info'.format(bootSector['Disk']))
        for name in bootSector:
            self.listWidget.addItem('\t{}:{}'.format(name, bootSector[name]))
        self.listWidget.addItem('\n\n')

    def onTreeClicked(self, qmodelindex):
        item = self.tree.currentItem()
        print("key={} ,value={}".format(item.text(0), item.text(1)))

    def addTreeNodeBtn(self):
        print('--- addTreeNodeBtn ---')
        item = self.tree.currentItem()

        node = QTreeWidgetItem(item)
        node.setText(0, 'newNode')
        node.setText(1, '10')

    def addRoot(self, info):
        root = QTreeWidgetItem(self.tree)
        root.setIcon(0, QIcon('icon/disk.icon'))
        root.setText(0, '{} ({})'.format(info[0], info[1]))
        self.tree.addTopLevelItem(root)
        self.dictNode[info[0]]['root'] = root

    def addNode(self, info):
        rootIndex = info['rootIndex']
        diskFile = self.dictNode[info['Disk']]
        if rootIndex not in diskFile:
            node = QTreeWidgetItem(diskFile['root'])
        else:
            node = QTreeWidgetItem(diskFile[rootIndex])
        if info['Type'] == 'Folder':
            node.setIcon(0, QIcon('icon/folder.icon'))
        else:
            node.setIcon(0, QIcon('icon/file.ico'))

        self.dictNode[info['Disk']][info['index']] = node

        # info['Sectors'] = '{}->{}'.format(info['Sectors'][0], info['Sectors'][1])
        # info['Clusters'] = '{}->{}'.format(str(info['Clusters'][0]), str(info['Clusters'][-1]))
        # info['Sectors'] = '{}->{}'.format(str(info['Sectors'][0]), str(info['Sectors'][-1]))

        for i, field in enumerate(self.fields):
            node.setText(i, str(info[field]))
        # if 'text' in info.keys():
        #     self.NTFSText[info['Path']] = info['text']

    def updateTreeNodeBtn(self):
        print('--- updateTreeNodeBtn ---')
        item = self.tree.currentItem()
        item.setText(0, 'updateNode')
        item.setText(1, '20')

    def delTreeNodeBtn(self):
        print('--- delTreeNodeBtn ---')
        item = self.tree.currentItem()
        root = self.tree.invisibleRootItem()
        for item in self.tree.selectedItems():
            (item.parent() or root).removeChild(item)
