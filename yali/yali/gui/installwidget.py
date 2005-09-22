# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'installwidget.ui'
#
# Created: Prş Eyl 22 04:22:58 2005
#      by: The PyQt User Interface Compiler (pyuic) 3.14.1
#
# WARNING! All changes made in this file will be lost!


from qt import *


class InstallWidget(QWidget):
    def __init__(self,parent = None,name = None,fl = 0):
        QWidget.__init__(self,parent,name,fl)

        if not name:
            self.setName("InstallWidget")


        InstallWidgetLayout = QGridLayout(self,1,1,11,6,"InstallWidgetLayout")

        self.pix = QLabel(self,"pix")
        self.pix.setSizePolicy(QSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding,0,0,self.pix.sizePolicy().hasHeightForWidth()))

        InstallWidgetLayout.addWidget(self.pix,0,0)

        self.info = QLabel(self,"info")

        InstallWidgetLayout.addWidget(self.info,1,0)

        self.languageChange()

        self.resize(QSize(588,347).expandedTo(self.minimumSizeHint()))
        self.clearWState(Qt.WState_Polished)


    def languageChange(self):
        self.setCaption(self.__tr("Form3"))
        self.pix.setText(self.__tr("pix"))
        self.info.setText(self.__tr("Installing Package: "))


    def __tr(self,s,c = None):
        return qApp.translate("InstallWidget",s,c)
