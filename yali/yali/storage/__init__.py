def storageInitialize():
    raise NotImplementedError("storageInitialize method not implemented.")

def storageComplete():
    raise NotImplementedError("storageComplete method not implemented.")


class Interface(object):
    def __init__(self):
        pass

    @property
    def devices(self):
        pass

    @property
    def devicesImmutable(self):
        pass

    @property
    def disks(self):
        pass

    @property
    def partitions(self):
        pass

    @property
    def lvs(self):
        raise NotImplementedError("lvs method not implemented in Interface class.")

    @property
    def vgs(self):
        raise NotImplementedError("vgs method not implemented in Interface class.")

    @property
    def pvs(self):
        raise NotImplementedError("pvs method not implemented in Interface class.")

    @property
    def mdarrays(self):
        raise NotImplementedError("mdarrays method not implemented in Interface class.")

    @property
    def mdmembers(self):
        raise NotImplementedError("mdmembers method not implemented in Interface class.")

    @property
    def unusedPVS(self):
        raise NotImplementedError("unusedPVS method not implemented in Interface class.")

    @property
    def unusedRaidMembers(self):
        raise NotImplementedError("unusedRaidMembers method not implemented in Interface class.")

    @property
    def mountpoints(self):
        pass

    def newPartition(self):
        pass

    def newVolumeGroup(self):
        raise NotImplementedError("newVolumeGroup method not implemented in Interface class.")
        pass

    def newLogicalVolume(self):
        raise NotImplementedError("newLogicalVolume method not implemented in Interface class.")
        pass

    def newRaidArray(self):
        raise NotImplementedError("newRaidArray method not implemented in Interface class.")
        pass

    def createDevice(self):
        pass

    def destroyDevice(self):
        pass

    def mountFilesystems(self):
        pass

    def umountFilesystems(self):
        pass

    def fstab(self):
        pass

    def createSwapFile(self):
        pass

    def raidConf(self):
        raise NotImplementedError("raidConf method not implemented in Interface class.")
