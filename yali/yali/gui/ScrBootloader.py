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
import gettext

__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext

from PyQt4 import QtGui
from PyQt4.QtCore import *

import yali.gui.context as ctx
from yali.gui.ScreenWidget import ScreenWidget
from yali.gui.Ui.bootloaderwidget import Ui_BootLoaderWidget
from yali.storage.bootloader import BOOT_TYPE_NONE, BOOT_TYPE_PARTITION, BOOT_TYPE_MBR, BootLoaderError, boot_type_strings

class DriveItem(QtGui.QListWidgetItem):
    def __init__(self, parent, drive):
        text = u"%s on %s (%s) MB" % (drive.model, drive.name, str(int(drive.size)))
        QtGui.QListWidgetItem.__init__(self, text, parent)
        self.drive = drive

    def setBootable(self):
        self.setText(_("%s (Boot Disk)" % self.text))


##
# BootLoader screen.
class Widget(QtGui.QWidget, ScreenWidget):
    title = _("Configure Bootloader")
    icon = "iconBootloader"
    help = _("""
<font size="+2">Bootloader</font>
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
The recommended way to use GRUB is to install it to the beginning of the boot disk.
You can always choose another installation method if you know what you are doing.
</p>
</font>
""")

    def __init__(self, *args):
        QtGui.QWidget.__init__(self,None)
        self.ui = Ui_BootLoaderWidget()
        self.ui.setupUi(self)
        self.bootloader = ctx.bootloader
        self.bootloader.storage = ctx.storage
        self.drives = self.bootloader.drives
        self.device = None
        self.initialDevice = None

        self.connect(self.ui.drives, SIGNAL("currentItemChanged(QListWidgetItem*, QListWidgetItem*)"), self.slotDeviceChanged)
        self.connect(self.ui.selectDrive, SIGNAL("stateChanged(int)"), self.slotSelectDriveState)
        self.connect(self.ui.installPartition,  SIGNAL("toggled(boo)"), self.disableDrives)

    def fillDrives(self):
        self.ui.drives.clear()
        self.drives = self.bootloader.drives

        if not len(self.drives):
            raise BootLoaderError, _("No drives found.")

        if len(self.drives) ==  1:
            self.ui.drives.hide()
        else:
            for drive in self.drives:
                DriveItem(self.ui.drives, ctx.storage.devicetree.getDeviceByName(drive))

            self.ui.drives.setCurrentRow(0)

    def shown(self):
        self.fillDrives()
        choices = self.bootloader.choices
        for choice, (device, bootType) in choices.items():
            if choice == BOOT_TYPE_MBR:
                self.ui.installMBR.setText("%s - %s" % (bootType, device))
            elif choice == BOOT_TYPE_PARTITION:
                self.ui.installPartition.setText("%s - %s" % (bootType, device))

        if self.bootloader.device is not None:
            self.device = self.bootloader.device
        else:
            if choices.has_key(BOOT_TYPE_MBR):
                self.device = choices[BOOT_TYPE_MBR][0]
                self.initialDevice = self.device
                self.ui.installMBR.setChecked(True)
            else:
                self.device = choices[BOOT_TYPE_PARTITION][0]
                self.ui.installPartition.setChecked(True)

    def backCheck(self):
        if ctx.storage.doAutoPart:
            ctx.mainScreen.moveInc = 2
        return True

    def disableDrives(self, state):
        if state:
            self.ui.drives.setEnabled(not state)
            self.ui.selectDrive.setChecked(Qt.Unchecked)

    def slotSelectDriveState(self, state):
        if state == Qt.Unchecked:
            self.device = self.initialDevice

    def slotDeviceChanged(self, current, previous):
        self.device = current.drive.name
        self.ui.installMBR.setText("%s - %s" % (boot_type_strings[BOOT_TYPE_MBR], self.device))

    def execute(self):
        self.bootloader.device = self.device
        if self.ui.noInstall.isChecked():
            ctx.bootloader.bootType = BOOT_TYPE_NONE
        elif self.ui.installPartition.isChecked():
            ctx.bootloader.bootType = BOOT_TYPE_PARTITION
        elif self.ui.installMBR.isChecked():
            ctx.bootloader.bootType = BOOT_TYPE_MBR

        self.bootloader.otherEnabled = self.ui.addOthers.isChecked()

        return True

