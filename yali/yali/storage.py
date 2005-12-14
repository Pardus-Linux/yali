# -*- coding: utf-8 -*-
#
# Copyright (C) 2005, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#


# Storage module will handle the disk/partitioning basics for
# installation. Basically this module can provide two main interfaces,
# one for physical storage and one for partitions.

# GPL code mostly taken from GLI (Gentoo Linux Installer).

import parted
import os

from yali.parteddata import *
from yali.partition import Partition, FreeSpace
from yali.exception import YaliError, YaliException
import yali.filesystem


class DeviceError(YaliError):
    pass


# all storage devices
devices = []

##
# initialize all devices and fill devices list
def init_devices(force = False):
    global devices

    if devices and not force:
        return

    devs = detect_all()
    for dev_path in devs:
        d = Device(dev_path)
        devices.append(d)


##
# Class representing a partitionable storage
class Device:

    ##
    # Init Device
    # @param device_path: Device node (eg. /dev/hda, /dev/sda)
    # @param arch: Architecture that we're partition for (defaults to 'x86')
    def __init__(self, device_path, arch="x86"):

        self._arch = arch
        self._path = ""
        self._device = None
        self._model = ""
        self._disk = None
        self._partitions = {}
        self._disklabel = ""
        self._length = 0       # total sectors
        self._sector_size = 0
        self._parted_type = deviceType

        dev = parted.PedDevice.get(device_path)

        self._model = dev.model
        self._length = dev.length
        self._sector_size = dev.sector_size

        self._dev = dev
        try:
            self._disk = parted.PedDisk.new(dev)
        except:
            label = archinfo[self._arch]["disklabel"]
            disk_type = parted.disk_type_get(label)
            self._disk = self._dev.disk_new_fresh(disk_type)

        self._disklabel = self._disk.type.name

        self._path = device_path

        self.update()

    def getType(self):
        return self._parted_type

    ##
    # clear and re-fill partitions dict.
    def update(self):
        self._partitions.clear()

        part = self._disk.next_partition()
        while part:
            self.__addToPartitionsDict(part)
            part = self._disk.next_partition(part)

    ##
    # get device capacity in bytes
    # returns: long
    def getTotalBytes(self):
        return long(self._length * self._sector_size)

    ##
    # get device capacity in MBs
    # returns: long
    def getTotalMB(self):
        return long(self.getTotalBytes() / MEGABYTE)

    def getTotalGB(self):
        return long(self.getTotalBytes() / GIGABYTE)

    ##
    # get device capacity string
    # returns: string
    def getSizeStr(self):
        bytes = self.getTotalBytes()
        if bytes > GIGABYTE:
            return "%d GB" % self.getTotalGB()
        else:
            return "%d MB" % self.getTotalMB()

    ##
    # get device path (eg. /dev/hda)
    # returns: string
    def getPath(self):
        return self._path

    ##
    # get device name (eg. hda)
    # returns: string
    def getName(self):
        return os.path.basename(self.getPath())

    ##
    # get device model
    # returns: string
    def getModel(self):
        return self._model

    ##
    # get partitions from disk
    # returns: [Partition]
    def getPartitions(self):
        return self._partitions.values()

    ##
    # get a partition by number
    # @param num: partition number
    #
    # returns: Partition
    def getPartition(self, num):
        return self._partitions[num]


    ##
    # check if the device has an extended partition
    # returns: True/False
    def hasExtendedPartition(self):
        if self.getExtendedPartition():
            return True

        return False

    ##
    # get the extended partition on device (if it has one)
    def getExtendedPartition(self):
        for p in self.getPartitions():
            if p._partition.type == parted.PARTITION_EXTENDED:
                return p

        return False

    ##
    # get the partition list in an order
    # returns: [Partition]
    def getOrderedPartitionList(self):

        def comp(x, y):
            """sort partitions using get_start()"""
            x = x.getStart()
            y = y.getStart()

            if x > y: return -1
            elif x == y: return 0
            else: return 1

        l = self.getPartitions()
        l.sort(comp)
        return l

    def getFreeMB(self):
        parts = self.getPartitions()
        
        size = 0
        for p in parts:
            if isinstance(p, FreeSpace):
                size += p.getMB()

        return size


    ###############################
    # Partition mangling routines #
    ###############################

    ##
    # Add (create) a new partition to the device
    # @param type: parted partition type (eg. parted.PARTITION_PRIMARY)
    # @param fs: filesystem.FileSystem or file system name (like "ext3")
    # @param size_mb: size of the partition in MBs.
    def addPartition(self, type, fs, size_mb, flags = []):

        size = int(size_mb * MEGABYTE / self._sector_size)

        part = self._disk.next_partition()
        while part:
            geom = part.geom

            if (part.type == parted.PARTITION_FREESPACE
                and geom.length >= size):

                return self.addPartitionStartEnd(type,
                                                 fs,
                                                 geom.start,
                                                 geom.start + size,
                                                 flags)

            part = self._disk.next_partition(part)

        raise DeviceError, ("Not enough free space on %s to create "
                            "new partition" % self.getPath())


    ##
    # add a partition starting from a given geom...
    def addPartitionFromStart(self, type, fs, start, size_mb):
        size = int(size_mb * MEGABYTE / self._sector_size)
        self.addPartitionStartEnd(type, fs, start, start + size)

        
    ##
    # Add (create) a new partition to the device from start to end.
    #
    # @param type: parted partition type (eg. parted.PARTITION_PRIMARY)
    # @param fs: filesystem.FileSystem or file system name (string like "ext3")
    # @param start: start geom..
    # @param end: end geom
    def addPartitionStartEnd(self, type, fs, start, end, flags = []):

        if isinstance(fs, str):
            # a string... get the corresponding FileSystem object
            fs = yali.filesystem.get_filesystem(fs)

        if isinstance(fs, yali.filesystem.FileSystem):
            fs = fs.getFSType()
        else:
            fs = None

        constraint = self._disk.dev.constraint_any()
        newp = self._disk.partition_new (type, fs, start, end)
        for flag in flags:
            newp.set_flag(flag, 1)
            

        try:
            self._disk.add_partition (newp, constraint)
        except parted.error, e:
            raise DeviceError, e
        
        return self.__addToPartitionsDict(newp)


    ##
    # internal function
    # add partition to the partitions dictionary
    # @param part: pyparted partition type
    #
    # returns: Partition
    def __addToPartitionsDict(self, part):

        geom = part.geom
        part_mb = long(
            (geom.end - geom.start + 1) * self._sector_size / MEGABYTE)

        if part.num >= 1:
            fs_name = ""
            if part.fs_type:
                fs_name = part.fs_type.name
            elif part.type == parted.PARTITION_EXTENDED:
                fs_name = "extended"

            self._partitions[part.num] = Partition(self, part,
                                                   part.num,
                                                   part_mb,
                                                   geom.start,
                                                   geom.end,
                                                   fs_name)
        elif part.type_name == "free":
            self._partitions[-1] = FreeSpace(self, part,
                                             part_mb,
                                             part.geom.start,
                                             part.geom.end)
        return part

    ##
    # delete a partition
    # @param part: Partition
    def deletePartition(self, part):
        self._disk.delete_partition(part.getPartition())

    def deleteAllPartitions(self):
        self._disk.delete_all()

    def resizePartition(self, fs, size_mb, part):

        # maximum cylinder size currently is less than 140 MB hence
        # this extra size should be always enough.
        #
        # see: http://mlf.linux.rulez.org/mlf/ezaz/ntfsresize.html
        size_mb += 140

        if isinstance(fs, str):
            # a string... get the corresponding FileSystem object
            fs = yali.filesystem.get_filesystem(fs)

        if not isinstance(fs, yali.filesystem.FileSystem):
            raise DeviceError, "filesystem is None, can't resize"

        print dir(fs)
        if not fs.resize(size_mb, part):
            raise DeviceError, "fs.resize ERROR"

        start = part.getPartition().geom.start
        fs_name = part.getFSName()
        self.deletePartition(part)
        self.commit()
        # FIXME: TYPE is 0
        self.addPartitionFromStart(0, fs_name, start, size_mb)
        self.commit()

    def commit(self):
        self._disk.commit()
        self.update()

    def close(self):
        # pyparted will do it for us.
        del self._disk




##
# Return a list of block devices in system
def detect_all():

    # Check for sysfs. Only works for >2.6 kernels.
    if not os.path.exists("/sys/bus"):
        raise BolError, "sysfs not found!"
    # Check for /proc/partitions
    if not os.path.exists("/proc/partitions"):
        raise BolError, "/proc/partitions not found!"

    partitions = []
    for line in open("/proc/partitions"):
        entry = line.split()

        if not entry:
            continue
        if not entry[0].isdigit() and not entry[1].isdigit():
            continue

        major = int(entry[0])
        minor = int(entry[1])
        device = "/dev/" + entry[3]

        partitions.append((major, minor, device))

    devices = []
    # Scan sysfs for the device types.
    for dev_type in ["ide", "scsi"]:
        sysfs_devs_path = "/sys/bus/" + dev_type + "/devices/"

        if os.path.exists(sysfs_devs_path):
            # walk trough sysfs devices list.
            for sysfs_dev in os.listdir(sysfs_devs_path):
                dev_file = sysfs_devs_path + sysfs_dev + "/block/dev"
                
                if not os.path.exists(dev_file):
                    continue

                major, minor = open(dev_file).read().split(":")
                major = int(major)
                minor = int(minor)

                # Find a device listed in /proc/partitions
                # that has the same minor and major as our
                # current block device.
                for record in partitions:
                    if major == record[0] and minor == record[1]:
                        devices.append(record[2])

    return devices
