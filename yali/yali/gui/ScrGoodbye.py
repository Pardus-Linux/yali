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
from yali.gui import ScreenWidget, register_gui_screen
from yali.gui.YaliDialog import InfoDialog
from yali.gui.YaliSteps import YaliSteps
from yali.gui.Ui.goodbyewidget import Ui_GoodByeWidget

class Widget(QWidget, ScreenWidget):
    name = "goodbye"
    title = "Goodbye"
    help = _("""
<p>
You have successfully installed Pardus on your computer. After restarting
your computer, you can finally enjoy the full benefits of Pardus.
</p>
<P>
Click Next to proceed. One note: You remember your password, don't you?
</p>
""")

    def __init__(self):
        QWidget.__init__(self, None)
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
        if not ctx.flags.install_type == 3:
            ctx.logger.debug("Trying to eject the CD.")
            yali.util.eject()

        ctx.logger.debug("Yali, reboot calling..")

        ctx.mainScreen.processEvents()
        time.sleep(4)
        yali.util.reboot()

    def processPendingActions(self):
        self.steps.setOperations([{"text":_("Connecting to D-Bus..."), "operation":yali.postinstall.connectToDBus}])

        steps = [{"text":_("Setting hostname..."), "operation":yali.postinstall.setHostName},
                 {"text":_("Setting timezone..."), "operation":yali.postinstall.setTimeZone},
                 {"text":_("Setting root password..."), "operation":yali.postinstall.setRootPassword},
                 {"text":_("Adding users..."), "operation":yali.postinstall.addUsers},
                 {"text":_("Setting console keymap..."), "operation":yali.postinstall.writeConsoleData},
                 {"text":_("Migrating Xorg configuration..."), "operation":yali.postinstall.setKeymap}]

        base_steps = [{"text":_("Copying repository index..."), "operation":yali.postinstall.copyPisiIndex},
                     {"text":_("Configuring other packages..."), "operation":yali.postinstall.setPackages},
                     {"text":_("Setup bootloader..."), "operation":yali.postinstall.setupBootLooder},
                     {"text":_("Writing bootloader..."), "operation":yali.postinstall.writeBootLooder},
                     {"text":_("Stopping to D-Bus..."), "operation":yali.util.stop_dbus}]

        if ctx.bootloader.device:
            base_steps.append({"text":_("Installing Bootloader..."), "operation":yali.postinstall.installBootloader})

        if ctx.flags.install_type == 1 or ctx.flags.install_type == 3:
            self.steps.setOperations(steps)

        self.steps.setOperations(base_steps)

register_gui_screen(Widget)
