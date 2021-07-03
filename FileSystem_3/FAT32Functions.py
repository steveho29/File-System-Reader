from struct import unpack


def getTime(x):
    b = '{:16b}'.format(x)
    try:
        hour = int(b[:5], 2)
        minute = int(b[5:11], 2)
        sec = int(b[11:], 2) * 2
    except:
        return '{}:{}:{}'.format(0, 0, 0)
    return '{}:{}:{}'.format(hour, minute, sec)


def isValidFile(status):
    return status == 16 or status == 32


def isFile(status):
    return status == 32


def isFolder(status):
    return status == 16


def isHiddened(status):
    b = '{:08b}'.format(status)
    if b[6] == 1:
        if isValidFile(status):
            return False
        else:
            return True

    return False


def getTimeCreated(x):
    b = '{:024b}'.format(x)
    hour = int(b[0:5], 2)
    min = int(b[5:11], 2)
    sec = int(b[11:17], 2)
    msec = int(b[17:], 2)

    return '{}:{}:{}:{}'.format(hour, min, sec, msec)


def getDate(x):
    b = '{:016b}'.format(x)
    day = int(b[11:16], 2)
    month = int(b[7:11], 2)
    year = int(b[0:7], 2) + 1980
    return '{}-{}-{}'.format(day, month, year)


def getSectors(clusterStartRDET, sectorStartRDET, sectorPerCluster, clusters):
    sectors = []
    for cluster in clusters:
        sector = (cluster - clusterStartRDET) * sectorPerCluster + sectorStartRDET
        for i in range(sectorPerCluster):
            sectors.append(sector+i)
    return sectors


def getStartCluster(low, high):
    return int('{:016b}'.format(high) + '{:016b}'.format(low), 2)


def checkCluster(data):
    if not data:
        return False
    next_cluster = unpack('<I', data)[0]
    check = [b'\xFF\xFF\xFF\x0F', b'\xff\xff\xff\xff', b'\xf8\xff\xff\x0f']
    if data in check or next_cluster == 0:
        return False
    return next_cluster


def getClusterFromFAT(start_cluster, FAT):
    clusters = [start_cluster]
    block = FAT[start_cluster*4:start_cluster*4+4]
    # print(block)
    next_cluster = checkCluster(block)

    while next_cluster:
        clusters.append(next_cluster)
        block = FAT[next_cluster * 4:next_cluster * 4 + 4]
        next_cluster = checkCluster(block)

    if next_cluster == b'\xff\xff\xff\xff':
        clusters.append(next_cluster)
    return clusters


