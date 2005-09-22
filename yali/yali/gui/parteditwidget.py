# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'parteditwidget.ui'
#
# Created: Prş Eyl 22 04:16:24 2005
#      by: The PyQt User Interface Compiler (pyuic) 3.14.1
#
# WARNING! All changes made in this file will be lost!


from qt import *


class PartEditWidget(QWidget):
    def __init__(self,parent = None,name = None,fl = 0):
        QWidget.__init__(self,parent,name,fl)

        if not name:
            self.setName("PartEditWidget")

        self.setSizePolicy(QSizePolicy(QSizePolicy.Preferred,QSizePolicy.Preferred,0,0,self.sizePolicy().hasHeightForWidth()))

        PartEditWidgetLayout = QGridLayout(self,1,1,11,6,"PartEditWidgetLayout")
        spacer11 = QSpacerItem(20,31,QSizePolicy.Minimum,QSizePolicy.Expanding)
        PartEditWidgetLayout.addItem(spacer11,2,0)

        layout14 = QHBoxLayout(None,0,6,"layout14")

        self.caption = QLabel(self,"caption")
        self.caption.setSizePolicy(QSizePolicy(QSizePolicy.Preferred,QSizePolicy.Maximum,0,0,self.caption.sizePolicy().hasHeightForWidth()))
        layout14.addWidget(self.caption)
        spacer8 = QSpacerItem(261,20,QSizePolicy.Expanding,QSizePolicy.Minimum)
        layout14.addItem(spacer8)

        PartEditWidgetLayout.addLayout(layout14,0,0)

        layout19 = QGridLayout(None,1,1,0,6,"layout19")

        self.textLabel3 = QLabel(self,"textLabel3")

        layout19.addWidget(self.textLabel3,0,0)

        self.mount_point = QComboBox(0,self,"mount_point")

        layout19.addWidget(self.mount_point,0,1)

        self.size = QLineEdit(self,"size")

        layout19.addWidget(self.size,1,1)

        self.textLabel1 = QLabel(self,"textLabel1")

        layout19.addWidget(self.textLabel1,1,0)

        PartEditWidgetLayout.addLayout(layout19,1,0)

        self.languageChange()

        self.resize(QSize(377,136).expandedTo(self.minimumSizeHint()))
        self.clearWState(Qt.WState_Polished)


    def languageChange(self):
        self.setCaption(self.__tr("Form1"))
        self.caption.setText(self.__tr("Edit Partition:"))
        self.textLabel3.setText(self.__tr("Partition Type:"))
        self.mount_point.clear()
        self.mount_point.insertItem(self.__tr("Install Root"))
        self.mount_point.insertItem(self.__tr("Users' Files"))
        self.mount_point.insertItem(self.__tr("Swap"))
        self.textLabel1.setText(self.__tr("Size (MB):"))


    def __tr(self,s,c = None):
        return qApp.translate("PartEditWidget",s,c)
