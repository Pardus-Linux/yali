#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import glob
import parted
import struct
import gettext

__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext

import yali
import yali.util
import yali.gui.context as ctx

class BootLoaderError(yali.Error):
    pass

class ReleaseError(BootLoaderError):
    pass

class KernelError(BootLoaderError):
    pass


dos_filesystems = ('FAT', 'fat16', 'fat32', 'ntfs', 'hpfs')
linux_filesystems = ('ext4', 'ext3', 'reisersfs', 'xfs')
allParameters = ["root", "initrd","init","xorg","yali","BOOT_IMAGE","lang","mudur"]

BOOT_TYPE_NONE = 0
BOOT_TYPE_MBR = 1
BOOT_TYPE_PARTITION = 2
BOOT_TYPE_RAID = 4

boot_type_strings = {BOOT_TYPE_PARTITION: "None",
                     BOOT_TYPE_MBR: "Master Boot Record(MBR)",
                     BOOT_TYPE_PARTITION: "First sector of Boot partition",
                     BOOT_TYPE_RAID: "RAID Device"}

def get_configs(rootpath):
    try:
        releasePath = os.path.join(rootpath, "etc/pardus-release")
        release = file(releasePath).readlines()[0].strip()
        bootDir = os.path.join(rootpath, "boot")
        kernels = glob.glob(bootDir + "/kernel-*")
        kernel = os.path.basename(sorted(kernels)[-1])
        kernelVersion = kernel[len("kernel-"):]
        initramfs = "initramfs-%s" % kernelVersion
    except IOError, msg:
        raise ReleaseError, msg
    except IndexError, msg:
        raise KernelError, msg
    else:
        return (release, kernel, initramfs)

def get_commands(storage):
    _commands = []
    _commands.append("root=%s" % (storage.rootDevice.fstabSpec))

    if storage.storageset.swapDevices:
        _commands.append("resume=%s" % storage.storageset.swapDevices[0].path)

    for command in [cmd for cmd in open("/proc/cmdline", "r").read().split()]:
        for parameter in allParameters:
            if not command.startswith("%s=" % parameter):
                _commands.append(command)

    return " ".join(_commands).strip()

def get_disk_name(storage, device):
    return "hd%d" % storage.drives.index(device.name)

def get_partition_name(storage, device):
    (disk, number) = get_disk_partition(device)
    if number is not None:
        return "(%s,%d)" % (get_disk_name(storage, disk), number - 1)
    else:
        return "(%s)" %(get_disk_name(storage, disk))

def get_disk_partition(device):
    if device.type == "partition":
        number = device.partedPartition.number
        disk = device.disk
    else:
        number = None
        disk = device

    return (disk, number)

grub_conf = """\
default 0
timeout 10
gfxmenu /boot/grub/message
background 10333C

title %(release)s
root %(root)s
kernel %(root)s%(bootpath)s%(kernel)s %(commands)s
initrd %(root)s%(bootpath)s%(initramfs)s

"""

windows_conf = """
title %(title)s (%(filesystem)s) on %(device)s
rootnoverify (%(root)s)
makeactive
chainloader +1

"""

def get_physical_devices(storage, device):
    _devices = []
    _physicalDevices = []
    if device.type == "mdarray":
        if device.level != 1:
            ctx.logger.error("Ignoring non level 1 raid array %s" % device.name)
            return _devices
        _devices = device.parents
    else:
        _devices = [device]

    for _device in _devices:
        if _device in storage.disks or _device.type == "partition":
            _physicalDevices.append(device)
        else:
            ctx.logger.error("Ignoring %s" % device.name)

    return _physicalDevices

def check_dual_boot():
    if yali.util.isX86():
        return 1
    return 0

def check_boot_block(device):
    fd = os.open(device, os.O_RDONLY)
    buf = os.read(fd, 512)
    os.close(fd)
    if len(buf) >= 512 and \
           struct.unpack("H", buf[0x1fe: 0x200]) == (0xaa55,):
        return True
    return False



class BootLoader(object):
    _grubConf = "grub.conf"
    _deviceMap = "device.map"
    def __init__(self, storage=None):
        self.storage = storage
        self._path = None
        self._device = None
        self._type = BOOT_TYPE_NONE
        self.enabledOthers = False

    def _setPath(self, path):
        self._path = path

    def _getPath(self):
        return self._path

    path = property(lambda f: f._getPath(),
                    lambda f,d: f._setPath(d))

    def _setDevice(self, device):
        self._device = device

        print "_setDevice --> device:%s" % device
        (disk, partition) = get_disk_partition(self.storage.devicetree.getDeviceByName(device))
        if partition is None:
            self._type = BOOT_TYPE_MBR
        else:
            self._type= BOOT_TYPE_PARTITION

    def _getDevice(self):
        return self._device

    device = property(lambda f: f._getDevice(),
                      lambda f,d: f._setDevice(d))

    def _setBootType(self, type):
        self._type = type

    def _getBootType(self):
        return self._type

    bootType = property(lambda f: f._getBootType(),
                       lambda f,d: f._setBootType(d))

    @property
    def choices(self):
        _choices = {}
        bootDevice = self.storage.storageset.bootDevice

        if not bootDevice:
            return _choices

        if bootDevice.type == "mdarray":
            _choices[BOOT_TYPE_RAID] = (bootDevice.name, _("%s" % boot_type_strings[BOOT_TYPE_RAID]))
            _choices[BOOT_TYPE_MBR] = (self.drives[0], _("%s" % boot_type_strings[BOOT_TYPE_MBR]))
        else:
            _choices[BOOT_TYPE_PARTITION] = (bootDevice.name, _("%s" % boot_type_strings[BOOT_TYPE_PARTITION]))
            _choices[BOOT_TYPE_MBR] = (self.drives[0], _("%s" % boot_type_strings[BOOT_TYPE_MBR]))

        return _choices

    def availablesDevices(self, root=True):
        _availableDevices = []

        for partition in [p for p in self.storage.partitions if p.exists]:
            if partition.partType not in (parted.PARTITION_NORMAL, parted.PARTITION_LOGICAL) or not partition.format:
                continue

            if (partition.format.type in dos_filesystems and check_dual_boot() \
                    and not partition.getFlag(parted.PARTITION_DIAG)) or \
                        partition.format.type in linux_filesystems:
                try:
                    bootable = check_boot_block(partition.path)
                except Exception, msg:
                    ctx.logger.debugger("Error in bootloader.availableDevices:%s" % msg)
                else:
                    if bootable:
                        _availableDevices.append((partition, partition.format.type))


        if root:
            rootDevice = self.storage.rootDevice
            if not rootDevice or not rootDevice.format:
                raise ValueError, ("Trying to pick boot devices but do not have a "
                                   "sane root partition.  Aborting install.")
            _availableDevices.append((rootDevice, rootDevice.format.type))

        _availableDevices.sort()

        return _availableDevices

    @property
    def drives(self):
        disks = self.storage.disks
        partitioned = self.storage.partitioned
        drives = [d.name for d in disks if d in partitioned]
        drives.sort(cmp=self.storage.compareDisks)
        return drives

    def setup(self):
        bootDevice = self.storage.storageset.bootDevice
        if bootDevice.format.mountpoint == "/boot":
            self.path = "/"
        else:
            self.path = "/boot/"

    def write(self):
        self.writeGrubConf()

        usedDevices = set()
        usedDevices.update(get_physical_devices(self.storage, self.storage.devicetree.getDeviceByName(self.device)))
        usedDevices.update(get_physical_devices(self.storage, self.storage.storageset.bootDevice))
        #usedDevices.update([device for device, (label, filesystem) in self.others.items()])

        self.writeDeviceMap(usedDevices)

    def writeGrubConf(self):
        bootDevices = get_physical_devices(self.storage, self.storage.storageset.bootDevice)
        (release, kernel, initramfs ) = get_configs(ctx.consts.target_dir)
        s = grub_conf % {"root": get_partition_name(self.storage, bootDevices[0]),
                         "bootpath" : self.path,
                         "release": release,
                         "kernel": kernel,
                         "commands": get_commands(self.storage),
                         "initramfs": initramfs}
        ctx.logger.debug("root:%s -  bootpath:%s - release:%s - kernel:%s -commands:%s - initramfs:%s" %
                        (get_partition_name(self.storage, bootDevices[0]),
                         self.path,
                         release,
                         kernel,
                         get_commands(self.storage),
                         initramfs))
        if self.enabledOthers:
            for device, (label, filesystem) in self.others().items():
                s += windows_conf % {"title": label,
                                     "filesystem": filesystem,
                                     "device":device.name,
                                     "root": get_partition_name(self.storage, device)}

        with open(os.path.join(ctx.consts.target_dir, "boot/grub", self._grubConf), "w") as grubConfFile:
            grubConfFile.write(s)

    def appendDOSSystems(self):
        return

    def appendLinuxSystems(self):
        return

    def writeDeviceMap(self, usedDevices):
        with open(os.path.join(ctx.consts.target_dir, "boot/grub", self._deviceMap), "w+") as deviceMapFile:
            deviceMapFile.write("# this device map was generated by YALI\n")
            usedDisks = set()
            for device in usedDevices:
                drive = get_disk_partition(device)[0]
                usedDisks.add(drive)
            devices = list(usedDisks)
            devices.sort(key=lambda d: d.name)
            for device in devices:
                deviceMapFile.write("(%s)     %s\n" % (get_disk_name(self.storage, device), device.path))

    def install(self):
        stage1Devices = get_physical_devices(self.storage, self.storage.devicetree.getDeviceByName(self.device))
        bootDevices = get_physical_devices(self.storage, self.storage.storageset.bootDevice)

        stage1Path = get_partition_name(self.storage, stage1Devices[0])
        bootPartitionPath = get_partition_name(self.storage, bootDevices[0])

        batch_template = """root %s
setup %s
quit
""" % (bootPartitionPath, stage1Path)

        ctx.logger.debug("Batch template: %s" % batch_template)
        file('/tmp/batch','w').write(batch_template)

        rc = yali.util.run_batch("grub", ["--no-floppy", "--batch < ", "/tmp/batch"])[0]
        yali.util.sync()
        return rc

    @property
    def others(self):
        _others= {}
        bootDevices = self.availableDevices()

        for (device, type) in bootDevices:
            if not _others.has_key(device.name):
                if type in dos_filesystems and check_dual_boot():
                    _others[device] = ("Other Windows", type)
                elif type in linux_filesystems:
                    _others[device] = ("Other Linux", type)

        return _others
