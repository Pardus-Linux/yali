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

# Auto Partition Methods
methodUseAvail, methodEraseAll, methodManual = range(3)

# Auto Installation Methods
methodInstallAutomatic, methodInstallManual = range(2)

# Auto Selected Kernels
defaultKernel, paeKernel, rtKernel = range(3)

kernels = {
        defaultKernel:"kernel.default",
        paeKernel:"kernel.pae",
        rtKernel:"kernel.rt"
        }

# Boot Loader Options
B_DONT_INSTALL = 0
B_INSTALL_PART = 1
B_INSTALL_MBR  = 2
B_INSTALL_SMART= 3

YALI_INSTALL, \
        YALI_DVDINSTALL, \
        YALI_FIRSTBOOT, \
        YALI_OEMINSTALL, \
        YALI_PLUGIN, \
        YALI_PARTITIONER, \
        YALI_RESCUE = range(7)

class InstallData:
    keyData = None
    rootPassword = None
    hostName = None
    users = []
    isKahyaUsed = False
    autoLoginUser = None
    autoPartDev = None
    autoPartPartition = None
    autoPartMethod = methodUseAvail
    autoInstallationKernel = None
    autoInstallationCollection = None
    autoInstallationMethod = methodInstallAutomatic
    bootLoaderDev = None
    bootLoaderOption = B_INSTALL_SMART
    bootLoaderOptionalDev = None
    bootLoaderDetectOthers = True
    rescuePartition = None
    orderedDiskList = []
    repoAddr = None
    useYaliFirstBoot = False
    timezone = "Europe/Istanbul"
    sessionLog = ""
    installAllLangPacks = False

