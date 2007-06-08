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
        
        self.window = Dialog(title,self.debugWidget,None)
        self.window.resize(500,400)
    
    def showWindow(self):
        self.window.show()
        
    def log(self,log):
        self.traceback.add(QString(log))

class DebugContainer(QTextEdit):
    def __init__(self, parent, showLineNumbers=True):
        QTextEdit.__init__(self, parent)
        
        f = QFont( "Bitstream Vera Sans Mono", 10);
        self.setFont(f)
        
        self.showLineNumbers = showLineNumbers
        self.setReadOnly(True)
        self.setOverwriteMode(True)
        self.plainLogs = ''
        self.line = 0
        
    def add(self,log):
        self.plainLogs += "%s\n" % log
        if self.showLineNumbers:
            self.append(QString("<b>%d :</b> %s" % (self.line,log)))
            self.line +=1
        else:
            self.append(QString(log))