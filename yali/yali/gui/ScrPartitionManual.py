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

import yali.util
import yali.context as ctx
from yali.gui.YaliDialog import Dialog, QuestionDialog
from yali.gui.ScreenWidget import ScreenWidget

from yali.gui.partition_gui import PartitionEditor
from yali.gui.lvm_gui import LVMEditor
from yali.gui.Ui.manualpartwidget import Ui_ManualPartWidget
from yali.gui.Ui.createdevicewidget import Ui_CreateDeviceWidget
from yali.storage.library import lvm
from yali.storage.devices.device import devicePathToName, Device
from yali.storage.devices.partition import Partition
from yali.storage.partitioning import doPartitioning, hasFreeDiskSpace, PartitioningError, PartitioningWarning
from yali.storage.storageBackendHelpers import doDeleteDevice, doClearPartitionedDevice, checkForSwapNoMatch, getPreExistFormatWarnings, confirmResetPartitionState

partition, volumeGroup, logicalVolume, physicalVolume, raidMember, raidArray = range(6)

class CreateDeviceWidget(QtGui.QWidget, Ui_CreateDeviceWidget):
    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)
        self.parent = parent
        self.setupUi(self)
        self.connect(self.partition, SIGNAL("clicked()"), self.clickedButton)
        self.connect(self.volumeGroup, SIGNAL("clicked()"), self.clickedButton)
        self.connect(self.logicalVolume, SIGNAL("clicked()"), self.clickedButton)
        self.connect(self.physicalVolume, SIGNAL("clicked()"), self.clickedButton)
        self.connect(self.raidMember, SIGNAL("clicked()"), self.clickedButton)
        self.connect(self.raidArray, SIGNAL("clicked()"), self.clickedButton)
        self.connect(self.buttonBox, SIGNAL("accepted()"), self.parent.accept)
        self.connect(self.buttonBox, SIGNAL("rejected()"), self.parent.reject)
        self.rc = None

    def clickedButton(self):
        if self.sender() == self.partition:
            self.rc = partition
        elif self.sender() == self.volumeGroup:
            self.rc = volumeGroup
        elif self.sender() == self.logicalVolume:
            self.rc = logicalVolume
        elif self.sender() == self.physicalVolume:
            self.rc = physicalVolume
        elif self.sender() == self.raidMember:
            self.rc = raidMember
        elif self.sender() == self.raidArray:
            self.rc = raidArray

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
        self.storage = ctx.storage
        self.intf = ctx.interface

        self.connect(self.ui.newButton, SIGNAL("clicked()"),self.createDevice)
        self.connect(self.ui.editButton, SIGNAL("clicked()"),self.editDevice)
        self.connect(self.ui.deleteButton, SIGNAL("clicked()"),self.deleteDevice)
        self.connect(self.ui.resetButton, SIGNAL("clicked()"),self.reset)
        self.connect(self.ui.deviceTree, SIGNAL("itemClicked(QTreeWidgetItem *, int)"), self.activateButtons)

    def shown(self):
        checkForSwapNoMatch(self.intf, self.storage)
        self.populate()
        (errors, warnings) =  self.storage.sanityCheck()
        if errors or warnings:
            ctx.mainScreen.disableNext()
        else:
            ctx.mainScreen.enableNext()

    def execute(self):
        ctx.logger.info("Manual Partitioning selected...")
        ctx.mainScreen.processEvents()
        check = self.nextCheck()
        if not check:
            ctx.mainScreen.enableBack()
        elif check is None:
            ctx.mainScreen.enableNext()
        return check

    def update(self):
        if self.storage.storageset.rootDevice:
            ctx.mainScreen.enableNext()
        else:
            ctx.mainScreen.disableNext()

    def activateButtons(self, item, index):
        if item and item.device is not None and isinstance(item.device, Device):
            self.ui.editButton.setEnabled(True)
            self.ui.deleteButton.setEnabled(True)
        else:
            self.ui.editButton.setEnabled(False)
            self.ui.deleteButton.setEnabled(False)

    def nextCheck(self):
        (errors, warnings) = self.storage.sanityCheck()
        if errors:
            detailed =  _("The partitioning scheme you requested caused the \n"
                          "following critical errors.You must correct these \n"
                          "errors before you continue your installation of %s." %
                          yali.util.product_name())

            comments = "\n\n".join(errors)
            self.intf.detailedMessageWindow(_("Partitioning Errors"),
                                             detailed, comments, type="ok")
            return False

        if warnings:
            detailed = _("The partitioning scheme you requested generated the \n"
                         "following warnings. Would you like to continue with \n"
                         "your requested partitioning "
                         "scheme?")

            comments = "\n\n".join(warnings)
            rc = self.intf.detailedMessageWindow(_("Partitioning Warnings"),
                                                  detailed, comments, type="yesno")
            if rc != 1:
                return True

        formatWarnings = getPreExistFormatWarnings(self.storage)
        if formatWarnings:
            detailed = _("The following pre-existing devices have been selected\n"
                         "to be formatted, destroying all data.")

            comments = ""
            for (device, type, mountpoint) in formatWarnings:
                comments = comments + "%s         %s         %s\n" % (device, type, mountpoint)

            rc = self.intf.detailedMessageWindow(_("Format Warnings"),
                                                  detailed, comments, type="custom",
                                                  customButtons=[_("Cancel"), _("Format")], default=0)
            if rc != 1:
                return False

        return True


    def backCheck(self):
        rc = self.intf.messageWindow(_("Warning"), _("All Changes that you made will be removed"), type="question")
        if rc:
            self.storage.reset()
            return True
        return False

    def reset(self):
        if not confirmResetPartitionState(self.intf):
            return
        self.storage.reset()
        self.ui.deviceTree.clear()
        self.populate()
        #self.refresh(justRedraw=True)

    def addDevice(self, device, item):
        if device.format.hidden:
            return

        format = device.format
        if format.formattable:
            formattable = _("Yes")
        else:
            formattable = _("No")

        if not format.exists:
            formatIcon = _("Yes")
        else:
            formatIcon = _("No")

        # mount point string
        if format.type == "lvmpv":
            vg = None
            for _vg in self.storage.vgs:
                if _vg.dependsOn(device):
                    vg = _vg
                    break
            mountpoint = getattr(vg, "name", "")
        else:
            mountpoint = getattr(format, "mountpoint", "")
            if mountpoint is None:
                mountpoint = ""

        # device name
        # device name
        name = getattr(device, "lvname", device.name)

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
        item.setFormattable(formattable)

    def populate(self):
        self.ui.deviceTree.clear()
        # first do LVM
        vgs = self.storage.vgs
        if vgs:
            volumeGroupsItem = DeviceTreeItem(self.ui.deviceTree)
            volumeGroupsItem.setName(_("LVM Volume Groups"))
            for vg in vgs:
                volumeGroupItem = DeviceTreeItem(volumeGroupsItem)
                self.addDevice(vg, volumeGroupItem)
                volumeGroupItem.setType("")
                for lv in vg.lvs:
                    logicalVolumeItem = DeviceTreeItem(volumeGroupItem)
                    self.addDevice(lv, logicalVolumeItem)

                # We add a row for the VG free space.
                if vg.freeSpace > 0:
                    freeLogicalVolumeItem = DeviceTreeItem(volumeGroupItem)
                    freeLogicalVolumeItem.setName(_("Free"))
                    freeLogicalVolumeItem.setSize("%Ld" % vg.freeSpace)
                    freeLogicalVolumeItem.setDevice(None)
                    freeLogicalVolumeItem.setMountpoint("")

        # now normal partitions
        disks = self.storage.partitioned
        # also include unpartitioned disks that aren't mpath or biosraid
        whole = filter(lambda d: not d.partitioned and not d.format.hidden,
                       self.storage.disks)
        disks.extend(whole)
        disks.sort(key=lambda d: d.name)
        # Disk&Partitions
        drivesItem = DeviceTreeItem(self.ui.deviceTree)
        drivesItem.setName(_("Hard Drives"))
        for disk in disks:
            diskItem = DeviceTreeItem(drivesItem)
            diskItem.setName(disk.name)
            #self.ui.deviceTree.expandItem(diskItem)
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
                self.addDevice(disk, diskItem)

        #Expands all item in selected device tree item
        for index in range(self.ui.deviceTree.topLevelItemCount()):
            self.ui.deviceTree.topLevelItem(index).setExpanded(True)
            childItem = self.ui.deviceTree.topLevelItem(index)
            for childIndex in range(childItem.childCount()):
                childItem.child(childIndex).setExpanded(True)

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
                self.intf.messageWindow(_("Error Partitioning"), _("Could not allocate requested partitions: %s.") % 
                                      (msg), customIcon="error")
                rc = -1
            except PartitioningWarning, msg:
                rc = self.intf.messageWindow(_("Warning Partitioning"), _("Warning: %s." % msg),
                        customButtons=[_("Modify Partition"), _("Continue")], customIcon="warning")
                if rc == 1:
                    rc = -1
                else:
                    rc = 0
                    all_devices = self.storage.devicetree.devices
                    bootDevs = [d for d in all_devices if d.bootable]

        if not rc == -1:
            self.populate()

        self.update()
        return rc


    def getCurrentDevice(self):
        if self.ui.deviceTree.currentItem():
            return self.ui.deviceTree.currentItem().device

    def getCurrentDeviceParent(self):
        """ Return the parent of the selected row.  Returns an item.
            None if there is no parent.
        """
        pass

    def createDevice(self):
        activatePartition = False
        freePartition = hasFreeDiskSpace(self.storage)
        if freePartition:
            activatePartition = True

        activateVolumeGroup = False
        availablePVS = len(self.storage.unusedPVS())
        if (lvm.has_lvm() and
                formats.getFormat("lvmpv").supported and
                availablePVS > 0):
            activateVolumeGroup = True

        activateRaidArray = False
        #availableRaidMembers = len(self.storage.unusedRaidMembers)
        #availableMinors = len(self.storage.unusedRaidMinors)
        #if (availableMinors > 0
        #        and formats.getFormat("software RAID").supported
        #        and availableRaidMembers > 1):
        #    activateRaidArray = True


        if (not activatePartition and not activateVolumeGroup):
            self.intf.messageWindow(_("Cannot perform any creation operation"),
                                    _("Note that the creation operation requires one of the\nfollowing:"
                                      " * Free space in one of the Hard Drives.\n"
                                      " * At least one free physical volume (LVM) partition.\n"
                                      " * At least one Volume Group with free space."),
                                    customIcon="warning")
            return

        freeVolumeGroupSpace = []
        for vg in self.storage.vgs:
            if vg.freeSpace > 0:
                freeVolumeGroupSpace.append(vg)

        activateLogicalVolume = False
        if len(freeVolumeGroupSpace) > 0:
            activateLogicalVolume = True

        dialog = Dialog(_("Create Storage"), closeButton=False)
        dialog.addWidget(CreateDeviceWidget(dialog))

        if activatePartition:
            dialog.content.partition.setEnabled(True)
            dialog.content.partitionLabel.setEnabled(True)
            dialog.content.physicalVolume.setEnabled(True)
            dialog.content.physicalVolumeLabel.setEnabled(True)
            #dialog.content.raidMember.setEnabled(True)
            #dialog.content.raidMemberLabel.setEnabled(Trueu)

        if activateVolumeGroup:
            dialog.content.volumeGroup.setEnabled(True)
            dialog.content.volumeGroupLabel.setEnabled(True)

        if activateLogicalVolume:
            #FIXME: find way to show only logical volume edit widget
            pass

        if activateRaidArray:
            #FIXME: Not implemented
            pass

        if activatePartition:
            #dialog.content.partition.setChecked(True)
            dialog.content.partition.click()
        elif activateVolumeGroup:
            #dialog.content.volumeGroup.setChecked(True)
            dialog.content.volumeGroup.click()
        elif activateRaidArray:
            dialog.content.raidArray.click()
            #dialog.content.raidArray.setClicked(True)

        rc = dialog.exec_()
        print "Dialog.rc --> %s" % rc
        if not rc:
            ctx.logger.debug(_("Received Create Storage Dialog code   != 1 (%d) witch should not happen" % rc))
            return

        print "Dialog.content.rc --> %s" % dialog.content.rc
        if dialog.content.rc == raidMember:
            raidmember = self.storage.newPartition(fmt_type="mdmember")
            self.editPartition(member, isNew = True, restricts=["mdmember"])
            return

        elif dialog.content.rc == raidArray:
            array = self.storage.newMDArray(fmt_type=self.storage.defaultFSType)
            self.editRaidArray(array, isNew = True)
            return

        elif dialog.content.rc == physicalVolume:
            physicalvolume = self.storage.newPartition(fmt_type="lvmpv")
            self.editPartition(physicalvolume, isNew = True, restricts=["lvmpv"])
            return

        elif dialog.content.rc == volumeGroup:
            vg = self.storage.newVolumeGroup()
            self.editVolumeGroup(vg, isNew=True)
            return

        elif dialog.content.rc == partition:
            format = self.storage.defaultFSType
            device = self.storage.newPartition(fmt_type=format)
            self.editPartition(device, isNew=True)
            return

    def editDevice(self, *args):
        device = self.getCurrentDevice()
        reason = self.storage.deviceImmutable(device, ignoreProtected=True)

        if reason:
            self.intf.messageWindow(_("Unable To Edit"),
                                   _("You cannot edit this device:\n\n%s")
                                    % reason,
                                    customIcon="error")
            return

        if device.type == "lvmvg":
            self.editVolumeGroup(device)
        elif device.type == "lvmlv":
            self.editLogicalVolume(lv=device)
        elif isinstance(device, Partition):
            self.editPartition(device)

    def deleteDevice(self):
        device = self.getCurrentDevice()
        if device.partitioned:
            if doClearPartitionedDevice(self.intf, self.storage, device):
                self.refresh()
        elif doDeleteDevice(self.intf, self.storage, device):
            if isinstance(device, Partition):
                justRedraw = False
            else:
                justRedraw = True
                if device.type == "lvmlv" and device in device.vg.lvs:
                    device.vg._removeLogicalVolume(device)

            self.refresh(justRedraw=justRedraw)


    def editVolumeGroup(self, device, isNew=False):
        volumegroupEditor =  LVMEditor(self, device, isNew=isNew)

        while True:
            origDevice = copy.copy(device)
            operations = volumegroupEditor.run()

            for operation in operations:
                self.storage.devicetree.registerOperation(operation)

            if self.refresh(justRedraw=not operations):
                operations.reverse()

                for operation in operations:
                    self.storage.devicetree.cancelOperation(operation)

                if not isNew:
                    device = origDevice

                if self.refresh():
                    raise RuntimeError, ("Returning partitions to state "
                                         "prior to edit failed")
            else:
                break

        volumegroupEditor.destroy()

    def editLogicalVolume(self, lv=None, vg=None):
        """Will be consistent with the state of things and use this funciton
        for creating and editing LVs.

        lv -- the logical volume to edit.  If this is set there is no need
              for the other two arguments.
        vg -- the volume group where the new lv is going to be created. This
              will only be relevant when we are createing an LV.
        """
        if lv != None:
            volumegroupEditor = LVMEditor(self, lv.vg, isNew = False)
            lv = volumegroupEditor.lvs[lv.lvname]
            isNew = False

        elif vg != None:
            volumegroupEditor = LVMEditor(self, vg, isNew = False)
            tempvg = volumegroupEditor.tmpVolumeGroup
            name = self.storage.createSuggestedLogicalVolumeName(tempvg)
            format = fornmats.getFormat(self.storage.defaultFSType)
            volumegroupEditor.lvs[name] = {'name': name,
                                           'size': vg.freeSpace,
                                           'format': format,
                                           'originalFormat': format,
                                           'stripes': 1,
                                           'logSize': 0,
                                           'snapshotSpace': 0,
                                           'exists': False}
            lv = volumegroupEditor.lvs[name]
            isNew = True

        else:
            return

        while True:
            #volumegroupEditor.editLogicalVolume(lv, isNew = isNew)
            operations = volumegroupEditor.run()

            for operation in operations:
                self.storage.devicetree.addOperation(operation)

            if self.refresh(justRedraw=True):
                operations.reverse()
                for operation in operations:
                    self.storage.devicetree.removeOperation(operation)

                if self.refresh():
                    raise RuntimeError, ("Returning partitions to state "
                                         "prior to edit failed")
                continue
            else:
                break

        volumegroupEditor.destroy()

    def editRaidArray(self, device, isNew = False):
        pass

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
                    device.req_size = origDevice.req_size
                    device.req_base_size = origDevice.req_base_size
                    device.req_grow = origDevice.req_grow
                    device.req_max_size = origDevice.req_max_size
                    device.req_primary = origDevice.req_primary
                    device.req_disks = origDevice.req_disks

                if self.refresh():
                    raise RuntimeError, ("Returning partitions to state "
                                         "prior to edit failed")
            else:
                break

        partitionEditor.destroy()

class DeviceTreeItem(QtGui.QTreeWidgetItem):
    def __init__(self, parent, device=None):
        QtGui.QTreeWidgetItem.__init__(self, parent)
        self.device = device

    def setDevice(self, device):
        self.device = device

    def setName(self, device):
        self.setText(0, device)

    def setMountpoint(self, mountpoint):
        self.setText(1, mountpoint)

    def setLabel(self, label):
        self.setText(2, label)

    def setType(self, type):
        self.setText(3, type)

    def setFormattable(self, formattable):
        self.setText(4, formattable)

    def setFormat(self, format):
        self.setText(5, format)

    def setSize(self, size):
        self.setText(6, size)
