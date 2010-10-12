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

import yali.context as ctx
from yali.gui.ScreenWidget import ScreenWidget
from yali.gui.Ui.bootloaderwidget import Ui_BootLoaderWidget
from yali.storage.bootloader import BOOT_TYPE_NONE, BOOT_TYPE_PARTITION, BOOT_TYPE_MBR, BootLoaderError, boot_type_strings

class DriveItem(QtGui.QListWidgetItem):
    def __init__(self, parent, drive):
        text = u"%s on %s (%s) MB" % (drive.model, drive.name, str(int(drive.size)))
        QtGui.QListWidgetItem.__init__(self, text, parent)
        self.drive = drive

##
# BootLoader screen.
class Widget(QtGui.QWidget, ScreenWidget):
    title = _("Configure Bootloader")
    icon = "iconBootloader"
    helpSummary = _("A bootloader is a tiny program that runs when a computer is first powered up.")
    help = _("""
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
""")

    def __init__(self, *args):
        QtGui.QWidget.__init__(self,None)
        self.ui = Ui_BootLoaderWidget()
        self.ui.setupUi(self)
        self.bootloader = ctx.bootloader
        self.bootloader.storage = ctx.storage
        self.device = None
        self.initialDevice = None

        self.connect(self.ui.defaultSettings, SIGNAL("toggled(bool)"), self.hideAdvancedSettings)
        self.connect(self.ui.advancedSettings, SIGNAL("toggled(bool)"), self.showAdvancedSettings)
        self.connect(self.ui.installMBR, SIGNAL("toggled(bool)"), self.ui.drives.setEnabled)
        self.connect(self.ui.installPartition, SIGNAL("toggled(bool)"), self.activateInstallPartition)
        self.connect(self.ui.drives, SIGNAL("currentRowChanged(int)"), self.currentDeviceChanged)

        self.ui.advancedSettingsBox.show()
        self.ui.defaultSettings.setChecked(True)

    def hideAdvancedSettings(self):
        self.ui.advancedSettingsBox.hide()

    def showAdvancedSettings(self):
        self.ui.advancedSettingsBox.show()


    def fillDrives(self):
        self.ui.drives.clear()
        if len(self.bootloader.drives) ==  1:
            self.ui.drives.hide()

        for drive in self.bootloader.drives:
            device = ctx.storage.devicetree.getDeviceByName(drive)
            item = u"%s" % (device.name)
            self.ui.drives.addItem(item, device)

        self.ui.drives.setCurrentRow(0)

    def activateChoices(self):
        for choice, (device, bootType) in self.bootloader.choices.items():
            if choice == BOOT_TYPE_MBR:
                self.ui.installMBR.setText("The first sector of")
            elif choice == BOOT_TYPE_PARTITION:
                self.ui.installPartition.setText("The partition where Pardus is installed")

        if self.bootloader.choices.has_key(BOOT_TYPE_MBR):
            self.device = self.bootloader.choices[BOOT_TYPE_MBR][0]
            self.initialDevice = self.device
            self.ui.installMBR.setChecked(True)
        else:
            self.device = self.bootloader.choices[BOOT_TYPE_PARTITION][0]
            self.initialDevice = self.device
            self.ui.installPartition.setChecked(True)


    def checkBoxState(self, state):
        if state == Qt.Checked:
            self.ui.drives.setEnabled(True)
            #self.device = self.bootloader.choices[BOOT_TYPE_PARTITION][0]
            for index in range(self.ui.drives.count()):
                if self.device == self.ui.drives.item(index).drive.name:
                    self.ui.drives.setCurrentRow(index)
        else:
            self.ui.drives.setEnabled(False)
            self.device = self.initialDevice
            self.ui.installMBR.setText("%s - %s" % (boot_type_strings[BOOT_TYPE_MBR], self.device))

    def activateInstallPartition(self, state):
        #self.ui.drives.setCurrentRow(0)
        self.ui.drives.setEnabled(not state)
        if state:
            self.device =  str(self.ui.installPartition.text()).split("-")[1].strip()

    def currentDeviceChanged(self, current):
        if self.ui.drives.item(current):
            self.device = self.ui.drives.itemData(current).toPyObject().name
            self.ui.installMBR.setText("%s - %s" % (boot_type_strings[BOOT_TYPE_MBR], self.device))

    def shown(self):
        self.fillDrives()
        self.activateChoices()

    def backCheck(self):
        if ctx.storage.doAutoPart:
            ctx.mainScreen.stepIncrement = 2
        return True

    def execute(self):
        self.bootloader.device = self.device
        if self.ui.noInstall.isChecked():
            self.bootloader.bootType = BOOT_TYPE_NONE
        elif self.ui.installPartition.isChecked():
            self.bootloader.bootType = BOOT_TYPE_PARTITION
        elif self.ui.installMBR.isChecked():
            self.bootloader.bootType = BOOT_TYPE_MBR

        self.bootloader.otherEnabled = self.ui.addOthers.isChecked()

        return True
