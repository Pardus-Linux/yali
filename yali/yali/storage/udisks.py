import dbus
import yali

class UDisksError(yali.Error):
    pass

class UDisks(object):

    def __init__(self):
        self._bus = dbus.SystemBus()
        self._udisks = dbus.Interface(self._bus.get_object('org.freedesktop.UDisks',
                                       '/org/freedesktop/UDisks'),
                                       dbus_interface="org.freedesktop.UDisks")
    def info(self, udi):
        """Retrieve all properties of a particular device(by UDI)"""
        properties = {}
        try:
            properties = dbus.Interface(self._bus.get_object("org.freedesktop.UDisks", udi),
                                        "org.freedesktop.DBus.Properties").GetAll("org.freedesktop.UDisks.Device")
        except dbus.exceptions.DBusException:
            return None
        else:
            return properties

    @property
    def enumerateDevices(self):
        _devices = []
        for device in self._udisks.EnumerateDevices():
            _devices.append(device)
        return _devices

    @property
    def drives(self, force=True):
        _drives=[]
        for device in self.enumerateDevices:
            if self.info(device)["DeviceIsDrive"]:
                _drives.append(device)

        return _drives

    @property
    def partitions(self):
        _partitions = []
        for device in self.enumerateDevices:
            if self.info(device)["DeviceIsPartition"]:
                _partitions.append(device)

        return _partitions

    @property
    def removables(self):
        _removables = []
        for drive in self.drives():
            if drive["DeviceIsRemovable"]:
                _removables.append(drive)

        return _removables

    @property
    def pvs(self):
        _pvs = []
        for device in self.enumerateDevices:
            if self.info(device)["DeviceIsLinuxLvm2PV"]:
                _pvs.append(device)

        return _pvs

    @property
    def vgs(self):
        _vgs = []
        for device in self.enumerateDevices:
            if self.info(device):
                pass
        return _vgs

    @property
    def lvs(self):
        _lvs = []
        for device in self.enumerateDevices:
            if self.info(device)["DeviceIsLinuxLvm2LV"]:
                _lvs.append(device)

        return _lvs

    @property
    def raidMembers(self):
        _raidMembers = []
        for device in self.enumerateDevices:
            if self.info(device)["DeviceIsLinuxMdComponent"]:
                _raidMembers.append(device)

        return _raidMembers

    @property
    def raidArrays(self):
        _raidComponent = []
        for device in self.enumerateDevices:
            if self.info(device)["DeviceIsLinuxMd"]:
                _raidComponent.append(device)

        return _raidComponent

    @property
    def luksClearTextDevices(self):
        _luks = []
        for device in self.enumerateDevices:
            if self.info(device)["DeviceIsLuksCleartext"]:
                _luks.append(device)

        return _luks

    @property
    def luksDevices(self):
        _luks = []
        for device in self.enumerateDevices:
            if self.info(device)["DeviceIsLuks"]:
                _luks.append(device)

        return _luks

    def isPartition(self, device):
        return self.info(device)["DeviceIsPartition"]

    def isRemovable(self, device):
        return self.info(device)["DeviceIsRemovable"]

    def isMediaAvailable(self, device):
        return self.info(device)["DeviceIsMediaAvailable"]

    def isDisk(self, device):
        return self.info(device)["DeviceIsDrive"]

    def isLuks(self, device):
        return self.info(device)["DeviceIsLuks"]

    def isLuksCleartext(self, device):
        return self.info(device)["DeviceIsLuksCleartext"]

    def isMdComponent(self, device):
        return self.info(device)["DeviceIsLinuxMdComponent"]

    def isMd(self, device):
        return self.info(device)["DeviceIsLinuxMd"]

    def isLvm2LV(self, device):
        return self.info(device)["DeviceIsLinuxLvm2LV"]

    def isLvm2PV(self, device):
        return self.info(device)["DeviceIsLinuxLvm2LV"]

    def getDevice(self, sysfsPath):
        for device in self.enumerateDevices:
            if self.getSysPath(device) == sysfsPath:
                return device
        return None

    def getDeviceName(self, device):
        return os.path.basename(self.info(device)["DeviceFile"])

    def getSysPath(self, device):
        return self.info(device)["NativaPath"]

    def getUUID(self, device):
        return self.info(device)["IdUuid"]

    def getMajor(self, device):
        return self.info(device)["DeviceMajor"]

    def getMinor(self, device):
        return self.info(device)["DeviceMinor"]

    def getSerial(self, device):
        return self.info(device)["DriveSerial"]

    def getVendor(self, device):
        return self.info(device)["DriveVendor"]
