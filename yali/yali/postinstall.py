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

import os
import grp
import time
import dbus
import yali
import shutil
import gettext

__trans = gettext.translation('yali', fallback=True)
_ = __trans.ugettext

import sysutils
import yali.pisiiface
import yali.gui.context as ctx
from yali.constants import consts
from yali.gui.installdata import *

def cp(s, d):
    src = os.path.join(consts.target_dir, s)
    dst = os.path.join(consts.target_dir, d)
    ctx.debugger.log("Copying from '%s' to '%s'" % (src,dst))
    shutil.copyfile(src, dst)

def touch(f, m=0644):
    f = os.path.join(consts.target_dir, f)
    open(f, "w", m).close()

def chgrp(f, group):
    f = os.path.join(consts.target_dir, f)
    gid = int(grp.getgrnam(group)[2])
    os.chown(f, 0, gid)

# necessary things after a full install

def initbaselayout():
    # create /etc/hosts
    cp("usr/share/baselayout/hosts", "etc/hosts")

    # create /etc/ld.so.conf
    cp("usr/share/baselayout/ld.so.conf", "etc/ld.so.conf")

    # /etc/passwd, /etc/shadow, /etc/group
    cp("usr/share/baselayout/passwd", "etc/passwd")
    cp("usr/share/baselayout/shadow", "etc/shadow")
    os.chmod(os.path.join(consts.target_dir, "etc/shadow"), 0600)
    cp("usr/share/baselayout/group", "etc/group")

    # create empty log file
    touch("var/log/lastlog")

    touch("var/run/utmp", 0664)
    chgrp("var/run/utmp", "utmp")

    touch("var/log/wtmp", 0664)
    chgrp("var/log/wtmp", "utmp")

    # create needed device nodes
    os.system("/bin/mknod %s/dev/console c 5 1" % consts.target_dir)
    os.system("/bin/mknod %s/dev/null c 1 3" % consts.target_dir)
    os.system("/bin/mknod %s/dev/random c 1 8" % consts.target_dir)
    os.system("/bin/mknod %s/dev/urandom c 1 9" % consts.target_dir)

def setTimeZone():

    # New Way; use zic
    sysutils.chrootRun("/usr/sbin/zic -l %s" % ctx.installData.timezone)

    # Old Way; copy proper timezone file as etc/localtime
    # os.system("rm -rf %s" % os.path.join(consts.target_dir, "etc/localtime"))
    # cp("usr/share/zoneinfo/%s" % ctx.installData.timezone, "etc/localtime")

    # Write the timezone data into /etc/timezone
    open(os.path.join(consts.target_dir, "etc/timezone"), "w").write("%s" % ctx.installData.timezone)

    return True

def migrateXorg():
    def joy(a):
        return os.path.join(consts.target_dir,a[1:])

    # copy confs
    files = ["/etc/X11/xorg.conf",
             "/etc/hal/fdi/policy/10-keymap.fdi",
             "/var/lib/zorg/config.xml"]

    for conf in files:
        if not os.path.exists(joy(os.path.dirname(conf))):
            os.makedirs(joy(os.path.dirname(conf)))

        if os.path.exists(conf):
            ctx.debugger.log("Copying from '%s' to '%s'" % (conf, joy(conf)))
            shutil.copyfile(conf, joy(conf))

global bus
bus = None

def connectToDBus():
    global bus
    for i in range(40):
        try:
            ctx.debugger.log("trying to start dbus..")
            ctx.bus = bus = dbus.bus.BusConnection(address_or_type="unix:path=%s" % ctx.consts.dbus_socket_file)
            break
        except dbus.DBusException:
            time.sleep(2)
            ctx.debugger.log("wait dbus for 1 second...")
    if bus:
        return True
    return False

def setHostName():
    global bus
    obj = bus.get_object("tr.org.pardus.comar", "/package/baselayout")
    obj.setHostName(str(ctx.installData.hostName), dbus_interface="tr.org.pardus.comar.Network.Stack")
    ctx.debugger.log("Hostname set as %s" % ctx.installData.hostName)
    return True

def getUserList():
    import comar
    link = comar.Link(socket=ctx.consts.dbus_socket_file)
    users = link.User.Manager["baselayout"].userList()
    return filter(lambda user: user[0]==0 or (user[0]>=1000 and user[0]<=65000), users)

def setUserPass(uid, password):
    import comar
    link = comar.Link(socket=ctx.consts.dbus_socket_file)
    info = link.User.Manager["baselayout"].userInfo(uid)
    return link.User.Manager["baselayout"].setUser(uid, info[1], info[3], info[4], password, info[5])

def getConnectionList():
    import comar
    link = comar.Link(socket=ctx.consts.dbus_socket_file)
    results = {}
    for package in link.Network.Link:
        results[package] = list(link.Network.Link[package].connections())
    return results

def connectTo(package, profile):
    import comar
    link = comar.Link(socket=ctx.consts.dbus_socket_file)
    return link.Network.Link[package].setState(profile, "up")

def addUsers():
    global bus

    import comar
    link = comar.Link(socket=ctx.consts.dbus_socket_file)

    def setNoPassword(uid):
        link.User.Manager["baselayout"].grantAuthorization(uid, "*")

    obj = bus.get_object("tr.org.pardus.comar", "/package/baselayout")
    for u in yali.users.pending_users:
        ctx.debugger.log("User %s adding to system" % u.username)
        uid = obj.addUser(-1, u.username, u.realname, "", "", unicode(u.passwd), u.groups, [], [], dbus_interface="tr.org.pardus.comar.User.Manager")
        ctx.debugger.log("New user's id is %s" % uid)

        # If new user id is different from old one, we need to run a huge chown for it
        user_home_dir = os.path.join(consts.target_dir, 'home', u.username)
        user_home_dir_id = os.stat(user_home_dir)[4]
        if not user_home_dir_id == uid:
            ctx.yali.info.updateAndShow(_("Preparing home directory for %s...") % u.username)
            os.system('chown -R %d:%d %s ' % (uid, 100, user_home_dir))
            ctx.yali.info.hide()

        os.chmod(user_home_dir, 0711)

        # Enable auto-login
        if u.username == ctx.installData.autoLoginUser:
            u.setAutoLogin()

        # Set no password ask for PolicyKit
        if u.noPass:
            setNoPassword(uid)

    return True

def setRootPassword():
    if not ctx.installData.useYaliFirstBoot:
        global bus
        obj = bus.get_object("tr.org.pardus.comar", "/package/baselayout")
        obj.setUser(0, "", "", "", str(ctx.installData.rootPassword), "", dbus_interface="tr.org.pardus.comar.User.Manager")
    return True

def writeConsoleData():
    keymap = ctx.installData.keyData["consolekeymap"]
    if isinstance(keymap, list):
        keymap = keymap[1]
    yali.localeutils.writeKeymap(ctx.installData.keyData["consolekeymap"])
    ctx.debugger.log("Keymap stored.")
    return True

def migrateXorgConf():
    if not ctx.yali.install_type == YALI_FIRSTBOOT:
        yali.postinstall.migrateXorg()
        ctx.debugger.log("xorg.conf and other files merged.")
    return True

def copyPisiIndex():
    target = os.path.join(ctx.consts.target_dir, "var/lib/pisi/index/%s" % ctx.consts.pardus_repo_name)

    if os.path.exists(ctx.consts.pisi_index_file):
        # Copy package index
        shutil.copy(ctx.consts.pisi_index_file, target)
        shutil.copy(ctx.consts.pisi_index_file_sum, target)

        # Extract the index
        import bz2
        pureIndex = file(os.path.join(target,"pisi-index.xml"),"w")
        pureIndex.write(bz2.decompress(open(ctx.consts.pisi_index_file).read()))
        pureIndex.close()

        ctx.debugger.log("pisi index files copied.")
    else:
        ctx.debugger.log("pisi index file not found!")

    ctx.debugger.log("Regenerating pisi caches.. ")
    yali.pisiiface.regenerateCaches()
    return True

def setPackages():
    global bus
    if ctx.yali.install_type == YALI_OEMINSTALL:
        ctx.debugger.log("OemInstall selected.")
        try:
            obj = bus.get_object("tr.org.pardus.comar", "/package/yali")
            obj.setState("on", dbus_interface="tr.org.pardus.comar.System.Service")
            file("%s/etc/yali-is-firstboot" % ctx.consts.target_dir, "w")
            obj = bus.get_object("tr.org.pardus.comar", "/package/kdebase")
            obj.setState("off", dbus_interface="tr.org.pardus.comar.System.Service")
        except:
            ctx.debugger.log("Dbus error: package doesnt exist !")
            return False
    elif ctx.yali.install_type in [YALI_INSTALL, YALI_FIRSTBOOT]:
        try:
            obj = bus.get_object("tr.org.pardus.comar", "/package/yali")
            obj.setState("off", dbus_interface="tr.org.pardus.comar.System.Service")
            #FIXME: We no longer have kdebase package in 2009!!
            obj = bus.get_object("tr.org.pardus.comar", "/package/kdebase")
            obj.setState("on", dbus_interface="tr.org.pardus.comar.System.Service")
            os.unlink("%s/etc/yali-is-firstboot" % ctx.consts.target_dir)
            os.system("pisi rm yali")
        except:
            ctx.debugger.log("Dbus error: package doesnt exist !")
            return False
    return True


def writeInitramfsConf(parameters=[]):
    path = os.path.join(consts.target_dir, "etc/initramfs.conf")
    rootDevice = ctx.storage.storageset.rootDevice
    parameters.append("root=%s" % rootDevice.fstabSpec)

    swapDevice = ctx.storage.storageset.swapDevices[0]

    if swapDevices:
        parameters.append("resume=%s" % swapDevice.path

    ctx.debugger.log("Configuring initramfs.conf file with parameters:%s" % " ".join(parameters))

    initramfsConf = open(path, 'w')

    for param in parameters:
        try:
            initramfsConf.write("%s\n" % param)
        except IOError, msg:
            ctx.debugger.log("Unexpected error: %s" % msg)
            raise IOError

    initramfsConf.close()

##### FIXME: Be sure after storage api rewrite will be finished
#def setPartitionPrivileges(request, mode, uid, gid):
#    requestPath =  os.path.join(ctx.consts.target_dir, request.partitionType().mountpoint.lstrip("/"))
#    ctx.debugger.log("Trying to change privileges %s path" % requestPath)
#    if os.path.exists(requestPath):
#        try:
#            os.chmod(requestPath, mode)
#            os.chown(requestPath, uid, gid)
#        except OSError, msg:
#                ctx.debugger.log("Unexpected error: %s" % msg)

