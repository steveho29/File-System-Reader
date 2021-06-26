MFT_Header_Structure={
    0x00:('Magic Number','4s'),
    0x04:('Offset to update sequence','<H'),
    0x06:('Number of entries','<H'),
    0x08:('Logfile sequence','<Q'),
    0x10:('SequenceNum','<H'),
    0x12:('LinkCount','<H'),
    0x14:('First_Attribute_ID','<H'),
    0x16:('Flag','<H'),
    0x18:('Used_size_MFT_entry','<L'),
    0x1C:('Allocated_size_MFT_entry','<L'),
    0x20:('File record','<Q'),
    0x28:('Next_attribute_ID','<H'),
    0x2A:('Boundary','2s'),
    0x2C:('RecordNum','<I'),
    0x30:('Fixup value','2s')
}

Attribute_header_structure={
    0x00:('Atrribute Type','<L'),
    0x04:('Attribute length','<L'),
    0x08:('Resident','B'),
    0x09:('Length of name','B'),
    0x0A:('Offset to name','<H'),
    0x0C:('Flags','<H'),
    0x0E:('Attribute identifier','<H')
}

FileName_Structure={
    0x00:('Parent_directory','<Q'),
    0x08:('Creation_time','<Q'),
    0x10:('Last_data_change_time','<Q'),
    0x18:('Last_mft_change_time','<Q'),
    0x20:('Last_access_time','<Q'),
    0x28:('Allocated_size','<Q'),
    0x30:('Real+size','<Q'),
    0x38:('Flag','<d'),
    #0x3C:('EA_size','<L'),
    #0x34:('Security_id','<L'),
    0x40:('File_name_len','B'),
    0x41:('File_namespace','B')
    #('File_name_unicode','')
}

Standard_Information_Structure={
    0x00:('Creation time','<Q'),
    0x08:('Last data changed time','<Q'),
    0x10:('MFT changed time','<Q'),
    0x18:('Last access time','<Q'),
}

