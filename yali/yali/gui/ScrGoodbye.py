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

import time
import gettext
_ = gettext.translation('yali', fallback=True).ugettext

from PyQt4.Qt import QWidget, QPixmap

import yali.util
import yali.context as ctx
from yali.gui import ScreenWidget
from yali.gui.YaliDialog import InfoDialog
from yali.gui.YaliSteps import YaliSteps
from yali.gui.Ui.goodbyewidget import Ui_GoodByeWidget

class Widget(QWidget, ScreenWidget):
    name = "goodbye"

    def __init__(self):
        QWidget.__init__(self)
        self.ui = Ui_GoodByeWidget()
        self.ui.setupUi(self)
        self.steps = YaliSteps()

    def shown(self):
        ctx.mainScreen.disableNext()
        ctx.interface.informationWindow.update(_("Running post-install operations..."))
        ctx.mainScreen.disableBack()
        self.processPendingActions()
        self.steps.slotRunOperations()

        if not ctx.mainScreen.ui.helpContent.isVisible():
            ctx.mainScreen.slotToggleHelp()

        self.ui.label.setPixmap(QPixmap(":/gui/pics/goodbye.png"))
        ctx.interface.informationWindow.hide()
        ctx.mainScreen.enableNext()

    def execute(self):
        ctx.mainScreen.disableNext()

        ctx.logger.debug("Show restart dialog.")
        InfoDialog(_("Press <b>Restart</b> to restart the computer."), _("Restart"))

        ctx.interface.informationWindow.update(_("<b>Please wait while restarting...</b>"))

        # remove cd...
        # if installation type is First Boot
        if not ctx.flags.install_type == ctx.STEP_FIRST_BOOT:
            ctx.logger.debug("Trying to eject the CD.")
            yali.util.eject()

        ctx.logger.debug("Yali, reboot calling..")

        ctx.mainScreen.processEvents()
        time.sleep(4)
        yali.util.reboot()

    def processPendingActions(self):
        self.steps.setOperations([{"text":_("Connecting to D-Bus..."), "operation":yali.postinstall.connectToDBus}])

        steps = [{"text":_("Setting hostname..."), "operation":yali.postinstall.setHostName},
                 {"text":_("Setting root password..."), "operation":yali.postinstall.setRootPassword}]

        base_steps = [{"text":_("Setting timezone..."), "operation":yali.postinstall.setTimeZone},
                      {"text":_("Migrating Xorg configuration..."), "operation":yali.postinstall.setKeymap},
                      {"text":_("Setting console keymap..."), "operation":yali.postinstall.writeConsoleData},
                      {"text":_("Copying repository index..."), "operation":yali.postinstall.copyPisiIndex},
                      {"text":_("Stopping to D-Bus..."), "operation":yali.util.stop_dbus}]


        if (ctx.flags.install_type == ctx.STEP_BASE or ctx.flags.install_type == ctx.STEP_DEFAULT) and ctx.bootloader.device:
            base_steps.insert(4, {"text":_("Setup bootloader..."), "operation":yali.postinstall.setupBootLooder})
            base_steps.insert(5, {"text":_("Writing bootloader..."), "operation":yali.postinstall.writeBootLooder})
            base_steps.append({"text":_("Installing bootloader..."), "operation":yali.postinstall.installBootloader})

        if ctx.flags.install_type == ctx.STEP_BASE:
            steps.append({"text":_("Setup First-Boot..."), "operation":yali.postinstall.setupFirstBoot})

        if ctx.flags.install_type == ctx.STEP_FIRST_BOOT or ctx.flags.install_type == ctx.STEP_DEFAULT:
            steps.append({"text":_("Adding users..."), "operation":yali.postinstall.addUsers})

        if ctx.flags.install_type == ctx.STEP_BASE  or ctx.flags.install_type == ctx.STEP_DEFAULT:
            steps.extend(base_steps)

        self.steps.setOperations(steps)


