#!/usr/bin/python

import sys
sys.path.append(".")
sys.path.append("..")

import yali.storage

def main():
    yali.storage.init_devices()

    for d in yali.storage.devices:

        print d.getPath(), ":", d.getModel()
        for part in d.getPartitions():
            print "\t", part.getMinor(), part.getFSType(), part.getMB()


if __name__ == "__main__":
    main()
