#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import subprocess
import gettext

__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext

import pisi
import yali
import yali.context as ctx
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
            ctx.logger.error("Inserting EDD Module failed !")
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

def getArch():
    if isX86(bits=32):
        return 'i386'
    elif isX86(bits=64):
        return 'x86_64'
    else:
        return os.uname()[4]

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

def get_sysfs_path_by_name(dev_name, class_name="block"):
    dev_name = os.path.basename(dev_name)
    sysfs_class_dir = "/sys/class/%s" % class_name
    dev_path = os.path.join(sysfs_class_dir, dev_name)
    if os.path.exists(dev_path):
        return dev_path

def mkdirChain(dir):
    try:
        os.makedirs(dir, 0755)
    except OSError as e:
        try:
            if e.errno == EEXIST and stat.S_ISDIR(os.stat(dir).st_mode):
                return
        except:
            pass

        ctx.logger.error("could not create directory %s: %s" % (dir, e.strerror))

def swap_amount():
    f = open("/proc/meminfo", "r")
    lines = f.readlines()
    f.close()

    for l in lines:
        if l.startswith("SwapTotal:"):
            fields = string.split(l)
            return int(fields[1])
    return 0

mountCount = {}

def mount(device, location, filesystem, readOnly=False,
          bindMount=False, remount=False, options=None):
    flags = None
    location = os.path.normpath(location)
    if not options:
        opts = ["defaults"]
    else:
        opts = options.split(",")

    if mountCount.has_key(location) and mountCount[location] > 0:
        mountCount[location] = mountCount[location] + 1
        return

    if readOnly or bindMount or remount:
        if readOnly:
            opts.append("ro")
        if bindMount:
            opts.append("bind")
        if remount:
            opts.append("remount")

    flags = ",".join(opts)
    argv = ["-t", filesystem, device, location, "-o", flags]
    rc = run_batch("mount", argv)[0]
    if not rc:
        mountCount[location] = 1

    return rc

def umount(location, removeDir = True):
    location = os.path.normpath(location)

    if not os.path.isdir(location):
        raise ValueError, "util.umount() can only umount by mount point"

    if mountCount.has_key(location) and mountCount[location] > 1:
        mountCount[location] = mountCount[location] - 1
        return

    ctx.logger.debug("util.umount()- going to unmount %s, removeDir = %s" % (location, removeDir))
    rc = run_batch("umount", [location])[0]

    if removeDir and os.path.isdir(location):
        try:
            os.rmdir(location)
        except:
            pass

    if not rc and mountCount.has_key(location):
        del mountCount[location]

    return rc

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


def chroot(command):
    run_batch("chroot", [ctx.consts.target_dir, command])

def start_dbus():
    chroot("/sbin/ldconfig")
    chroot("/sbin/update-environment")
    chroot("/bin/service dbus start")

def stop_dbus():
    filesdb = pisi.db.filesdb.FilesDB()
    if filesdb.is_initialized():
        filesdb.close()

    # stop dbus
    chroot("/bin/service dbus stop")
    # kill comar in chroot if any exists
    chroot("/bin/killall comar")

    # store log content
    ctx.logger.debug("Finalize Chroot called this is the last step for logs ..")
    #if ctx.debugEnabled:
    #    open(ctx.consts.log_file,"w").write(str(ctx.logger.traceback.plainLogs))

    # store session log as kahya xml
    open(ctx.consts.session_file,"w").write(str(ctx.installData.sessionLog))
    os.chmod(ctx.consts.session_file,0600)

def reboot():
    run_batch("/tmp/reboot", ["-f"])

def shutdown():
    run_batch("/tmp/shutdown", ["-h", "now"])

def eject(mount_point=ctx.consts.source_dir):
    if "copytoram" not in open("/proc/cmdline", "r").read().strip().split():
        run_batch("eject", ["-m", mount_point])
    else:
        reboot()

def sync():
    os.system("sync")
    os.system("sync")
    os.system("sync")


