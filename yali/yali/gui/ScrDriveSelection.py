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
        self.intf = ctx.interface
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
