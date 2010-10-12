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
from yali.gui.Ui.driveselectionwidget import Ui_DriveSelectionWidget
from yali.gui.Ui.partitionshrinkwidget import Ui_PartShrinkWidget
from yali.gui.Ui.diskItem import Ui_DiskItem
from yali.storage.partitioning import CLEARPART_TYPE_ALL, CLEARPART_TYPE_LINUX, CLEARPART_TYPE_NONE, doAutoPartition, defaultPartitioning
from yali.storage.operations import OperationResizeDevice, OperationResizeFormat


class ShrinkWidget(QtGui.QWidget):
    def __init__(self, parent):
        QtGui.QWidget.__init__(self, ctx.mainScreen)
        self.parent = parent
        self.ui = Ui_PartShrinkWidget()
        self.ui.setupUi(self)
        self.setStyleSheet("""
                     QSlider::groove:horizontal {
                         border: 1px solid #999999;
                         height: 12px;
                         background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #B1B1B1, stop:1 #c4c4c4);
                         margin: 2px 0;
                     }

                     QSlider::handle:horizontal {
                         background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #b4b4b4, stop:1 #8f8f8f);
                         border: 1px solid #5c5c5c;
                         width: 18px;
                         margin: 0 0;
                         border-radius: 2px;
                     }

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

    def check(self):
        return self.ui.partitions.count() == 0

    def fillPartitions(self):
        biggest = -1
        i = -1
        for partition in self.parent.storage.partitions:
            if not partition.exists:
                continue

            if partition.resizable and partition.format.resizable:
                entry = PartitionItem(self.ui.partitions, partition)

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
        try:
            reqlower = long(math.ceil(request.format.minSize))
        except FilesystemError, msg:
            raise GUIError, msg
        else:
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

class DrivesListItem(QtGui.QListWidgetItem):
    def __init__(self, parent, widget):
        QtGui.QListWidgetItem.__init__(self, parent)
        self.widget = widget
        self.setSizeHint(QSize(widget.width()-20, widget.height()))

class DriveItem(QtGui.QWidget, Ui_DiskItem):
    def __init__(self, parent, drive, name):
        QtGui.QWidget.__init__(self, parent)
        self.setupUi(self)
        if drive.removable:
            self.icon.setPixmap(QtGui.QPixmap(":/gui/pics/drive-removable-media-usb-big.png"))
        elif drive.name.startswith("mmc"):
            self.icon.setPixmap(QtGui.QPixmap(":/gui/pics/media-flash-sd-mmc-big.png"))
        else:
            self.icon.setPixmap(QtGui.QPixmap(":/gui/pics/drive-harddisk-big.png"))
        self.labelDrive.setText("%s" % (name))
        self.labelInfo.setText("%s\n%s GB" % (drive.model, str(int(drive.size) / 1024)))
        #self.drive = drive
        #self.parent = parent

class PartitionItem(QtGui.QListWidgetItem):

    def __init__(self, parent, partition):
        text = u"%s (%s, %d MB)" % (partition.name, partition.format.name, math.floor(partition.format.size))
        QtGui.QListWidgetItem.__init__(self, text, parent)
        self.partition = partition


class Widget(QtGui.QWidget, ScreenWidget):
    title = _("Select a Drive to Install Pardus")
    icon = "iconPartition"
    help = _('''
<p>
You can install Pardus if you have an unpartitioned-unused disk space 
of 4GBs (10 GBs recommended) or an unused-unpartitioned disk. 
The disk area or partition selected for installation will automatically 
be formatted. Therefore, it is advised to backup your data to avoid future problems.
</p>
<p>Auto-partitioning will automatically format the select disk part/partition 
and install Pardus. If you like, you can do the partitioning manually or make 
Pardus create a new partition for installation.</p>
''')

    def __init__(self, *args):
        QtGui.QWidget.__init__(self,None)
        self.ui = Ui_DriveSelectionWidget()
        self.ui.setupUi(self)
        self.storage = ctx.storage
        self.intf = ctx.yali
        self.shrinkOperations = None
        self.clearPartDisks = None

        self.useAllSpace, self.replaceExistingLinux, self.shrinkCurrent, self.useFreeSpace, self.createCustom = range(5)
        self.connect(self.ui.drives, SIGNAL("itemSelectionChanged()"), self.itemStateChanged)

    def itemStateChanged(self):
        self.selectedDisks = []

        for item in self.ui.drives.selectedItems():
            self.selectedDisks.append(str(item.statusTip()))

        self.selectedDisks.sort(self.storage.compareDisks)

        if len(self.selectedDisks):
            ctx.mainScreen.enableNext()
        else:
            ctx.mainScreen.disableNext()

        print self.selectedDisks

    def typeChanged(self, index):
        if index != self.createCustom:
            self.ui.review.setEnabled(True)
            if index == self.shrinkCurrent:
                shrinkwidget = ShrinkWidget(self)
                if shrinkwidget.check():
                    self.intf.messageWindow(_("Error"),
                                            _("No partitions are available to resize.Only physical\n"
                                              "partitions with specific filesystems can be resized."),
                                            type="warning", customIcon="error")
                else:
                    shrinkwidget.show()
                    if shrinkwidget.operations:
                        self.shrinkOperations = shrinkwidget.operations
                    else:
                        return False
        else:
            self.ui.review.setEnabled(False)

        ctx.mainScreen.enableNext()

    def fillDrives(self):
        disks = filter(lambda d: not d.format.hidden, self.storage.disks)
        self.ui.drives.clear()

        count = 1
        for disk in disks:
            if disk.size >= ctx.consts.min_root_size:
                # GUI Hack
                if len(disks) <= 4:
                    self.ui.drives.setMinimumWidth(150 * len(disks))
                    self.ui.drives.setMaximumWidth(150 * len(disks))
                else:
                    self.ui.drives.setMinimumWidth(600)
                    self.ui.drives.setMaximumWidth(600)

                name = "Disk %s" % count
                drive = DriveItem(self.ui.drives, disk, name)
                listItem = DrivesListItem(self.ui.drives, drive)
                listItem.setStatusTip(disk.name)
                listItem.setToolTip("System Path: %s" % (disk.name))
                self.ui.drives.setGridSize(QSize(drive.width(), drive.height()))
                self.ui.drives.setItemWidget(listItem, drive)

            count += 1
        # select the first disk by default
        self.ui.drives.setCurrentRow(0)

    def shown(self):
        self.storage.reset()
        if self.storage.checkNoDisks(self.intf):
            sys.exit(0)
        else:
            self.fillDrives()

    def nextCheck(self):

        if len(self.selectedDisks) == 0:
            self.intf.messageWindow(_("Error"),
                                    _("You must select at least one "
                                      "drive to be used for installation."), customIcon="error")
            return False
        else:
            self.selectedDisks.sort(self.storage.compareDisks)
            self.storage.clearPartDisks = self.selectedDisks
            return True

    def execute(self):
        return self.nextCheck()
