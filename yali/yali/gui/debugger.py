# -*- coding: utf-8 -*-
#
# Copyright (C) 2007, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#

from qt import *
from pyaspects.meta import MetaAspect
import yali.gui.context as ctx

import gettext
__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext

from yali.gui.YaliDialog import Dialog

class Debugger:
    def __init__(self,showLineNumbers=True):
        title = _("Debug")
        self.debugWidget = QWidget()
        self.traceback = DebugContainer(self.debugWidget,showLineNumbers)

        l = QVBoxLayout(self.debugWidget)
        l.addWidget(self.traceback)

        self.window = Dialog(title,self.debugWidget,None,extraButtons=True)
        self.window.resize(500,400)
        self.aspect = DebuggerAspect(self)

    def showWindow(self):
        self.window.show()

    def log(self,log,type=1):
        if ctx.debugEnabled:
            self.traceback.add(QString(log),type)

class DebugContainer(QTextEdit):
    def __init__(self, parent, showLineNumbers=True):
        QTextEdit.__init__(self, parent)

        f = QFont( "Bitstream Vera Sans Mono", 11);
        self.setFont(f)

        self.showLineNumbers = showLineNumbers
        self.setReadOnly(True)
        self.setOverwriteMode(True)
        self.plainLogs = ''
        self.line = 0

    def add(self,log,type):
        if type==1:
            self.plainLogs += "%s\n" % log
            log = "<b>%s</b>" % log
        if self.showLineNumbers:
            self.append(QString("<b>%d :</b> %s" % (self.line,log)))
            self.line +=1
        else:
            self.append(QString(log))

class DebuggerAspect:
    __metaclass__ = MetaAspect
    name = "DebugAspect"

    def __init__(self, out ):
        self.out = out

    def before(self, wobj, data, *args, **kwargs):
        met_name = data['original_method_name']
        fun_str = "%s (args: %s -- kwargs: %s)" % (met_name, args, kwargs)
        self.out.log("Entering function: %s\n" % fun_str,0)


    def after(self, wobj, data, *args, **kwargs):
        met_name = data['original_method_name']
        fun_str = "%s (args: %s -- kwargs: %s)" % (met_name, args, kwargs)
        self.out.log("Left function: %s\n" % fun_str,0)
