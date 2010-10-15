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

import os
import time
import gettext

__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext

from PyQt4 import QtGui
from PyQt4.QtCore import *

import yali.util
import yali.context as ctx
from yali.installdata import YALI_FIRSTBOOT
from yali.gui.ScreenWidget import ScreenWidget
from yali.gui.YaliDialog import InfoDialog
from yali.gui.YaliSteps import YaliSteps
from yali.gui.Ui.goodbyewidget import Ui_GoodByeWidget

class Widget(QtGui.QWidget, ScreenWidget):
    title = "Goodbye"
    # FIXME
    helpSummary = _("Selametle")
    help = _("""
<p>
You have successfully installed Pardus on your computer. After restarting
your computer, you can finally enjoy the full benefits of Pardus.
</p>
<P>
Click Next to proceed. One note: You remember your password, don't you?
</p>
""")

    def __init__(self, *args):
        QtGui.QWidget.__init__(self,None)
        self.ui = Ui_GoodByeWidget()
        self.ui.setupUi(self)

        self.steps = YaliSteps()

    def shown(self):
        ctx.mainScreen.disableNext()
        ctx.interface.informationWindow.update(_("Running post-install operations..."))
        ctx.mainScreen.disableBack()
        ctx.yali.processPendingActions(self)
        self.steps.slotRunOperations()
        if not ctx.mainScreen.ui.helpContent.isVisible():
            ctx.mainScreen.slotToggleHelp()
        self.ui.label.setPixmap(QtGui.QPixmap(":/gui/pics/goodbye.png"))
        ctx.interface.informationWindow.hide()
        ctx.mainScreen.enableNext()

    def execute(self):
        ctx.mainScreen.disableNext()

        ctx.logger.debug("Show restart dialog.")
        InfoDialog(_("Press <b>Restart</b> to restart the computer."), _("Restart"))

        ctx.interface.informationWindow.update(_("<b>Please wait while restarting...</b>"))

        # remove cd...
        if not ctx.yali.install_type == YALI_FIRSTBOOT:
            ctx.logger.debug("Trying to eject the CD.")
            yali.util.eject()

        ctx.logger.debug("Yali, reboot calling..")

        ctx.mainScreen.processEvents()
        time.sleep(4)
        yali.util.reboot()

