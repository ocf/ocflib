#!/usr/bin/env python3
import time
from contextlib import contextmanager
from datetime import datetime
from datetime import timedelta

from ocflib.lab.stats import list_desktops
from ocflib.lab.stats import UtilizationProfile


@contextmanager
def timeit():
    start = time.time()
    yield
    print("Time taken: {}".format(time.time() - start))


if __name__ == "__main__":
    start = datetime(2015, 11, 23)
    end = start + timedelta(days=1)

    print("Testing naive time to create profiles.")
    with timeit():
        slow_profiles = {
            host
            + ".ocf.berkeley.edu": UtilizationProfile.from_hostname(host, start, end)
            for host in list_desktops()
        }

    print("Testing optimized time to create profiles.")
    with timeit():
        fast_profiles = UtilizationProfile.from_hostnames(list_desktops(), start, end)
