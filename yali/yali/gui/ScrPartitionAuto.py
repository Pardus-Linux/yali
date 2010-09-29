# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2010 TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#
import sys
import math
import gettext

__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext

from PyQt4 import QtGui
from PyQt4.QtCore import *

import yali.context as ctx
from yali.gui.ScreenWidget import ScreenWidget, GUIError
from yali.gui.Ui.autopartwidget import Ui_AutoPartWidget
from yali.gui.shrink_gui import ShrinkEditor
from yali.storage.partitioning import CLEARPART_TYPE_ALL, CLEARPART_TYPE_LINUX, CLEARPART_TYPE_NONE, doAutoPartition, defaultPartitioning

class DrivesListItem(QtGui.QListWidgetItem):
    def __init__(self, parent, widget):
        QtGui.QListWidgetItem.__init__(self, parent)
        self.widget = widget
        self.setSizeHint(QSize(300, 64))

class DriveItem(QtGui.QWidget):
    def __init__(self, parent, drive):
        QtGui.QWidget.__init__(self, parent)
        self.layout = QtGui.QHBoxLayout(self)
        self.checkBox = QtGui.QCheckBox(self)
        self.layout.addWidget(self.checkBox)
        self.labelDrive = QtGui.QLabel(self)
        self.labelDrive.setText("%s on %s - (%s) MB" % (drive.model, drive.name, str(int(drive.size))))
        self.layout.addWidget(self.labelDrive)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.layout.addItem(spacerItem)
        self.connect(self.checkBox, SIGNAL("stateChanged(int)"), self.stateChanged)
        self.drive = drive
        self.parent = parent

    def stateChanged(self, state):
        if state == Qt.Checked:
            ctx.mainScreen.enableNext()
        else:
            selectedDisks = []
            for index in range(self.parent.count()):
                if self.checkBox.checkState() == Qt.Checked:
                    selectedDisks.append(self.ui.drives.item(index).drive.name)

            if len(selectedDisks):
                ctx.mainScreen.enableNext()
            else:
                ctx.mainScreen.disableNext()




class Widget(QtGui.QWidget, ScreenWidget):
    title = _("Select Partitioning Method")
    icon = "iconPartition"
    help = _('''
<font size="+2">Partitioning Method</font>
<font size="+1">
<p>
You can install Pardus if you have an unpartitioned-unused disk space 
of 4GBs (10 GBs recommended) or an unused-unpartitioned disk. 
The disk area or partition selected for installation will automatically 
be formatted. Therefore, it is advised to backup your data to avoid future problems.
</p>
<p>Auto-partitioning will automatically format the select disk part/partition 
and install Pardus. If you like, you can do the partitioning manually or make 
Pardus create a new partition for installation.</p>
</font>
''')

    def __init__(self, *args):
        QtGui.QWidget.__init__(self,None)
        self.ui = Ui_AutoPartWidget()
        self.ui.setupUi(self)
        self.storage = ctx.storage
        self.intf = ctx.interface
        self.shrinkOperations = None
        self.clearPartDisks = None

        self.connect(self.ui.useAllSpace, SIGNAL("clicked()"), self.typeChanged)
        self.connect(self.ui.replaceExistingLinux, SIGNAL("clicked()"), self.typeChanged)
        self.connect(self.ui.shrinkCurrent, SIGNAL("clicked()"), self.typeChanged)
        self.connect(self.ui.useFreeSpace, SIGNAL("clicked()"), self.typeChanged)
        self.connect(self.ui.createCustom, SIGNAL("clicked()"), self.typeChanged)
        #self.connect(self.ui.drives,   SIGNAL("currentItemChanged(QListWidgetItem *, QListWidgetItem * )"),self.slotDeviceChanged)
        #self.ui.drives.hide()
        #self.ui.drivesLabel.hide()

    def typeChanged(self):
        if self.sender() != self.ui.createCustom:
            self.ui.review.setEnabled(True)
            if self.sender() == self.ui.shrinkCurrent:
                resizablePartitions = [partition for partition in self.storage.partitions if partition.exists and
                                                                                             partition.resizable and
                                                                                             partition.format.resizable]
                if not len(resizablePartitions):
                    self.intf.messageWindow(_("Warning"),
                                            _("No partitions are available to resize.Only physical\n"
                                              "partitions with specific filesystems can be resized."),
                                            type="warning", customIcon="error")
        else:
            self.ui.review.setEnabled(False)

        ctx.mainScreen.enableNext()

    def setPartitioningType(self):
        if self.storage.clearPartType is None or self.storage.clearPartType == CLEARPART_TYPE_LINUX:
            self.ui.replaceExistingLinux.toggle()
        elif self.storage.clearPartType == CLEARPART_TYPE_NONE:
            self.ui.useFreeSpace.toggle()
        elif self.storage.clearPartType == CLEARPART_TYPE_ALL:
            self.ui.useAllSpace.toggle()

    def setDrives(self):
        def fillDrives(drives):
            for drive in drives:
                if drive.size >= ctx.consts.min_root_size:
                    drive = DriveItem(self.ui.drives, drive)
                    listItem = DrivesListItem(self.ui.drives, drive)
                    self.ui.drives.setItemWidget(listItem, drive)

        if self.storage.clearPartDisks:
            if len(self.storage.clearPartDisks) == 1:
                self.ui.drives.hide()
            else:
                self.ui.drives.clear()
                fillDrives(self.storage.clearPartDisks)
                self.ui.drives.setCurrentRow(0)
        else:
            disks = filter(lambda d: not d.format.hidden, self.storage.disks)
            if len(disks) == 1:
                self.storage.clearPartDisks = [disk.name for disk in disks]
                self.ui.drives.hide()
            else:
                self.ui.drives.clear()
                fillDrives(disks)
                self.ui.drives.setCurrentRow(0)

    def shown(self):
        self.storage.reset()
        if self.storage.checkNoDisks(self.intf):
            sys.exit(0)
        else:
            self.setDrives()
            self.setPartitioningType()

    def execute(self):
        rc = self.nextCheck()
        if rc is None:
            #FIXME:Unknown bug
            #sys.exit(0)
            return True
        else:
            return rc

    def checkClearPartDisks(self):
        selectedDisks = []
        for index in range(self.ui.drives.count()):
            if self.ui.drives.item(index).widget.checkBox.checkState() == Qt.Checked:
                selectedDisks.append(self.ui.drives.item(index).widget.drive.name)

        if not self.storage.clearPartDisks:
            if not selectedDisks:
                self.intf.messageWindow(_("Error"),
                                        _("You must select at least one "
                                          "drive to be used for installation."), customIcon="error")
                return False
            else:
                selectedDisks.sort(self.storage.compareDisks)
                self.storage.clearPartDisks = selectedDisks
                return True
        else:
            return True

    def nextCheck(self):
        if self.checkClearPartDisks():
            if self.ui.createCustom.isChecked():
                self.storage.clearPartType = CLEARPART_TYPE_NONE
                ctx.mainScreen.stepIncrement = 1
                self.storage.doAutoPart = False
                return True
            else:
                if self.ui.shrinkCurrent.isChecked():
                    shrinkeditor = ShrinkEditor(self, self.storage)
                    rc, operations = shrinkeditor.run()
                    if rc:
                        for operation in operations:
                            self.storage.devicetree.addOperation(operation)
                    else:
                        return False
                    # we're not going to delete any partitions in the resize case
                    self.storage.clearPartType = CLEARPART_TYPE_NONE
                elif self.ui.useAllSpace.isChecked():
                    self.storage.clearPartType = CLEARPART_TYPE_ALL
                elif self.ui.replaceExistingLinux.isChecked():
                    self.storage.clearPartType = CLEARPART_TYPE_LINUX
                elif self.ui.useFreeSpace.isChecked():
                    self.storage.clearPartType = CLEARPART_TYPE_NONE

                self.storage.doAutoPart = True
                self.storage.autoPartitionRequests = defaultPartitioning(self.storage, quiet=0)
                if not self.storage.clearPartDisks:
                    return False

                if self.ui.review.isChecked():
                    increment = 1
                else:
                    increment = 2
                ctx.mainScreen.stepIncrement = increment
                return doAutoPartition(self.storage)

        return False
