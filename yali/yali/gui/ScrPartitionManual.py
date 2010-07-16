# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2008, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#
import copy
import parted
import gettext

__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext


from PyQt4 import QtGui
from PyQt4.QtCore import *

import yali.gui.context as ctx
from yali.gui.YaliDialog import Dialog, QuestionDialog
from yali.gui.GUIException import *
from yali.gui.ScreenWidget import ScreenWidget

from yali.gui.GUIAdditional import DeviceTreeItem
from yali.gui.ManualPartition import PartitionEditor
from yali.gui.Ui.manualpartwidget import Ui_ManualPartWidget
from yali.storage.devices.device import devicePathToName
from yali.storage.devices.partition import Partition
from yali.storage.partitioning import doPartitioning, PartitioningError, PartitioningWarning
from yali.storage.storageBackendHelpers import doDeleteDevice, doClearPartitionedDevice


class Widget(QtGui.QWidget, ScreenWidget):
    title = _('Manual Partitioning')
    desc = _('You can easily configure your partitions...')
    icon = "iconPartition"
    help = _('''
<font size="+2">Partitioning your hard disk</font>
<font size="+1">
<p>
In this screen, you can manually partition your disk. You can select 
existing partitions and resize or delete them. You can create new 
partition(s) in the empty parts, make Pardus use them for system files, 
users' home directories, swap space or general use. The changes that you 
make will not be applied until you go on with the installation, 
which means you can revert if you make any unwanted changes or change your configuration.
</p>
<p>
Please refer to Pardus Installing and Using Guide for more information
about disk partitioning.
</p>
</font>
''')


    def __init__(self, *args):
        QtGui.QWidget.__init__(self,None)
        self.ui = Ui_ManualPartWidget()
        self.ui.setupUi(self)

        self.connect(self.ui.newButton, SIGNAL("clicked()"),self.createPartition)
        self.connect(self.ui.editButton, SIGNAL("clicked()"),self.editDevice)
        self.connect(self.ui.deleteButton, SIGNAL("clicked()"),self.deleteDevice)

    def shown(self):
        ctx.mainScreen.disableNext()
        self.storage = ctx.storage
        self.reset()


    # do the work and run requested actions on partitions.
    def execute(self):
        ctx.logger.info("Manual Partitioning selected...")
        ctx.mainScreen.processEvents()
        return True

    def backCheck(self):
        reply = QuestionDialog(_("Warning"),
                               _("All changes that you made will be removed."))

        if reply == "yes":
            self.devicetree.refreshDevices()
            return True
        return False

    def reset(self):
        self.storage.reset()
        self.refresh(justRedraw=True)

    def addDevice(self, device, item):
        format = device.format
        if format.formattable:
            formattable = Qt.Checked
        else:
            formattable = Qt.Unchecked

        if not format.exists:
            formatIcon = Qt.Checked
        else:
            formatIcon = Qt.Unchecked

        mountpoint = getattr(format, "mountpoint", "")
        if mountpoint is None:
            mountpoint = ""

        # device name
        name = getattr(device, "name", "")

        # label
        label = getattr(format, "label", "")
        if label is None:
            label = ""

        item.setDevice(device)
        item.setName(name)
        item.setMountpoint(mountpoint)
        item.setLabel(label)
        item.setType(format.name)
        item.setSize("%Ld" % device.size)
        item.setFormat(formatIcon)
        item.setFormattable(format.formattable)

    def populate(self):
        disks = self.storage.partitioned
        disks.sort(key=lambda d: d.name)
        # Disk&Partitions
        drivesItem = DeviceTreeItem(self.ui.deviceTree)
        drivesItem.setName(_("Hard Drives"))
        for disk in disks:
            diskItem = DeviceTreeItem(drivesItem)
            if disk.partitioned:
                partition = disk.format.firstPartition
                extendedItem = None
                while partition:
                    if partition.type & parted.PARTITION_METADATA:
                        partition = partition.nextPartition()
                        continue

                    partName = devicePathToName(partition.getDeviceNodeName())
                    device = self.storage.devicetree.getDeviceByName(partName)

                    if not device and not partition.type & parted.PARTITION_FREESPACE:
                        ctx.logger.debug("can't find partition %s in device tree" % partName)

                    if partition.getSize(unit="MB") <= 1:
                        if not partition.active or not partition.getFlag(parted.PARTITION_BOOT):
                            partition = partition.nextPartition()
                            continue

                    if device and device.isExtended:
                        if extendedItem:
                            raise RuntimeError, _("Can't handle more than "
                                                 "one extended partition per disk")
                        extendedItem = partItem = DeviceTreeItem(diskItem)
                        partitionItem = extendedItem

                    elif device and device.isLogical:
                        if not extendedItem:
                            raise RuntimeError, _("Crossed logical partition before extended")
                        partitionItem = DeviceTreeItem(extendedItem)

                    else:
                        partitionItem = DeviceTreeItem(diskItem)


                    if device and not device.isExtended:
                        self.addDevice(device, partitionItem)
                    else:
                        # either extended or freespace
                        if partition.type & parted.PARTITION_FREESPACE:
                            deviceName = _("Free")
                            deviceType = ""
                        else:
                            deviceName = device.name
                            deviceType = _("Extended")

                        partitionItem.setName(deviceName)
                        partitionItem.setType(deviceType)
                        size = partition.getSize(unit="MB")
                        if size < 1.0:
                            size = "< 1"
                        else:
                            size = "%Ld" % (size)
                        partitionItem.setSize(size)
                        partitionItem.setDevice(device)

                    partition = partition.nextPartition()
            else:
                self.__addDevice(disk, diskItem)

            self.ui.deviceTree.expandItem(diskItem)

    def refresh(self, justRedraw=None):
        ctx.logger.debug("refresh: justRedraw=%s" % justRedraw)
        self.ui.deviceTree.clear()
        if justRedraw:
            rc = 0
        else:
            try:
                doPartitioning(self.storage)
                rc = 0
            except PartitioningError, msg:
                ctx.yali.messageWindow(_("Error Partitioning"), _("Could not allocate requested partitions: %s.") % 
                                      (msg), customIcon="error")
                rc = -1
            except PartitioningWarning, msg:
                rc = ctx.yali.messageWindow(_("Warning Partitioning"), _("Warning: %s." % msg),
                        customButtons=[_("Modify Partition"), _("Continue")], customIcon="warning")
                if rc == 1:
                    rc = -1
                else:
                    rc = 0
                    all_devices = self.storage.devicetree.devices
                    bootDevs = [d for d in all_devices if d.bootable]

        if not rc == -1:
            self.populate()

        return rc


    def getCurrentDevice(self):
        return self.ui.deviceTree.currentItem().device

    def createPartition(self):
        # create new request of size 1M
        tempformat = self.storage.defaultFSType
        device = self.storage.newPartition(format_type=tempformat)
        self.editPartition(device, isNew=True)

    def editDevice(self, *args):
        device = self.getCurrentDevice()
        reason = self.storage.deviceImmutable(device, ignoreProtected=True)

        if reason:
            ctx.yali.messageWindow(_("Unable To Edit"),
                                   _("You cannot edit this device:\n\n%s")
                                    % reason,
                                    customIcon="error")
            return

        if isinstance(device, Partition):
            self.editPartition(device)

    def editPartition(self, device, isNew=False, restricts=None):
        partitionEditor = PartitionEditor(self, device, isNew=isNew, restricts=restricts)

        while True:
            origDevice = copy.copy(device)
            operations = partitionEditor.run()
            for operation in operations:
                self.storage.devicetree.addOperation(operation)

            if self.refresh(justRedraw=not operations):
                operations.reverse()
                for operation in operations:
                    self.storage.devicetree.removeOperation(operation)

                if not isNew:
                    device.req_size = orig_device.req_size
                    device.req_base_size = orig_device.req_base_size
                    device.req_grow = orig_device.req_grow
                    device.req_max_size = orig_device.req_max_size
                    device.req_primary = orig_device.req_primary
                    device.req_disks = orig_device.req_disks

                if self.refresh():
                    raise RuntimeError, ("Returning partitions to state "
                                         "prior to edit failed")
            else:
                break

        partitionEditor.destroy()

    def deleteDevice(self):
        device = self.getCurrentDevice()
        if device.partitioned:
            if doClearPartitionedDevice(ctx.yali, self.storage, device):
                self.refresh()
        elif doDeleteDevice(ctx.yali, self.storage, device):
            if isinstance(device, Partition):
                justRedraw = False
            else:
                justRedraw = True

            self.refresh(justRedraw=justRedraw)
