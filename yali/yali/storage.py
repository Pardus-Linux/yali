# -*- coding: utf-8 -*-

# Storage module will handle the disk/partitioning basics for
# installation. Basically this module can provide two main interfaces,
# one for physical storage and one for partitions.

# GPL code mostly taken from GLI (Gentoo Linux Installer).

import parted
import os

from exception import YaliError, YaliException


MEGABYTE = 1024 * 1024

archinfo = {
    'x86': {'fixedparts': [],
            'disklabel': 'msdos',
            'extended': True},

    'amd64': {'fixedparts': [],
              'disklabel': 'msdos',
              'extended': True},

    'ppc': {'fixedparts':[{'minor': 1, 'type': "metadata"}],
            'disklabel': 'mac',
            'extended': False }
    }



##
# Class representing a single partition within a Device object
class Partition:

    def __init__(self, device, part, minor, mb, start, end, type):
        self._device = device
        self._parted_part = part
        self._minor = minor
        self._mb = mb
        self._start = start
        self._end = end
        self._type = type or "unknown"

    def get_minor(self):
        return self._minor

    def get_type(self):
        return self._type

    def get_start(self):
        return self._start

    def get_end(self):
        return self._end

    def get_mb(self):
        return self._mb


##
# Class representing a partitionable device.
class Device:

    def __init__(self, device, arch="x86"):
        self._arch = arch
        self._device = device
        self._parted_dev = parted.PedDevice.get(self._device)
        self._parted_disk = None
        self._disklabel = None
        self._partitions = {}
        self._total_mb = 0
        self._sector_bytes = 0
        self._total_bytes = 0
        self._total_sectors = 0
        self._cylinder_bytes = 0
        self._sectors_in_cylinder = 0
        self._geometry = {'cylinders': 0, 'heads': 0, 'sectors': 0, 'sectorsize': 512}

        try:
            self._parted_disk = parted.PedDisk.new(self._parted_dev)
        except:
            label = archinfo[self._arch]["disklabel"]
            self._parted_disk = self._parted_dev.disk_new_fresh(parted.disk_type_get(label))

        self._disklabel = self._parted_disk.type.name
        
        self.set_disk_geometry_from_disk()


    ##
    # Sets disk geometry info from disk.
    # This function is used internally by __init__()
    def set_disk_geometry_from_disk(self):

        self._total_bytes = self._parted_dev.length * self._parted_dev.sector_size

        self._geometry['heads'] = self._parted_dev.heads
        self._geometry['sectors'] = self._parted_dev.sectors
        self._geometry['cylinders'] = self._parted_dev.cylinders

        self._sector_bytes = self._parted_dev.sector_size

        self._cylinder_bytes = self._geometry['heads'] * self._geometry['sectors'] * self._sector_bytes

        self._total_sectors = self._parted_dev.length

        self._sectors_in_cylinder = self._geometry['heads'] * self._geometry['sectors']

        self._total_mb = long(self._total_bytes / MEGABYTE)


    ##
    # Sets partition info from disk.
    def set_partitions_from_disk(self):

        # loop over partition list...
        parted_part = self._parted_disk.next_partition()
        while parted_part:
            part_mb = long((parted_part.geom.end - parted_part.geom.start + 1) * self._sector_bytes / MEGABYTE)

            if parted_part.num >= 1:
                fs_type = ""
                if parted_part.fs_type: fs_type = parted_part.fs_type.name
                elif parted_part.type == parted.PARTITION_EXTENDED: fs_type = "extended"

                self._partitions[parted_part.num] = Partition(self, parted_part,
                                                              parted_part.num,
                                                              part_mb,
                                                              parted_part.geom.start,
                                                              parted_part.geom.end,
                                                              fs_type)

            elif parted_part.type_name == "free":
                    print "free", self._device, parted_part.num, parted_part.fs_type

            parted_part = self._parted_disk.next_partition(parted_part)

    def get_device(self):
        return self._device

    def get_model(self):
        return self._parted_dev.model

    def get_total_mb(self):
        return self._total_mb

    def get_partitions(self):
        return self._partitions


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


