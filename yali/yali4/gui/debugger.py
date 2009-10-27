# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2009, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#

from pyaspects.meta import MetaAspect
import yali4.gui.context as ctx
import time

import gettext
__trans = gettext.translation('yali4', fallback=True)
_ = __trans.ugettext

from PyQt4 import QtGui
from PyQt4.QtCore import *

from yali4.gui.YaliDialog import Dialog

class Debugger:
    def __init__(self,showTimeStamp=True):
        title = _("Debug")
        self.debugWidget = QtGui.QWidget()
        self.debugShortCut = QtGui.QShortcut(QtGui.QKeySequence(Qt.Key_F2),self.debugWidget)
        QObject.connect(self.debugShortCut, SIGNAL("activated()"), self.toggleDebug)

        self.traceback = DebugContainer(self.debugWidget,showTimeStamp)
        self.loglevel = QtGui.QComboBox(self.debugWidget)
        self.loglevel.addItem("0 : Developer Messages")
        self.loglevel.addItem("1 : All Messages")
        QObject.connect(self.loglevel, SIGNAL("currentIndexChanged(int)"),self.loglevelChanged)

        l = QtGui.QVBoxLayout(self.debugWidget)
        l.addWidget(self.loglevel)
        l.addWidget(self.traceback)

        self.window = Dialog(title,self.debugWidget)
        self.window.resize(500,400)
        self.aspect = DebuggerAspect(self)

    def loglevelChanged(self,newLevel):
        self.traceback.level = newLevel

    def showWindow(self):
        self.window.show()

    def hideWindow(self):
        self.window.hide()

    def isVisible(self):
        return self.window.isVisible()

    def toggleDebug(self):
        if self.isVisible():
            self.hideWindow()
        else:
            self.showWindow()

    def log(self,log,type=0,indent=0):
        if ctx.debugEnabled and not log == '':
            self.traceback.add(unicode(log),type,indent)

class DebugContainer(QtGui.QTextBrowser):
    def __init__(self, parent, showTimeStamp=True, sysoutEnabled=True):
        QtGui.QTextBrowser.__init__(self, parent)
        self.setStyleSheet("font-size:8pt;")
        self.sysout = "/var/log/yali"
        self.showTimeStamp = showTimeStamp
        self.sysoutEnabled = sysoutEnabled
        self.setReadOnly(True)
        self.setOverwriteMode(True)
        self.plainLogs = ''
        self.indent = 0
        self.level = 0

    def add(self,log,type,indent):
        if indent==+1:
            self.indent += indent
        _now = time.strftime("%H:%M:%S", time.localtime())
        _indent = " "+"»"*self.indent
        if type==0:
            self.plainLogs += "%s : %s\n" % (_now, log)
            if self.sysoutEnabled:
                mes = "YALI - %s : %s" % (_now, log)
                try:
                    file(self.sysout,"a+").write("%s\n" % mes)
                except:
                    print mes
            log = "<b>%s</b>" % log
            _indent = ""

        if self.level==1 or type==self.level:
            self.append(unicode("%s :%s %s" % (_now, _indent, log)))

        if indent==-1:
            self.indent += indent

class DebuggerAspect:
    __metaclass__ = MetaAspect
    name = "DebugAspect"

    def __init__(self, out ):
        self.out = out

    def before(self, wobj, data, *args, **kwargs):
        met_name = data['original_method_name']
        class_ = str(data['__class__'])[8:-2]
        fun_str = "%s%s from %s" % (met_name, args, class_)
        self.out.log("call, %s" % fun_str,1,+1)

    def after(self, wobj, data, *args, **kwargs):
        met_name = data['original_method_name']
        fun_str = "%s%s" % (met_name, args)
        self.out.log("left, %s" % fun_str,1,-1)

