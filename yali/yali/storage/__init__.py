import parted
import gettext

__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext

import yali
import yali.util
from operations import *
from yali.gui import context as ctx
from yali.storage.devices.device import Device, DeviceError
from yali.storage.devices.partition import Partition
from yali.storage.formats import getFormat, get_default_filesystem_type
from yali.storage.devicetree import DeviceTree
from yali.storage.storageset import StorageSet


class StorageError(yali.Error):
    pass

def storageInitialize():
    raise NotImplementedError("storageInitialize method not implemented.")

def storageComplete():
    raise NotImplementedError("storageComplete method not implemented.")

class Storage(object):
    def __init__(self, ignoredDisks=[]):
        self._nextID = 0
        self.ignoredDisks = []
        self.exclusiveDisks = []
        self.doAutoPart = False
        self.clearPartType = None
        self.clearPartDisks = []
        self.clearPartChoice = None
        self.reinitializeDisks = False
        self.zeroMbr = None
        self.protectedDevSpecs = []
        self.autoPartitionRequests = []
        self.defaultFSType = get_default_filesystem_type()
        self.defaultBootFSType = get_default_filesystem_type(boot=True)
        self.eddDict = {}
        self.defaultFSType = get_default_filesystem_type()
        self.defaultBootFSType = get_default_filesystem_type(boot=True)
        self.devicetree = DeviceTree(ignored=self.ignoredDisks,
                                     exclusive=self.exclusiveDisks,
                                     type=self.clearPartType,
                                     clear=self.clearPartDisks,
                                     reinitializeDisks=self.reinitializeDisks,
                                     protected=self.protectedDevSpecs,
                                     zeroMbr=self.zeroMbr)
        self.storageset = StorageSet(self.devicetree, ctx.consts.target_dir)

    def compareDisks(self, first, second):
        if self.eddDict.has_key(first) and self.eddDict.has_key(second):
            one = self.eddDict[first]
            two = self.eddDict[second]
            if (one < two):
                return -1
            elif (one > two):
                return 1

        # if one is in the BIOS and the other not prefer the one in the BIOS
        if self.eddDict.has_key(first):
            return -1
        if self.eddDict.has_key(second):
            return 1

        if first.startswith("hd"):
            type1 = 0
        elif first.startswith("sd"):
            type1 = 1
        elif (first.startswith("vd") or first.startswith("xvd")):
            type1 = -1
        else:
            type1 = 2

        if second.startswith("hd"):
            type2 = 0
        elif second.startswith("sd"):
            type2 = 1
        elif (second.startswith("vd") or second.startswith("xvd")):
            type2 = -1
        else:
            type2 = 2

        if (type1 < type2):
            return -1
        elif (type1 > type2):
            return 1
        else:
            len1 = len(first)
            len2 = len(second)

            if (len1 < len2):
                return -1
            elif (len1 > len2):
                return 1
            else:
                if (first < second):
                    return -1
                elif (first > second):
                    return 1

        return 0

    def doIt(self):
        self.devicetree.processOperations()

        # now set the boot partition's flag
        try:
            boot = self.storageset.bootDevice
            bootDevs = [boot]
        except DeviceError:
            bootDevs = []
        else:
            for dev in bootDevs:
                if hasattr(dev, "bootable"):
                    skip = False
                    if dev.disk.format.partedDisk.type == "msdos":
                        for p in dev.disk.format.partedDisk.partitions:
                            if p.type == parted.PARTITION_NORMAL and \
                               p.getFlag(parted.PARTITION_BOOT):
                                skip = True
                                break
                    if skip:
                         ctx.logger.info("not setting boot flag on %s as there is"
                                  "another active partition" % dev.name)
                         continue
                    ctx.logger.info("setting boot flag on %s" % dev.name)
                    dev.bootable = True
                    dev.disk.setup()
                    dev.disk.format.commitToDisk()

    @property
    def nextID(self):
        id = self._nextID
        self._nextID += 1
        return id

    def reset(self):
        """ Reset storage configuration to reflect actual system state.

            This should rescan from scratch but not clobber user-obtained
            information like passphrases, iscsi config, &c

        """
        self.devicetree = DeviceTree(ignored=self.ignoredDisks,
                                     exclusive=self.exclusiveDisks,
                                     type=self.clearPartType,
                                     clear=self.clearPartDisks,
                                     reinitializeDisks=self.reinitializeDisks,
                                     protected=self.protectedDevSpecs,
                                     zeroMbr=self.zeroMbr)
        self.devicetree.populate()
        self.storageset = StorageSet(self.devicetree, ctx.consts.target_dir)
        self.eddDict = yali.util.get_edd_dict(self.partitioned)

    def deviceImmutable(self, device, ignoreProtected=False):
        """ Return any reason the device cannot be modified/removed.

            Return False if the device can be removed.

            Devices that cannot be removed include:

                - protected partitions
                - extended partition containing logical partitions that
                  meet any of the above criteria

        """
        if not isinstance(device, Device):
            raise ValueError("arg1 (%s) must be a Device instance" % device)

        if not ignoreProtected and device.protected:
            return _("This partition is holding the data for the hard "
                      "drive install.")
        elif isinstance(device, Partition) and device.isProtected:
            return _("You cannot delete a partition of a LDL formatted "
                     "DASD.")
        elif isinstance(device, Partition) and device.isExtended:
            reasons = {}
            for dep in self.deviceDeps(device):
                reason = self.deviceImmutable(dep)
                if reason:
                    reasons[dep.path] = reason
            if reasons:
                msg =  _("This device is an extended partition which "
                         "contains logical partitions that cannot be "
                         "deleted:\n\n")
                for dev in reasons:
                    msg += "%s: %s" % (dev, reasons[dev])
                return msg

        if device.immutable:
            return device.immutable

        return False

    @property
    def devices(self):
        """A list of all devices in the device tree."""
        devices =  self.devicetree.devices
        devices.sort(key=lambda d: d.name)
        return devices

    @property
    def drives(self):
        disks = self.disks
        partitioned = self.partitioned
        drives = [d.name for d in disks if d in partitioned]
        drives.sort(cmp=self.compareDisks)
        return drives

    @property
    def disks(self):
        """ A list of the disks in the device tree.

            Ignored disks are not included, as are disks with no media present.

            This is based on the current state of the device tree and
            does not necessarily reflect the actual on-disk state of the
            system's disks.
        """
        disks = []
        for device in self.devicetree.devices:
            if device.isDisk:
                if not device.mediaPresent:
                    ctx.logger.info("Skipping disk: %s: No media present" % device.name)
                    continue
                disks.append(device)
        disks.sort(key=lambda d: d.name, cmp=self.compareDisks)
        return disks

    def exceptionDisks(self):
        """ Return a list of removable devices to save exceptions to.

        """
        # When a usb is connected from before the start of the installation,
        # it is not correctly detected.
        udev_trigger(subsystem="block", action="change")
        self.reset()

        dests = []

        for disk in self.disks:
            if not disk.removable and \
                    disk.format is not None  and \
                    disk.format.mountable:
                dests.append([disk.path, disk.name])

        for part in self.partitions:
            if not part.disk.removable:
                continue

            elif part.partedPartition.active and \
                    not part.partedPartition.getFlag(parted.PARTITION_RAID) and \
                    not part.partedPartition.getFlag(parted.PARTITION_LVM) and \
                    part.format is not None and part.format.mountable:
                dests.append([part.path, part.name])

        return dests

    @property
    def partitions(self):
        """ A list of the partitions in the device tree.

            This is based on the current state of the device tree and
            does not necessarily reflect the actual on-disk state of the
            system's disks.
        """
        partitions = self.devicetree.getDevicesByInstance(Partition)
        partitions.sort(key=lambda d: d.name)
        return partitions

    @property
    def partitioned(self):
        """ A list of the partitioned devices in the device tree.

            Ignored devices are not included, nor disks with no media present.

            Devices of types for which partitioning is not supported are also
            not included.

            This is based on the current state of the device tree and
            does not necessarily reflect the actual on-disk state of the
            system's disks.
        """
        partitioned = []
        for device in self.devicetree.devices:
            if not device.partitioned:
                continue

            if not device.mediaPresent:
                ctx.logger.info("Skipping device: %s: No media present" % device.name)
                continue

            partitioned.append(device)

        partitioned.sort(key=lambda d: d.name)
        return partitioned

    @property
    def lvs(self):
        raise NotImplementedError("lvs method not implemented in Interface class.")

    @property
    def vgs(self):
        raise NotImplementedError("vgs method not implemented in Interface class.")

    @property
    def pvs(self):
        raise NotImplementedError("pvs method not implemented in Interface class.")

    @property
    def mdarrays(self):
        raise NotImplementedError("mdarrays method not implemented in Interface class.")

    @property
    def mdmembers(self):
        raise NotImplementedError("mdmembers method not implemented in Interface class.")

    @property
    def unusedPVS(self):
        raise NotImplementedError("unusedPVS method not implemented in Interface class.")

    @property
    def unusedRaidMembers(self):
        raise NotImplementedError("unusedRaidMembers method not implemented in Interface class.")

    @property
    def rootDevice(self):
        return self.storageset.rootDevice

    @property
    def swaps(self):
        """ A list of the swap devices in the device tree.

            This is based on the current state of the device tree and
            does not necessarily reflect the actual on-disk state of the
            system's disks.
        """
        devices = self.devicetree.devices
        swaps = [d for d in devices if d.format.type == "swap"]
        swaps.sort(key=lambda d: d.name)
        return swaps

    @property
    def mountpoints(self):
        return self.storageset.mountpoints

    def deviceDeps(self, device):
        return self.devicetree.getDependentDevices(device)

    @property
    def protectedDevices(self):
        devices = self.devicetree.devices
        protected = [d for d in devices if d.protected]
        protected.sort(key=lambda d: d.name)
        return protected

    def newPartition(self, *args, **kwargs):
        """ Return a new PartitionDevice instance for configuring. """
        if kwargs.has_key("fmt_type"):
            kwargs["format"] = getFormat(kwargs.pop("fmt_type"),
                                         mountpoint=kwargs.pop("mountpoint",None),
                                         **kwargs.pop("fmt_args", {}))

        if kwargs.has_key("disks"):
            parents = kwargs.pop("disks")
            if isinstance(parents, Device):
                kwargs["parents"] = [parents]
            else:
                kwargs["parents"] = parents

        if kwargs.has_key("name"):
            name = kwargs.pop("name")
        else:
            name = "req%d" % self.nextID

        return Partition(name, *args, **kwargs)

    def newVolumeGroup(self):
        raise NotImplementedError("newVolumeGroup method not implemented in Interface class.")

    def newLogicalVolume(self):
        raise NotImplementedError("newLogicalVolume method not implemented in Interface class.")

    def newRaidArray(self):
        raise NotImplementedError("newRaidArray method not implemented in Interface class.")

    def createDevice(self, device):
        """ Schedule creation of a device.

            TODO: We could do some things here like assign the next
                  available raid minor if one isn't already set.
        """
        self.devicetree.addOperation(OperationCreateDevice(device))
        if device.format.type:
            self.devicetree.addOperation(OperationCreateFormat(device))

    def destroyDevice(self, device):
        """ Schedule destruction of a device. """
        if device.format.exists and device.format.type:
            # schedule destruction of any formatting while we're at it
            self.devicetree.addOperation(OperationDestroyFormat(device))

        operation = OperationDestroyDevice(device)
        self.devicetree.addOperation(operation)

    def formatDevice(self, device, format):
        """ Schedule formatting of a device. """
        self.devicetree.addOperation(OperationDestroyFormat(device))
        self.devicetree.addOperation(OperationCreateFormat(device, format))

    def formatByDefault(self, device):
        """Return whether the device should be reformatted by default."""
        formatlist = ['/boot', '/var', '/tmp', '/usr']
        exceptlist = ['/home', '/usr/local', '/opt', '/var/www']

        if not device.format.linuxNative:
            return False

        if device.format.mountable:
            if not device.format.mountpoint:
                return False

            if device.format.mountpoint == "/" or \
               device.format.mountpoint in formatlist:
                return True

            for p in formatlist:
                if device.format.mountpoint.startswith(p):
                    for q in exceptlist:
                        if device.format.mountpoint.startswith(q):
                            return False
                    return True
        elif device.format.type == "swap":
            return True

        # be safe for anything else and default to off
        return False

    def turnOnSwap(self):
        self.storageset.turnOnSwap()

    def mountFilesystems(self, readOnly=None, skipRoot=False):
        self.storageset.mountFilesystems(readOnly=readOnly, skipRoot=skipRoot)

    def umountFilesystems(self, swapoff=True):
        self.storageset.umountFilesystems(swapoff=swapoff)

    def createSwapFile(self, device, size):
        self.storageset.createSwapFile(device, size)

    def raidConf(self):
        raise NotImplementedError("raidConf method not implemented in Interface class.")

    @property
    def extendedPartitionsSupported(self):
        """ Return whether any disks support extended partitions."""
        for disk in self.partitioned:
            if disk.format.partedDisk.supportsFeature(parted.DISK_TYPE_EXTENDED):
                return True
        return False

    def sanityCheck(self):
        """ Run a series of tests to verify the storage configuration.

            This function is called at the end of partitioning so that
            we can make sure you don't have anything silly (like no /,
            a really small /, etc).  Returns (errors, warnings) where
            each is a list of strings.
        """
        checkSizes = [('/usr', 250), ('/tmp', 50), ('/var', 384),
                      ('/home', 100), ('/boot', 75)]
        warnings = []
        errors = []

        mustbeonlinuxfs = ['/', '/var', '/tmp', '/usr', '/home', '/usr/share', '/usr/lib']
        mustbeonroot = ['/bin','/dev','/sbin','/etc','/lib','/root', '/mnt', 'lost+found', '/proc']

        filesystems = self.mountpoints
        root = self.storageset.rootDevice
        swaps = self.storageset.swapDevices

        try:
            boot = self.storageset.bootDevice
        except StorageError:
            boot = None

        if not root:
            errors.append(_("You have not defined a root partition (/),\n "
                            "which is required for installation of %s \n "
                            "to continue.") % (yali.util.product_name(),))

        if root and root.size < 250:
            warnings.append(_("Your root partition is less than 250 \n"
                              "megabytes which is usually too small to \n "
                              "install %s.") % (yali.util.product_name(),))

        if (root and
            root.size < ctx.consts.min_root_size):
            errors.append(_("Your / partition is less than %(min)s \n"
                            "MB which is lower than recommended \n"
                            "for a normal %(productName)s install.\n")
                          % {'min': ctx.consts.min_root_size,
                             'productName': yali.util.product_name()})

        for (mount, size) in checkSizes:
            if mount in filesystems and filesystems[mount].size < size:
                warnings.append(_("Your %(mount)s partition is less than \n"
                                  "%(size)s megabytes which is lower than \n"
                                  "recommended for a normal %(productName)s \n"
                                  "install.\n")
                                % {'mount': mount, 'size': size,
                                   'productName': yali.util.product_name()})


        errors.extend(self.storageset.checkBootRequest(boot))

        if not swaps:
            if yali.util.memInstalled() < yali.util.EARLY_SWAP_RAM:
                errors.append(_("You have not specified a swap partition.  \n"
                                "Due to the amount of memory present, a \n"
                                "swap partition is required to complete \n"
                                "installation."))
            else:
                warnings.append(_("You have not specified a swap partition.  \n"
                                  "Although not strictly required in all cases, \n"
                                  "it will significantly improve performance \n"
                                  "for most installations.\n"))

        for (mountpoint, dev) in filesystems.items():
            if mountpoint in mustbeonroot:
                errors.append(_("This mount point is invalid.  The %s directory must "
                                "be on the / file system.") % mountpoint)

            if mountpoint in mustbeonlinuxfs and (not dev.format.mountable or not dev.format.linuxNative):
                errors.append(_("The mount point %s must be on a linux file system.") % mountpoint)

        return (errors, warnings)

    def isProtected(self, device):
        """ Return True is the device is protected. """
        return device.protected

    def checkNoDisks(self, intf):
        """Check that there are valid disk devices."""
        if not self.disks:
            intf.messageWindow(_("No Drives Found"),
                               _("An error has occurred - no valid devices were "
                                 "found on which to create new file systems. "
                                 "Please check your hardware for the cause "
                                 "of this problem."))
            return True
        return False
