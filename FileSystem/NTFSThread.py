from NTFS import NTFS
from PyQt5.QtCore import QThread, pyqtSignal
from NTFSFunctions import parse_record


class NTFSThread(QThread):
    fileSignal = pyqtSignal(object)
    diskSignal = pyqtSignal(object)
    rootSignal = pyqtSignal(object)

    def __init__(self, diskName):
        super(NTFSThread, self).__init__()
        self.diskName = diskName
        self.diskPath = r'\\.\{}:'.format(diskName)
        self.NTFS = NTFS(diskName)
        self.filePaths = {5: '{}:'.format(diskName)}

    def run(self) -> None:
        self.NTFS.read_boot_sector(self.NTFS.diskPath)

        self.diskSignal.emit(self.NTFS.bootSector)
        self.rootSignal.emit((self.diskName, 'NTFS'))
        with open(self.diskPath, 'rb') as f:
            f.seek(self.NTFS.MFT_start + 15 * 1024)
            mft_raw = f.read(1024)
            while mft_raw != b'':
                data = parse_record(mft_raw)
                if data and data['Name'][0] != '$' and data['ParentRecord'] in self.filePaths:
                    data['Disk'] = self.diskName
                    data['rootIndex'] = data['ParentRecord']
                    data['index'] = data['RecordNum']
                    data['Path'] = self.filePaths[data['ParentRecord']] + '\\' + data['Name']
                    self.filePaths[data['RecordNum']] = data['Path']
                    self.fileSignal.emit(data)
                mft_raw = f.read(1024)

        f.close()
