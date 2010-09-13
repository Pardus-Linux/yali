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
from yali.storage.devices.volumegroup import VolumeGroup
from yali.storage.devices.logicalvolume import LogicalVolume
from yali.storage.library import lvm


class LVMEditor(object):
    def __init__(self, storage, parent, interface, parent, volumegroup, isNew=0):
        self.parent = parent
        self.storage = storage
        self.volumeGroup = volumegroup
        self.peSize = volumegroup.peSize
        self.pvs = volumegroup.pvs[:]
        self.lvs = {}
        self.isNew = isNew
        self.intf = interface
        self.parent = parent
        self.actions = []
        self.dialog = None

        for logicalVolume in self.volumeGroup.lvs:
            self.lvs[logicalVolume.lvname] = {"name": logicalVolume.lvname,
                                              "size": logicalVolume.size,
                                              "format": copy.copy(logicalVolume.format),
                                              "originalFormat": logicalVolume.originalFormat,
                                              "stripes": logicalVolume.stripes,
                                              "logSize": logicalVolume.logSize,
                                              "snapshotSpace": logicalVolume.snapshotSpace,
                                              "exists": logicalVolume.exists}

        self.availlvmparts = self.storage.unusedPVs(vg=volumeGroup)
        # if no PV exist, raise an error message and return
        if len(self.availlvmparts) < 1:
            self.intf.messageWindow(_("Not enough physical volumes"),
                                    _("At least one unused physical "
                                      "volume partition is "
                                      "needed to create an LVM Volume Group.\n\n"
                                      "Create a partition or RAID array "
                                      "of type \"physical volume (LVM)\" and then "
                                      "select the \"LVM\" option again."),
                                    customIcon="error")
            self.dialog = None
            return

        if isNew:
            title = _("Make LVM Volume Group")
        else:
            try:
                title = _("Edit LVM Volume Group: %s") % (volumegroup.name,)
            except AttributeError:
                title = _("Edit LVM Volume Group")
        self.dialog = Dialog(title, closeButton=False)

    @property
    def getTmpVolumeGroup(self):
        pvs = [copy.deepcopy(pv) for pv in self.pvs]
        volumeGroup = VolumeGroup('tmp-%s' % self.vg.name,
                                  parents=pvs, peSize=self.peSize)
        for logicalVolume in self.lvs.values():
            lv = LogicalVolume(logicalVolume['name'], volumeGroup,
                               format=logicalVolume['format'], size=logicalVolume['size'],
                               exists=logicalVolume['exists'], stripes=logicalVolume['stripes'],
                               logSize=logicalVolume['logSize'], snapshotSpace=logicalVolume['snapshotSpace'])
            lv.originalFormat = logicalVolume['originalFormat']

        return volumeGroup

    def availableLogicalVolumes(self):
        return max(0, lvm.MAX_LV_SLOTS - len(self.lvs))

    def computeSpaceValues(self):
        volumeGroup = self.getTmpVolumeGroup
        size = volumeGroup.size
        free = volumeGroup.freeSpace
        used = size - free
        return (size, used, free)

    def addLogicalVolume(self):
        pass

    def editLogicalVolume(self):
        pass

    def deleteLogicalVolume(self):
        pass

    def run(self):
        pass



class LVMWidget(QtGui.QWidget):
    def __init__(self, parent, isNew):
        QtGui.QWidget.__init__(self, parent.parent)
        self.layout = QtGui.QGridLayout(self)
        self.parent = parent
        self.isNew = isNew
        row = 0

        label = QtGui.QLabel(_("Volume Group Name:"), self)
        self.layout.addWidget(label, row, 0, 1, 1)
        if not vg.exists:
            self.volumeGroupName = QtGui.QLineEdit(self)
            if not self.isNew:
                self.volumeGroupName.setText(self.volumeGroup.name)
            else:
                self.volumeGroupName.setText(self.storage.createSuggestedVolumeGroupName())
        else:
            self.volumeGroupName = QtGui.QLabel(self)
            self.volumeGroupName.setText(self.volumeGroup.name)
        self.layout.addWidget(self.volumeGroupName, row, 1, 1, 1)

        row += 1

        label = QtGui.QLabel(_("Physical Extent:"), self)
        self.layout.addWidget(label, row, 0, 1, 1)
        self.physicalExtendsCombo =  storageGuiHelpers.createPhysicalExtendsMenu(self.volumeGroup.peSize * 1024)
        self.layout.addWidget(self.physicalExtendsCombo, row, 1, 1, 1)
        if volumegroup.exists:
            self.physicalExtendsCombo.setEnabled(False)

        row += 1

        label = QtGui.QLabel(_("Physical Volumes to Use:"), self)
        self.layout.addWidget(label, row, 0, 1, 1)
        self.physicals =  storageGuiHelpers.createAllowedPhysicals(self)
        if volumegroup.exists:
            sellf.physicals.setEnabled(False)

        self.layout.addWidget(self.physicals, row, 1, 1, 1)

        row += 1

        label = QtGui.QLabel(_("Used Space:"), self)
        self.layout.addWidget(label, row, 0, 1, 1)
        self.usedPercent = QtGui.QLabel(_(""), self)
