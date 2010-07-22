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
import dbus
import time
import shutil
import gettext

__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext

from PyQt4 import QtGui
from PyQt4.QtCore import *


import pisi.ui
from pardus.sysutils import get_kernel_option
import yali.pisiiface
import yali.sysutils
import yali.localeutils
from yali.constants import consts
import yali.gui.context as ctx
from yali.gui.installdata import *
from yali.gui.debugger import DebuggerAspect
from yali.gui.YaliDialog import Dialog, QuestionDialog, InfoDialog, InformationWindow, MessageWindow, DetailedMessageWindow

# screens
import yali.gui.ScrKahyaCheck
import yali.gui.ScrWelcome
import yali.gui.ScrCheckCD
import yali.gui.ScrKeyboard
import yali.gui.ScrDateTime
import yali.gui.ScrAdmin
import yali.gui.ScrUsers
import yali.gui.ScrPartitionAuto
import yali.gui.ScrPartitionManual
import yali.gui.ScrBootloader
import yali.gui.ScrInstallationAuto
import yali.gui.ScrInstall
import yali.gui.ScrSummary
import yali.gui.ScrGoodbye
import yali.gui.ScrRescue
import yali.gui.ScrRescueGrub
import yali.gui.ScrRescuePisi
import yali.gui.ScrRescuePassword
import yali.gui.ScrRescueFinish

class Yali:
    def __init__(self, install_type=YALI_INSTALL, install_plugin=None):

        self._screens = {}

        # Normal Installation process
        self._screens[YALI_INSTALL] = [                                  # Numbers can be used with -s paramter
                                       yali.gui.ScrKahyaCheck,          # 00
                                       yali.gui.ScrWelcome,             # 01
                                       yali.gui.ScrCheckCD,             # 02
                                       yali.gui.ScrKeyboard,            # 03
                                       yali.gui.ScrDateTime,            # 04
                                       yali.gui.ScrUsers,               # 05
                                       yali.gui.ScrAdmin,               # 06
                                       yali.gui.ScrPartitionAuto,       # 07
                                       yali.gui.ScrPartitionManual,     # 08
                                       yali.gui.ScrBootloader,          # 09
                                       yali.gui.ScrSummary,             # 10
                                       yali.gui.ScrInstall,             # 11
                                       yali.gui.ScrGoodbye              # 12
                                      ]

        self._screens[YALI_DVDINSTALL] = [                              # Numbers can be used with -s paramter
                                       yali.gui.ScrKahyaCheck,          # 00
                                       yali.gui.ScrWelcome,             # 01
                                       yali.gui.ScrCheckCD,             # 02
                                       yali.gui.ScrKeyboard,            # 03
                                       yali.gui.ScrDateTime,            # 04
                                       yali.gui.ScrUsers,               # 05
                                       yali.gui.ScrAdmin,               # 06
                                       yali.gui.ScrPartitionAuto,       # 07
                                       yali.gui.ScrPartitionManual,     # 08
                                       yali.gui.ScrBootloader,          # 09
                                       yali.gui.ScrInstallationAuto,    # 10
                                       yali.gui.ScrSummary,             # 11
                                       yali.gui.ScrInstall,             # 12
                                       yali.gui.ScrGoodbye              # 13
                                      ]

        # FirstBoot Installation process
        self._screens[YALI_FIRSTBOOT] = [                                # Numbers can be used with -s paramter
                                         yali.gui.ScrWelcome,           # 00
                                         yali.gui.ScrKeyboard,          # 01
                                         yali.gui.ScrDateTime,          # 02
                                         yali.gui.ScrUsers,             # 03
                                         yali.gui.ScrAdmin,             # 04
                                         yali.gui.ScrGoodbye            # 05
                                        ]

        # Oem Installation process
        self._screens[YALI_OEMINSTALL] = [                                  # Numbers can be used with -s paramter
                                          yali.gui.ScrWelcome,             # 00
                                          yali.gui.ScrCheckCD,             # 01
                                          yali.gui.ScrPartitionAuto,       # 02
                                          yali.gui.ScrPartitionManual,     # 03
                                          yali.gui.ScrBootloader,          # 04
                                          yali.gui.ScrSummary,             # 05
                                          yali.gui.ScrInstall,             # 06
                                          yali.gui.ScrGoodbye              # 07
                                         ]

        # Use YALI just for partitioning
        self._screens[YALI_PARTITIONER] = [
                                           yali.gui.ScrPartitionManual  # Manual Partitioning
                                          ]

        # Rescue Mode
        self._screens[YALI_RESCUE] = [
                                      yali.gui.ScrRescue,            # Rescue Mode
                                      yali.gui.ScrRescueGrub,        # Grub Rescue
                                      yali.gui.ScrRescuePisi,        # Pisi HS Rescue
                                      yali.gui.ScrRescuePassword,    # Password Rescue
                                      yali.gui.ScrRescueFinish       # Final step for rescue
                                     ]

        self.plugin = None

        # mutual exclusion
        self.mutex = QMutex()
        self.waitCondition = QWaitCondition()
        self.retryAnswer = False

        # Let the show begin..
        if install_type == YALI_PLUGIN:
            self.plugin  = self.getPlugin(install_plugin)
            if self.plugin:
                self.screens = self.plugin.config.screens
                # run plugins setup
                self.plugin.config.setup()
            else:
                install_type = YALI_INSTALL
                InfoDialog(_("Plugin '%s' could not be loaded or found, switching to normal installation process." % install_plugin))

        if not self.plugin:
            self.screens = self._screens[install_type]

        self.install_type = install_type
        self.info = InformationWindow("Please wait...")
        self.checkCDStop = True

    def messageWindow(self, title, text, type="ok", default=None, customButtons=None, customIcon=None):
        return MessageWindow(title, text, type, default, customButtons, customIcon, run=True).rc

    def detailedMessageWindow(self, title, text, longText, type="ok", default=None, customButtons=None, customIcon=None):
        return DetailedMessageWindow(title, text, longText, type, default, customButtons, customIcon, run=True).rc

    def getPlugin(self, p):
        try:
            _p = __import__("yali.plugins.%s.config" % p)
        except ImportError:
            return False
        plugin = getattr(_p.plugins,p)
        return plugin

    def checkCD(self, rootWidget):
        ctx.mainScreen.disableNext()
        ctx.mainScreen.disableBack()

        self.info.updateAndShow(_("Starting validation..."))
        class PisiUI(pisi.ui.UI):
            def notify(self, event, **keywords):
                pass
            def display_progress(self, operation, percent, info, **keywords):
                pass

        yali.pisiiface.initialize(ui = PisiUI(), with_comar = False, nodestDir = True)
        yali.pisiiface.addCdRepo()
        ctx.mainScreen.processEvents()
        pkg_names = yali.pisiiface.getAvailablePackages()

        rootWidget.progressBar.setMaximum(len(pkg_names))

        cur = 0
        for pkg_name in pkg_names:
            cur += 1
            ctx.debugger.log("Validating %s " % pkg_name)
            self.info.updateMessage(_("Validating %s") % pkg_name)
            if self.checkCDStop:
                continue
            try:
                yali.pisiiface.checkPackageHash(pkg_name)
                rootWidget.progressBar.setValue(cur)
            except:
                self.showError(_("Validation Failed"),
                               _("<b><p>Validation of installation packages failed.\
                                  Please remaster your installation medium and restart the installation.</p></b>"))

        if not self.checkCDStop:
            rootWidget.checkLabel.setText(_('<font color="#FFF"><b>Validation succeeded. You can proceed with the installation.</b></font>'))
            rootWidget.checkButton.setText(_("Validate Integrity"))
        else:
            rootWidget.checkLabel.setText("")
            rootWidget.progressBar.setValue(0)

        yali.pisiiface.removeRepo(ctx.consts.cd_repo_name)

        ctx.mainScreen.enableNext()
        ctx.mainScreen.enableBack()

        self.info.hide()

    def setKeymap(self, keymap):
        yali.localeutils.setKeymap(keymap["xkblayout"], keymap["xkbvariant"])
        ctx.installData.keyData = keymap

    def setTime(self, rootWidget):
        self.info.updateAndShow(_("Adjusting time settings..."))
        date = rootWidget.calendarWidget.selectedDate()
        args = "%02d%02d%02d%02d%04d.%02d" % (date.month(), date.day(),
                                              rootWidget.timeHours.time().hour(), rootWidget.timeMinutes.time().minute(),
                                              date.year(), rootWidget.timeSeconds.time().second())

        # Set current date and time
        ctx.debugger.log("Date/Time setting to %s" % args)
        yali.sysutils.run("date %s" % args)

        # Sync date time with hardware
        ctx.debugger.log("YALI's time is syncing with the system.")
        yali.sysutils.run("hwclock --systohc")
        self.info.hide()

    def setTimeZone(self, rootWidget):
        # Store time zone selection we will set it in processPending actions.
        ctx.installData.timezone = rootWidget.timeZoneList.currentItem().text()
        ctx.debugger.log("Time zone selected as %s " % ctx.installData.timezone)

    def storageComplete(self):
        title = None
        message = None
        details = None
        try:
            ctx.storage.doIt()
        except FilesystemResizeError as (msg, device):
            title = _("Resizing Failed")
            message = _("There was an error encountered while "
                        "resizing the device %s.") % (device,)
            details = "%s" %(msg,)

        except FilesystemMigrateError as (msg, device):
            title = _("Migration Failed")
            message = _("An error was encountered while "
                        "migrating filesystem on device %s.") % (device,)
            details = msg
        except Exception as e:
            raise

        if title:
            rc = self.detailedMessageWindow(title, message, details,
                                            type = "custom",
                                            customButtons = [_("File Bug"), _("Exit installer")])

            if rc == 0:
                raise
            elif rc == 1:
                sys.exit(1)

        ctx.storage.turnOnSwap()
        ctx.storage.mountFilesystems(readOnly=False, skipRoot=False)

    def fillFstab(self):
        ctx.storage.storageset.write(ctx.consts.target_dir)

    def backupInstallData(self):
        import piksemel

        def insert(root,tag,data):
            _ = root.insertTag(tag)
            _.insertData(str(data))

        # let create a yali piksemel..
        yali = piksemel.newDocument("yali")

        # let store keymap and language options
        insert(yali,"language",ctx.consts.lang)
        insert(yali,"keymap",ctx.installData.keyData["xkblayout"])
        insert(yali,"variant",ctx.installData.keyData["xkbvariant"])

        # we will store passwords as shadowed..
        insert(yali,"root_password",yali.sysutils.getShadowed(ctx.installData.rootPassword or ""))

        # time zone..
        insert(yali,"timezone",ctx.installData.timezone)

        # hostname ..
        insert(yali,"hostname",ctx.installData.hostName)

        # users ..
        if len(yali.users.pending_users) > 0:
            users = yali.insertTag("users")
        for u in yali.users.pending_users:
            user = users.insertTag("user")
            insert(user,"username",u.username)
            insert(user,"realname",u.realname)
            insert(user,"password",yali.sysutils.getShadowed(u.passwd))
            insert(user,"groups",",".join(u.groups))

        # partitioning ..
        devices = []
        for dev in yali.storage.devices:
            if dev.getTotalMB() >= ctx.consts.min_root_size:
                devices.append(dev.getPath())

        partitioning = yali.insertTag("partitioning")
        partitioning.setAttribute("partition_type",
                                 {methodEraseAll:"auto",
                                  methodUseAvail:"smartAuto",
                                  methodManual:"manual"}[ctx.installData.autoPartMethod])
        if not ctx.installData.autoPartMethod == methodManual:
            try:
                partitioning.insertData("disk%d" % devices.index(ctx.installData.autoPartDev.getPath()))
            except:
                partitioning.insertData(ctx.installData.autoPartDev.getPath())

        ctx.installData.sessionLog = yali.toPrettyString()
        # ctx.debugger.log(yali.toPrettyString())

    def processPendingActions(self, rootWidget):
        rootWidget.steps.setOperations([{"text":_("Connecting to D-Bus..."),"operation":yali.postinstall.connectToDBus}])

        steps = [{"text":_("Setting hostname..."),"operation":yali.postinstall.setHostName},
                 {"text":_("Setting timezone..."),"operation":yali.postinstall.setTimeZone},
                 {"text":_("Setting root password..."),"operation":yali.postinstall.setRootPassword},
                 {"text":_("Adding users..."),"operation":yali.postinstall.addUsers},
                 {"text":_("Setting console keymap..."),"operation":yali.postinstall.writeConsoleData},
                 {"text":_("Migrating Xorg configuration..."),"operation":yali.postinstall.migrateXorgConf}]

        stepsBase = [{"text":_("Copying repository index..."),"operation":yali.postinstall.copyPisiIndex},
                    # FIXME: This is weird, look at setPackages
                     {"text":_("Configuring other packages..."),"operation":yali.postinstall.setPackages},
                     {"text":_("Installing Bootloader..."),"operation":self.installBootloader}]

        if self.install_type in [YALI_INSTALL, YALI_DVDINSTALL, YALI_FIRSTBOOT]:
            rootWidget.steps.setOperations(steps)
        elif self.install_type == YALI_PLUGIN:
            rootWidget.steps.setOperations(self.plugin.config.steps)

        rootWidget.steps.setOperations(stepsBase)

    def installBootloader(self, pardusPart = None):
        ctx.bootloader.setup()
        ctx.logger.debug("Setup bootloader")
        ctx.bootloader.write()
        ctx.logger.debug("Writing grub.conf and devicemap")
        # BUG:#11255 normal user doesn't mount /mnt/archive directory. 
        # We set new formatted partition priveleges as user=root group=disk and change mod as 0770
        # Check archive partition type
        #archiveRequest = partrequests.searchPartTypeAndReqType(parttype.archive, request.mountRequestType)
        #if archiveRequest:
        #    ctx.debugger.log("Archive type request found!")
        #    yali.postinstall.setPartitionPrivileges(archiveRequest, 0770, 0, 6)

        # Umount system paths
        ctx.storage.storageset.umountFilesystems()
        ctx.logger.debug("Unmount system paths")
        rc = ctx.bootloader.install()
        if rc:
            ctx.logger.debug("Bootloader installed")
        else:
            ctx.logger.debug("Bootloader installation failed!")

    def showError(self, title, message, parent=None):
        r = ErrorWidget(parent)
        r.label.setText(message)
        d = Dialog(title, r, self, closeButton=False)
        d.resize(300,200)
        d.exec_()

class ErrorWidget(QtGui.QWidget):

    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)

        self.gridlayout = QtGui.QGridLayout(self)
        self.vboxlayout = QtGui.QVBoxLayout()

        self.label = QtGui.QLabel(self)
        self.vboxlayout.addWidget(self.label)

        self.hboxlayout = QtGui.QHBoxLayout()

        spacerItem = QtGui.QSpacerItem(40,20,QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
        self.hboxlayout.addItem(spacerItem)

        self.reboot = QtGui.QPushButton(self)
        self.reboot.setFocusPolicy(Qt.NoFocus)
        self.reboot.setText(_("Reboot"))

        self.hboxlayout.addWidget(self.reboot)
        self.vboxlayout.addLayout(self.hboxlayout)
        self.gridlayout.addLayout(self.vboxlayout,0,0,1,1)

        yali.sysutils.ejectCdrom()

        self.connect(self.reboot, SIGNAL("clicked()"),self.slotReboot)

    def slotReboot(self):
        yali.sysutils.reboot()

