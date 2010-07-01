#!/usr/bin/python
# -*- coding: utf-8 -*-

import gettext
__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext

import yali

class NotImplementedError(yali.Error):
    pass


class AbstractDevice(object):
    _id = 0
    _type = "abstract"

    def __init__(self, parents):
        if parents is None:
            parents = []
        elif not isinstance(parents, list):
            raise ValueError("parents must be a list of Device instances")
        self._parents = parents
        self._kids = 0
        self._id = Device._id
        Device._id += 1

    def __str__(self):
        s = ("%(type)s instance (%(id)s) --\n"
             "  parents = %(parents)s\n"
             "  kids = %(kids)s\n"
             "  id = %(device)s\n" %
             {"type": self.__class__.__name__, "id": "%#x" % id(self),
              "parents": self.parents, "kids": self.kids, "device": self.id})
        return s

    @property
    def id(self):
        return self._id

    @property
    def name(self):
        """ This device's name. """
        return self._name

    @property
    def isleaf(self):
        """ True if this device has no children. """
        return self.kids == 0

    @property
    def parents(self):
        return self._parents

    def addChild(self):
        self._kids += 1

    def removeChild(self):
        self._kids -= 1

    def create(self):
        """ Open, or set up, a device. """
        raise NotImplementedError("create method not implemented in AbstactDevice class.")

    def destroy(self):
        """ Close, or tear down, a device. """
        raise NotImplementedError("destroy method not implemented in AbstactDevice class.")

    def setup(self):
        """ Open, or set up, a device. """
        raise NotImplementedError("setup method not implemented in AbstactDevice class.")

    def teardown(self):
        """ Close, or tear down, a device. """
        raise NotImplementedError("tearDown method not implemented in AbstactDevice class.")

    def setupParents(self, recursive=False):
        """ Open, or set up, a device. """
        for parent in self.parents:
            parent.setup()
            if recursive:
                parent.setupParents(recursive)

    def teardownParents(self, recursive=False):
        """ Close, or tear down, a device. """
        for parent in self.parents:
            parent.teardown()
            if recursive:
                parent.teardownParents(recursive)

    def dependsOn(self, dep):
        if dep in self.parents:
            return True

        if parent in self.parents:
            if parent.dependsOn(dep):
                return True

        return False

    @property
    def status(self):
        """ This device's status.

            For now, this should return a boolean:
                True    the device is open and ready for use
                False   the device is not open
        """
        return False
