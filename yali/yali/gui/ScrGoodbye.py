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
import time
import gettext
_ = gettext.translation('yali', fallback=True).ugettext

from PyQt4.Qt import QWidget, QPixmap

import yali.util
import yali.context as ctx
from yali.gui import ScreenWidget
from yali.gui.YaliDialog import InfoDialog
from yali.gui.Ui.goodbyewidget import Ui_GoodByeWidget
from yali.postinstall import Operation

class Widget(QWidget, ScreenWidget):
    name = "goodbye"

    def __init__(self):
        QWidget.__init__(self)
        self.ui = Ui_GoodByeWidget()
        self.ui.setupUi(self)

    def shown(self):
        ctx.mainScreen.disableNext()
        ctx.interface.informationWindow.update(_("Running post-install operations..."))
        ctx.mainScreen.disableBack()
        self.processPendingActions()
        ctx.mainScreen.pds_helper.toggleHelp()
        self.ui.label.setPixmap(QPixmap(":/gui/pics/goodbye.png"))
        ctx.interface.informationWindow.hide()
        ctx.mainScreen.enableNext()

    def execute(self):
        ctx.mainScreen.disableNext()

        if not ctx.flags.install_type == ctx.STEP_FIRST_BOOT:
            ctx.logger.debug("Show restart dialog.")
            InfoDialog(_("Press <b>Restart</b> to restart the computer."), _("Restart"))
            ctx.interface.informationWindow.update(_("<b>Please wait while restarting...</b>"))
            ctx.logger.debug("Trying to eject the CD.")
            yali.util.eject()
            ctx.logger.debug("Yali, reboot calling..")
            ctx.mainScreen.processEvents()
            time.sleep(4)
            yali.util.reboot()
        else:
            sys.exit(0)



    def processPendingPostinstallOperations(self):
        ctx.postInstallOperations.append(Operation(_("Connecting to D-Bus..."), yali.postinstall.connectToDBus))

        if not ctx.flags.install_type == ctx.STEP_RESCUE:
            ctx.postInstallOperations.append(Operation(_("Setting hostname..."), yali.postinstall.setHostName))
            ctx.postInstallOperations.append(Operation(_("Setting root password..."), yali.postinstall.setRootPassword))

        #FIXME:These are the base operations which have to be.
        base_operations = [Operation(_("Setting timezone..."), yali.postinstall.setTimeZone),
                      Operation(_("Migrating Xorg configuration..."), yali.postinstall.setKeymap),
                      Operation(_("Setting console keymap..."), yali.postinstall.writeConsoleData),
                      Operation(_("Copying repository index..."), yali.postinstall.copyPisiIndex),
                      Operation(_("Stopping to D-Bus..."), yali.util.stop_dbus)]

        #FIXME:If user doesn't select any device to install bootloader base_operations order must be like above.
        #However in the other case installing bootloader operation must execute after stopping dbus.
        if (ctx.flags.install_type == ctx.STEP_BASE or
            ctx.flags.install_type == ctx.STEP_DEFAULT or
            (ctx.flags.install_type == ctx.STEP_RESCUE and ctx.installData.rescueMode == ctx.RESCUE_GRUB)) and ctx.bootloader.device:
            base_operations.insert(4, Operation(_("Setup bootloader..."), yali.postinstall.setupBootLooder))
            base_operations.insert(5, Operation(_("Writing bootloader..."), yali.postinstall.writeBootLooder))
            base_operations.append(Operation(_("Installing bootloader..."), yali.postinstall.installBootloader))

        if ctx.flags.install_type == ctx.STEP_BASE:
            ctx.postInstallOperations.append(Operation(_("Setup First-Boot..."), yali.postinstall.setupFirstBoot))

        if ctx.flags.install_type == ctx.STEP_FIRST_BOOT or ctx.flags.install_type == ctx.STEP_DEFAULT:
            ctx.postInstallOperations.append(Operation(_("Adding users..."), yali.postinstall.addUsers))

        if ctx.flags.install_type == ctx.STEP_FIRST_BOOT:
            ctx.postInstallOperations.append(Operation(_("Cleanup systems..."), yali.postinstall.cleanup))

        if ctx.flags.install_type == ctx.STEP_BASE  or ctx.flags.install_type == ctx.STEP_DEFAULT:
            ctx.postInstallOperations.extend(base_ctx.postInstallOperations)

        for operation in ctx.postInstallOperations:
            if not operation.status:
                operation.run()
