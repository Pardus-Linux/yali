# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2009, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#

# base
import os
import time
import yali.sysutils
from yali.gui.installdata import *

# multi language
import gettext
__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext

# PyQt4 Rocks
from PyQt4 import QtGui
from PyQt4.QtCore import *

# libParted
from yali.parteddata import *
import yali.partitionrequest as request
import yali.partitiontype as parttype

# GUI Stuff
from yali.gui.ScreenWidget import ScreenWidget
from yali.gui.YaliDialog import QuestionDialog
from yali.gui.Ui.summarywidget import Ui_SummaryWidget
import yali.gui.context as ctx

##
# Summary screen
class Widget(QtGui.QWidget, ScreenWidget):
    title = _('The last step before install')
    desc = _('Summary of your installation...')
    #icon = "iconKeyboard"
    help = _('''
<font size="+2">Install Summary</font>
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

        # Handle translators tool problems ..
        try:
            #self.connect(self.ui.install, SIGNAL("clicked()"), ctx.mainScreen.slotNext)
            #self.connect(self.ui.cancel, SIGNAL("clicked()"), self.slotReboot)
            self.connect(self.timer, SIGNAL("timeout()"), self.updateCounter)
        except:
            pass

    def slotReboot(self):
        reply = QuestionDialog(_("Reboot"),
                               _('''<b><p>This action will reboot your system.</p></b>'''))
        if reply == "yes":
            yali.sysutils.reboot()

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
        ctx.yali.info.updateAndShow(_("Install starts in: <b>%s seconds</b>") % remain)
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
            content.append(item % _("Selected keyboard layout is <b>%s</b>") % ctx.installData.keyData["name"])
            content.append(end)

        # TimeZone
        content.append(subject % _("Date/Time Settings"))
        content.append(item % _("Selected TimeZone is <b>%s</b>") % ctx.installData.timezone)
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
            content.append(item % _("Hostname is set as <b>%s</b>") % ctx.installData.hostName)
            content.append(end)

        # Partition
        pardus_path = None
        self.resizeAction = False
        content.append(subject % _("Partition Settings"))
        if ctx.installData.autoPartMethod == methodEraseAll:
            content.append(item % _("Automatic Partitioning selected."))
            dev = ctx.installData.autoPartDev
            _sum = {"device":dev.getModel(),
                    "partition":dev.getName()+"1",
                    "size":dev.getTotalMB(),
                    "fs":parttype.root.filesystem.name(),
                    "type":parttype.root.name}

            pardus_path = dev.getPath()+"1"
            content.append(item % _("All partitions on device <b>%(device)s</b> has been deleted.") % _sum)
            content.append(item % _("Partition <b>%(partition)s</b> <b>added</b> to device <b>%(device)s</b> with <b>%(size)s MBs</b> as <b>%(fs)s</b>.") % _sum)
            content.append(item % _("Partition <b>%(partition)s</b> <b>selected</b> as <b>%(type)s</b>.") % _sum)

        elif ctx.installData.autoPartMethod == methodUseAvail:
            dev = ctx.installData.autoPartDev
            _part = ctx.installData.autoPartPartition
            part = _part["partition"]
            pardus_path = "%s%s" % (dev.getPath(), int(part._minor)+1)

            if part.isFreespace():
                _sum = {"device":dev.getModel(),
                        "partition":part.getName(),
                        "newPartition":part.getName(),
                        "size":part.getMB(),
                        "currentFs":part._fsname,
                        "fs":parttype.root.filesystem.name(),
                        "type":parttype.root.name}
            else:
                content.append(item % _("Automatic Partitioning (resize method) selected."))
                self.resizeAction = True
                newPartSize = int(_part["newSize"]/2)
                ctx.debugger.log("UA: newPartSize : %s " % newPartSize)
                resizeTo = int(part.getMB()) - newPartSize

                _sum = {"device":dev.getModel(),
                        "partition":part.getName(),
                        "newPartition":"%s%s" % (part.getName()[:-1],int(part._minor)+1),
                        "size":newPartSize,
                        "currentFs":part._fsname,
                        "fs":parttype.root.filesystem.name(),
                        "type":parttype.root.name,
                        "currentSize":part.getMB(),
                        "resizeTo":resizeTo}

                content.append(item % _("Partition <b>%(partition)s - %(currentFs)s</b> <b>resized</b> to <b>%(resizeTo)s MBs</b>, previous size was <b>%(currentSize)s MBs</b>.") % _sum)

            content.append(item % _("Partition <b>%(newPartition)s</b> <b>added</b> to device <b>%(device)s</b> with <b>%(size)s MBs</b> as <b>%(fs)s</b>.") % _sum)
            content.append(item % _("Partition <b>%(newPartition)s</b> <b>selected</b> as <b>%(type)s</b>.") % _sum)

        else:
            for operation in ctx.partSum:
                content.append(item % operation)
        content.append(end)

        # Find BootLoader Device
        if not pardus_path:
            # manual partitioning gives us new grub target
            root_part_req = ctx.partrequests.searchPartTypeAndReqType(parttype.root,
                                                                      request.mountRequestType)
            pardus_path = root_part_req.partition().getPath()

        # Bootloader
        content.append(subject % _("Bootloader Settings"))
        grub_str = _("GRUB will be installed to <b>%s</b>.")
        if ctx.installData.bootLoaderOption == B_DONT_INSTALL:
            content.append(item % _("GRUB will not be installed."))
        elif ctx.installData.bootLoaderOption == B_INSTALL_PART:
            content.append(item % grub_str % pardus_path)
        elif ctx.installData.bootLoaderOption == B_INSTALL_MBR:
            content.append(item % grub_str % ctx.installData.bootLoaderOptionalDev.getPath())
        else:
            _path = ctx.yali.guessBootLoaderDevice(pardus_path)
            if not _path.startswith("/dev"): _path = "/dev/" + _path
            content.append(item % grub_str % _path)
        content.append(end)

        if ctx.yali.install_type == YALI_DVDINSTALL:
            # DVD INSTALL
            content.append(subject % _("Package Installation Settings"))
            #installation_str = _("Installation Collection <b>%s</b> installed.")
            if ctx.installData.autoInstallationMethod == methodInstallAutomatic:
                content.append(item % _("Auto installation selected."))
            else:
                content.append(item % _("Manual Installation ( %s ) selected" % ctx.installData.autoInstallationCollection.title))

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
        if ctx.yali.install_type == 0:
            ctx.yali.backupInstallData()

        self.timer.stop()

        if self.resizeAction:
            reply = QuestionDialog(_("Before Starting"),
                                   _("""<p><b><u>Warning</u></b>: There is a resizing operation and it may corrupt your partition,<br>
                                        rendering your data unreachable.<br>
                                        Make sure that you have a backup for this partition.<br>
                                        <b>Note that this operation cannot be undone.</b></p>"""))
            if reply == "no":
                ctx.mainScreen.moveInc = 0
                return

        #self.ui.install.setEnabled(False)
        #self.ui.cancel.setEnabled(False)
        ctx.installData.installAllLangPacks = self.ui.installAllLangPacks.isChecked()
        ctx.mainScreen.processEvents()

        # We should do partitioning operations in here.
        if ctx.options.dryRun == True:
            ctx.debugger.log("dryRun activated Yali stopped")
            return

        # Auto Partitioning
        if ctx.installData.autoPartDev:
            ctx.use_autopart = True

            if ctx.installData.autoPartMethod == methodEraseAll:
                ctx.yali.autoPartDevice()
                ctx.yali.checkSwap()
                ctx.yali.info.updateMessage(_("Formatting..."))
                ctx.mainScreen.processEvents()
                ctx.partrequests.applyAll()

            elif ctx.installData.autoPartMethod == methodUseAvail:
                if ctx.installData.autoPartPartition["partition"].isFreespace():
                    ctx.yali.info.updateAndShow(_("Writing disk tables..."))
                else:
                    ctx.yali.info.updateAndShow(_("Resizing..."))
                ctx.yali.autoPartUseAvail()
                ctx.yali.checkSwap()
                ctx.yali.info.updateMessage(_("Formatting..."))
                ctx.mainScreen.processEvents()
                ctx.partrequests.applyAll()

        # Manual Partitioning
        else:
            ctx.debugger.log("Format Operation Started")
            ctx.yali.info.updateAndShow(_("Writing disk tables..."))
            for dev in yali.storage.devices:
                ctx.mainScreen.processEvents()
                if dev._needs_commit:
                    ctx.debugger.log("Parted Device.commit() calling...")
                    dev.commit()
            # wait for udev to create device nodes
            time.sleep(2)
            ctx.yali.checkSwap()
            ctx.yali.info.updateMessage(_("Formatting..."))
            ctx.mainScreen.processEvents()
            ctx.partrequests.applyAll()
            ctx.debugger.log("Format Operation Finished")

        ctx.yali.info.hide()

        # Find GRUB Dev
        root_part_req = ctx.partrequests.searchPartTypeAndReqType(parttype.root,
                                                                  request.mountRequestType)

        if ctx.installData.bootLoaderOption == B_DONT_INSTALL:
            ctx.installData.bootLoaderDev = None
        elif ctx.installData.bootLoaderOption == B_INSTALL_PART:
            ctx.installData.bootLoaderDev = os.path.basename(root_part_req.partition().getPath())
        elif ctx.installData.bootLoaderOption == B_INSTALL_MBR:
            ctx.installData.bootLoaderDev = os.path.basename(ctx.installData.bootLoaderOptionalDev.getPath())
        else:
            ctx.yali.guessBootLoaderDevice()

        root_part_req = ctx.partrequests.searchPartTypeAndReqType(parttype.root,request.mountRequestType)
        _ins_part = root_part_req.partition().getPath()

        ctx.debugger.log("Pardus Root is %s" % _ins_part)
        ctx.debugger.log("GRUB will be installed to %s" % ctx.installData.bootLoaderDev)

        ctx.mainScreen.moveInc = 1
        ctx.mainScreen.ui.buttonNext.setText(_("Next"))
        return True

