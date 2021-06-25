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


def getSectors(start_cluster, start_sector, sectorPerCluster, clusters):
    sectors = []
    for cluster in clusters:
        sector = (cluster - start_cluster) * sectorPerCluster + start_sector
        sectors.append(sector)
    if len(sectors) == 1:
        return sectors[0], sectors[0]+sectorPerCluster
    return sectors[0], sectors[-1]+sectorPerCluster


def getStartCluster(low, high):
    return int('{:016b}'.format(high) + '{:016b}'.format(low), 2)


def checkCluster(data):
    next_cluster = unpack('<I', data)[0]
    if (b'\xff\xff\x0f' or b'\xff\xff\xff\xff') in data or next_cluster == 0:
        return False
    return next_cluster


def getClusterFromFAT(start_cluster, FAT):
    clusters = [start_cluster]
    # print(start_cluster)
    block = FAT[start_cluster*4:start_cluster*4+4]
    next_cluster = checkCluster(block)
    # print(next_cluster)
    while next_cluster:
        clusters.append(next_cluster)
        block = FAT[start_cluster * 4:start_cluster*4 + 4]
        next_cluster = checkCluster(block)
        # print(next_cluster)

    return clusters
