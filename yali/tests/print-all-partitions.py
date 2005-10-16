#!/usr/bin/python

import sys
sys.path.append(".")
sys.path.append("..")

import yali.storage

def main():
    devs = yali.storage.detect_all()

    for dev in devs:
        d = yali.storage.Device(dev)
        d.open()

        print d.get_device(), ":", d.get_model()
        for part in d.get_partitions().itervalues():
            print "\t", part.get_minor(), part.get_fsType(), part.get_mb()

if __name__ == "__main__":
    main()
