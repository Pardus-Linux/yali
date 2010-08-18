# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2010 TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#

import os
import gettext
__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext

from PyQt4 import QtGui
from PyQt4.QtCore import SIGNAL

import yali.storage
from yali.gui.installdata import *
from yali.gui.ScreenWidget import ScreenWidget
from yali.gui.Ui.rescuegrubwidget import Ui_RescueGrubWidget
from yali.gui.GUIException import GUIException
import yali.gui.context as ctx

##
# BootLoader screen.
class Widget(QtGui.QWidget, ScreenWidget):
    title = _("Repair the Bootloader")
    icon = "iconBootloader"
    help = _("""
<font size="+2">Repair bootloader</font>
<font size="+1">
<p>
A bootloader is a tiny program that runs when a computer is first powered up.
It is responsible for loading the operating system into memory and then transferring
the control to it.
</p>
<p>
Pardus uses GRUB (GRand Unified Bootloader) as the default bootloader. GRUB allows you
to boot any supported operating system by presenting the user with a menu.
</p>
<p>
You may want to repair GRUB bootloader if you installed another operating system which replaces GRUB with its own bootloader thus avoiding you to boot into Pardus. You may also want to repair GRUB if you're stuck with strange GRUB errors during boot.
<p>
The recommended way to use GRUB is to install it to the beginning of the boot disk.
You can always choose another installation method if you know what you are doing.
</p>
</font>
""")

    def __init__(self, *args):
        QtGui.QWidget.__init__(self,None)
        self.ui = Ui_RescueGrubWidget()
        self.ui.setupUi(self)

        self.ui.installFirstMBR.setChecked(True)

        # fill device list
        for dev in yali.storage.devices:
            DriveItem(self.ui.deviceList, dev)

        # select the first disk by default
        self.ui.deviceList.setCurrentRow(0)

        # be sure first is selected device
        self.device = self.ui.deviceList.item(0).getDevice()

        self.connect(self.ui.deviceList, SIGNAL("currentItemChanged(QListWidgetItem*,QListWidgetItem*)"), self.slotDeviceChanged)
        self.connect(self.ui.deviceList, SIGNAL("itemClicked(QListWidgetItem*)"), self.slotSelect)

    def shown(self):
        ctx.mainScreen.disableBack()
        yali.storage.setOrderedDiskList()
        ctx.logger.debug("Disks BIOS Boot order : %s " % ','.join(ctx.installData.orderedDiskList))

    def slotSelect(self):
        self.ui.installSelectedDisk.toggle()

    def slotDeviceChanged(self, o, n):
        self.device = o.getDevice()
        ctx.bootLoaderOptionalDev = self.device

    def execute(self):
        ctx.installData.bootLoaderOptionalDev = self.device

        # Apply GRUB Options
        if self.ui.installSelectedPart.isChecked():
            ctx.installData.bootLoaderOption = B_INSTALL_PART
            ctx.installData.bootLoaderDev = ctx.installData.rescuePartition.getPath()
        elif self.ui.installSelectedDisk.isChecked():
            ctx.installData.bootLoaderOption = B_INSTALL_MBR
            ctx.installData.bootLoaderDev = os.path.basename(ctx.installData.bootLoaderOptionalDev.getPath())
        elif self.ui.installFirstMBR:
            ctx.installData.bootLoaderOption = B_INSTALL_SMART
            ctx.yali.guessBootLoaderDevice(ctx.installData.rescuePartition.getPath())

        ctx.logger.debug("Bootloader Option is %s" % ctx.installData.bootLoaderOption)
        ctx.logger.debug("Bootloader Device is %s" % ctx.installData.bootLoaderDev)
        ctx.logger.debug("Bootloader Partition is %s" % ctx.installData.rescuePartition.getPath())

        ctx.mainScreen.stepIncrement = 3
        return True

class DriveItem(QtGui.QListWidgetItem):
    def __init__(self, parent, drive):
        text = u"%s on %s (%s) MB" % (drive.model, drive.name, str(int(drive.size)))
        QtGui.QListWidgetItem.__init__(self, text, parent)
        self.drive = drive

    def setBootable(self):
        self.setText(_("%s (Boot Disk)" % self.text))
