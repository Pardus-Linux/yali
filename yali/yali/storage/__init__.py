
import gettext
__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext

import yali
import yali.util
from devices.partition import Partition
from formats import getFormat

class StorageError(yali.Error):
    pass

def storageInitialize():
    raise NotImplementedError("storageInitialize method not implemented.")

def storageComplete():
    raise NotImplementedError("storageComplete method not implemented.")


class Interface(object):
    def __init__(self, ignoredDisk=[]):
        self.eddDict = yali.util.get_edd_dict(self.partitioned)
        self._nextID = 0
        self.devicetree = DeviceTree(ignoredDisk)
        self.devicetree.populate()

    def __compareDisks(self, first, second):
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
        self.devicetree = DeviceTree(ignored=self.ignoredDisks)
        self.devicetree.populate()
        self.eddDict = get_edd_dict(self.partitioned)

    def deviceImmutable(self, device, ignoreProtected=False):
        """ Return any reason the device cannot be modified/removed.

            Return False if the device can be removed.

            Devices that cannot be removed include:

                - protected partitions
                - devices that are part of an md array or lvm vg
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
        disks.sort(key=lambda d: d.name, cmp=self.__compareDisks)
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
    def mountpoints(self):
        pass

    def deviceDeps(self, device):
        return self.devicetree.getDependentDevices(device)

    def newPartition(self, *args, **kwargs):
        """ Return a new PartitionDevice instance for configuring. """
        if kwargs.has_key("format_type"):
            kwargs["format"] = getFormat(kwargs.pop("format_type"),
                                         mountpoint=kwargs.pop("mountpoint",None),
                                         **kwargs.pop("format_args", {}))

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

    def createDevice(self):
        pass

    def destroyDevice(self):
        pass

    def mountFilesystems(self):
        pass

    def umountFilesystems(self):
        pass

    def fstab(self):
        pass

    def createSwapFile(self):
        pass

    def raidConf(self):
        raise NotImplementedError("raidConf method not implemented in Interface class.")

    @property
    def extendedPartitionsSupported(self):
        """ Return whether any disks support extended partitions."""
        for disk in self.partitioned:
            if disk.format.partedDisk.supportsFeature(parted.DISK_TYPE_EXTENDED):
                return True
        return False
