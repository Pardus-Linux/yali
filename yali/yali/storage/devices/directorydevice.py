#!/usr/bin/python
# -*- coding: utf-8 -*-

import gettext
__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext

import yali
import yali.util
from device import Device, DeviceError
from filedevice import FileDevice

class DirectoryDeviceError(yali.Error):
    pass

class DirectoryDevice(FileDevice):
    """ A directory on a filesystem.

        This exists because of bind mounts.
    """
    _type = "directory"

    def create(self):
        """ Create the device. """
        if self.exists:
            raise DeviceError("device already exists", self.name)

        self.createParents()
        self.setupParents()
        try:
            yali.util.mkdirChain(self.path)
        except Exception, e:
            raise DeviceError(e, self.name)

        self.exists = True

    def destroy(self):
        """ Destroy the device. """
        if not self.exists:
            raise DeviceError("device has not been created", self.name)

        os.unlink(self.path)
        self.exists = False
