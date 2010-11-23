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
import time
import gettext
_ = gettext.translation('yali', fallback=True).ugettext

from PyQt4.Qt import QWidget, SIGNAL, QTimer, QString

import yali.util
import yali.context as ctx
import yali.storage
import yali.users
from yali.gui import ScreenWidget
from yali.gui.YaliDialog import QuestionDialog
from yali.gui.Ui.summarywidget import Ui_SummaryWidget
from yali.storage.partitioning import CLEARPART_TYPE_ALL, CLEARPART_TYPE_LINUX, CLEARPART_TYPE_NONE
from yali.storage.bootloader import BOOT_TYPE_NONE

class Widget(QWidget, ScreenWidget):
    name = "summary"

    def __init__(self):
        QWidget.__init__(self)
        self.ui = Ui_SummaryWidget()
        self.ui.setupUi(self)

        self.ui.content.setText("")
        self.timer = QTimer()
        self.start_time = 0

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
        self.start_time = int(time.time())
        self.timer.start(1000)

    def backCheck(self):
        self.timer.stop()
        ctx.interface.informationWindow.hide()
        ctx.mainScreen.ui.buttonNext.setText(_("Next"))
        if (ctx.flags.install_type == ctx.STEP_BASE or ctx.flags.install_type == ctx.STEP_DEFAULT) \
           and not ctx.flags.collection:
            ctx.mainScreen.step_increment = 2
        return True

    def updateCounter(self):
        remain = 20 - (int(time.time()) - self.start_time)
        ctx.interface.informationWindow.update(_("Installation starts in <b>%s</b> seconds") % remain)
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

        # Keyboard Layout
        if ctx.installData.keyData:
            content.append(subject % _("Keyboard Settings"))
            content.append(item %
                           _("Selected keyboard layout is <b>%s</b>") %
                           ctx.installData.keyData["name"])
            content.append(end)

        # TimeZone
        if ctx.installData.timezone:
            content.append(subject % _("Date/Time Settings"))
            content.append(item %
                           _("Selected TimeZone is <b>%s</b>") %
                           ctx.installData.timezone)
            content.append(end)

        # Users
        if len(yali.users.PENDING_USERS) > 0:
            content.append(subject % _("User Settings"))
            for user in yali.users.PENDING_USERS:
                state = _("User %(username)s (<b>%(realname)s</b>) added.")
                if "wheel" in user.groups:
                    state = _("User %(username)s (<b>%(realname)s</b>) added with <u>administrator privileges</u>.")
                content.append(item % state % {"username":user.realname, "realname":user.username})
            content.append(end)

        # HostName
        if ctx.installData.hostName:
            content.append(subject % _("Hostname Settings"))
            content.append(item %
                           _("Hostname is set as <b>%s</b>") %
                           ctx.installData.hostName)
            content.append(end)

        # Partition
        if ctx.storage.clearPartType is not None:
            content.append(subject % _("Partition Settings"))
            devices = ""
            for disk in ctx.storage.clearPartDisks:
                device = ctx.storage.devicetree.getDeviceByName(disk)
                devices += "(%s on %s)" % (device.model, device.name)

            if ctx.storage.doAutoPart:
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
        if ctx.bootloader.device:
            content.append(subject % _("Bootloader Settings"))
            grubstr = _("GRUB will be installed to <b>%s</b>.")
            if ctx.bootloader.bootType == BOOT_TYPE_NONE:
                content.append(item % _("GRUB will not be installed."))
            else:
                content.append(item % grubstr % ctx.bootloader.device)

            content.append(end)

        if ctx.flags.collection:
            content.append(subject % _("Package Installation Settings"))
            if ctx.installData.autoInstallationMethod == ctx.methodInstallAutomatic:
                content.append(item % _("Auto installation selected."))
            else:
                content.append(item % _("Manual Installation ( %s ) selected" %
                               ctx.installData.autoInstallationCollection.title))

            if ctx.installData.autoInstallationKernel == ctx.defaultKernel:
                content.append(item % _("Default Kernel selected"))
            elif ctx.installData.autoInstallationKernel == ctx.paeKernel:
                content.append(item % _("PAE Kernel selected"))

            content.append(end)

        content.append("""</ul></body></html>""")

        self.ui.content.setHtml(content)

    def execute(self):
        self.timer.stop()

        if ctx.flags.dryRun:
            ctx.logger.debug("dryRun activated Yali stopped")
            ctx.mainScreen.enableBack()
            return False

        if ctx.flags.install_type == ctx.STEP_BASE or ctx.flags.install_type == ctx.STEP_DEFAULT:
            rc = ctx.interface.messageWindow(_("Confirm"),
                                        _("The partitioning options you have selected "
                                          "will now be\nwritten to disk.  Any "
                                          "data on deleted or reformatted partitions\n"
                                          "will be lost."),
                                          type = "custom", customIcon="question",
                                          customButtons=[_("Write Changes to Disk"), _("Go Back")],
                                          default=1)

            ctx.installData.installAllLangPacks = self.ui.installAllLangPacks.isChecked()
            ctx.mainScreen.processEvents()

            if not rc:
                if yali.storage.complete(ctx.storage, ctx.interface):
                    ctx.storage.turnOnSwap()
                    ctx.storage.mountFilesystems(readOnly=False, skipRoot=False)
                    ctx.mainScreen.step_increment = 1
                    ctx.mainScreen.ui.buttonNext.setText(_("Next"))
                    return True

            ctx.mainScreen.enableBack()
            return False

        elif ctx.flags.install_type == ctx.STEP_FIRST_BOOT:
            return True


        # Auto Partitioning
        #if not ctx.storage.storageset.swapDevices:
        #    size = 0
        #    if yali.util.memInstalled() > 512:
        #        size = 300
        #    else:
        #        size = 600
        #    ctx.storage.storageset.createSwapFile(ctx.storage.storageset.rootDevice, ctx.consts.target_dir, size)


