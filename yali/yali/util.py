#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import resource
import subprocess
import gettext


__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext

import yali.gui.context as ctx
from pardus.diskutils import EDD

EARLY_SWAP_RAM = 512 * 1024 # 512 MB

def product_name():
    if os.path.exists("/etc/pardus-release"):
        return open("/etc/pardus-release",'r').read()
    return ''


def numeric_type(num):
    """ Verify that a value is given as a numeric data type.

        Return the number if the type is sensible or raise ValueError
        if not.
    """
    if num is None:
        num = 0
    elif not (isinstance(num, int) or \
              isinstance(num, long) or \
              isinstance(num, float)):
        raise ValueError("value (%s) must be either a number or None" % num)

    return num

def get_edd_dict(devices):
    eddDevices = {}

    if not os.path.exists("/sys/firmware/edd"):
        rc = run_batch("modprobe", ["edd"])[0]
        if rc > 0:
            ctx.loggererror("Inserting EDD Module failed !")
            return eddDevices

    edd = EDD()
    edds = edd.list_edd_signatures()
    mbrs = edd.list_mbr_signatures()

    for number, signature in edds.items():
        if mbrs.has_key(signature):
            if mbrs[signature] in devices:
                eddDevices[os.path.basename(mbrs[signature])] = number
    return eddDevices

def run_batch(cmd, argv):
    """Run command and report return value and output."""
    ctx.logger.info(_('Running %s') % " ".join(cmd))
    cmd = "%s %s" % (cmd, ' '.join(argv))
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    ctx.logger.debug(_('return value for "%s" is %s') % (cmd, p.returncode))
    return (p.returncode, out, err)


# TODO: it might be worthwhile to try to remove the
# use of ctx.stdout, and use run_batch()'s return
# values instead. but this is good enough :)
def run_logged(cmd):
    """Run command and get the return value."""
    ctx.logger.info(_('Running %s') % " ".join(cmd))
    if ctx.stdout:
        stdout = ctx.stdout
    else:
        if ctx.get_option('debug'):
            stdout = None
        else:
            stdout = subprocess.PIPE
    if ctx.stderr:
        stderr = ctx.stderr
    else:
        if ctx.get_option('debug'):
            stderr = None
        else:
            stderr = subprocess.STDOUT

    p = subprocess.Popen(cmd, shell=True, stdout=stdout, stderr=stderr)
    out, err = p.communicate()
    ctx.logger.debug(_('return value for "%s" is %s') % (" ".join(cmd), p.returncode))

    return p.returncode

efi = None
def isEfi():
    global efi
    if efi is not None:
        return efi

    efi = False
    if os.path.exists("/sys/firmware/efi"):
        efi = True

    return efi

def isX86(bits=None):
    arch = os.uname()[4]

    # x86 platforms include:
    #     i*86
    #     x86_64
    if bits is None:
        if (arch.startswith('i') and arch.endswith('86')) or arch == 'x86_64':
            return True
    elif bits == 32:
        if arch.startswith('i') and arch.endswith('86'):
            return True
    elif bits == 64:
        if arch == 'x86_64':
            return True

    return False

def memInstalled():
    f = open("/proc/meminfo", "r")
    lines = f.readlines()
    f.close()

    for line in lines:
        if line.startswith("MemTotal:"):
            fields = line.split()
            mem = fields[1]
            break

    return int(mem)

def swap_suggestion(quiet=0):
    mem = memInstalled()/1024
    mem = ((mem/16)+1)*16
    if not quiet:
        ctx.logger.info("Detected %sM of memory", mem)

    if mem <= 256:
        minswap = 256
        maxswap = 512
    else:
        if mem > 2048:
            minswap = 1024
            maxswap = 2048 + mem
        else:
            minswap = mem
            maxswap = 2*mem

    if not quiet:
        ctx.logger.info("Swap attempt of %sM to %sM", minswap, maxswap)

    return (minswap, maxswap)

def notify_kernel(path, action="change"):
    """ Signal the kernel that the specified device has changed. """
    ctx.logger.debug("notifying kernel of '%s' event on device %s" % (action, path))
    path = os.path.join(path, "uevent")
    if not path.startswith("/sys/") or not os.access(path, os.W_OK):
        ctx.logger.debug("sysfs path '%s' invalid" % path)
        raise ValueError("invalid sysfs path")

    f = open(path, "a")
    f.write("%s\n" % action)
    f.close()

def name_from_dm_node(node):
    name = block.getNameFromDmNode(dm_node)
    if name is not None:
        return name

    st = os.stat("/dev/%s" % dm_node)
    major = os.major(st.st_rdev)
    minor = os.minor(st.st_rdev)
    name = run_batch("dmsetup", ["info", "--columns",
                      "--noheadings", "-o", "name",
                      "-j", str(major), "-m", str(minor)])[1]
    ctx.logger.debug("name_from_dm(%s) returning '%s'" % (node, name.strip()))
    return name.strip()

def dm_node_from_name(name):
    dm_node = block.getDmNodeFromName(map_name)
    if dm_node is not None:
        return dm_node

    devnum = run_batch("dmsetup", ["info", "--columns",
                        "--noheadings", "-o", "devno",name])[1]
    (major, sep, minor) = devnum.strip().partition(":")
    if not sep:
        raise DMError("dm device does not exist")

    dm_node = "dm-%d" % int(minor)
    ctx.logger.debug("dm_node_from_name(%s) returning '%s'" % (name, dm_node))
    return dm_node

def get_sysfs_path_by_name(dev_name, class_name="block"):
    dev_name = os.path.basename(dev_name)
    sysfs_class_dir = "/sys/class/%s" % class_name
    dev_path = os.path.join(sysfs_class_dir, dev_name)
    if os.path.exists(dev_path):
        return dev_path

def mkswap(device, label=''):
    # We use -f to force since mkswap tends to refuse creation on lvs with
    # a message about erasing bootbits sectors on whole disks. Bah.
    argv = ["-f"]
    if label:
        argv.extend(["-L", label])
    argv.append(device)

    rc = yali.util.run_batch("mkswap", argv)[0]

    if rc:
        raise SwapError("mkswap failed for '%s'" % device)

def swapon(device, priority=None):
    pagesize = resource.getpagesize()
    buf = None
    sig = None

    if pagesize > 2048:
        num = pagesize
    else:
        num = 2048

    try:
        fd = os.open(device, os.O_RDONLY)
        buf = os.read(fd, num)
    except OSError:
        pass
    finally:
        try:
            os.close(fd)
        except (OSError, UnboundLocalError):
            pass

    if buf is not None and len(buf) == pagesize:
        sig = buf[pagesize - 10:]
        if sig == 'SWAP-SPACE':
            raise OldSwapError
        if sig == 'S1SUSPEND\x00' or sig == 'S2SUSPEND\x00':
            raise SuspendError

    if sig != 'SWAPSPACE2':
        raise UnknownSwapError

    argv = []
    if isinstance(priority, int) and 0 <= priority <= 32767:
        argv.extend(["-p", "%d" % priority])
    argv.append(device)
    rc = yali.util.run_batch("swapon",argv)[0]

    if rc:
        raise SwapError("swapon failed for '%s'" % device)

def swap_off(device):
    rc = yali.util.run_batch("swapoff", [device])[0]

    if rc:
        raise SwapError("swapoff failed for '%s'" % device)

def swap_status(device):
    alt_dev = None
    if device.startswith("/dev/mapper/"):
        # get the real device node for device-mapper devices since the ones
        # with meaningful names are just symlinks
        try:
            alt_dev = "/dev/%s" % dm_node_from_name(device.split("/")[-1])
        except DMError:
            alt_dev = None

    lines = open("/proc/swaps").readlines()
    status = False
    for line in lines:
        if not line.strip():
            continue

        swap_dev = line.split()[0]
        if swap_dev in [device, alt_dev]:
            status = True
            break

    return status

def swap_amount():
    f = open("/proc/meminfo", "r")
    lines = f.readlines()
    f.close()

    for l in lines:
        if l.startswith("SwapTotal:"):
            fields = string.split(l)
            return int(fields[1])
    return 0

def createAvailableSizeSwapFile(storage):
    (minsize, maxsize) = swap_suggestion()
    filesystems = []

    for device in storage.storageset.devices:
        if not device.format:
            continue
        if device.format.mountable and device.format.linuxNative:
            if not device.format.status:
                continue
            space = sysutils.available_space(ctx.consts.target_dir + device.format.mountpoint)
            if space > 16:
                info = (device, space)
                filesystems.append(info)

    for (device, availablespace) in filesystems:
        if availablespace > maxsize and (size > (suggestion + 100)):
            suggestedDevice = device
