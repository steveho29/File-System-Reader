# from PyQt5.QtCore import QThread, pyqtSignal
# from FAT32 import *
#
#
# class FAT32Thread(QThread):
#     fileSignal = pyqtSignal(object)
#     rootSignal = pyqtSignal(object)
#
#     def __init__(self, disk):
#         super(FAT32Thread, self).__init__()
#         self.fat32 = Fat32(disk)
#
#     def run(self):
#         self.fat32.read_boot_sector()
#         self.rootSignal.emit(self.fat32.diskName)
#         self.fat32.show_info()
#         self.fat32.read_rdet()
#         for f in self.fat32.rootFolder:
#             self.fileSignal.emit(f.copy())
#         for f in self.fat32.treeFiles[0]:
#             self.fileSignal.emit(f.copy())
#
#         fp = self.fat32.getRDETPointer()
#         self.fat32.rootFolder.reverse()
#         for folder in self.fat32.rootFolder:
#             print(folder['Name'])
#             start_sector, end_sector = folder['Sectors'][0], folder['Sectors'][-1]
#             # self.fat32.DFS_SDET(self.fat32.sectorStartRDET, folder, start_sector, end_sector, fp)
#             for f in self.fat32.DFS_SDET(self.fat32.sectorStartRDET, folder, start_sector, end_sector, fp):
#                 self.fileSignal.emit(f.copy())
#         fp.close()
#
#
