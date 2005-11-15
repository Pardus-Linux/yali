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
import crypt
import glob
import os

from yali.constants import consts

Shadow = lambda x: crypt.crypt(x, str(random.random())[-2:])


class User:

    def __init__(self, username = ''):
        self.username = username
        self.groups = []
        self.realname = ''
        self.home_dir = ''
        self.passwd = ''
        self.uid = -1

        self.shadow_path = os.path.join(consts.target_dir, "etc/shadow")
        self.passwd_path = os.path.join(consts.target_dir, "etc/passwd")
        self.group_path  = os.path.join(consts.target_dir, "etc/group")

    def changePasswd(self, passwd):
        shadow_content = open(self.shadow_path, 'r').readlines()
        shadow_file = open(self.shadow_path, 'w')

        for line in shadow_content:
            parts = line.split(':')
            if parts[0] == self.username:
                parts[1] = Shadow(passwd)
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
                                             'shadowedpasswd': Shadow(self.passwd)})

        
        user_home_dir = os.path.join(consts.target_dir, 'home', self.username)
        
        if not os.path.exists(user_home_dir):
            os.makedirs(user_home_dir, mode=511)

        for f in glob.glob(os.path.join(consts.target_dir, 'etc/skel/.*')):
            shutil.copy(f, user_home_dir)
        
        os.chown(user_home_dir, self.uid, 100)
        for root, dirs, files in os.walk(user_home_dir):
            for file in files:
                os.chown(os.path.join(root, file), self.uid, 100)
            for dir in dirs:
                os.chown(os.path.join(root, dir), self.uid, 100)

        self.__appendGroups()

    def getAvailableUid(self):
        j = map(lambda x: int(x[2]), [line.split(':') for line in open(self.passwd_path, 'r').readlines()])
        j.sort()

        for i in range(1000 + len(j), 1000, -1):
            if [int(x)+1 for x in j if i != int(x) if i == int(x) + 1]:
                return i
        return i-1

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



if __name__ == '__main__':
    pass

