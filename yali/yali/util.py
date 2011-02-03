#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import grp
import shutil
import subprocess
import string
import stat
import errno
import ConfigParser
import gettext

_ = gettext.translation('yali', fallback=True).ugettext

import pisi
import piksemel
import yali
import yali.localedata
import yali.context as ctx
from pardus.diskutils import EDD

EARLY_SWAP_RAM = 512 * 1024 # 512 MB

def cp(source, destination):
    source = os.path.join(ctx.consts.target_dir, source)
    destination = os.path.join(ctx.consts.target_dir, destination)
    ctx.logger.debug("Copying from '%s' to '%s'" % (source, destination))
    shutil.copyfile(source, destination)

def touch(path, mode=0644):
    f = os.path.join(ctx.consts.target_dir, path)
    open(f, "w", mode).close()

def chgrp(path, group):
    f = os.path.join(ctx.consts.target_dir, path)
    gid = int(grp.getgrnam(group)[2])
    os.chown(f, 0, gid)

def product_name():
    if os.path.exists(ctx.consts.pardus_release_file):
        return open(ctx.consts.pardus_release_file,'r').read()
    return ''

def produc_id():
    release = product_name().split()
    return release[1].lower()

def product_release():
    release = product_name().split()
    return "".join(release[:2]).lower()

def target_pardus_release(device, file_system):
    result = False
    if not os.path.isdir(ctx.consts.tmp_mnt_dir):
        os.makedirs(ctx.consts.tmp_mnt_dir)

    umount(ctx.consts.tmp_mnt_dir)

    ctx.logger.debug("Mounting %s to %s" % (partition_path, ctx.consts.tmp_mnt_dir))

    try:
        mount(device, ctx.consts.tmp_mnt_dir, file_system)
    except:
        ctx.logger.debug("Mount failed for %s " % device)
        return False

    fpath = os.path.join(ctx.consts.tmp_mnt_dir, ctx.consts.pardus_release_file)
    if os.path.exists(fpath):
        return open(fpath,'r').read().strip()
    return ''

def is_text_valid(text):
    allowed_chars = string.ascii_letters + string.digits + '.' + '_' + '-'
    return len(text) == len(filter(lambda u: [x for x in allowed_chars if x == u], text))

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

def insert_colons(a_string):
    """
    Insert colon between every second character.

    E.g. creates 'al:go:ri:th:ms' from 'algoritms'. Useful for formatting MAC
    addresses and wwids for output.
    """
    suffix = a_string[-2:]
    if len(a_string) > 2:
        return insert_colons(a_string[:-2]) + ':' + suffix
    else:
        return suffix

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

def run_batch(cmd, argv=[]):
    """Run command and report return value and output."""
    ctx.logger.info('Running %s' % "".join(cmd))
    env = os.environ.copy()
    env.update({"LC_ALL": "C"})
    cmd = "%s %s" % (cmd, ' '.join(argv))
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    out, error = p.communicate()
    ctx.logger.debug('return value for "%(command)s" is %(return)s' % {"command":cmd, "return":p.returncode})
    if ctx.flags.debug:
        ctx.logger.debug('output for "%(command)s" is %(output)s' % {"command":cmd, "output":out})
        ctx.logger.debug('error value for "%(command)s" is %(error)s' % {"command":cmd, "error":error})
    return (p.returncode, out, error)


# TODO: it might be worthwhile to try to remove the
# use of ctx.stdout, and use run_batch()'s return
# values instead. but this is good enough :)
def run_logged(cmd, argv):
    """Run command and get the return value."""
    ctx.logger.info('Running %s' % " ".join(cmd))
    env = os.environ.copy()
    env.update({"LC_ALL": "C"})
    if ctx.stdout:
        stdout = ctx.stdout
    else:
        if ctx.flags.debug:
            stdout = None
        else:
            stdout = subprocess.PIPE
    if ctx.stderr:
        stderr = ctx.stderr
    else:
        if ctx.flags.debug:
            stderr = None
        else:
            stderr = subprocess.STDOUT

    cmd = "%s %s" % (cmd, ' '.join(argv))
    p = subprocess.Popen(cmd, shell=True, stdout=stdout, stderr=stderr, env=env)
    out, error = p.communicate()
    ctx.logger.debug('return value for "%(command)s" is %(return)s' % {"command":cmd, "return":p.returncode})
    ctx.logger.debug('output for "%(command)s" is %(output)s' % {"command":cmd, "output":out})
    ctx.logger.debug('error value for "%(command)s" is %(error)s' % {"command":cmd, "error":error})

    return (p.returncode, out, error)

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
        return 'i686'
    elif isX86(bits=64):
        return 'x86_64'
    else:
        return os.uname()[4]

def isX86(bits=None):
    arch = os.uname()[4]

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
            if e.errno == errno.EEXIST and stat.S_ISDIR(os.stat(dir).st_mode):
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

def umount(location, removeDir=True):
    location = os.path.normpath(location)

    if not os.path.isdir(location):
        raise ValueError, "util.umount() can only umount by mount point. %s is not existing directory" % location

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
    try:
        shutil.copyfile("/var/log/yali.log", os.path.join(ctx.consts.target_dir, "var/log/yaliInstall.log"))
    except IOError, msg:
        ctx.logger.debug(_("YALI log file doesn't exists."))
    except Error, msg:
        ctx.logger.debug(_("File paths are the same."))
    else:
        return True

    # store session log as kahya xml
    #open(ctx.consts.session_file,"w").write(str(ctx.installData.sessionLog))
    #os.chmod(ctx.consts.session_file,0600)

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

def check_dual_boot():
    return isX86()

def writeLocaleFromCmdline():
    locale_file_path = os.path.join(ctx.consts.target_dir, "etc/env.d/03locale")
    f = open(locale_file_path, "w")

    f.write("LANG=%s\n" % yali.localedata.locales[ctx.consts.lang]["locale"])
    f.write("LC_ALL=%s\n" % yali.localedata.locales[ctx.consts.lang]["locale"])

def setKeymap(keymap, variant=None, root=False):
    ad = ""
    if variant:
        ad = "-variant %s" % variant
    else:
        variant = "\"\""

    if not root:
        if "," in keymap:
            ad += " -option grp:alt_shift_toggle"
        run_batch("setxkbmap", ["-option", "-layout", keymap, ad])

    elif os.path.exists("/usr/libexec/xorg-save-xkb-config.sh"):
        run_batch("/usr/libexec/xorg-save-xkb-config.sh", [ctx.consts.target_dir])

    else:
        chroot("hav call zorg Xorg.Display setKeymap %s %s" % (keymap, variant))

def writeKeymap(keymap):
    mudur_file_path = os.path.join(ctx.consts.target_dir, "etc/conf.d/mudur")
    lines = []
    for l in open(mudur_file_path, "r").readlines():
        if l.strip().startswith('keymap=') or l.strip().startswith('# keymap='):
            l = 'keymap="%s"\n' % keymap
        if l.strip().startswith('language=') or l.strip().startswith('# language='):
            if ctx.consts.lang == "pt":
                l = 'language="pt_BR"\n'
            else:
                l = 'language="%s"\n' % ctx.consts.lang
        lines.append(l)

    open(mudur_file_path, "w").writelines(lines)

def write_config_option(conf_file, section, option, value):
    configParser = ConfigParser.ConfigParser()
    configParser.read(conf_file)
    if not configParser.has_section(section):
        configParser.add_section(section)
    configParser.set(section, option, value)
    with open(conf_file, "w")  as conf:
        configParser.write(conf)

def parse_branding_screens(release_file):
    try:
        document = piksemel.parse(release_file)
    except OSError, msg:
        if msg.errno == 2:
            raise yali.Error, _("Release file is missing")
    except piksemel.ParseError:
        raise yali.Error, _("Release file is inconsistent")

    if document.name() != "Release":
        raise yali.Error, _("Invalid xml file")

    screens = {}
    screens_tag = document.getTag("screens")
    if screens_tag:
        for screen_tag in screens_tag.tags("screen"):
            name = screen_tag.getTagData("name")
            icon = screen_tag.getTagData("icon")
            if not icon:
                icon  = ""

            title_tags = screen_tag.tags("title")
            if title_tags:
                titles = {}
                for title_tag in title_tags:
                    lang = title_tag.getAttribute("xml:lang")
                    if not lang:
                        lang = "en"
                    titles[lang] = unicode(title_tag.firstChild().data())

            help_tags = screen_tag.tags("help")
            if help_tags:
                helps = {}
                for help_tag in help_tags:
                    lang = help_tag.getAttribute("xml:lang")
                    if not lang:
                        lang = "en"
                    helps[lang] = unicode(help_tag.firstChild().data())

            screens[name] = (icon, titles, helps)

    return screens

def parse_branding_slideshows(release_file):
    try:
        document = piksemel.parse(release_file)
    except OSError, msg:
        if msg.errno == 2:
            raise yali.Error, _("Release file is missing")
    except piksemel.ParseError:
        raise yali.Error, _("Release file is inconsistent")

    if document.name() != "Release":
        raise yali.Error, _("Invalid xml file")

    slideshows = []
    slideshows_tag = document.getTag("slideshows")
    if slideshows_tag:
        for slideshow_tag in slideshows_tag.tags("slideshow"):
            picture = slideshow_tag.getTagData("picture")

            description_tags = slideshow_tag.tags("description")
            if description_tags:
                descriptions = {}
                for description_tag in description_tags:
                    lang = description_tag.getAttribute("xml:lang")
                    if not lang:
                        lang = "en"
                    descriptions[lang] = unicode(description_tag.firstChild().data())

            slideshows.append((picture, descriptions))

    return slideshows

def set_partition_privileges(device, mode, uid, gid):
    device_path =  os.path.join(ctx.consts.target_dir, device.format.mountpoint.lstrip("/"))
    ctx.logger.debug("Trying to change privileges %s path" % device_path)
    if os.path.exists(device_path):
        try:
            os.chmod(device_path, mode)
            os.chown(device_path, uid, gid)
        except OSError, msg:
                ctx.logger.debug("Unexpected error: %s" % msg)

