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
import time
import dbus
import yali
import shutil
import gettext

_ = gettext.translation('yali', fallback=True).ugettext

import yali.util
import yali.pisiiface
import yali.context as ctx

def initbaselayout():
    # create /etc/hosts
    yali.util.cp("usr/share/baselayout/hosts", "etc/hosts")

    # create /etc/ld.so.conf
    yali.util.cp("usr/share/baselayout/ld.so.conf", "etc/ld.so.conf")

    # /etc/passwd, /etc/shadow, /etc/group
    yali.util.cp("usr/share/baselayout/passwd", "etc/passwd")
    yali.util.cp("usr/share/baselayout/shadow", "etc/shadow")
    os.chmod(os.path.join(ctx.consts.target_dir, "etc/shadow"), 0600)
    yali.util.cp("usr/share/baselayout/group", "etc/group")

    # create empty log file
    yali.util.touch("var/log/lastlog")

    yali.util.touch("var/run/utmp", 0664)
    yali.util.chgrp("var/run/utmp", "utmp")

    yali.util.touch("var/log/wtmp", 0664)
    yali.util.chgrp("var/log/wtmp", "utmp")

    # create needed device nodes
    os.system("/bin/mknod %s/dev/console c 5 1" % ctx.consts.target_dir)
    os.system("/bin/mknod %s/dev/null c 1 3" % ctx.consts.target_dir)
    os.system("/bin/mknod %s/dev/random c 1 8" % ctx.consts.target_dir)
    os.system("/bin/mknod %s/dev/urandom c 1 9" % ctx.consts.target_dir)

def setTimeZone():

    # New Way; use zic
    yali.util.chroot("/usr/sbin/zic -l %s" % ctx.installData.timezone)

    # Old Way; copy proper timezone file as etc/localtime
    # os.system("rm -rf %s" % os.path.join(consts.target_dir, "etc/localtime"))
    # yali.util.cp("usr/share/zoneinfo/%s" % ctx.installData.timezone, "etc/localtime")

    # Write the timezone data into /etc/timezone
    open(os.path.join(ctx.consts.target_dir, "etc/timezone"), "w").write("%s" % ctx.installData.timezone)

    return True

def migrateXorg():
    def joy(a):
        return os.path.join(ctx.consts.target_dir,a[1:])

    # copy confs
    files = ["/etc/X11/xorg.conf",
             "/etc/hal/fdi/policy/10-keymap.fdi",
             "/var/lib/zorg/config.xml"]

    for conf in files:
        if os.path.exists(conf):
            if not os.path.exists(joy(os.path.dirname(conf))):
                os.makedirs(joy(os.path.dirname(conf)))
            ctx.logger.debug("Copying from '%s' to '%s'" % (conf, joy(conf)))
            shutil.copyfile(conf, joy(conf))

bus = None

def connectToDBus():
    global bus
    for i in range(40):
        try:
            ctx.logger.debug("trying to start dbus..")
            if ctx.flags.install_type == ctx.STEP_BASE or ctx.flags.install_type == ctx.STEP_DEFAULT:
                bus = dbus.bus.BusConnection(address_or_type="unix:path=%s" % ctx.consts.target_dbus_socket)

            if ctx.flags.install_type == ctx.STEP_FIRST_BOOT:
                bus = dbus.bus.BusConnection(address_or_type="unix:path=%s" % ctx.consts.dbus_socket)

            break
        except dbus.DBusException:
            time.sleep(2)
            ctx.logger.debug("wait dbus for 1 second...")
    if bus:
        return True
    return False

def setHostName():
    global bus
    obj = bus.get_object("tr.org.pardus.comar", "/package/baselayout")
    if ctx.flags.install_type == ctx.STEP_FIRST_BOOT:
        yali.util.run_batch("hostname", [str(ctx.installData.hostName)])
        yali.util.run_batch("update-environment")
        obj.setHostName(str(ctx.installData.hostName), dbus_interface="tr.org.pardus.comar.Network.Stack")
    elif ctx.flags.install_type == ctx.STEP_DEFAULT:
        obj.setHostName(str(ctx.installData.hostName), dbus_interface="tr.org.pardus.comar.Network.Stack")

    if ctx.flags.install_type == ctx.STEP_BASE:
        obj.setHostName(str(yali.util.product_release()), dbus_interface="tr.org.pardus.comar.Network.Stack")

    ctx.logger.debug("Hostname set as %s" % ctx.installData.hostName)
    return True

def get_users():
    import comar
    link = None
    if ctx.flags.install_type == ctx.STEP_BASE or ctx.flags.install_type == ctx.STEP_DEFAULT:
        link = comar.Link(socket=ctx.consts.target_dbus_socket)

    if ctx.flags.install_type == ctx.STEP_FIRST_BOOT:
        link = comar.Link(socket=ctx.consts.dbus_socket)

    users = link.User.Manager["baselayout"].userList()
    return filter(lambda user: user[0]==0 or (user[0]>=1000 and user[0]<=65000), users)

def setUserPass(uid, password):
    import comar
    link = None
    if ctx.flags.install_type == ctx.STEP_BASE or ctx.flags.install_type == ctx.STEP_DEFAULT:
        link = comar.Link(socket=ctx.consts.target_dbus_socket)

    if ctx.flags.install_type == ctx.STEP_FIRST_BOOT:
        link = comar.Link(socket=ctx.consts.dbus_socket)

    info = link.User.Manager["baselayout"].userInfo(uid)
    return link.User.Manager["baselayout"].setUser(uid, info[1], info[3], info[4], password, info[5])

def getConnectionList():
    import comar
    if ctx.flags.install_type == ctx.STEP_BASE or ctx.flags.install_type == ctx.STEP_DEFAULT:
        link = comar.Link(socket=ctx.consts.target_dbus_socket)

    if ctx.flags.install_type == ctx.STEP_FIRST_BOOT:
        link = comar.Link(socket=ctx.consts.dbus_socket)

    results = {}
    for package in link.Network.Link:
        results[package] = list(link.Network.Link[package].connections())
    return results

def connectTo(package, profile):
    import comar
    if ctx.flags.install_type == ctx.STEP_BASE or ctx.flags.install_type == ctx.STEP_DEFAULT:
        link = comar.Link(socket=ctx.consts.target_dbus_socket)

    if ctx.flags.install_type == ctx.STEP_FIRST_BOOT:
        link = comar.Link(socket=ctx.consts.dbus_socket)

    return link.Network.Link[package].setState(profile, "up")

def addUsers():
    import comar
    if ctx.flags.install_type == ctx.STEP_BASE or ctx.flags.install_type == ctx.STEP_DEFAULT:
        link = comar.Link(socket=ctx.consts.target_dbus_socket)

    if ctx.flags.install_type == ctx.STEP_FIRST_BOOT:
        link = comar.Link(socket=ctx.consts.dbus_socket)

    def setNoPassword(uid):
        link.User.Manager["baselayout"].grantAuthorization(uid, "*")

    global bus
    obj = bus.get_object("tr.org.pardus.comar", "/package/baselayout")
    for user in yali.users.PENDING_USERS:
        ctx.logger.debug("User %s adding to system" % user.username)
        uid = obj.addUser(user.uid, user.username, user.realname, "", "",
                          unicode(user.passwd), user.groups, [], [],
                          dbus_interface="tr.org.pardus.comar.User.Manager")
        ctx.logger.debug("New user's id is %s" % uid)

        # If new user id is different from old one, we need to run a huge chown for it
        user_home_dir = ""
        if ctx.flags.install_type == ctx.STEP_BASE or ctx.flags.install_type == ctx.STEP_DEFAULT:
            user_home_dir = os.path.join(ctx.consts.target_dir, 'home', user.username)
        if ctx.flags.install_type == ctx.STEP_FIRST_BOOT:
            user_home_dir = os.path.join('/home', user.username)

        user_home_dir_id = os.stat(user_home_dir)[4]
        if not user_home_dir_id == uid:
            ctx.interface.informationWindow.update(_("Preparing home directory for %s...") % user.username)
            os.system('chown -R %d:%d %s ' % (uid, 100, user_home_dir))
            ctx.interface.informationWindow.hide()

        os.chmod(user_home_dir, 0711)

        # Enable auto-login
        if user.username == ctx.installData.autoLoginUser:
            user.setAutoLogin()

        # Set no password ask for PolicyKit
        if user.no_password:
            setNoPassword(uid)

    return True

def setRootPassword():
    global bus
    obj = bus.get_object("tr.org.pardus.comar", "/package/baselayout")
    if ctx.flags.install_type == ctx.STEP_FIRST_BOOT or ctx.flags.install_type == ctx.STEP_DEFAULT:
        obj.setUser(0, "", "", "", str(ctx.installData.rootPassword), "", dbus_interface="tr.org.pardus.comar.User.Manager")

    if ctx.flags.install_type == ctx.STEP_BASE:
        obj.setUser(0, "", "", "", str("pardus"), "", dbus_interface="tr.org.pardus.comar.User.Manager")

    return True

def writeConsoleData():
    keymap = ctx.installData.keyData["consolekeymap"]
    if isinstance(keymap, list):
        keymap = keymap[1]
    yali.util.writeKeymap(ctx.installData.keyData["consolekeymap"])
    ctx.logger.debug("Keymap stored.")
    return True

def setKeymap():
    keymap = ctx.installData.keyData
    yali.util.setKeymap(keymap["xkblayout"], keymap["xkbvariant"], root=True)

def migrateXorgConf():
    # if installation type is not First Boot
    if not ctx.flags.install_type == ctx.STEP_FIRST_BOOT:
        migrateXorg()
        ctx.logger.debug("xorg.conf and other files merged.")
    return True

def copyPisiIndex():
    target = os.path.join(ctx.consts.target_dir, "var/lib/pisi/index/%s" % ctx.consts.pardus_repo_name)

    if os.path.exists(ctx.consts.pisi_index_file):
        # Copy package index
        shutil.copy(ctx.consts.pisi_index_file, target)
        shutil.copy(ctx.consts.pisi_index_file_sum, target)

        # Extract the index
        pureIndex = file(os.path.join(target,"pisi-index.xml"),"w")
        if ctx.consts.pisi_index_file.endswith("bz2"):
            import bz2
            pureIndex.write(bz2.decompress(open(ctx.consts.pisi_index_file).read()))
        else:
            import lzma
            pureIndex.write(lzma.decompress(open(ctx.consts.pisi_index_file).read()))
        pureIndex.close()

        ctx.logger.debug("pisi index files copied.")
    else:
        ctx.logger.debug("pisi index file not found!")

    ctx.logger.debug("Regenerating pisi caches.. ")
    yali.pisiiface.regenerateCaches()
    return True

def writeInitramfsConf(parameters=[]):
    path = os.path.join(ctx.consts.target_dir, "etc/initramfs.conf")
    rootDevice = ctx.storage.storageset.rootDevice
    parameters.append("root=%s" % rootDevice.fstabSpec)

    swapDevices = ctx.storage.storageset.swapDevices

    if swapDevices:
        parameters.append("resume=%s" % swapDevices[0].path)

    if ctx.storage.lvs:
        parameters.append("lvm=1")

    if ctx.storage.raidArrays:
        parameters.append("raid=1")

    ctx.logger.debug("Configuring initramfs.conf file with parameters:%s" % parameters)

    initramfsConf = open(path, 'w')

    for param in parameters:
        try:
            initramfsConf.write("%s\n" % param)
        except IOError, msg:
            ctx.logger.debug("Unexpected error: %s" % msg)
            raise IOError

    initramfsConf.close()


def fillFstab():
    ctx.logger.debug("Generating fstab configuration file")
    ctx.storage.storageset.write(ctx.consts.target_dir)

def setupFirstBoot():
    yali.util.write_config_option(os.path.join(ctx.consts.target_dir, "etc/yali/yali.conf"), "general", "installation", "firstboot")
    ctx.logger.debug("Setup firstboot")

def setupBootLooder():
    ctx.bootloader.setup()
    ctx.logger.debug("Setup bootloader")

def writeBootLooder():
    ctx.bootloader.write()
    ctx.logger.debug("Writing grub.conf and devicemap")

def installBootloader():
    # BUG:#11255 normal user doesn't mount /mnt/archive directory. 
    # We set new formatted partition priveleges as user=root group=disk and change mod as 0770
    default_mountpoints = ['/', '/boot', '/home', '/tmp', '/var', '/opt']
    user_defined_mountpoints = [device for mountpoint, device in ctx.storage.mountpoints.items() if mountpoint not in default_mountpoints]
    if user_defined_mountpoints:
        ctx.logger.debug("User defined device mountpoints:%s" % [device.format.mountpoint for device in user_defined_mountpoints])
        for device in user_defined_mountpoints:
            yali.util.set_partition_privileges(device, 0770, 0, 6)

    # Umount system paths
    ctx.storage.storageset.umountFilesystems()
    ctx.logger.debug("Unmount system paths")
    rc = ctx.bootloader.install()
    if rc:
        ctx.logger.debug("Bootloader installation failed!")
        return False
    else:
        ctx.logger.debug("Bootloader installed")
        return True


def cleanup():
    yali.util.run_batch("pisi", ["rm", "yali", "yali-theme-pardus", "yali-branding-pardus"])
