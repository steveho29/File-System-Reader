from struct import unpack

from NTFS_STRUCTURE import *

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
        0x30: ('MFTClusterNumber','<Q'),
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

        self.MFT_start=0

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

        self.MFT_start =int(self.offset_name['BytesPerSector'] * self.offset_name['SectorsPerCluster'] * self.offset_name['MFTClusterNumber'])


    def show_info(self,list_name):
        for name_offset, data in list(list_name.items()):
            print('{}: {}'.format(name_offset, data))
        #print('Total size: {} gb'.format(self.size))
        #print('MFT START: {}'.format (self.MFT_start))


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

    def read_MFT_header(self,mft_raw):
        data={}
        mft_header=list(MFT_Header_Structure.items())
        for i, (start_offset,info) in enumerate(mft_header):
            if i == len(mft_header) - 1:
                end_offset = 0x32
            else:
                end_offset = mft_header[i + 1][0]
            #print(end_offset)
            data[info[0]] = unpack(info[1], mft_raw[start_offset:end_offset])[0]
        return data

    def read_attribute_header(self,mft_raw):
        data = {'Attr_type': unpack("<L", mft_raw[:4])[0]}
        #print(d['Attr_type'])
        if data['Attr_type'] == 0xFFFFFFFF:
            return data
        data['Attr_len'] =unpack("<L", mft_raw[4:8])[0]
        #print(d['Attr_len'])
        data['Resident'] = unpack("B", mft_raw[8:9])[0]
        #print("Resident:",data['Resident'])
        data['Name_len'] =unpack("B", mft_raw[9:10])[0]
        data['Name_off'] = unpack("<H",mft_raw[10:12])[0]
        data['Flags'] =unpack("<H", mft_raw[12:14])[0]
        data['ID'] = unpack("<H", mft_raw[14:16])[0]
        if data['Resident'] == 0:
            data['content_size'] = unpack("<L", mft_raw[16:20])[0]
            data['content_off'] =unpack("<H", mft_raw[20:22])[0]
            data['idxflag'] = unpack("B", mft_raw[22:23])[0]
            _ = unpack("B", mft_raw[23:24])[0]
        else:
            data['start_vcn'] = unpack("<Q", mft_raw[16:24])[0]
            data['end_vcn'] = unpack("<Q", mft_raw[24:32])[0]
            data['runlist_off'] = unpack("<H", mft_raw[32:34])[0]
            data['compress_size'] =unpack("<H", mft_raw[34:36])[0]
            data['unused']= unpack("<I", mft_raw[36:40])[0]
            data['allocated_size'] = unpack("<Lxxxx", mft_raw[40:48])[0]
            data['real_size'] = unpack("<Lxxxx", mft_raw[48:56])[0]
            data['initialized_size'] = unpack("<Lxxxx", mft_raw[56:64])[0]

        return data

    def read_Standard_Info_attr(self,mft_raw):
        data={}
        standard_info=list(Standard_Information_Structure.items())
        for i, (start_offset, info) in enumerate(standard_info):
            if i == len(standard_info) - 1:
                end_offset = 0x20
            else:
                end_offset = standard_info[i + 1][0]
            data[info[0]] = unpack(info[1], mft_raw[start_offset:end_offset])[0]
        return data

    def read_File_Name_attr(self,mft_raw):
        data = {}
        file_name = list(FileName_Structure.items())
        for i, (start_offset, info) in enumerate(file_name):
            if start_offset==0x41:
                end_offset = 0x42
            else:
                end_offset = file_name[i + 1][0]
            data[info[0]] = unpack(info[1], mft_raw[start_offset:end_offset])[0]

        name = mft_raw[0x42:0x42 + data['File_name_len'] * 2]

        
        try:
            data['File_name_Unicode'] = name.decode('utf-16').encode('utf-8')
        except:
            data['File_name_Unicode'] = 'UnableToDecodeFilename'
        
        print(data['File_name_Unicode'])

        return data

    def read_Attribute_list(self,mft_raw):
        data = {
            'type':unpack(" <I", mft_raw[:4])[0],
            'len':unpack("<H", mft_raw[4:6])[0],
            'nlen': unpack("B", mft_raw[6:7])[0],
            'f1': unpack("B", mft_raw[7:8])[0],
            'start_vcn': unpack("<d", mft_raw[8:16])[0],
            'file_ref': unpack("<Lxx", mft_raw[16:22])[0],
            'seq':unpack("<H", mft_raw[22:24])[0],
            'id': unpack("<H", mft_raw[24:26])[0],
        }

        name = mft_raw[26:26 + data['nlen'] * 2]
        data['name'] = name.decode('utf-16').encode('utf-8')
        print(data['name'])
        return data

    def check_flag_mft(self,flag):
        if flag & 0x0001:
            act='active'
        else:
            act='inactive'

        if int(flag) & 0x0002:
            type = 'Folder'
        else:
            type = 'File'
        return act,type

    def parse_record(self,mft_raw):
        mft_header=self.read_MFT_header(mft_raw)
        status=mft_header['Magic Number']
        print(status)
        #if status == 0x454C4946:
        if status == b'FILE':
            print("success")
        else:
            return
        self.show_info(mft_header)
        act,type=self.check_flag_mft(mft_header['Flag'])
        print(act," ", type)
        read_pointer=mft_header['First_Attribute_ID']

        while read_pointer<1024:
            #read attribute header
            attr_record = self.read_attribute_header(mft_raw[read_pointer:])
            print("=======================")
            print("Attr_type: ",attr_record['Attr_type'])

            if attr_record['Attr_type'] == 0xFFFFFFFF :
                break

            #parse attribute type
            if attr_record['Attr_type']==0x10:  #STANDARD INFO
                standard_info=self.read_Standard_Info_attr(mft_raw[read_pointer + attr_record['content_off']:])

            elif attr_record['Attr_type']==0x30:  #FILE NAME
                file_name=self.read_File_Name_attr(mft_raw[read_pointer + attr_record['content_off']:])

            elif attr_record['Attr_type']==0x20: #ATTRIBUTE LIST
                print("ATTRIBUTE LIST")
            #elif attr_record['Attr_type']==0x80: #DATA


            if attr_record['Attr_len'] > 0:
                read_pointer = read_pointer + attr_record['Attr_len']
            else:
                break
            print("read_pointer:", read_pointer)
            print("Attr_len", attr_record['Attr_len'])

        return


    def Read_MFT(self):
        with open(self.diskPath,'rb') as f:
            f.seek(0)
            f.seek(self.MFT_start)
            mft_raw=f.read(1024)
            
            while mft_raw!="":
                self.parse_record(mft_raw)
                mft_raw=f.read(1024)
                print("------------NEW ENTRY----------------------")

        f.close()




drive = r"\\.\C:"
b = NTFSPartitionBoot(drive)
b.Read_MFT()
#b.show_info()
# b.read_rdet()
