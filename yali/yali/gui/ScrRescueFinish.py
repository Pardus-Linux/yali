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

import gettext
_ = gettext.translation('yali', fallback=True).ugettext

from PyQt4.Qt import QWidget, SIGNAL, QPixmap

import time
import yali.postinstall
import yali.pisiiface
import yali.util
from yali.gui import ScreenWidget, register_gui_screen
from yali.gui.YaliDialog import InfoDialog
from yali.gui.YaliSteps import YaliSteps
from yali.gui.Ui.goodbyewidget import Ui_GoodByeWidget
import yali.context as ctx

class Widget(QWidget, ScreenWidget):
    name = "finishRescue"
    title = _("System Repair")
    help = _("""
<p>
There is no help available for this section.
</p>
""")

    def __init__(self):
        QWidget.__init__(self)
        self.ui = Ui_GoodByeWidget()
        self.ui.setupUi(self)

        self.steps = YaliSteps()

    def installBootLoader(self):
        # Install bootloader
        ctx.yali.installBootloader(ctx.installData.rescuePartition)
        return True

    def takeBackPisi(self):
        try:
            yali.pisiiface.takeBack(ctx.takeBackOperation.no)
        except Exception, e:
            ctx.logger.debug("Exception occured while taking back the system.")
            ctx.logger.debug(e)
            return False
        return True

    def shown(self):
        ctx.mainScreen.disableNext()
        if ctx.rescueMode == "grub":
            self.steps.setOperations([{"text":      _("Installing Bootloader..."),
                                       "operation": self.installBootLoader}])
        elif ctx.rescueMode == "pisi":
            self.steps.setOperations([{"text":      _("Taking back operation..."),
                                       "operation": self.takeBackPisi}])

        ctx.interface.informationWindow.update(_("Running rescue operations..."))
        ctx.mainScreen.disableBack()
        self.steps.slotRunOperations()

        # Umount system paths
        yali.sysutils.umountSystemPaths()

        if not ctx.mainScreen.ui.helpContent.isVisible():
            ctx.mainScreen.slotToggleHelp()
        self.ui.label.setPixmap(QPixmap(":/gui/pics/goodbye.png"))
        ctx.interface.informationWindow.hide()
        ctx.mainScreen.enableNext()

    def execute(self):
        ctx.mainScreen.disableNext()

        ctx.logger.debug("Show reboot dialog.")
        InfoDialog(_("Press <b>Restart</b> to restart your system."), _("Restart"))

        ctx.interface.informationWindow.update(_('<b>Please wait while restarting...</b>'))

        # remove cd...
        # if installation type is First Boot
        if not ctx.flags.install_type == 3:
            ctx.logger.debug("Trying to eject the CD.")
            yali.util.eject()

        ctx.logger.debug("Yali, reboot calling..")

        ctx.mainScreen.processEvents()
        yali.util.sync()
        time.sleep(4)
        yali.util.reboot()

register_gui_screen(Widget)
