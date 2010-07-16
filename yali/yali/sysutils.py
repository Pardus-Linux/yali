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

# sysutils module provides basic system utilities

import os
import sys
import time
import subprocess
from string import ascii_letters
from string import digits
from pardus.sysutils import find_executable
from pardus import procutils

from yali._sysutils import *
from yali.constants import consts

import gettext
__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext

_sys_dirs = ['dev', 'proc', 'sys']

def run(cmd, params=None, capture=False, appendToLog=True):
    import yali.gui.context as ctx

    # Merge parameters with command
    if params:
        cmd = "%s %s" % (cmd, ' '.join(params))

    # to use Popen we need a tuple
    _cmd = tuple(cmd.split())
    ctx.logger.debug("RUN : %s" % cmd)

    # Create an instance for Popen
    try:
        proc = subprocess.Popen(_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception, e:
        if e.errno == 2:
            # No such executable
            ctx.logger.debug("FAILED : '%s' %s" % (cmd, e))
            return False
    else:
        # Capture the output
        stdout, stderr = proc.communicate()
        result = proc.poll()

        ctx.logger.debug(stderr)
        if appendToLog:
            ctx.logger.debug(stdout)

        # if return code larger then zero, means there is a problem with this command
        if result > 0:
            ctx.logger.debug("FAILED : %s" % cmd)
            return False
        ctx.logger.debug("SUCCESS : %s" % cmd)
        if capture:
            return stdout
        return True

def chrootRun(cmd):
    run("chroot %s %s" % (consts.target_dir, cmd))

# run dbus daemon in chroot
def chrootDbus():

    for _dir in _sys_dirs:
        tgt = os.path.join(consts.target_dir, _dir)
        run("mount --bind /%s %s" % (_dir, tgt))

    chrootRun("/sbin/ldconfig")
    chrootRun("/sbin/update-environment")
    chrootRun("/bin/service dbus start")

def finalizeChroot():
    # close filesDB if it is still open
    import pisi
    filesdb = pisi.db.filesdb.FilesDB()
    if filesdb.is_initialized():
        filesdb.close()

    # stop dbus
    chrootRun("/bin/service dbus stop")

    # kill comar in chroot if any exists
    chrootRun("/bin/killall comar")

    # unmount sys dirs
    c = _sys_dirs
    c.reverse()
    for _dir in c:
        tgt = os.path.join(consts.target_dir, _dir)
        umount_(tgt)

    # store log content
    import yali.gui.context as ctx
    ctx.logger.debug("Finalize Chroot called this is the last step for logs ..")
    if ctx.debugEnabled:
        open(ctx.consts.log_file,"w").write(str(ctx.logger.traceback.plainLogs))

    # store session log as kahya xml
    open(ctx.consts.session_file,"w").write(str(ctx.installData.sessionLog))
    os.chmod(ctx.consts.session_file,0600)

    # swap off if it is opened
    run("swapoff -a")

    # umount target dir
    umount_(consts.target_dir)

def udevSettle(timeout=None):
    arg = ''
    if timeout:
        arg = "--timeout=%d" % int(timeout)
    run("udevadm settle %s" % arg)

def checkKernelFlags(flag):
    for line in open("/proc/cpuinfo", "r").readlines():
        if line.startswith("flags"):
            return flag in line

def isLoadedKernelPAE():
    if os.uname()[2].split("-")[-1].__eq__("pae"):
        return True
    else:
        return False

def checkYaliParams(param):
    for i in [x for x in open("/proc/cmdline", "r").read().split()]:
        if i.startswith("yali="):
            if param in i.split("=")[1].split(","):
                return True
    return False

def checkYaliOptions(param):
    for i in [x for x in open("/proc/cmdline", "r").read().split(' ')]:
        if i.startswith("yali=") and not i.find("%s:" % param) == -1:
            for part in i.split("=")[1].split(","):
                if part.startswith("%s:" % param):
                    return str(part.split(':')[1]).strip()
    return None

def swapAsFile(filepath, mb_size):
    dd, mkswap = find_executable('dd'), find_executable('mkswap')

    if (not dd) or (not mkswap): return False

    create_swap_file = "%s if=/dev/zero of=%s bs=1024 count=%d" % (dd, filepath, (int(mb_size)*1024))
    mk_swap          = "%s %s" % (mkswap, filepath)

    try:
        for cmd in [create_swap_file, mk_swap]:
            p = os.popen(cmd)
            p.close()
        os.chmod(filepath, 0600)
    except:
        return False

    return True

def swapOn(partition):
    # swap on
    params = ["-v", partition]
    run("swapon", params)

##
# total memory size
def memTotal():
    m = open("/proc/meminfo")
    for l in m:
        if l.startswith("MemTotal"):
            return int(l.split()[1]) / 1024
    return None

def ejectCdrom(mount_point=consts.source_dir):
    if "copytoram" not in open("/proc/cmdline", "r").read().strip().split():
        run("eject -m %s" % mount_point)
    else:
        reboot()

def setMouse(key="left"):
    struct = {_("left") :"1 2 3",
              _("right"):"3 2 1"}
    os.system("xmodmap -e \"pointer = %s\"" % struct[key])

    # Fix for TouchPads in left handed mouse...
    if key == "right":
        os.system("synclient TapButton1=3 TapButton3=1")

def isTextValid(text):
    allowed_chars = ascii_letters + digits + '.' + '_' + '-'
    return len(text) == len(filter(lambda u: [x for x in allowed_chars if x == u], text))

def mount(source, target, fs, needs_mtab=False):
    params = ["-t", fs, source, target]
    if not needs_mtab:
        params.insert(0,"-n")
    run("mount",params)

def umount_(dir=None, params=''):
    if not dir:
        dir = consts.tmp_mnt_dir
    param = [dir, params]
    run("umount",param)

def umountSystemPaths():
    import yali.gui.context as ctx
    try:
        ctx.logger.debug("Trying to umount %s" % ctx.consts.tmp_mnt_dir)
        umount_(ctx.consts.tmp_mnt_dir)
        ctx.logger.debug("Trying to umount %s" % (ctx.consts.target_dir + "/mnt/archive"))
        umount_(ctx.consts.target_dir + "/mnt/archive")
        ctx.logger.debug("Trying to umount %s" % (ctx.consts.target_dir + "/home"))
        umount_(ctx.consts.target_dir + "/home")
    except:
        ctx.logger.debug("Umount Failed ")

def isWindowsBoot(partition_path, file_system):
    m_dir = consts.tmp_mnt_dir
    if not os.path.isdir(m_dir):
        os.makedirs(m_dir)
    umount(m_dir)
    try:
        if file_system == "fat32":
            mount(partition_path, m_dir, "vfat")
        else:
            mount(partition_path, m_dir, file_system)
    except:
        return False

    exist = lambda f: os.path.exists(os.path.join(m_dir, f))

    if exist("boot.ini") or exist("command.com") or exist("bootmgr"):
        umount_(m_dir)
        return True
    else:
        umount_(m_dir)
        return False

def isLinuxBoot(partition_path, file_system):
    import yali.gui.context as ctx
    result = False
    m_dir = consts.tmp_mnt_dir
    if not os.path.isdir(m_dir):
        os.makedirs(m_dir)
    umount_(m_dir)

    ctx.logger.debug("Mounting %s to %s" % (partition_path, consts.tmp_mnt_dir))

    try:
        mount(partition_path, m_dir, file_system)
    except:
        ctx.logger.debug("Mount failed for %s " % partition_path)
        return False

    exist = lambda f: os.path.exists(os.path.join(m_dir,"boot/grub/", f))

    if exist("grub.conf") or exist("menu.lst"):
        menuLst = os.path.join(m_dir,"boot/grub/menu.lst")
        grubCnf = os.path.join(m_dir,"boot/grub/grub.conf")
        if os.path.islink(menuLst):
            ctx.logger.debug("grub.conf found on device %s" % partition_path)
            result = grubCnf
        else:
            ctx.logger.debug("menu.lst found on device %s" % partition_path)
            result = menuLst

    return result

def liveMediaSystem(path=None):
    if not path:
        path  = "/var/run/pardus/livemedia"
    if os.path.exists(path):
        return file("/var/run/pardus/livemedia", 'r').read().split('\n')[0]
    else:
        return None

def pardusRelease(partition_path, file_system):
    import yali.gui.context as ctx
    result = False
    m_dir = consts.tmp_mnt_dir
    if not os.path.isdir(m_dir):
        os.makedirs(m_dir)
    umount_(m_dir)

    ctx.logger.debug("Mounting %s to %s" % (partition_path, consts.tmp_mnt_dir))

    try:
        mount(partition_path, m_dir, file_system)
    except:
        ctx.logger.debug("Mount failed for %s " % partition_path)
        return False

    fpath = os.path.join(m_dir, consts.pardus_release_path)
    if os.path.exists(fpath):
        return open(fpath,'r').read().strip()
    return ''

def reboot():
    run("/tmp/reboot -f")
    # fastreboot()

def shutdown():
    run("/tmp/shutdown -h now")

# Shamelessly stolen from Anaconda :)
def execClear(command, argv, stdin = 0, stdout = 1, stderr = 2):
    import yali.gui.context as ctx

    argv = list(argv)
    if isinstance(stdin, str):
        if os.access(stdin, os.R_OK):
            stdin = open(stdin)
        else:
            stdin = 0
    if isinstance(stdout, str):
        stdout = open(stdout, "w")
    if isinstance(stderr, str):
        stderr = open(stderr, "w")
    if stdout is not None and not isinstance(stdout, int):
        ctx.logger.debug("RUN : %s" %([command] + argv,))
        stdout.write("Running... %s\n" %([command] + argv,))

    p = os.pipe()
    childpid = os.fork()
    if not childpid:
        os.close(p[0])
        os.dup2(p[1], 1)
        os.dup2(stderr.fileno(), 2)
        os.dup2(stdin, 0)
        os.close(stdin)
        os.close(p[1])
        stderr.close()

        os.execvp(command, [command] + argv)
        os._exit(1)

    os.close(p[1])
    log = ''
    while 1:
        try:
            s = os.read(p[0], 1)
        except OSError, args:
            (num, msg) = args
            if (num != 4):
                raise IOError, args

        stdout.write(s)
        log+=s
        ctx.mainScreen.processEvents()

        if len(s) < 1:
            break

    try:
        ctx.logger.debug("OUT : %s" % log)
    except Exception, e:
        ctx.logger.debug("Debuger itself crashed yay :) %s" % e)

    try:
        (pid, status) = os.waitpid(childpid, 0)
    except OSError, (num, msg):
        ctx.logger.debug("exception from waitpid: %s %s" %(num, msg))

    if status is None:
        return 0

    if os.WIFEXITED(status):
        return os.WEXITSTATUS(status)

    return 1


## Run an external program and capture standard out.
# @param command The command to run.
# @param argv A list of arguments.
# @param stdin The file descriptor to read stdin from.
# @param stderr The file descriptor to redirect stderr to.
# @param root The directory to chroot to before running command.
# @return The output of command from stdout.
def execWithCapture(command, argv, stdin = 0, stderr = 2, root ='/'):
    argv = list(argv)

    if isinstance(stdin, str):
        if os.access(stdin, os.R_OK):
            stdin = open(stdin)
        else:
            stdin = 0

    if isinstance(stderr, str):
        stderr = open(stderr, "w")

    try:
        pipe = subprocess.Popen([command] + argv, stdin = stdin,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                cwd=root)
    except OSError, ( errno, msg ):
        raise RuntimeError, "Error running " + command + ": " + msg

    rc = pipe.stdout.read()
    pipe.wait()
    return rc

import re
import string

# Based on RedHat's ZoneTab class
class TimeZoneEntry:
    def __init__(self, code=None, timeZone=None):
        self.code = code
        self.timeZone = timeZone

class TimeZoneList:
    def __init__(self, fromFile='/usr/share/zoneinfo/zone.tab'):
        self.entries = []
        self.readTimeZone(fromFile)

    def getEntries(self):
        return self.entries

    def readTimeZone(self, fn):
        f = open(fn, 'r')
        comment = re.compile("^#")
        while 1:
            line = f.readline()
            if not line:
                break
            if comment.search(line):
                continue
            fields = string.split(line, '\t')
            if len(fields) < 3:
                continue
            code = fields[0]
            timeZone = string.strip(fields[2])
            entry = TimeZoneEntry(code, timeZone)
            self.entries.append(entry)

# getShadow for passwd ..
import random
import hashlib

def getShadowed(passwd):
    des_salt = list('./0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz') 
    salt, magic = str(random.random())[-8:], '$1$'

    ctx = hashlib.new('md5', passwd)
    ctx.update(magic)
    ctx.update(salt)

    ctx1 = hashlib.new('md5', passwd)
    ctx1.update(salt)
    ctx1.update(passwd)

    final = ctx1.digest()

    for i in range(len(passwd), 0 , -16):
        if i > 16:
            ctx.update(final)
        else:
            ctx.update(final[:i])

    i = len(passwd)

    while i:
        if i & 1:
            ctx.update('\0')
        else:
            ctx.update(passwd[:1])
        i = i >> 1
    final = ctx.digest()

    for i in range(1000):
        ctx1 = hashlib.new('md5')
        if i & 1:
            ctx1.update(passwd)
        else:
            ctx1.update(final)
        if i % 3: ctx1.update(salt)
        if i % 7: ctx1.update(passwd)
        if i & 1:
            ctx1.update(final)
        else:
            ctx1.update(passwd)
        final = ctx1.digest()

    def _to64(v, n):
        r = ''
        while (n-1 >= 0):
            r = r + des_salt[v & 0x3F]
            v = v >> 6
            n = n - 1
        return r

    rv = magic + salt + '$'
    final = map(ord, final)
    l = (final[0] << 16) + (final[6] << 8) + final[12]
    rv = rv + _to64(l, 4)
    l = (final[1] << 16) + (final[7] << 8) + final[13]
    rv = rv + _to64(l, 4)
    l = (final[2] << 16) + (final[8] << 8) + final[14]
    rv = rv + _to64(l, 4)
    l = (final[3] << 16) + (final[9] << 8) + final[15]
    rv = rv + _to64(l, 4)
    l = (final[4] << 16) + (final[10] << 8) + final[5]
    rv = rv + _to64(l, 4)
    l = final[11]
    rv = rv + _to64(l, 2)

    return rv

