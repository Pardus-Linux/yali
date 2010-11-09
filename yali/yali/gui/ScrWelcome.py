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
import codecs
import gettext
_ = gettext.translation('yali', fallback=True).ugettext

from PyQt4.Qt import QWidget, SIGNAL, QTextBrowser

import yali.context as ctx
from yali.gui import ScreenWidget, GUIError, register_gui_screen
from yali.gui.YaliDialog import Dialog
from yali.gui.Ui.welcomewidget import Ui_WelcomeWidget

##
# Welcome screen is the first screen to be shown.
class Widget(QWidget, ScreenWidget):
    name = "welcome"
    title = _("Welcome to Pardus")
    icon = "applications-other"
    help = _("""
<p>Welcome to Pardus that contains many easy-to-use software components. You can do everything you need to, including, but not limited to, connecting to the Internet, creating documents, playing games, listening to music using Pardus.</p>
<p>This application will help you with the installation of Pardus to your computer in few and easy steps and then do what is necessary to identify and configure your hardware. We advise you to backup your data in your disk(s) before starting with the installation.</p>
<p>You can start the installation process (and step in on a free world) by pressing the Next button.</p>
""")

    def __init__(self):
        QWidget.__init__(self)
        self.ui = Ui_WelcomeWidget()
        self.ui.setupUi(self)

        self.connect(self.ui.accept, SIGNAL("toggled(bool)"),
                     self.slotAcceptToggled)

        self.connect(self.ui.gplButton, SIGNAL("clicked()"),
                     self.showGPL)

    def slotAcceptToggled(self, state):
        if state:
            ctx.mainScreen.enableNext()
        else:
            ctx.mainScreen.disableNext()

    def showGPL(self):
        dialog = Dialog("GPL", LicenseBrowser(self), self)
        dialog.resize(500, 400)
        dialog.exec_()

    def shown(self):
        ctx.mainScreen.disableBack()
        if self.ui.accept.isChecked():
            ctx.mainScreen.enableNext()
        else:
            ctx.mainScreen.disableNext()
        ctx.mainScreen.processEvents()

class LicenseBrowser(QTextBrowser):

    def __init__(self, *args):
        apply(QTextBrowser.__init__, (self,) + args)

        self.setStyleSheet("background:white;color:black;")

        try:
            self.setText(codecs.open(self.loadFile(), "r", "UTF-8").read())
        except Exception, msg:
            GUIError, _(msg)

    def loadFile(self):
        licence = os.path.join(ctx.consts.source_dir, "license/license-" + ctx.consts.lang + ".txt")

        if not os.path.exists(licence):
            licence = os.path.join(ctx.consts.source_dir, "license/license-en.txt")
        if os.path.exists(licence):
            return licence
        raise GUIError, _("License text could not be found.")

register_gui_screen(Widget)
