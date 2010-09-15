#!/usr/bin/python
# -*- coding: utf-8 -*-

import gettext
__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext


import copy
from PyQt4 import QtGui
from PyQt4.QtCore import *

import yali.util
import yali.context as ctx
from yali.gui.YaliDialog import Dialog
from yali.gui import storageGuiHelpers
from yali.storage import formats
from yali.storage import partitioning
from yali.storage.operations import *
from yali.storage.storageBackendHelpers import queryNoFormatPreExisting, sanityCheckMountPoint, doUIRAIDLVMChecks

class PartitionEditor:
    def __init__(self, parent, origrequest, isNew=False, restricts=None):
        self.storage = parent.storage
        self.origrequest = origrequest
        self.isNew = isNew
        self.parent = parent

        if isNew:
            title = _("Add Partition")
        else:
            try:
                title = _("Edit Partition %s") % origrequest.device
            except:
                title = _("Edit Partition")

        self.dialog = Dialog(title, closeButton=False)
        self.dialog.addWidget(PartitionWidget(self, origrequest, isNew, restricts))
        self.dialog.resize(300,200)

    def run(self):
        if self.dialog is None:
            return []

        while 1:
            rc = self.dialog.exec_()
            operations = []

            if not rc:
                self.destroy()
                return []

            widget = self.dialog.content

            mountpoint = str(widget.mountCombo.currentText())
            active = widget.mountCombo.isEnabled()
            #if widget.mountCombo.isEditable() and mountpoint:
            if active and mountpoint:
                msg = sanityCheckMountPoint(mountpoint)
                if msg:
                    ctx.interface.messageWindow(_("Mount Point Error"),
                                            msg,
                                            customIcon="error")
                    continue

                used = False
                for (mp, dev) in self.storage.mountpoints.iteritems():
                    if mp == mountpoint and \
                       dev.id != self.origrequest.id and \
                       not (self.origrequest.format.type == "luks" and
                            self.origrequest in dev.parents):
                        used = True
                        break

                if used:
                    ctx.interface.messageWindow(_("Mount point in use"),
                                            _("The mount point \"%s\" is in "
                                              "use. Please pick another.") %
                                            (mountpoint,),
                                            customIcon="error")
                    continue

            if not self.origrequest.exists:
                formatType = str(widget.newfstypeCombo.currentText())

                if widget.primaryCheckBox.isChecked():
                    primary = True
                else:
                    primary = None

                if widget.fixedRadioButton.isChecked():
                    grow = None
                else:
                    grow = True

                if widget.fillMaxsizeRadioButton.isChecked():
                    maxsize = widget.fillMaxsizeSpinBox.value()
                else:
                    maxsize = 0

                allowedDrives = []
                for index in range(widget.driveview.count()):
                    if widget.driveview.item(index).checkState() == Qt.Checked:
                        allowedDrives.append(widget.driveview.item(index).drive)

                if len(allowedDrives) == len(self.storage.partitioned):
                    allowedDrives = None

                size = widget.sizeSpin.value()

                disks = []
                if allowedDrives:
                    for drive in allowedDrives:
                        for disk in self.storage.partitioned:
                            if disk.name == drive.name:
                                disks.append(disk)

                format = formats.getFormat(formatType, mountpoint=mountpoint)

                err = doUIRAIDLVMChecks(format, disks, self.storage)
                if err:
                    self.intf.messageWindow(_("Error With Request"),
                                            err, customIcon="error")
                    continue

                weight = partitioning.weight(mountpoint=mountpoint, fstype=format.type)

                if self.isNew:
                    request = self.storage.newPartition(size=size,
                                                        grow=grow,
                                                        maxsize=maxsize,
                                                        primary=primary,
                                                        format=format,
                                                        parents=disks)
                else:
                    request = self.origrequest
                    request.weight = weight

                usedev = request

                if self.isNew:
                    operations.append(OperationCreateDevice(request))
                else:
                    request.req_size = size
                    request.req_base_size = size
                    request.req_grow = grow
                    request.req_max_size = maxsize
                    request.req_primary = primary
                    request.req_disks = disks

                operations.append(OperationCreateFormat(usedev, format))

            else:
                # preexisting partition
                request = self.origrequest
                usedev = request

                origformat = usedev.format
                devicetree = self.storage.devicetree

                if widget.fsoptions.has_key("formatCheckBox"):
                    if widget.fsoptions["formatCheckBox"].isChecked():
                        formatType = str(widget.fsoptions["fstypeComboBox"].currentText())
                        format = formats.getFormat(formatType, mountpoint=mountpoint, device=usedev.path)

                        operations.append(OperationCreateFormat(usedev, format))
                    elif not widget.fsoptions["formatCheckBox"].isChecked():
                        cancel = []
                        cancel.extend(devicetree.findOperations(type="destroy",
                                                                object="format",
                                                                devid=request.id))
                        cancel.extend(devicetree.findOperations(type="create",
                                                                object="format",
                                                                devid=request.id))
                        cancel.reverse()
                        for operation in cancel:
                            devicetree.removeOperation(operation)

                        request.format = request.originalFormat
                        usedev = request

                        if usedev.format.mountable:
                            usedev.format.mountpoint = mountpoint

                elif self.origrequest.protected and usedev.format.mountable:
                    # users can set a mountpoint for protected partitions
                    usedev.format.mountpoint = mountpoint

                request.weight = partitioning.weight(mountpoint=mountpoint, fstype=request.format.type)

                if widget.fsoptions.has_key("migrateCheckBox") and \
                   widget.fsoptions["migrateCheckBox"].isChecked():
                    operations.append(OperationMigrateFormat(usedev))

                if widget.fsoptions.has_key("resizeCheckBox") and \
                   widget.fsoptions["resizeCheckBox"].isChecked():
                    size = widget.fsoptions["resizeSpinBox"].value()

                    try:
                        operations.append(OperationResizeDevice(request, size))
                        if request.format.type and request.format.exists:
                            operations.append(OperationResizeFormat(request, size))
                    except ValueError:
                        pass

                if request.format.exists and \
                   getattr(request, "mountpoint", None) and \
                   self.storage.formatByDefault(request):
                    if not queryNoFormatPreExisting(self.intf):
                        continue

            # everything ok, fall out of loop
            break

        return operations

    def destroy(self):
        if self.dialog:
            self.dialog = None


class PartitionWidget(QtGui.QWidget):
    def __init__(self, parent, request, isNew, restricts=None):
        QtGui.QWidget.__init__(self, parent.parent)
        self.layout = QtGui.QGridLayout(self)
        self.parent = parent
        self.origrequest = request
        self.isNew = isNew
        row = 0

        # Mount Point entry
        label = QtGui.QLabel(_("Mount Point:"), self)
        self.layout.addWidget(label, row, 0, 1, 1)
        self.mountCombo = storageGuiHelpers.createMountpointMenu(self, self.origrequest)
        self.layout.addWidget(self.mountCombo,row, 1, 1, 1)

        row += 1

        # Partition Type
        if not self.origrequest.exists:
            label = QtGui.QLabel(_("File System Type:"), self)
            self.layout.addWidget(label, row, 0, 1, 1)
            self.newfstypeCombo = storageGuiHelpers.createFSTypeMenu(self,
                                                                     self.origrequest.format,
                                                                     self.mountCombo,
                                                                     availablefstypes=restricts,
                                                                     filesystemComboCB=self.fstypechangeCB,
                                                                     mountComboCB=self.mountptchangeCB)

            self.layout.addWidget(self.newfstypeCombo, row, 1, 1, 1)
            QObject.connect(self.newfstypeCombo, SIGNAL("currentIndexChanged(int)"), self.fstypechangeCB)

        else:
            self.newfstypeCombo = None

        row += 1

        # Allowable Drives
        if not self.origrequest.exists:
            label = QtGui.QLabel(_("Allowable Drives :"),self)
            self.layout.addWidget(label, row, 0, 1, 1)
            req_disk_names = [d.name for d in self.origrequest.req_disks]
            self.driveview = storageGuiHelpers.createAllowedDrivesList(self,
                                                                    self.parent.storage.partitioned,
                                                                    req_disk_names)
            self.layout.addWidget(self.driveview, row, 1, 1, 1)

            row += 1

        # Original filesystem type and label
        if self.origrequest.exists:
            label = QtGui.QLabel(_("Original File System Type:"), self)
            self.layout.addWidget(label, row, 0, 1, 1)
            label = QtGui.QLabel(self.origrequest.originalFormat.name, self)
            self.layout.addWidget(label, row, 1, 1, 1 )
            row += 1

            if getattr(self.origrequest.originalFormat, "label", None):
                label = QtGui.QLabel(_("Original File System Label:"), self)
                self.layout.addWidget(label, row, 0, 1, 1)
                label = QtGui.QLabel(self.origrequest.originalFormat.label, self)
                self.layout.addWidget(label, row, 1, 1, 1)
                row += 1

        #Size
        if not self.origrequest.exists:
            label = QtGui.QLabel(_("Size (MB)"), self)
            self.layout.addWidget(label, row, 0, 1, 1)
            maxsize = ctx.consts.MAX_PART_SIZE
            self.sizeSpin = QtGui.QSpinBox(self)
            self.sizeSpin.setMaximum(maxsize)
            if self.origrequest.req_size:
                self.sizeSpin.setValue(self.origrequest.req_size)
            self.layout.addWidget(self.sizeSpin, row, 1, 1, 1)
        else:
            self.sizeSpin = None

        row += 1

        #size options
        if not self.origrequest.exists:
            (groupBox,
            self.fixedRadioButton,
            self.fillMaxsizeRadioButton,
            self.fillMaxsizeSpinBox) = storageGuiHelpers.createAdvancedSizeOptions(self, self.origrequest)
            self.layout.addWidget(groupBox, row, 0, 1, 2)
            QObject.connect(self.sizeSpin, SIGNAL("valueChanged(int)"), self.sizeSpinChanged)
            row += 1

        # format/migrate option  for pre-exist partitions, as long as they aren't protected
        # (we will still like to be mount them, though)
        self.fsoptions = {}
        if self.origrequest.exists and not self.origrequest.protected:
            (row, self.fsoptions) = storageGuiHelpers.createPreExistFSOption(self, self.origrequest,
                                                                             row, self.mountCombo,
                                                                             self.parent.storage)
            row += 1

        #create only as primary
        if not self.origrequest.exists:
            self.primaryCheckBox = QtGui.QCheckBox(_("Force to be a primary partition"),self)
            self.primaryCheckBox.setChecked(False)
            if self.origrequest.req_primary:
                self.primaryCheckBox.setChecked(True)

            if self.parent.storage.extendedPartitionsSupported:
                self.layout.addWidget(self.primaryCheckBox, row, 0, 1, 1)
                row += 1

        self.buttonBox = QtGui.QDialogButtonBox(self)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.layout.addWidget(self.buttonBox, row, 0, 1, 2)
        self.connect(self.buttonBox, SIGNAL("accepted()"), self.parent.dialog.accept)
        self.connect(self.buttonBox, SIGNAL("rejected()"), self.parent.dialog.reject)

    def fstypechangeCB(self, index):
        format  = formats.getFormat(self.sender().itemText(index))
        self.setMntptComboStateFromFStype(format, self.mountCombo)

    def sizeSpinChanged(self, size):
        maxsize = self.fillMaxsizeSpinBox.value()
        if size < 1:
            self.sizeSpin.setValue(1)
            size = 1
        if size > maxsize:
            self.sizeSpin.setValue(maxsize)

        self.sizeSpin.setMinimum(size)

    def mountptchangeCB(self, index):
        if yali.util.isEfi() and self.sender().itemText(0) == "/boot/efi":
            self.fstypeComboBox.setCurrentText(self.fstypeComboBox.findText(formats.getFormat("efi").name))

        if self.sender().itemText(0) == "/boot":
            self.fstypeComboBox.setCurrentText(self.fstypeComboBox.findText(formats.get_default_filesystem_type(boot=True)))

    def formatOptionResize(self, state):
        if state:
            lower = 1
        else:
            lower = self.fsoptions["resizeSpinBox"].minimum()

        #if self.fsoptions["resizeSpinBox"].value() < lower:
        #    self.fsoptions["resizeSpinBox"].setValue(lower)

        self.fsoptions["resizeCheckBox"].setEnabled(not state)
        self.fsoptions["resizeSpinBox"].setEnabled(not state)

    def formatOptionCB(self, state):
        widget = None
        otherCheckBox = None
        otherComboBox = None

        if self.fsoptions.has_key("migrateCheckBox") and self.sender() == self.fsoptions["migrateCheckBox"]:
            self.fsoptions["migratefstypeComboBox"].setEnabled(state)
            widget = self.fsoptions["migratefstypeComboBox"]

            if self.fsoptions.has_key("formatCheckBox") and self.fsoptions.has_key("fstypeComboBox"):
                otherCheckBox = self.fsoptions["formatCheckBox"]
                otherComboBox = self.fsoptions["fstypeComboBox"]

        elif self.fsoptions.has_key("formatCheckBox") and self.sender() == self.fsoptions["formatCheckBox"]:
            self.fsoptions["fstypeComboBox"].setEnabled(state)
            widget = self.fsoptions["fstypeComboBox"]

            if self.fsoptions.has_key("migrateCheckBox") and self.fsoptions.has_key("migratefstypeComboBox"):
                otherCheckBox = self.fsoptions["migrateCheckBox"]
                otherComboBox = self.fsoptions["migratefstypeComboBox"]

        if otherComboBox and otherComboBox:
            otherCheckBox.setEnabled(not state)
            otherComboBox.setChecked(not state)

        if state:
            format = formats.getFormat(widget.itemText(widget.currentIndex()))
            self.setMntptComboStateFromFStype(format, self.mountCombo)
        else:
            self.setMntptComboStateFromFStype(self.origrequest.format, self.mountCombo)

    def setMntptComboStateFromFStype(self, fstype, mountCombo):
        if fstype.mountable:
            mountCombo.setEnabled(True)
        else:
            mountCombo.setEnabled(False)
            if mountCombo.itemText(0) != _("<Not Applicable>"):
                mountCombo.insertItem(0, _("<Not Applicable>"))

    def resizeOption(self, state):
        self.fsoptions["resizeSpinBox"].setEnabled(state)
        if self.fsoptions["formatCheckBox"]:
            self.fsoptions["formatCheckBox"].setEnabled(not state)
