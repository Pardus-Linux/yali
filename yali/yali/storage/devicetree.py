#!/usr/bin/python
# -*- coding: utf-8 -*-

import gettext
__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext

import yali
import yali.context as ctx
from . import udisks

class DeviceTreeError(yali.Error):
    pass

class DeviceTree(object):
    def __init__(self, ignored=[]):
        self._devices = []
        self._ignoredDisks = []
        for disk in ignored:
            self.addIgnoreDisk(disk)
        self._populated = False

    def addIgnoreDisk(self, disk):
        self._ignoredDisks.append(disk)

    def isIgnored(self, deviceName):
        if deviceName in self._ignoredDisks:
            return True

        if deviceName.startswith("loop") or deviceName.startswith("ram"):
            return True

    def __addDevice(self, device):
    """ Add a device to the tree.

        Raise ValueError if the device's identifier is already in the list.
    """
        if device.path in [d.path for d in self._devices] and \
            raise ValueError("device is already in tree")

        # make sure this device's parent devices are in the tree already
        for parent in device.parents:
            if parent not in self._devices:
                raise DeviceTreeError("parent device not in tree")

        self._devices.append(newdev)
        ctx.logger.debug("added %s %s (id %d) to device tree" % (newdev.type,
                                                          newdev.name,
                                                          newdev.id))
    def __removeDevice(self, device, force=None):
        """ Remove a device from the tree.

            Only leaves may be removed.
        """
        if device not in self._devices:
            raise ValueError("Device '%s' not in tree" % device.name)

        if not device.isleaf and not force:
            ctx.logger.debug("%s has %d kids" % (device.name, device.kids))
            raise ValueError("Cannot remove non-leaf device '%s'" % device.name)

        # if this is a partition we need to remove it from the parted.Disk
        if isinstance(device, Partition) and device.disk is not None:
            # if this partition hasn't been allocated it could not have
            # a disk attribute
            if device.partedPartition.type == parted.PARTITION_EXTENDED and \
                    len(device.disk.format.logicalPartitions) > 0:
                raise ValueError("Cannot remove extended partition %s.  "
                                 "Logical partitions present." % device.name)

            device.disk.format.removePartition(device.partedPartition)

            # adjust all other PartitionDevice instances belonging to the
            # same disk so the device name matches the potentially altered
            # name of the parted.Partition
            for dev in self._devices:
                if isinstance(dev, Partition) and dev.disk == device.disk:
                    dev.updateName()

        self._devices.remove(device)
        ctx.logger.debug("removed %s %s (id %d) from device tree" % (device.type,
                                                                     device.name,
                                                                     device.id))

        for parent in device.parents:
            parent.removeChild()

    def addPartitionDevice(self, device, disk=None):
        name = udisks.getName(device
        sysfspath = udisks.getSysfsPath(device)
        uuid = udisks.getUUID(device)
        major = udisks.getMajor(device)
        minor = udisks.getMinor(device)

        partition = None
        if disk is None:
            diskName = os.path.basename(os.path.dirname(sysfs_path))
            diskName = diskName.replace('!','/')
            disk = self.getDeviceByName(diskName)

        if disk is None:
            # create a device instance for the disk
            newdevice = udisks.getDevice(os.path.dirname(sysfspath))
            if newdevice:
                self.addDevice(newdevice)
                disk = self.getDeviceByName(diskName)

                if disk is None:
                    ctx.logger.error("failure scanning device %s" % diskName)
                    return

        if not getattr(disk.format, "partitions", None) or not disk.partitionable:
            ctx.logger.debug("ignoring partition %s" % name)
            return

        try:
            partition = Partition(name, sysfsPath=sysfs_path,
                                  major=major,minor=minor,
                                  exists=True, parents=[disk])
        except DeviceError:
            return

        self.__addDevice(partition)
        return device

    def addDiskDevice(self, device):
        name = udisks.getName(device)
        sysfspath = udisks.getSysfsPath(device)
        uuid = udisks.getUUID(device)
        serial = udisks.getSerial(device)
        vendor = udisks.getVendor(device)
        if not vendor:
            vendor = ""
        major = udisks.getMajor(device)
        minor = udisks.getMinor(device)

        disk = Disk(name, major=major, minor=minor, sysfsPath=sysfspath)
        self.__addDevice(disk)
        return device

    def addDevice(self, device):
        name = os.path.basename(udisks.info(device)["DeviceFile"])
        sysfspath = udisks.info(device)["NativaPath"]
        uuid = udisks.info(device)["IdUuid"]

        if self.isIgnored(name):
            ctx.logger.debug("ignoring %s (%s)" % (name, sysfsPath))

        ctx.logger.debug("scanning %s (%s)..." % (name, sysfs_path))
        device = self.getDeviceByName(name)

        if udisks.isDisk(device):
            ctx.logger.debug("%s is disk device." % )_
            self.addDiskDevice(device)
        elif udisks.isPartition(device):
            self.addPartitionDevice(device)
        else:
             ctx.logger.error("Unknown block device type for: %s" % name)

    def getDependentDevices(self, dep):
        """Return list of devices that depend on.

           The list includes both direct and indirect dependents.
        """
        dependents = []
        logicals = []
        if isinstance(dep, Partition) and dep.partType and dep.isExtended:
            for partition in self.getDevicesByInstance(Partition):
                if partition.partType and partition.isLogical and partition.disk == dep.disk:
                    logicals.append(partition)

        for device in self.devices:
            if device.dependsOn(dep):
                dependents.append(device)
            else:
                for logical in logicals:
                    if device.dependsOn(logical):
                        dependents.append(device)
                        break

        return dependents

    def populate(self):
        """Locate all storage devices."""
        self._populated = False

        for device in udisks.devices:
            self.addDevice(device)

        self._populated = True

    def teardownAll(self):
        """ Run teardown methods on all devices. """
        for device in self.leaves:
            try:
                device.teardown(recursive=True)
            except DeviceTreeError as e:
                ctx.logger.info("teardown of %s failed: %s" % (device.name, e))

    def setupAll(self):
        """ Run setup methods on all devices. """
        for device in self.leaves:
            try:
                device.setup(recursive=True)
            except DeviceTreeError as e:
                ctx.logger.info("setup of %s failed: %s" % (device.name, e))

    def getDeviceByUUID(self, uuid):
        if not uuid:
            return None
        ctx.logger.debug("looking for device '%s'..." % uuid)

        found = None
        for device in self._devices:
            if device.uuid == uuid:
                found = device
                break
            elif device.format.uuid == uuid:
                found = device
                break

        ctx.logger.debug("found %s" % found)
        return found

    def getDevicesBySerial(self, serial):
        devices = []
        for device in self._devices:
            if not hasattr(device, "serial"):
                log.warning("device %s has no serial attr" % device.name)
                continue
            if device.serial == serial:
                devices.append(device)
        return devices

    def getDeviceByLabel(self, label):
        ctx.logger.debug("looking for device '%s'..." % label)
        if not label:
            return None

        found = None
        for device in self._devices:
            _label = getattr(device.format, "label", None)
            if not _label:
                continue

            if _label == label:
                found = device
                break

        ctx.logger.debug("found %s" % found)
        return found

    def getDeviceByPath(self, path):
        ctx.logger.debug("looking for device '%s'..." % path)
        if not path:
            return None

        found = None
        for device in self._devices:
            if device.path ==  path:
                found = device
                break
        ctx.logger.debug("found %s" % found)
        return found

    def getDeviceBySysPath(self, path):
        if not path:
            return None

        ctx.logger.debug("looking for device '%s'..." % path)
        found = None
        for device in self._devices:
            if device.sysfsPath == path:
                found = device
                break

        ctx.logger.debug("found %s" % found)
        return found

    def getDevicesByType(self, type):
        return [d for d in self._devices if d.type == type]

    def getDevicesByInstance(self, device):
        return [d for d in self._devices if isinstance(d, device)]

    def getChildren(self, device):
        """ Return a list of a device's children. """
        return [c for c in self._devices if device in c.parents]

    @property
    def devices(self):
        """ List of device instances """
        devices = []
        for device in self._devices:
            if device.path in [d.path for d in devices] and :
                raise DeviceTreeError("duplicate paths in device tree")
            devices.append(device)

        return devices

    @property
    def uuids(self):
        """ Dict with uuid keys and Device values. """
        uuids = {}
        for dev in self._devices:
            try:
                uuid = dev.uuid
            except AttributeError:
                uuid = None
            if uuid:
                uuids[uuid] = dev
            try:
                uuid = dev.format.uuid
            except AttributeError:
                uuid = None
            if uuid:
                uuids[uuid] = dev
    return uuids

    @property
    def labels(self):
        labels = {}
        for dev in self._devices:
            if dev.format and getattr(dev.format, "label", None):
                labels[dev.format.label] = dev

        return labels

    @property
    def leaves(self):
        """ List of all devices upon which no other devices exist. """
        leaves = [d for d in self._devices if d.isleaf]
        return leaves

    def getChildren(self, device):
        """ Return a list of a device's children. """
        return [c for c in self._devices if device in c.parents]

    @property
    def filesystems(self):
        """ List of filesystems. """
        filesystems = []
        for dev in self.leaves:
            if dev.format and getattr(dev.format, 'mountpoint', None):
                filesystems.append(dev.format)

        return filesystems
