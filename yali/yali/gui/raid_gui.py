#!/usr/bin/python
# -*- coding: utf-8 -*-
import copy
import gettext
__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext

from PyQt4 import QtGui
from PyQt4.QtCore import *

import yali.context as ctx
from yali.gui.YaliDialog import Dialog
from yali.gui import storageGuiHelpers

class RaidEditor(object):
    def __init__(self, parent, request, isNew=False):
        self.parent = parent
        self.storage = parent.storage
        self.intf = parent.intf
        self.origrequest = request

        if isNew:
            title = _("Make RAID Device")
        else:
            if request.minor is not None:
                title = _("Edit RAID Device: %s") % (request.path,)
            else:
                title = _("Edit RAID Device")

    def run(self):
        pass

    def destroy(self):
        if self.dialog:
            self.dialog = None

class RaidWidget(QtGui.QWidget):
    def __init__(self, parent, request, isNew):
        QtGui.QWidget.__init__(self, parent.parent)
        self.layout = QtGui.QGridLayout(self)
        self.parent = parent
        self.origrequest = request
        self.isNew = isNew

        availraidparts = self.parent.storage.unusedMDMembers(array=self.origrequest)
        if availraidparts < 2:
            self.intf.messageWindow(_("Invalid Raid Members"),
                                    _("At least two unused software RAID "
                                     "partitions are needed to create "
                                     "a RAID device.\n\n"
                                     "First create at least two partitions "
                                     "of type \"software RAID\", and then "
                                     "select the \"RAID\" option again."))
                                    customIcon="error")
            return

        row = 0

        # Mount Point entry
        label = QtGui.QLabel(_("Mount Point:"), self)
        self.layout.addWidget(label, row, 0, 1, 1)
        self.mountCombo = storageGuiHelpers.createMountpointMenu(self, self.origrequest)
        self.layout.addWidget(self.mountCombo,row, 1, 1, 1)

        row += 1

        # Filesystem Type
        if not self.origrequest.exists:
            label = QtGui.QLabel(_("File System Type:"), self)
            self.layout.addWidget(label, row, 0, 1, 1)
            self.newfstypeCombo = storageGuiHelpers.createFSTypeMenu(self,
                                                                     self.origrequest.format,
                                                                     self.mountCombo,
                                                                     ignorefs=["mdmember", "efi", "prepboot", "appleboot"],
                                                                     filesystemComboCB=self.fstypechangeCB,
                                                                     mountComboCB=self.mountptchangeCB)
            self.layout.addWidget(self.newfstypeCombo, row, 1, 1, 1)
            QObject.connect(self.newfstypeCombo, SIGNAL("currentIndexChanged(int)"), self.fstypechangeCB)

        else:
            self.newfstypeCombo = None

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

        # Raid minors
        label = QtGui.QLabel(_("RAID Device:"), self)
        self.layout.addWidget(label, row, 0, 1, 1)
        if not self.origrequest.exists:
            numparts =  len(availraidparts)
            if self.origrequest.spares:
                spares = origrequest.spares
            else:
                spares = 0

            if self.origrequest.level:
                maxspares = raid.get_raid_max_spares(self.origrequest.level, numparts)
            else:
                maxspares = 0

            self.spareSpinBox = QtGui.QSpinBox(self)
            self.spareSpinBox.setMinimum(0)
            self.spareSpinBox.setMaximum(maxspares)
            self.spareSpinBox.setValue(spares)

            if maxspares > 0:
                self.spareSpinBox.setEnabled(True)
            else:
                self.spareSpinBox.setEnabled(False)
                self.spareSpinBox.setValue(0)
        else:
            self.spareSpinBox = QtGui.QLabel(str(self.origrequest.spares))
        self.layout.addWidget(label, row, 1, 1, 1)

        row += 1

        label = QtGui.QLabel(_("RAID Members:"), self)
        self.layout.addWidget(label, row, 0, 1, 1)
        self.raidlist = storageGuiHelpers.createAllowedRaidPartitionsList(self,
                                                                          availraidparts,
                                                                          self.origrequest.devices,
                                                                          self.origrequest.exists)
        if self.origrequest.exists
            self.raidlist.setEnabled(False)
        self.layout.addWidget(self.raidlist, row, 1, 1, 1)

        row += 1

        self.fsoptions = {}
        if self.origrequest.exists and self.origrequest.format.exists:
            (row, self.fsoptions) = storageGuiHelpers.createPreExistFSOption(self, self.origrequest,
                                                                             row, self.mountCombo,
                                                                             self.parent.storage)
            row += 1

        self.buttonBox = QtGui.QDialogButtonBox(self)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.layout.addWidget(self.buttonBox, row, 0, 1, 2)
        self.connect(self.buttonBox, SIGNAL("accepted()"), self.parent.dialog.accept)
        self.connect(self.buttonBox, SIGNAL("rejected()"), self.parent.dialog.reject)

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
