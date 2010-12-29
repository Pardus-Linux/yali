#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import glob
import parted
import gettext

__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext

import yali
import yali.util
import yali.context as ctx
from pardus.grubutils import grubConf

class BootLoaderError(yali.Error):
    pass

class ReleaseError(BootLoaderError):
    pass

class KernelError(BootLoaderError):
    pass


dos_filesystems = ('FAT', 'fat16', 'fat32', 'ntfs', 'hpfs')
linux_filesystems = ('ext4', 'ext3', 'reisersfs', 'xfs')
allParameters = ["root", "initrd", "init", "xorg", "yali", "BOOT_IMAGE", \
                 "lang", "mudur", "copytoram"]

BOOT_TYPE_NONE = 0
BOOT_TYPE_MBR = 1
BOOT_TYPE_PARTITION = 2
BOOT_TYPE_RAID = 4

boot_type_strings = {BOOT_TYPE_PARTITION: "None",
                     BOOT_TYPE_MBR: "Master Boot Record(MBR)",
                     BOOT_TYPE_PARTITION: "First sector of Pardus Boot partition",
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
    def is_required(parameter):
        for p in allParameters:
            if parameter.startswith("%s=" % p):
                return False
        return True

    _commands = []
    _commands.append("root=%s" % (storage.rootDevice.fstabSpec))

    if storage.storageset.swapDevices:
        _commands.append("resume=%s" % storage.storageset.swapDevices[0].path)

    for parameter in [x for x in open("/proc/cmdline", "r").read().split()]:
        if is_required(parameter):
            _commands.append(parameter)

    if ctx.blacklistedKernelModules:
        _commands.append("blacklist=%s" % ",".join(ctx.blacklistedKernelModules))

    return " ".join(_commands).strip()

def get_disk_name(storage, device, exists=False):
    if exists:
        return "hd%d" % (storage.drives.index(device.name) + 1)
    else:
        return "hd%d" % storage.drives.index(device.name)

def get_partition_name(storage, device, exists=False):
    (disk, number) = get_disk_partition(device)
    if number is not None:
        return "(%s,%d)" % (get_disk_name(storage, disk, exists), number - 1)
    else:
        return "(%s)" % (get_disk_name(storage, disk, exists))

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
gfxmenu %(bootpath)sgrub/message
background 10333C

title %(release)s
uuid %(uuid)s
kernel %(bootpath)s%(kernel)s %(commands)s
initrd %(bootpath)s%(initramfs)s

"""

windows_conf = """
title %(title)s on %(device)s
rootnoverify %(root)s
makeactive
chainloader +1

"""
windows_conf_multiple_disks = """
title %(title)s on %(device)s
map (hd0) %(root)s
map %(root)s (hd0)
rootnoverify %(root)s
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


class BootLoader(object):
    _conf = "boot/grub/grub.conf"
    _deviceMap = "device.map"
    def __init__(self, storage=None):
        self.storage = storage
        self._path = None
        self._device = None
        self._type = BOOT_TYPE_NONE
        self.grubConf = None
        self.removableExists = False

    def _setPath(self, path):
        self._path = path

    def _getPath(self):
        return self._path

    path = property(lambda f: f._getPath(),
                    lambda f,d: f._setPath(d))

    def _setDevice(self, device):
        self._device = device

        if device:
            partition = get_disk_partition(self.storage.devicetree.getDeviceByName(device))[1]
            if partition is None:
                self._type = BOOT_TYPE_MBR
            else:
                self._type = BOOT_TYPE_PARTITION

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

        self.writeDeviceMap(usedDevices)

    def writeGrubConf(self):
        bootDevices = get_physical_devices(self.storage, self.storage.storageset.bootDevice)
        (release, kernel, initramfs ) = get_configs(ctx.consts.target_dir)
        s = grub_conf % {"uuid": bootDevices[0].fstabSpec.split("=")[1].lower(),
                         "bootpath" : self.path,
                         "release": release,
                         "kernel": kernel,
                         "commands": get_commands(self.storage),
                         "initramfs": initramfs}
        ctx.logger.debug("uuid:%s -  bootpath:%s - release:%s - kernel:%s -commands:%s - initramfs:%s" %
                        (bootDevices[0].fstabSpec.split("=")[1].lower(), self.path, release, kernel,
                         get_commands(self.storage), initramfs))
        ctx.logger.debug("conf:%s" % os.path.join(ctx.consts.target_dir, self._conf))
        with open(os.path.join(ctx.consts.target_dir, self._conf), "w") as grubConfFile:
            grubConfFile.write(s)

        target_conf_dir = os.path.join(ctx.consts.target_dir, "etc")
        if os.path.exists(target_conf_dir):
            ctx.logger.debug("Target grub.conf file is writing")
            self.writeGrubInstallConf(os.path.join(target_conf_dir, "grub.conf"), removableExists=False)

        self.writeGrubInstallConf("/tmp/batch", removableExists=self.removableExists)
        self.appendOtherSystems()

    def appendOtherSystems(self):
        for partition in [p for p in self.storage.partitions if p.exists]:
            if partition.partType not in (parted.PARTITION_NORMAL, parted.PARTITION_LOGICAL) or not partition.format:
                continue

            if not partition.getFlag(parted.PARTITION_DIAG):
                if partition.format.type in  ('fat32', 'ntfs-3g') and \
                        yali.util.check_dual_boot():
                    if partition.format.type == "fat32":
                        self.appendDOSSystems(partition.path, "vfat")
                    else:
                        self.appendDOSSystems(partition.path, "ntfs")

                elif partition.format.type in ('ext4', 'ext3', 'reisersfs', 'xfs'):
                    bootDevice = get_physical_devices(self.storage, self.storage.storageset.bootDevice)[0]
                    if partition.path != bootDevice.path:
                        self.appendLinuxSystems(partition.path, partition.format.type)

    def appendDOSSystems(self, device, formatType):
        if not os.path.isdir(ctx.consts.tmp_mnt_dir):
            ctx.logger.debug("Creating temporary mount point %s for %s to check partitions" % (ctx.consts.tmp_mnt_dir, device))
            os.makedirs(ctx.consts.tmp_mnt_dir)
        else:
            yali.util.umount(ctx.consts.tmp_mnt_dir)

        try:
            ctx.logger.debug("Mounting %s to %s to check partition" % (device, ctx.consts.tmp_mnt_dir))
            yali.util.mount(device, ctx.consts.tmp_mnt_dir, formatType)
        except Exception:
            ctx.logger.debug("Mount failed for %s " % device)
            return None
        else:
            is_exist = lambda f: os.path.exists(os.path.join(ctx.consts.tmp_mnt_dir, f))
            if is_exist("boot.ini") or is_exist("command.com") or is_exist("bootmgr"):
                with open(os.path.join(ctx.consts.target_dir, self._conf), "a") as grubConfFile:
                    windowsBoot = get_partition_name(self.storage, self.storage.devicetree.getDeviceByPath(device))
                    bootDevice = get_physical_devices(self.storage, self.storage.storageset.bootDevice)[0]
                    ctx.logger.debug("Windows boot on %s" % windowsBoot)

                    if bootDevice.name == self.storage.devicetree.getDeviceByPath(device).parents[0]:
                        s = windows_conf % {"title": _("Windows"),
                                            "device": device,
                                            "root": windowsBoot}
                    else:
                        s = windows_conf_multiple_disks % {"title": _("Windows"),
                                                           "device": device,
                                                           "root": windowsBoot}
                    grubConfFile.write(s)

            yali.util.umount(ctx.consts.tmp_mnt_dir)

    def appendLinuxSystems(self, device, formatType):
        self.grubConf = grubConf()
        self.grubConf.parseConf(os.path.join(ctx.consts.target_dir, self._conf))
        if not os.path.isdir(ctx.consts.tmp_mnt_dir):
            ctx.logger.debug("Creating temporary mount point %s for %s to check partitions" % (ctx.consts.tmp_mnt_dir, device))
            os.makedirs(ctx.consts.tmp_mnt_dir)
        else:
            yali.util.umount(ctx.consts.tmp_mnt_dir)

        try:
            ctx.logger.debug("Mounting %s to %s to check partition" % (device, ctx.consts.tmp_mnt_dir))
            yali.util.mount(device, ctx.consts.tmp_mnt_dir, formatType)
        except Exception:
            ctx.logger.debug("Mount failed for %s " % device)
            return None
        else:
            is_exist = lambda p, f: os.path.exists(os.path.join(ctx.consts.tmp_mnt_dir, p, f))

            boot_path = None
            if is_exist("boot/grub", "grub.conf") or is_exist("boot/grub", "menu.lst"):
                boot_path = "boot/grub"
            elif is_exist("grub", "grub.conf") or is_exist("grub", "menu.lst"):
                boot_path = "grub"

            if boot_path:
                ctx.logger.debug("%s device has bootloader configuration to parse." % device)
                menulst = os.path.join(ctx.consts.tmp_mnt_dir, boot_path, "menu.lst")
                grubconf = os.path.join(ctx.consts.tmp_mnt_dir, boot_path, "grub.conf")
                path = None
                if os.path.islink(menulst):
                    ctx.logger.debug("Additional grub.conf found on device %s" % device)
                    path = grubconf
                else:
                    ctx.logger.debug("Additional menu.lst found on device %s" % device)
                    path = menulst

                guestGrubConf = None
                if path and os.path.exists(path):
                    guestGrubConf = grubConf()
                    guestGrubConf.parseConf(path)
                    for entry in guestGrubConf.entries:
                        if entry.getCommand("root"):
                            entry.title = entry.title + " [ %s ]" % device

                            if entry.getCommand("root"):
                                rootCommand = entry.getCommand("root")
                                if rootCommand.value != "":
                                    rootCommand.value = get_partition_name(self.storage, self.storage.devicetree.getDeviceByPath(device))

                                kernelCommand = entry.getCommand("kernel")
                                if kernelCommand and rootCommand.value:
                                    if kernelCommand.value.startswith('('):
                                        kernelCommand.value = ''.join([rootCommand.value, kernelCommand.value.split(')')[1]])

                                # update device order for initrd command if already defined
                                initrdCommand = entry.getCommand("initrd")
                                if initrdCommand and rootCommand.value:
                                    if initrdCommand.value.startswith('('):
                                        initrdCommand.value = ''.join([rootCommand.value, initrdCommand.value.split(')')[1]])

                            self.grubConf.addEntry(entry)

                self.grubConf.write(os.path.join(ctx.consts.target_dir, self._conf))

            yali.util.umount(ctx.consts.tmp_mnt_dir)

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

    def writeGrubInstallConf(self, path, removableExists=False):
        stage1Devices = get_physical_devices(self.storage, self.storage.devicetree.getDeviceByName(self.device))
        bootDevices = get_physical_devices(self.storage, self.storage.storageset.bootDevice)

        stage1Path = get_partition_name(self.storage, stage1Devices[0], exists=removableExists)
        bootPartitionPath = get_partition_name(self.storage, bootDevices[0], exists=removableExists)

        batch_template = """root %s
setup %s
quit
""" % (bootPartitionPath, stage1Path)

        ctx.logger.debug("Writng Batch template to %s:\n%s" % (path, batch_template))
        file(path,'w').write(batch_template)


    def install(self):
        rc = yali.util.run_batch("grub", ["--no-floppy", "--batch < ", "/tmp/batch"])[0]
        yali.util.sync()
        return rc
