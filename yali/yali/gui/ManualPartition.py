#!/usr/bin/python
# -*- coding: utf-8 -*-

import gettext
__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext


import copy
from PyQt4 import QtGui
from PyQt4.QtCore import *

import yali.gui.context as ctx
from yali.gui.YaliDialog import Dialog, QuestionDialog, InfoDialog
from yali.gui.GUIException import *
from yali.gui.ScreenWidget import ScreenWidget
from yali.gui import storageGuiHelpers
from yali.storage import formats
from yali.storage import partitioning
from yali.storage.operations import *
from yali.storage.storageBackendHelpers import queryNoFormatPreExisting, sanityCheckMountPoint

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
        self.dialog.addWidget(PartitionWidget(self, origrequest, isNew))

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

            mountpoint = widget.mountCombo.currentText()
            if widget.mountCombo.isEditable() and mountpoint:
                msg = sanityCheckMountPoint(mountpoint)
                if msg:
                    ctx.yali.messageWindow(_("Mount Point Error"),
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
                    ctx.yali.messageWindow(_("Mount point in use"),
                                            _("The mount point \"%s\" is in "
                                              "use. Please pick another.") %
                                            (mountpoint,),
                                            customIcon="error")
                    continue

            if not self.origrequest.exists:
                format = widget.newfstypeCombo.currentText()

                if widget.primaryCheckBox.isChecked():
                    primary = True
                else:
                    primary = None

                if widget.fixedRadioButton.isEnabled():
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
                            if disk.name == drive:
                                disks.append(disk)

                format = formats.getFormat(format, mountpoint=mountpoint)

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

            else:
                # preexisting partition
                request = self.origrequest
                usedev = request

                origformat = usedev.format
                devicetree = self.storage.devicetree

                if self.fsoptionsDict.has_key("formatCheckBox"):
                    if self.fsoptionsDict["formatCheckBox"].isChecked():
                        formatType = self.fsoptionsDict["fstypeComboBox"].currentText()
                        format = formats.getFormat(mountpoint=mountpoint, device=usedev.path)

                        operations.append(OperationCreateFormat(usedev, format))
                    elif not self.fsoptionsDict["formatCheckBox"].isChecked():
                        cancel = []
                        cancel.extend(devicetree.findOperations(type="destroy",
                                                                object="format",
                                                                devid=request.id))
                        cancel.extend(devicetree.findOperations(type="create",
                                                                object="format",
                                                                devid=request.id))
                        cancel.reverse()
                        for operation in cancel:
                            devicetree.cancelOperation(operation)

                        usedev = request

                        if usedev.format.mountable:
                            usedev.format.mountpoint = mountpoint

                elif self.origrequest.protected and usedev.format.mountable:
                    # users can set a mountpoint for protected partitions
                    usedev.format.mountpoint = mountpoint

                request.weight = storage.partitioning.weight(mountpoint=mountpoint, fstype=request.format.type)

                if self.fsoptionsDict.has_key("migrateCheckBox") and \
                   self.fsoptionsDict["migrateCheckBox"].isChecked():
                    operations.append(OperationMigrateFormat(usedev))

                if self.fsoptionsDict.has_key("resizeCheckBox") and \
                   self.fsoptionsDict["resizeCheckBox"].isChecked():
                    size = self.fsoptionsDict["resizeSpinBox"].value()

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
                                                                     availablefstypes=restricts)
            self.layout.addWidget(self.newfstypeCombo, row, 1, 1, 1)
            QObject.connect(self.newfstypeCombo, SIGNAL("currentIndexChanged(int)"), self.fstypechange)

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
                                                                    req_disk_names,
                                                                    selectDrives=False)
            self.layout.addWidget(self.driveview, row, 1, 1, 1)

            row += 1

        # Original fs label
        if self.origrequest.exists:
            label = QtGui.QLabel(_("Original File System  Label:"), self)
            self.layout.addWidget(label, row, 0, 1, 1)
            label = QtGui.QLabel(self.origrequest.originalFormat.name, self)
            self.layout.addWidget(label, row, 1, 1, 1 )
            row += 1

            if getattr(self.origrequest.originalFormat, "label", None):
                label = QtGui.QLabel(_("Original File System  Label:"), self)
                self.layout.addWidget(label, row, 0, 1, 1)
                label = QtGui.QLabel(self.origrequest.originalFormat.name, self)
                self.layout.addWidget(label, row, 1, 1, 1)
                row += 1

        #Size
        if not self.origrequest.exists:
            label = QtGui.QLabel(_("Size (MB)"), self)
            self.layout.addWidget(label, row, 0, 1, 1)
            maxsize = ctx.consts.MAX_PART_SIZE
            self.sizeSpin = QtGui.QSpinBox(self)
            self.layout.addWidget(self.sizeSpin, row, 1, 1, 1)
            self.sizeSpin.setRange(1, maxsize)
            if self.origrequest.req_size:
                self.sizeSpin.setValue(self.origrequest.req_size)
        else:
            self.sizeSpin = None

        row += 1

        # format/migrate option  for pre-exist partitions, as long as they aren't protected
        # (we will still like to be mount them, though)
        self.fsoptions = {}
        if self.origrequest.exists and not self.origrequest.protected:
            (row, self.fsoptions) = storageGuiHelpers.createPreExistFSOption(self, self.origrequest,
                                                                             row, self.mountCombo,
                                                                             self.parent.storage)

        #size options
        if not self.origrequest.exists:
            (groupBox,
            self.fixedRadioButton,
            self.fillMaxsizeRadioButton,
            self.fillMaxsizeSpinBox) = storageGuiHelpers.createAdvancedSizeOptions(self, self.origrequest)
            self.layout.addWidget(groupBox, row, 0, 1, 2)
            QObject.connect(self.sizeSpin, SIGNAL("valueChanged(int)"), self.sizeSpinChanged)
            row += 1
        else:
            pass

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

    def fstypechange(self, index):
        format  = formats.getFormat(self.newfstypeCombo.itemText(index))
        if format.mountable:
            self.mountCombo.setEnabled(True)
        else:
            self.mountCombo.setItemText(0, _("<Not Applicable>"))
            self.mountCombo.setEnabled(False)

    def fillMaxSizeCB(self):
        self.fillMaxsizeSpinBox.setEnabled(True)

    def sizeSpinChanged(self):
        size = self.sizeSpin.value()
        maxsize = self.fillMaxsizeSpinBox.value()
        if size < 1:
            self.sizeSpin.setValue(1)
        if size > maxsize:
            self.sizeSpin.setValue(maxsize)

    def formatOptionResize(self, state):
        if self.fsoptions["formatCheckBox"].isEnabled():
            lower = 1
        else:
            lower = self.fsoptions["resizeSpinBox"].minimum

        if self.fsoptions["resizeSpinBox"].value() < lower:
            self.fsoptions["resizeSpinBox"].setValue(lower)

        self.fsoptions["resizeCheckBox"].setEnabled(not self.fsoptions["formatCheckBox"].isEnabled())
        self.fsoptions["resizeSpinBox"].setEnabled(self.fsoptions["formatCheckBox"].isEnabled())

    def formatOptionCB(self, state):
        widget = None
        if self.fsoptions.has_key("migrateCheckBox") and self.sender() == self.fsoptions["migrateCheckBox"]:
            self.fsoptions["migratefstypeComboBox"].setEnabled(state)
            widget = self.fsoptions["migratefstypeComboBox"]
        elif self.fsoptions.has_key("formatCheckBox") and self.sender() == self.fsoptions["formatCheckBox"]:
            self.fsoptions["fstypeComboBox"].setEnabled(state)
            widget = self.fsoptions["fstypeComboBox"]


        if self.sender().isEnabled():
            format = formats.getFormat(widget.itemText(widget.currentIndex()))
            self.setMntptComboStateFromFStype(format, self.mountCombo)
        else:
            self.setMntptComboStateFromFStype(self.origrequest.format, self.mountCombo)

    def setMntptComboStateFromFStype(self, fstype, mountCombo):
        if fstype.mountable:
            mountCombo.setEnabled(True)
        else:
            mountCombo.setEnabled(False)
            mountCombo.setItemText(0, _("<Not Applicable>"))

    def resizeOption(self, state):
        self.fsoptions["formatCheckBox"].setEnabled(not state)
        self.fsoptions["resizeSpinBox"].setEnabled(state)
