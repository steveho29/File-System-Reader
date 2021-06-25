
def getTime(x):
    b = '{:16b}'.format(x)
    hour = int(b[:5], 2)
    minute = int(b[5:11], 2)
    sec = int(b[11:], 2) * 2
    return '{}:{}:{}'.format(hour, minute, sec)


def isFile(status):
    status = "{:08b}".format(status)
    return status[5] == 1


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
    year = int(b[0:7], 2)+1980
    return '{}-{}-{}'.format(day, month, year)