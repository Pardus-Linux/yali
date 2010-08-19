# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2010 TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#
import os
import time
import gettext

__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext

from PyQt4 import QtGui
from PyQt4.QtCore import *

import yali.util
import yali.context as ctx
from yali.installdata import YALI_PLUGIN, YALI_INSTALL, YALI_DVDINSTALL
from yali.gui.ScreenWidget import ScreenWidget
from yali.gui.YaliDialog import QuestionDialog
from yali.gui.Ui.summarywidget import Ui_SummaryWidget
from yali.storage.partitioning import CLEARPART_TYPE_ALL, CLEARPART_TYPE_LINUX, CLEARPART_TYPE_NONE
from yali.storage.bootloader import BOOT_TYPE_NONE
class Widget(QtGui.QWidget, ScreenWidget):
    title = _("Summary")
    #icon = "iconKeyboard"
    help = _('''
<font size="+2">Installation Summary</font>
<font size="+1">
<p>
Here you can see your install options before installation starts.
</p>
</font>
''')

    def __init__(self, *args):
        QtGui.QWidget.__init__(self,None)
        self.ui = Ui_SummaryWidget()
        self.ui.setupUi(self)

        self.ui.content.setText("")
        self.timer = QTimer()

        try:
            self.connect(self.timer, SIGNAL("timeout()"), self.updateCounter)
        except:
            pass

    def slotReboot(self):
        reply = QuestionDialog(_("Restart"),
                               _('''<b><p>Are you sure you want to restart the computer?</p></b>'''))
        if reply == "yes":
            yali.util.reboot()

    def startBombCounter(self):
        self.startTime = int(time.time())
        self.timer.start(1000)

    def backCheck(self):
        self.timer.stop()
        ctx.yali.info.hide()
        ctx.mainScreen.ui.buttonNext.setText(_("Next"))
        return True

    def updateCounter(self):
        remain = 20 - (int(time.time()) - self.startTime)
        ctx.yali.info.updateAndShow(_("Installation starts in <b>%s</b> seconds") % remain)
        if remain <= 0:
            self.timer.stop()
            ctx.mainScreen.slotNext()

    def shown(self):
        #ctx.mainScreen.disableNext()
        ctx.mainScreen.ui.buttonNext.setText(_("Start Installation"))
        if ctx.installData.isKahyaUsed:
            self.startBombCounter()
        self.fillContent()
        # FIXME Later
        self.ui.installAllLangPacks.setChecked(True)
        self.ui.installAllLangPacks.hide()

    def fillContent(self):
        subject = "<p><li><b>%s</b></li><ul>"
        item    = "<li>%s</li>"
        end     = "</ul></p>"
        content = QString("")

        content.append("""<html><body><ul>""")

        # Plugin Summary
        if ctx.yali.install_type == YALI_PLUGIN:
            try:
                _summary = ctx.yali.plugin.config.getSummary()
                content.append(subject % _summary["subject"])
                for _item in _summary["items"]:
                    content.append(item % _item)
                content.append(end)
            except:
                pass

        # Keyboard Layout
        if ctx.installData.keyData:
            content.append(subject % _("Keyboard Settings"))
            content.append(item %
                           _("Selected keyboard layout is <b>%s</b>") %
                           ctx.installData.keyData["name"])
            content.append(end)

        # TimeZone
        content.append(subject % _("Date/Time Settings"))
        content.append(item %
                       _("Selected TimeZone is <b>%s</b>") %
                       ctx.installData.timezone)
        content.append(end)

        # Users
        if len(yali.users.pending_users)>0:
            content.append(subject % _("User Settings"))
            for user in yali.users.pending_users:
                state = _("User %s (<b>%s</b>) added.")
                if "wheel" in user.groups:
                    state = _("User %s (<b>%s</b>) added with <u>administrator privileges</u>.")
                content.append(item % state % (user.realname, user.username))
            content.append(end)

        # HostName
        if ctx.installData.hostName:
            content.append(subject % _("Hostname Settings"))
            content.append(item %
                           _("Hostname is set as <b>%s</b>") %
                           ctx.installData.hostName)
            content.append(end)

        # Partition
        self.resizeAction = ctx.storage.devicetree.findOperations(type="resize")
        content.append(subject % _("Partition Settings"))
        if ctx.storage.doAutoPart:
            summary = ""
            clearPartDisks = ctx.storage.clearPartDisks
            devices = ""
            for disk in clearPartDisks:
                devices += "(%s on %s)" % (disk.model, disk.name)

            content.append(item % _("Automatic Partitioning selected."))
            if ctx.storage.clearPartType == CLEARPART_TYPE_ALL:
                content.append(item % _("Use All Space"))
                content.append(item % _("Removes all partitions on the selected"\
                                        "%s device(s). This includes partitions "\
                                        "created by other operating systems.") % devices)
            elif ctx.storage.clearPartType == CLEARPART_TYPE_LINUX:
                content.append(item % _("Replace Existing Linux System(s)"))
                content.append(item % _("Removes all Linux partitions on the selected" \
                                        "%s device(s). This does not remove "\
                                        "other partitions you may have on your " \
                                        "storage device(s) (such as VFAT or FAT32)") % devices)
            elif ctx.storage.clearPartType == CLEARPART_TYPE_NONE:
                content.append(item % _("Use Free Space"))
                content.append(item % _("Retains your current data and partitions" \
                                        " and uses only the unpartitioned space on " \
                                        "the selected %s device(s), assuming you have"\
                                        "enough free space available.") % devices)

        else:
            content.append(item % _("Manual Partitioning selected."))
            for operation in ctx.storage.devicetree.operations:
                content.append(item % operation)

        content.append(end)

        # Bootloader
        content.append(subject % _("Bootloader Settings"))
        grubstr = _("GRUB will be installed to <b>%s</b>.")
        if ctx.bootloader.bootType == BOOT_TYPE_NONE:
            content.append(item % _("GRUB will not be installed."))
        else:
            content.append(item % grubstr % ctx.bootloader.device)

        content.append(end)

        if ctx.yali.install_type == YALI_DVDINSTALL:
            # DVD INSTALL
            content.append(subject % _("Package Installation Settings"))
            #installation_str = _("Installation Collection <b>%s</b> installed.")
            if ctx.installData.autoInstallationMethod == methodInstallAutomatic:
                content.append(item % _("Auto installation selected."))
            else:
                content.append(item % _("Manual Installation ( %s ) selected" %
                               ctx.installData.autoInstallationCollection.title))

            if ctx.installData.autoInstallationKernel == defaultKernel:
                content.append(item % _("Default Kernel selected"))
            elif ctx.installData.autoInstallationKernel == paeKernel:
                content.append(item % _("PAE Kernel selected"))
            #elif ctx.installData.autoInstallationKernel == rtKernel:
            #    content.append(item % _("Real Time Kernel selected"))

            content.append(end)

        content.append("""</ul></body></html>""")

        self.ui.content.setHtml(content)

    def execute(self):

        # Just store normal installation session
        #if ctx.yali.install_type == YALI_INSTALL:
        #    ctx.yali.backupInstallData()

        self.timer.stop()

        rc = ctx.yali.messageWindow(_("Confirm"),
                                    _("The partitioning options you have selected"
                                      "will now be\nwritten to disk.  Any"
                                      "data on deleted or reformatted partitions\n"
                                      "will be lost."),
                                      type = "custom", customIcon="warning",
                                      customButtons=[_("Go Back"), _("Write Changes to Disk")],
                                      default = 0)
        ctx.storage.devicetree.teardownAll()

        if rc == 0:
            ctx.logger.info("unmounting filesystems")
            ctx.storage.umountFilesystems()
            return

        ctx.installData.installAllLangPacks = self.ui.installAllLangPacks.isChecked()
        ctx.mainScreen.processEvents()

        if ctx.options.dryRun == True:
            ctx.logger.debug("dryRun activated Yali stopped")
            return

        # Auto Partitioning
        if not ctx.storage.storageset.swapDevices:
            size = 0
            if yali.util.memInstalled() > 512:
                size = 300
            else:
                size = 600
            ctx.storage.storageset.createSwapFile(ctx.storage.storageset.rootDevice,\
                                                  ctx.constants.target_dir, size)
        if ctx.storage.doAutoPart:
            ctx.yali.info.updateMessage(_("Auto partitioning..."))
            ctx.logger.debug("Auto partitioning")
        else:
            ctx.yali.info.updateMessage(_("Manual partitioning..."))
            ctx.logger.debug("Manual partitioning...")

        ctx.yali.storageComplete()
        ctx.yali.info.updateMessage(_("Partitioning finished..."))
        ctx.logger.debug("Partitioning finished")
        ctx.yali.info.hide()

        ctx.mainScreen.stepIncrement = 1
        ctx.mainScreen.ui.buttonNext.setText(_("Next"))
        return True
