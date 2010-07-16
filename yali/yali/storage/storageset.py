#!/usr/bin/python
# -*- coding: utf-8 -*-

from devices import *
from devicetree import DeviceTree

class StorageSet(object):
    def __init__(self, devicetree, rootPath):
        self.devicetree = devicetree
        self.rootpath = rootpath
        self.active = False
        self._debugfs = None
        self._sysfs = None
        self._proc = None
        self._devshm = None

    @property
    def devices(self):
        return sorted(self.devicetree.devices, key=lambda d: d.path)

    @property
    def sysfs(self):
        if not self._sysfs:
            self._sysfs = NoDevice(format=getFormat("sysfs",
                                                    device="sys",
                                                    mountpoint="/sys"))
        return self._sysfs

    @property
    def debugfs(self):
        if not self._devpts:
            self._debugfs = NoDevice(format=getFormat("debugfs",
                                                     device="debugfs",
                                                     mountpoint="/sys/kernel/debug"))
        return self._debugfs

    @property
    def proc(self):
        if not self._proc:
            self._proc = NoDevice(format=getFormat("proc",
                                                   device="proc",
                                                   mountpoint="/proc"))
        return self._proc

    @property
    def devshm(self):
        if not self._devshm:
            self._devshm = NoDevice(format=getFormat("tmpfs",
                                                     device="tmpfs",
                                                     mountpoint="/dev/shm"))
        return self._devshm

    @property
    def mountpoints(self):
        filesystems = {}
        for device in self.devices:
            if device.format.mountable and device.format.mountpoint:
                filesystems[device.format.mountpoint] = device
        return filesystems

    def mountFilesystems(self, readOnly=None, skipRoot=False):
        devices = self.mountpoints.values() + self.swapDevices
        devices.extend([self.dev, self.devshm, self.devpts, self.sysfs, self.proc])
        devices.sort(key=lambda d: getattr(d.format, "mountpoint", None))

        for device in devices:
            if not device.format.mountable or not device.format.mountpoint:
                continue

            if skipRoot and device.format.mountpoint == "/":
                continue

            options = device.format.options
            if "noauto" in options.split(","):
                continue

            if device.format.type == "bind" and device != self.dev:
                # set up the DirectoryDevice's parents now that they are
                # accessible
                #
                # -- bind formats' device and mountpoint are always both
                #    under the chroot. no exceptions. none, damn it.
                targetDir = "%s/%s" % (anaconda.rootPath, device.path)
                parent = get_containing_device(targetDir, self.devicetree)
                if not parent:
                    ctx.logger.error("cannot determine which device contains "
                              "directory %s" % device.path)
                    device.parents = []
                    self.devicetree._removeDevice(device)
                    continue
                else:
                    device.parents = [parent]

            try:
                device.setup()
            except Exception as msg:
                # FIXME: need an error popup
                continue

            if readOnly:
                options = "%s,%s" % (options, readOnly)

            try:
                device.format.setup(options=options,
                                    chroot=anaconda.rootPath)
            except OSError as e:
                ctx.logger.error("OSError: (%d) %s" % (e.errno, e.strerror))

                if ctx.yali.messageWindow:
                    if e.errno == errno.EEXIST:
                        ctx.yali.messageWindow(_("Invalid mount point"),
                                           _("An error occurred when trying "
                                             "to create %s.  Some element of "
                                             "this path is not a directory. "
                                             "This is a fatal error and the "
                                             "install cannot continue.\n\n"
                                             "Press <Enter> to exit the "
                                             "installer.")
                                           % (device.format.mountpoint,))
                    else:
                        na = {'mountpoint': device.format.mountpoint,
                              'msg': e.strerror}
                        ctx.yali.messageWindow(_("Invalid mount point"),
                                           _("An error occurred when trying "
                                             "to create %(mountpoint)s: "
                                             "%(msg)s.  This is "
                                             "a fatal error and the install "
                                             "cannot continue.\n\n"
                                             "Press <Enter> to exit the "
                                             "installer.") % na)
                sys.exit(0)
            except SystemError as (num, msg):
                ctx.logger.error("SystemError: (%d) %s" % (num, msg) )

                if ctx.yali.messageWindow and not device.format.linuxNative:
                    na = {'path': device.path,
                          'mountpoint': device.format.mountpoint}
                    ret = ctx.yali.messageWindow(_("Unable to mount filesystem"),
                                             _("An error occurred mounting "
                                             "device %(path)s as "
                                             "%(mountpoint)s.  You may "
                                             "continue installation, but "
                                             "there may be problems.") % na,
                                             type="custom",
                                             customIcon="warning",
                                             customButtons=[_("_Exit installer"),
                                                            _("_Continue")])

                    if ret == 0:
                        sys.exit(0)
                    else:
                        continue

                sys.exit(0)
            except FSError as msg:
                ctx.logger.error("FSError: %s" % msg)

                if ctx.yali.messageWindow:
                    na = {'path': device.path,
                          'mountpoint': device.format.mountpoint,
                          'msg': msg}
                    ctx.yali.messageWindow(_("Unable to mount filesystem"),
                                       _("An error occurred mounting "
                                         "device %(path)s as %(mountpoint)s: "
                                         "%(msg)s. This is "
                                         "a fatal error and the install "
                                         "cannot continue.\n\n"
                                         "Press <Enter> to exit the "
                                         "installer.") % na)
                sys.exit(0)

        self.active = True

    def umountFilesystems(self, swapoff=True):
        devices = self.mountpoints.values() + self.swapDevices
        devices.extend([self.dev, self.devshm, self.devpts, self.sysfs, self.proc])
        devices.sort(key=lambda d: getattr(d.format, "mountpoint", None))
        devices.reverse()
        for device in devices:
            if not device.format.mountable and \
               (device.format.type != "swap" or swapoff):
                continue

            device.format.teardown()
            device.teardown()

        self.active = False

    def turnOnSwap(self):
        def swapError(msg, device):
            if not ctx.yali.messageWindow:
                sys.exit(0)

            buttons = [_("Skip"), _("Format"), _("_Exit")]
            ret = ctx.yali.messageWindow(_("Error"), msg, type="custom",
                                              customButtons=buttons,
                                              customIcon="warning")

            if ret == 0:
                self.devicetree._removeDevice(device)
                return False
            elif ret == 1:
                device.format.create(force=True)
                return True
            else:
                sys.exit(0)

        for device in self.swapDevices:
            if isinstance(device, FileDevice):
                targetDir = "%s/%s" % (self.rootPath, device.path)
                parent = get_containing_device(targetDir, self.devicetree)
                if not parent:
                    ctx.logger.error("cannot determine which device contains "
                              "directory %s" % device.path)
                    device.parents = []
                    self.devicetree._removeDevice(device)
                    continue
                else:
                    device.parents = [parent]

            while True:
                try:
                    device.setup()
                    device.format.setup()
                except OldSwapError:
                    msg = _("The swap device:\n\n     %s\n\n"
                            "is an old-style Linux swap partition.  If "
                            "you want to use this device for swap space, "
                            "you must reformat as a new-style Linux swap "
                            "partition.") \
                          % device.path

                    if swapError(msg, device):
                        continue
                except SuspendError:
                        msg = _("The swap device:\n\n     %s\n\n"
                                "in your /etc/fstab file is currently in "
                                "use as a software suspend device, "
                                "which means your system is hibernating. "
                                "If you are performing a new install, "
                                "make sure the installer is set "
                                "to format all swap devices.") \
                              % device.path

                    if swapError(msg, device):
                        continue
                except UnknownSwapError:
                    msg = _("The swap device:\n\n     %s\n\n"
                            "does not contain a supported swap volume.  In "
                            "order to continue installation, you will need "
                            "to format the device or skip it.") \
                          % device.path

                    if swapError(msg, device):
                        continue
                except DeviceError as (msg, name):
                    if ctx.yali.messageWindow:
                        err = _("Error enabling swap device %(name)s: "
                                    "%(msg)s\n\n"
                                    "This most likely means this swap "
                                    "device has not been initialized.\n\n"
                                    "Press OK to exit the installer.") % \
                                  {'name': name, 'msg': msg}
                        ctx.yali.messageWindow(_("Error"), err)
                    sys.exit(0)

                break

    def createSwapFile(self, device, size, rootPath=None):
        """ Create and activate a swap file under rootPath. """
        if not rootPath:
            rootPath = self.rootpath

        filename = "/SWAP"
        count = 0
        basedir = os.path.normpath("%s/%s" % (rootPath, device.format.mountpoint))
        while os.path.exists("%s/%s" % (basedir, filename)) or \
              self.devicetree.getDeviceByName(filename):
            file = os.path.normpath("%s/%s" % (basedir, filename))
            count += 1
            filename = "/SWAP-%d" % count

        dev = FileDevice(filename,
                         size=size,
                         parents=[device],
                         format=getFormat("swap", device=filename))
        dev.create()
        dev.setup()
        dev.format.create()
        dev.format.setup()
        self.devicetree._addDevice(dev)

    @property
    def rootDevice(self):
        for path in ["/", self.rootpath]:
            for device in self.devices:
                try:
                    mountpoint = device.format.mountpoint
                except AttributeError:
                    mountpoint = None

                if mountpoint == path:
                    return device

    @property
    def swapDevices(self):
        swaps = []
        for device in self.devices:
            if device.format.type == "swap":
                swaps.append(device)
        return swaps

    def fstab(self):
        format = "%-23s %-23s %-7s %-15s %d %d\n"
        fstab = """
#
# Created by YALI on %s
#
""" % time.asctime()

        devices = sorted(self.mountpoints.values(),
                         key=lambda d: d.format.mountpoint)
        devices += self.swapDevices
        devices.extend([self.devshm, self.debugfs, self.sysfs, self.proc])
        for device in devices:
            # why the hell do we put swap in the fstab, anyway?
            if not device.format.mountable and device.format.type != "swap":
                continue

            fstype = getattr(device.format, "mountType", device.format.type)
            if fstype == "swap":
                mountpoint = "swap"
                options = device.format.options
            else:
                mountpoint = device.format.mountpoint
                options = device.format.options
                if not mountpoint:
                    ctx.logger.warning("%s filesystem on %s has no mountpoint" % \
                                                            (fstype,
                                                             device.path))
                    continue

            options = options or "defaults"
            devspec = device.fstabSpec
            dump = device.format.dump
            if device.format.check and mountpoint == "/":
                passno = 1
            elif device.format.check:
                passno = 2
            else:
                passno = 0
            fstab = fstab + device.fstabComment
            fstab = fstab + format % (devspec, mountpoint, fstype, options, dump, passno)

        return fstab

    def write(self, installPath):
        """ write out all config files based on the set of filesystems """
        if not installPath:
            installPath = self.rootpath

        # /etc/fstab
        fstabPath = os.path.normpath("%s/etc/fstab" % installPath)
        fstab = self.fstab()
        open(fstabPath, "w").write(fstab)
