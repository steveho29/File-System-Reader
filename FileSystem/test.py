from multiprocessing import Pool, freeze_support
import concurrent.futures
from threading import Thread
import time


def func(f):
    return f.read(512)


if __name__ == '__main__':
    freeze_support()
    # p = Pool(6)
    s = time.time()
    drive = r'\\.\D:'

    i = 0
    f = open(drive, 'rb')
    threads = []
    # while f.tell() != 51200000:
    #     q = Thread(target=func, args=(f, ))
    #     threads.append(q)
    #     q.start()
        # func(f)
    for i in range(100000):
        func(f)
    print(f.tell())
    print(time.time() - s)
