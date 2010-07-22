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

import yali.gui.context as ctx
from yali.gui.ScreenWidget import ScreenWidget
from yali.gui.Ui.autopartwidget import Ui_AutoPartWidget
from yali.gui.Ui.partitionshrinkwidget import Ui_PartShrinkWidget
from yali.storage.partitioning import CLEARPART_TYPE_ALL, CLEARPART_TYPE_LINUX, CLEARPART_TYPE_NONE, doAutoPartition
from yali.storage.operations import OperationResizeDevice, OperationResizeFormat

class ShrinkWidget(QtGui.QWidget):
    def __init__(self, parent):
        QtGui.QWidget.__init__(self, ctx.mainScreen)
        self.parent = parent
        self.ui = Ui_PartShrinkWidget()
        self.ui.setupUi(self)
        self.setStyleSheet("""
                QFrame#mainFrame {
                    background-image: url(:/gui/pics/transBlack.png);
                    border: 1px solid #BBB;
                    border-radius:8px;
                }
                QWidget#Ui_PartShrinkWidget {
                    background-image: url(:/gui/pics/trans.png);
                }
        """)
        self.operations = []
        QObject.connect(self.ui.partitions, SIGNAL("currentRowChanged(int)"), self.updateSpin)
        self.connect(self.ui.shrinkButton, SIGNAL("clicked()"), self.slotShrink)
        self.connect(self.ui.cancelButton, SIGNAL("clicked()"), self.hide)
        self.fillPartitions()
        if self.ui.partitions.count() == 0:
            self.hide()
            self.parent.intf.messageWindow(_("Error"),
                                           _("No partitions are available to resize.  Only "
                                             "physical partitions with specific filesystems can be resized."),
                                             type="warning", customIcon="error")

    def fillPartitions(self):
        biggest = -1
        i = -1
        for partition in self.parent.storage.partitions:
            if not partition.exists:
                continue

            if partition.resizable and partition.format.resizable:
                entry = PartitionItem(self.ui.partitions, partition)
                print "size:%s minsize:%s currentsize%s" % (partition.size, partition.format.minSize, partition.format.currentSize )

                i += 1
                if biggest == -1:
                    biggest = i
                else:
                    current = self.ui.partitions.item(biggest).partition
                    if partition.format.targetSize > current.format.targetSize:
                        biggest = i

        if biggest > -1:
            self.ui.partitions.setCurrentRow(biggest)

    def updateSpin(self, index):
        request = self.ui.partitions.item(index).partition
        reqlower = long(math.ceil(request.format.minSize))
        requpper = long(math.floor(request.format.currentSize))
        self.ui.shrinkMB.setMinimum(max(1, reqlower))
        self.ui.shrinkMB.setMaximum(requpper)
        self.ui.shrinkMB.setValue(reqlower)
        self.ui.shrinkMBSlider.setMinimum(max(1, reqlower))
        self.ui.shrinkMBSlider.setMaximum(requpper)
        self.ui.shrinkMBSlider.setValue(reqlower)

    def slotShrink(self):
        self.hide()
        runResize = True
        while runResize:
           index = self.ui.partitions.currentRow()
           request = self.ui.partitions.item(index).partition
           newsize = self.ui.shrinkMB.value()
           try:
               self.operations.append(OperationResizeFormat(request, newsize))
           except ValueError as e:
               self.parent.intf.messageWindow(_("Resize FileSystem Error"),
                                              _("%(device)s: %(msg)s") %
                                              {'device': request.format.device, 'msg': e.message},
                                              type="warning", customIcon="error")
               continue

           try:
               self.operations.append(OperationResizeDevice(request, newsize))
           except ValueError as e:
               self.parent.intf.messageWindow(_("Resize Device Error"),
                                              _("%(name)s: %(msg)s") %
                                               {'name': request.name, 'msg': e.message},
                                               type="warning", customIcon="error")
               continue

           runResize = False

        self.hide()

class DriveItem(QtGui.QListWidgetItem):
    def __init__(self, parent, drive):
        text = u"%s on %s (%s) MB" % (drive.model, drive.name, str(int(drive.size)))
        QtGui.QListWidgetItem.__init__(self, text, parent)
        self.drive = drive
        self.setCheckState(Qt.Unchecked)

class PartitionItem(QtGui.QListWidgetItem):

    def __init__(self, parent, partition):
        text = u"%s (%s, %d MB)" % (partition.name, partition.format.name, math.floor(partition.format.size))
        QtGui.QListWidgetItem.__init__(self, text, parent)
        self.partition = partition

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
        self.intf = ctx.yali
        self.shrinkOperations = None

        self.connect(self.ui.useAllSpace, SIGNAL("clicked()"), self.typeChanged)
        self.connect(self.ui.replaceExistingLinux, SIGNAL("clicked()"), self.typeChanged)
        self.connect(self.ui.shrinkCurrent, SIGNAL("clicked()"), self.typeChanged)
        self.connect(self.ui.useFreeSpace, SIGNAL("clicked()"), self.typeChanged)
        self.connect(self.ui.createCustom, SIGNAL("clicked()"), self.typeChanged)
        #self.connect(self.ui.review, SIGNAL("stateChanged(int) "), self.typeChanged)
        #self.connect(self.ui.drives,   SIGNAL("currentItemChanged(QListWidgetItem *, QListWidgetItem * )"),self.slotDeviceChanged)
        self.ui.drives.hide()
        self.ui.drivesLabel.hide()

    def typeChanged(self):
        print "type changed sender:%s" % self.sender().objectName()
        if self.sender() != self.ui.createCustom:
            self.ui.review.setEnabled(True)
            print "not else sender:%s" % self.sender().objectName()
            if self.sender() == self.ui.shrinkCurrent:
                print "shrink control sender:shrinkCurrent"
                shrinkwidget = ShrinkWidget(self)
                shrinkwidget.show()
                if shrinkwidget.operations:
                    self.shrinkOperations = shrinkwidget.operations
                else:
                    return False
            else:
                print "not shrink control sender:%s" % self.sender().objectName()
        else:
            self.ui.review.setEnabled(False)

        ctx.mainScreen.enableNext()

    def setPartitioningType(self):
        if self.storage.clearPartType is None or self.storage.clearPartType == CLEARPART_TYPE_LINUX:
            self.ui.replaceExistingLinux.toggle()
        elif self.storage.clearPartType == CLEARPART_TYPE_NONE:
            self.ui.useFreeSpace.togg()
        elif self.storage.clearPartType == CLEARPART_TYPE_ALL:
            self.ui.useAllSpace.toggle()

    def fillDrives(self):
        disks = filter(lambda d: not d.format.hidden, self.storage.disks)
        self.ui.drives.clear()

        for disk in disks:
            if disk.size >= ctx.consts.min_root_size:
                DriveItem(self.ui.drives, disk)

        # select the first disk by default
        self.ui.drives.setCurrentRow(0)

    def shown(self):
        if self.storage.checkNoDisks(self.intf):
            raise GUIException, _("No storage device found.")
        else:
            self.fillDrives()
            self.setPartitioningType()

    def checkSelectedDisk(self):
        clearDisks = []
        for index in range(self.ui.drives.count()):
            if self.ui.drives.item(index).checkState() == Qt.Checked:
                clearDisks.append(self.ui.drives.item(index).drive)

        if len(clearDisks) == 0:
            self.intf.messageWindow(_("Error"),
                                    _("You must select at least one "
                                      "drive to be used for installation."), customIcon="error")
            ctx.mainScreen.disableNext()

        clearDisks.sort(self.storage.compareDisks)
        self.storage.clearPartDisks = clearDisks

    def execute(self):
        #self.checkSelectedDisk()
        rc = self.nextCheck()
        if rc is None:
            sys.exit(0)
        else:
            return rc

    def nextCheck(self):
        increment = 0
        if self.ui.createCustom.isChecked():
            ctx.mainScreen.stepIncrement = 1
            self.storage.clearPartType = CLEARPART_TYPE_NONE
        else:
            if self.ui.shrinkCurrent.isChecked():
                if self.shrinkOperations:
                    for operation in self.shrinkOperations:
                        self.storage.addOperation(operation)
                    self.storage.clearPartType = CLEARPART_TYPE_NONE
            elif self.ui.useAllSpace.isChecked():
                self.storage.clearPartType = CLEARPART_TYPE_ALL
            elif self.ui.replaceExistingLinux.isChecked():
                self.storage.clearPartType = CLEARPART_TYPE_LINUX
            elif self.ui.useFreeSpace.isChecked():
                self.storage.clearPartType = CLEARPART_TYPE_NONE

            self.storage.doAutoPart = True

            if self.ui.review.isChecked():
                increment = 1
            else:
                increment = 2

        ctx.mainScreen.stepIncrement = increment
        return doAutoPartition(self.storage)
