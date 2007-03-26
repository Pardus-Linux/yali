# -*- coding: utf-8 -*-
#
# Copyright (C) 2005, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# Please read the COPYING file.
#
# User management module for YALI.

import random
import shutil
import glob
import md5
import os

from string import ascii_letters, digits
from yali.constants import consts


# a set of User instances waiting...
# we'll add these users at the last step of the installation.
pending_users = set()

def reset_pending_users():
    global pending_users
    pending_users = set()



def iter_head_images():
    left, right, images = [], [], []

    g = glob.glob(consts.user_faces_dir + "/*.png")
    
    for e in g: left.append(e)
    
    for n in range(0, 5):
        right = []
        for i in range(0, len(g)/2 + 1):
            right.append(left.pop(random.randrange(len(g) - i)))
        left.reverse()
        left = right + left
    
    for p in left:
        images.append(p)

    while True:
        for image in images:
            yield image

head_images = iter_head_images()

class User:

    def __init__(self, username = ''):
        self.username = username
        self.groups = []
        self.realname = ''
        self.passwd = ''
        self.uid = -1

        # KDE AutoLogin Defaults
        self.autoLoginDefaults = {"AutoLoginAgain":"false",
                                  "AutoLoginDelay":"0",
                                  "AutoLoginLocked":"false"}
        
        self.shadow_path = os.path.join(consts.target_dir, 'etc/shadow')
        self.passwd_path = os.path.join(consts.target_dir, 'etc/passwd')
        self.group_path  = os.path.join(consts.target_dir, 'etc/group')

    def changePasswd(self, passwd):
        self.passwd = passwd
        shadow_content = open(self.shadow_path, 'r').readlines()
        shadow_file = open(self.shadow_path, 'w')

        for line in shadow_content:
            parts = line.split(':')
            if parts[0] == self.username:
                parts[1] = self.__getShadowed()
            shadow_file.write(":".join(parts))
        shadow_file.close()

    def addUser(self):
        passwd_template = "%(username)s:x:%(uid)d:100:%(realname)s:/home/%(username)s:/bin/bash\n"
        shadow_template = "%(username)s:%(shadowedpasswd)s:13094:0:99999:7:::\n"
        self.uid = self.getAvailableUid()
        
        open(self.passwd_path, 'a').write(passwd_template % \
                                            {'username': self.username, \
                                             'uid': self.uid, \
                                             'realname': self.realname})

        open(self.shadow_path, 'a').write(shadow_template % \
                                            {'username': self.username, \
                                             'shadowedpasswd': self.__getShadowed()})

        
        user_home_dir = os.path.join(consts.target_dir, 'home', self.username)

        if not os.path.exists(user_home_dir):
            os.system('cp -r %s %s' % (os.path.join(consts.target_dir, 'etc/skel'), user_home_dir))

        shutil.copy(head_images.next(), os.path.join(user_home_dir, '.face.icon'))
        os.chmod(os.path.join(user_home_dir, '.face.icon'), 0644)

        os.system('chown -R %d:%d %s ' % (self.uid, 100, user_home_dir))
        os.chmod(user_home_dir, 0711)

        self.__appendGroups()

    def getAvailableUid(self):
        j = map(lambda x: int(x[2]), [line.split(':') for line in open(self.passwd_path, 'r').readlines()])
        j.sort()

        for i in range(1000 + len(j), 1000, -1):
            if [x for x in j if i != int(x) if i == int(x) + 1]:
                return i
        return i-1

    def exists(self):
        if filter(lambda x: x == self.username, \
              map(lambda x: x[0], [line.split(':') for line in open(self.passwd_path, 'r').readlines()])):
            return True
        return False

    def usernameIsValid(self):
        valid = ascii_letters + '_' + digits
        name = self.username
        if len(name) == 0 or filter(lambda x: not x in valid, name) or not name[0] in ascii_letters:
            return False
        return True

    def realnameIsValid(self):
        not_allowed_chars = '\n' + ':'
        return '' == filter(lambda r: [x for x in not_allowed_chars if x == r], self.realname)

    # KDE AutoLogin
    def setAutoLogin(self,user,state=True):
        import ConfigParser
        section = 'X-:0-Core'
        confFile = os.path.join(consts.target_dir, 'etc/X11/kdm/kdmrc')
        kdmrc = ConfigParser.ConfigParser()
        kdmrc.optionxform = str
        kdmrc.readfp(open(confFile))
        for opt in self.autoLoginDefaults.keys():
            kdmrc.set(section,opt,self.autoLoginDefaults[opt])
        # Set State
        kdmrc.set(section,'AutoLoginEnable',str(state).lower())
        # Set User
        kdmrc.set(section,'AutoLoginUser',user)
        kdmrc.write(open(confFile,'w'))

    def __appendGroups(self):
        group_content = open(self.group_path, 'r').readlines()
        group_file = open(self.group_path, 'w')
        for line in group_content:
            line = line.strip('\n')
            group_info, group_users = line.split(':')[:-1], line.split(':')[-1:][0].split(',')
            for group in self.groups:
                if group_info[0] == group:
                    if group_users[0]: group_users.append(self.username)
                    else: group_users = [self.username]
            group_users, group_info = ','.join(group_users), ':'.join(group_info)
            group_file.write(group_info + ':' + group_users + '\n')
        group_file.close()

    def __getShadowed(self):
        passwd = self.passwd 
        des_salt = list('./0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz') 
        salt, magic = str(random.random())[-8:], '$1$'
    
        ctx = md5.new(passwd)
        ctx.update(magic)
        ctx.update(salt)
    
        ctx1 = md5.new(passwd)
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
            ctx1 = md5.new()
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


if __name__ == '__main__':
    pass

