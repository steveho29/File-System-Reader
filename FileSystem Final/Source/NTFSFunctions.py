from struct import unpack
from NTFS_STRUCTURE import *
from datetime import datetime


def read_MFT_header(mft_raw):
    data = {}
    mft_header = list(MFT_Header_Structure.items())
    for i, (start_offset, info) in enumerate(mft_header):
        if i == len(mft_header) - 1:
            end_offset = 0x32
        else:
            end_offset = mft_header[i + 1][0]
        # print(end_offset)
        data[info[0]] = unpack(info[1], mft_raw[start_offset:end_offset])[0]
    return data


def read_attribute_header(mft_raw):
    data = {'Attr_type': unpack("<L", mft_raw[:4])[0]}
    # print(d['Attr_type'])
    if data['Attr_type'] == 0xFFFFFFFF:
        return data
    data['Attr_len'] = unpack("<L", mft_raw[4:8])[0]
    # print(d['Attr_len'])
    data['Resident'] = unpack("B", mft_raw[8:9])[0]
    # print("Resident:",data['Resident'])
    data['Name_len'] = unpack("B", mft_raw[9:10])[0]
    data['Name_off'] = unpack("<H", mft_raw[10:12])[0]
    data['Flags'] = unpack("<H", mft_raw[12:14])[0]
    data['ID'] = unpack("<H", mft_raw[14:16])[0]
    if data['Resident'] == 0:
        data['content_size'] = unpack("<L", mft_raw[16:20])[0]
        data['content_off'] = unpack("<H", mft_raw[20:22])[0]
        data['idxflag'] = unpack("B", mft_raw[22:23])[0]
        _ = unpack("B", mft_raw[23:24])[0]
    else:
        data['start_vcn'] = unpack("<Q", mft_raw[16:24])[0]
        data['end_vcn'] = unpack("<Q", mft_raw[24:32])[0]
        data['runlist_off'] = unpack("<H", mft_raw[32:34])[0]
        data['compress_size'] = unpack("<H", mft_raw[34:36])[0]
        data['unused'] = unpack("<I", mft_raw[36:40])[0]
        data['allocated_size'] = unpack("<Lxxxx", mft_raw[40:48])[0]
        data['real_size'] = unpack("<Lxxxx", mft_raw[48:56])[0]
        data['initialized_size'] = unpack("<Lxxxx", mft_raw[56:64])[0]

    return data


def getTime(low, high):
    t = float(high) * 2 ** 32 + low
    t = t * 1e-7 - 11644473600
    dt = datetime.fromtimestamp(t)
    return dt.isoformat(' ')


def read_File_Name_attr(mft_raw):
    data = {}
    file_name = list(FileName_Structure.items())
    for i, (start_offset, info) in enumerate(file_name):
        if start_offset == 0x41:
            end_offset = 0x42
        else:
            end_offset = file_name[i + 1][0]
        data[info[0]] = unpack(info[1], mft_raw[start_offset:end_offset])[0]

    name = mft_raw[0x42:0x42 + data['File_name_len'] * 2]

    try:
        name = name.decode('utf-16')
    except:
        pass
    data['File_name_Unicode'] = name

    return data


def read_Standard_Info_attr(s):
    data = {'Created Time': getTime(unpack("<L", s[:4])[0], unpack("<L", s[4:8])[0]),
            'atime': getTime(unpack("<L", s[8:12])[0], unpack("<L", s[12:16])[0]),
            'mtime': getTime(unpack("<L", s[16:20])[0], unpack("<L", s[20:24])[0]),
            'rtime': getTime(unpack("<L", s[24:28])[0], unpack("<L", s[28:32])[0])}
    return data


def read_Attribute_list(mft_raw):
    data = {
        'type': unpack("<I", mft_raw[:4])[0],
        'len': unpack("<H", mft_raw[4:6])[0],
        'nlen': unpack("B", mft_raw[6:7])[0],
        'f1': unpack("B", mft_raw[7:8])[0],
        'start_vcn': unpack("<d", mft_raw[8:16])[0],
        'file_ref': unpack("<Lxx", mft_raw[16:22])[0],
        'seq': unpack("<H", mft_raw[22:24])[0],
        'id': unpack("<H", mft_raw[24:26])[0],
    }

    name = mft_raw[26:26 + data['nlen'] * 2]
    data['name'] = name.decode('utf-16').encode('utf-8')
    print(data['name'])
    return data


def check_flag_mft(flag):
    if flag & 0x0001:
        act = 'active'
    else:
        act = 'inactive'

    if int(flag) & 0x0002:
        type = 'Folder'
    else:
        type = 'File'
    return act, type


def parse_record(mft_raw):
    mft_header = read_MFT_header(mft_raw)
    # print(mft_header)
    status = mft_header['Magic Number']
    # print(status)
    # if status == 0x454C4946:
    if not status == b'FILE':
        return None
    data = {}
    data['Created Date'] = ''
    data['Created Time'] = ''
    data['Latest Access'] = ''
    data['Latest Modified Time'] = ''
    data['Latest Modified Day'] = ''
    data['ParentRecord'] = ''
    data['Name'] = ''
    data['Size'] = 0

    print("------------NEW ENTRY----------------------")
    print('RECORD NUM: ' + str(mft_header['RecordNum']))
    # self.show_info(mft_header)
    act, type = check_flag_mft(mft_header['Flag'])
    data['Status'] = act
    data['Sectors'], data['Clusters'] = '', ''
    data['RecordNum'] = mft_header['RecordNum']
    data['Type'] = type.strip()

    print(act, " ", type)
    read_pointer = mft_header['First_Attribute_ID']

    while read_pointer < 1024:
        # read attribute header
        attr_record = read_attribute_header(mft_raw[read_pointer:])

        if attr_record['Attr_type'] == 0xFFFFFFFF:
            break

        # parse attribute type

        if 'content_off' not in attr_record.keys():
            start = attr_record['runlist_off']
        else:
            start = attr_record['content_off']

        start += read_pointer

        if attr_record['Attr_type'] == 0x10:  # STANDARD INFO
            standard_info = read_Standard_Info_attr(mft_raw[start:])
            print(standard_info)
            data['Created Date'], data['Created Time'] = standard_info['Created Time'].split()
            data['Latest Access'] = standard_info['rtime']
            data['Latest Modified Day'], data['Latest Modified Time'] = standard_info['atime'].split()

        elif attr_record['Attr_type'] == 0x30:  # FILE NAME

            file_name = read_File_Name_attr(mft_raw[start:])
            # print(file_name)
            print('Parent: ' + str(file_name['Parent_directory']))
            print('FILE NAME: ' + str(file_name['File_name_Unicode']))
            data['Name'] = file_name['File_name_Unicode']
            data['ParentRecord'] = file_name['Parent_directory']
            data['Size'] = file_name['AllocatedSize'] if file_name['RealSize'] == 0 else file_name['RealSize']

        elif attr_record['Attr_type'] == 0x20:  # ATTRIBUTE LIST
            atblist = read_Attribute_list(mft_raw[start:])
            print('Seq ' + str(atblist['seq']))
            # print("ATTRIBUTE LIST")

        elif attr_record['Attr_type'] == 0x80: #DATA
            pass
            # data['Size'] = attr_record['content_size'] if not attr_record['Resident'] else attr_record['compress_size']
            # if '.txt' in data['Name']:
            #     text = mft_raw[start:start + attr_record['Attr_len']]
            #     try:
            #         text = text.decode('utf-8')
            #     except:
            #         pass
            #     data['text'] = text

        if attr_record['Attr_len'] > 0:
            read_pointer = read_pointer + attr_record['Attr_len']
        else:
            break
        # print("read_pointer:", read_pointer)
        # print("Attr_len", attr_record['Attr_len'])

    if not data['ParentRecord']:
        return None
    return data
