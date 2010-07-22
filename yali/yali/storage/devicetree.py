#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import parted
import gettext

__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext

import yali
import yali.gui.context as ctx
import formats
from udev import *
from partitioning import shouldClear, CLEARPART_TYPE_ALL, CLEARPART_TYPE_LINUX, CLEARPART_TYPE_NONE
from devices.device import DeviceNotFoundError, deviceNameToDiskByPath
from devices.nodevice import NoDevice
from devices.disk import Disk
from devices.partition import Partition
from formats.disklabel import InvalidDiskLabelError
from formats.filesystem import FilesystemError
from operations import *

class DeviceTreeError(yali.Error):
    pass

class DeviceTree(object):
    def __init__(self, ignored=[], exclusive=[], type=CLEARPART_TYPE_NONE,
                 clear=[],zeroMbr=None, reinitializeDisks=None, protected=[]):
        self._devices = []
        self.operations = []
        self.exclusiveDisks = exclusive
        self.clearPartType = type
        self.clearPartDisks = clear
        self.zeroMbr = zeroMbr
        self.reinitializeDisks = reinitializeDisks

        # protected device specs as provided by the user
        self.protectedDevSpecs = protected

        # names of protected devices at the time of tree population
        self.protectedDevNames = []

        self._ignoredDisks = []
        for disk in ignored:
            self.addIgnoredDisk(disk)

        self._populated = False

    def addIgnoreDisk(self, disk):
        self._ignoredDisks.append(disk)

    def isIgnored(self, info):
        sysfs_path = udev_device_get_sysfs_path(info)
        name = udev_device_get_name(info)
        if not sysfs_path:
            return None

        if name in self._ignoredDisks:
            return True

        # Special handling for mdraid external metadata sets (mdraid BIOSRAID):
        # 1) The containers are intermediate devices which will never be
        # in exclusiveDisks
        # 2) Sets get added to exclusive disks with their dmraid set name by
        # the filter ui.  Note that making the ui use md names instead is not
        # possible as the md names are simpy md# and we cannot predict the #
        if udev_device_get_md_level(info) == "container":
            return False

        if udev_device_get_md_container(info) and \
               udev_device_get_md_name(info):
            md_name = udev_device_get_md_name(info)
            for i in range(0, len(self.exclusiveDisks)):
                if re.match("isw_[a-z]*_%s" % md_name, self.exclusiveDisks[i]):
                    self.exclusiveDisks[i] = name
                    return False

        if udev_device_is_disk(info) and \
                not udev_device_is_md(info) and \
                not udev_device_is_dm(info) and \
                not udev_device_is_biosraid(info) and \
                not udev_device_is_multipath_member(info):
            if self.exclusiveDisks and name not in self.exclusiveDisks:
                self.addIgnoredDisk(name)
                return True

        # Ignore loop and ram devices, we normally already skip these in
        # udev.py: enumerate_block_devices(), but we can still end up trying
        # to add them to the tree when they are slaves of other devices, this
        # happens for example with the livecd
        if name.startswith("loop") or name.startswith("ram"):
            return True

    def _addDevice(self, device):
        """ Add a device to the tree.

            Raise ValueError if the device's identifier is already in the list.
        """
        if device.path in [d.path for d in self._devices] and \
           not isinstance(newdev, NoDevice):
            raise ValueError("device is already in tree")

        # make sure this device's parent devices are in the tree already
        for parent in device.parents:
            if parent not in self._devices:
                raise DeviceTreeError("parent device not in tree")

        self._devices.append(device)
        ctx.logger.debug("added %s %s (id %d) to device tree" % (device.type, device.name, device.id))

    def _removeDevice(self, device, force=None):
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

            # adjust all other Partition instances belonging to the
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

    def addOperation(self, operation):
        """ Register an operation to be performed at a later time.

        """
        if (operation.isDestroy() or operation.isResize() or \
            (operation.isCreate() and operation.isFormat())) and \
           operation.device not in self._devices:
            raise DeviceTreeError("device is not in the tree")
        elif (operation.isCreate() and operation.isDevice()):
            if operation.device in self._devices:
                self._removeDevice(operation.device)
            for d in self._devices:
                if d.path == operation.device.path:
                    self._removeDevice(d)

        if operation.isCreate() and operation.isDevice():
            self._addDevice(operation.device)
        elif operation.isDestroy() and operation.isDevice():
            self._removeDevice(operation.device)
        elif operation.isCreate() and operation.isFormat():
            if isinstance(operation.device.format, formats.filesystem.Filesystem) and \
               operation.device.format.mountpoint in self.filesystems:
                raise DeviceTreeError("mountpoint already in use")

        ctx.logger.debug("registered operation: %s" % operation)
        self.operations.append(operation)

    def removeOperation(self, operation):
        """ Cancel a registered operation.

        """
        if operation.isCreate() and operation.isDevice():
            # remove the device from the tree
            self._removeDevice(operation.device)
        elif operation.isDestroy() and operation.isDevice():
            # add the device back into the tree
            self._addDevice(operation.device)
        elif operation.isFormat() and \
             (operation.isCreate() or operation.isMigrate() or operation.isResize()):
            operation.cancel()

        self.operations.remove(operation)

    def findOperations(self, device=None, type=None, object=None, path=None, devid=None):
        """ Find all operations that match all specified parameters.

            Keyword arguments:

                device -- device to match (Device, or None to match any)
                type -- operation type to match (string, or None to match any)
                object -- operand type to match (string, or None to match any)
                path -- device path to match (string, or None to match any)

        """
        if device is None and type is None and object is None and \
           path is None and devid is None:
            return self.operations[:]

        # convert the string arguments to the types used in operations
        _type = operation_type_from_string(type)
        _object = operation_object_from_string(object)

        operations = []
        for operation in self.operations:
            if device is not None and operation.device != device:
                continue

            if _type is not None and operation.type != _type:
                continue

            if _object is not None and operation.obj != _object:
                continue

            if path is not None and operation.device.path != path:
                continue

            if devid is not None and operation.device.id != devid:
                continue

            operations.append(operation)

        return operations

    def processOperation(self):
        ctx.logger.debug("resetting parted disks...")
        for device in self.devices:
            if device.partitioned:
                device.format.resetPartedDisk()
                if device.originalFormat.type == "disklabel" and \
                   device.originalFormat != device.format:
                    device.originalFormat.resetPartedDisk()

        # Call preCommitFixup on all devices
        mpoints = [getattr(d.format, 'mountpoint', "") for d in self.devices]
        for device in self.devices:
            device.preCommitFixup(mountpoints=mpoints)

        # Also call preCommitFixup on any devices we're going to
        # destroy (these are already removed from the tree)
        for operation in self.operations:
            if isinstance(operation, OperationDestroyDevice):
                operation.device.preCommitFixup(mountpoints=mpoints)

        # setup operations to create any extended partitions we added
        #
        # XXX At this point there can be duplicate partition paths in the
        #     tree (eg: non-existent sda6 and previous sda6 that will become
        #     sda5 in the course of partitioning), so we access the list
        #     directly here.
        for device in self._devices:
            if isinstance(device, Partition) and \
               device.isExtended and not device.exists:
                # don't properly register the operation since the device is
                # already in the tree
                self.operations.append(OperationsreateDevice(device))

        for operation in self.operations:
            ctx.logger.debug("operation: %s" % operation)

        #ctx.logger.debug("pruning operation queue...")
        #self.pruneOperations()
        #for operation in self.operations:
        #    log.debug("operation: %s" % operation)

        #log.debug("sorting operations...")
        #self.operations.sort(cmp=cmpOperations)
        #for operation in self.operations:
        #    ctx.logger.debug("operation: %s" % operation)

        for operation in self.operations:
            ctx.logger.info("executing operation: %s" % operation)
            if not dryRun:
                try:
                    operation.execute(intf=self.intf)
                except DiskLabelCommitError:
                    # it's likely that a previous format destroy operation
                    # triggered setup of an lvm or md device.
                    self.teardownAll()
                    operation.execute(intf=self.intf)

                udev_settle()
                for device in self._devices:
                    # make sure we catch any renumbering parted does
                    if device.exists and isinstance(device, PartitionDevice):
                        device.updateName()
                        device.format.device = device.path

    def addPartitionDevice(self, info, disk=None):
        name = udev_device_get_name(info)
        uuid = udev_device_get_uuid(info)
        sysfs_path = udev_device_get_sysfs_path(info)
        device = None

        if disk is None:
            disk_name = os.path.basename(os.path.dirname(sysfs_path))
            disk_name = disk_name.replace('!','/')
            disk = self.getDeviceByName(disk_name)

        if disk is None:
            # create a device instance for the disk
            new_info = udev_get_block_device(os.path.dirname(sysfs_path))
            if new_info:
                self.addDevice(new_info)
                disk = self.getDeviceByName(disk_name)

            if disk is None:
                # if the current device is still not in
                # the tree, something has gone wrong
                ctx.logger.error("failure scanning device %s" % disk_name)
                return

        # Check that the disk has partitions. If it does not, we must have
        # reinitialized the disklabel.
        #
        # Also ignore partitions on devices we do not support partitioning
        # of, like logical volumes.
        if not getattr(disk.format, "partitions", None) or \
           not disk.partitionable:
            # When we got here because the disk does not have a disklabel
            # format (ie a biosraid member), or because it is not
            # partitionable we want LVM to ignore this partition too
            if disk.format.type != "disklabel" or not disk.partitionable:
                pass
            ctx.logger.debug("ignoring partition %s" % name)
            return

        try:
            device = Partition(name, sysfsPath=sysfs_path,
                               major=udev_device_get_major(info),
                               minor=udev_device_get_minor(info),
                               exists=True, parents=[disk])
        except DeviceTreeError:
            # corner case sometime the kernel accepts a partition table
            # which gets rejected by parted, in this case we will
            # prompt to re-initialize the disk, so simply skip the
            # faulty partitions.
            return

        self._addDevice(device)
        return device

    def addDiskDevice(self, info):
        name = udev_device_get_name(info)
        uuid = udev_device_get_uuid(info)
        sysfs_path = udev_device_get_sysfs_path(info)
        serial = udev_device_get_serial(info)
        bus = udev_device_get_bus(info)

        # udev doesn't always provide a vendor.
        vendor = udev_device_get_vendor(info)
        if not vendor:
            vendor = ""

        device = None

        kwargs = { "serial": serial, "vendor": vendor, "bus": bus }
        ctx.logger.debug("%s is a disk" % name)

        device = Disk(name,
                      major=udev_device_get_major(info),
                      minor=udev_device_get_minor(info),
                      sysfsPath=sysfs_path, **kwargs)

        self._addDevice(device)
        return device

    def addDevice(self, info):
        name = udev_device_get_name(info)
        uuid = udev_device_get_uuid(info)
        sysfs_path = udev_device_get_sysfs_path(info)

        if self.isIgnored(info):
            ctx.logger.debug("ignoring %s (%s)" % (name, sysfs_path))
            return

        ctx.logger.debug("scanning %s (%s)..." % (name, sysfs_path))
        device = self.getDeviceByName(name)
        if udev_device_is_disk(info):
            if device is None:
                device = self.addDiskDevice(info)
        elif udev_device_is_partition(info):
            ctx.logger.debug("%s is a partition" % name)
            if device is None:
                device = self.addPartitionDevice(info)
        else:
            ctx.logger.error("Unknown block device type for: %s" % name)
            return

        if not device or not device.mediaPresent:
            return

        self.handleFormat(info, device)
        ctx.logger.debug("got device: %s" % device)
        if device.format.type:
            ctx.logger.debug("got format: %s" % device.format)
        device.originalFormat = device.format

    def handleFormat(self, info, device):
        name = udev_device_get_name(info)
        sysfs_path = udev_device_get_sysfs_path(info)
        uuid = udev_device_get_uuid(info)
        label = udev_device_get_label(info)
        fmt_type = udev_device_get_format(info)
        serial = udev_device_get_serial(info)

        if not udev_device_is_biosraid(info) and \
           not udev_device_is_multipath_member(info):
            self.handleDiskLabelFormat(info, device)
            if device.partitioned or self.isIgnored(info) or \
               (not device.partitionable and
                device.format.type == "disklabel"):
                # If the device has a disklabel, or the user chose not to
                # create one, we are finished with this device. Otherwise
                # it must have some non-disklabel formatting, in which case
                # we fall through to handle that.
                return

        format = None
        if (not device) or (not fmt_type) or device.format.type:
            # this device has no formatting or it has already been set up
            # FIXME: this probably needs something special for disklabels
            ctx.logger.debug("no type or existing type for %s, bailing" % (name,))
            return

        # set up the common arguments for the format constructor
        args = [fmt_type]
        kwargs = {"uuid": uuid,
                  "label": label,
                  "device": device.path,
                  "serial": serial,
                  "exists": True}
        if fmt_type == "vfat":
            if isinstance(device, Partition) and device.bootable:
                efi = formats.getFormat("efi")
                if efi.minSize <= device.size <= efi.maxSize:
                    args[0] = "efi"
        try:
            ctx.logger.debug("type detected on '%s' is '%s'" % (name, fmt_type,))
            device.format = formats.getFormat(*args, **kwargs)
        except FilesystemError:
            ctx.logger.debug("type '%s' on '%s' invalid, assuming no format" %
                      (fmt_type, name,))
            device.format = formats.Format()
            return

        if shouldClear(device, self.clearPartType, clearPartDisks=self.clearPartDisks):
            # if this is a device that will be cleared by clearpart,
            # don't bother with format-specific processing
            return

    def handleDiskLabelFormat(self, info, device):
        if udev_device_get_format(info):
            ctx.logger.debug("device %s does not contain a disklabel" % device.name)
            return

        if device.partitioned:
            # this device is already set up
            ctx.logger.debug("disklabel format on %s already set up" % device.name)
            return

        try:
            device.setup()
        except Exception as e:
            ctx.logger.debug("setup of %s failed: %s" % (device.name, e))
            ctx.logger.warning("aborting disklabel handler for %s" % device.name)
            return

        # special handling for unsupported partitioned devices
        if not device.partitionable:
            try:
                format = formats.getFormat("disklabel",
                                   device=device.path,
                                   exists=True)
            except InvalidDiskLabelError:
                pass
            else:
                if format.partitions:
                    # parted's checks for disklabel presence are less than
                    # rigorous, so we will assume that detected disklabels
                    # with no partitions are spurious
                    device.format = format
            return

        # if the disk contains protected partitions we will not wipe the
        # disklabel even if clearpart --initlabel was specified
        if not self.clearPartDisks or device.name in self.clearPartDisks:
            initlabel = self.reinitializeDisks
            sysfs_path = udev_device_get_sysfs_path(info)
            for protected in self.protectedDevNames:
                # check for protected partition
                _p = "/sys/%s/%s" % (sysfs_path, protected)
                if os.path.exists(os.path.normpath(_p)):
                    initlabel = False
                    break

                # check for protected partition on a device-mapper disk
                disk_name = re.sub(r'p\d+$', '', protected)
                if disk_name != protected and disk_name == device.name:
                    initlabel = False
                    break
        else:
            initlabel = False

        if self.zeroMbr:
            initcb = lambda: True
        else:
            description = device.description or device.model
            try:
                bypath = os.path.basename(deviceNameToDiskByPath(device.name))
                details = "\n\nDevice details:\n%s" % (bypath,)
            except DeviceNotFoundError:
                # some devices don't have a /dev/disk/by-path/ #!@#@!@#
                bypath = device.name
                details = ""
            def questionInitializeDisk(path, description, size, details):
                if ctx.yali:
                    rc = ctx.yali.messageWindow(_("Warning"),
                                                  _("Error processing drive:\n\n"
                                                    "%(path)s\n%(size)-0.fMB\n%(description)s\n\n"
                                                    "This device may need to be reinitialized.\n\n"
                                                    "REINITIALIZING WILL CAUSE ALL DATA TO BE LOST!\n\n"
                                                    "This operation may also be applied to all other disks "
                                                    "needing reinitialization.%(details)s")
                                                    % {'path': path, 'size': size,
                                                       'description': description, 'details': details},
                                                    type="custom",
                                                    customButtons = [_("Ignore"), _("Ignore all"),
                                                                     _("Re-initialize"), ("Re-initialize all") ],
                                                    customIcon="question")
                    if rc == 0:
                        return False
                    elif rc == 1:
                        return False
                    elif rc == 2:
                        return True
                    elif rc == 3:
                        return True
                else:
                    return True


            initcb = lambda: self.intf.questionInitializeDisk(bypath,
                                                              description,
                                                              device.size,
                                                              details)

        try:
            format = formats.getFormat("disklabel",
                               device=device.path,
                               exists=not initlabel)
        except InvalidDiskLabelError:
            # if there is preexisting formatting on the device we will
            # use it instead of ignoring the device
            if not self.zeroMbr and \
               formats.getFormat(udev_device_get_format(info)).type is not None:
                return
            # if we have a cb function use it. else we ignore the device.
            if initcb is not None and initcb():
                format = formats.getFormat("disklabel",
                                   device=device.path,
                                   exists=False)
            else:
                self._removeDevice(device)
                self.addIgnoredDisk(device.name)
                return

        if not format.exists:
            # if we just initialized a disklabel we should schedule
            # operations for destruction of the previous format and creation
            # of the new one
            self.addOperation(OperationDestroyFormat(device))
            self.addOperation(OperationCreateFormat(device, format))

            # If this is a mac-formatted disk we just initialized, make
            # sure the partition table partition gets added to the device
            # tree.
            if device.format.partedDisk.type == "mac" and \
               len(device.format.partitions) == 1:
                name = device.format.partitions[0].getDeviceNodeName()
                if not self.getDeviceByName(name):
                    partition = Partition(name, exists=True, parents=[device])
                    self._addDevice(partition)

        else:
            device.format = format

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

        # First iteration - let's just look for disks.
        old_devices = {}

        devices = udev_get_block_devices()
        ctx.logger.info("devices to scan: %s" % [d['name'] for d in devices])
        for dev in devices:
            self.addDevice(dev)

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

    def getDeviceByName(self, name):
        ctx.logger.debug("looking for device '%s'..." % name)
        if not name:
            return None

        found = None
        for device in self._devices:
            if device.name == name:
                found = device
                break

        ctx.logger.debug("found %s" % found)
        return found

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
            if device.path in [d.path for d in devices] and \
               not isinstance(device, NoDevice):
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
