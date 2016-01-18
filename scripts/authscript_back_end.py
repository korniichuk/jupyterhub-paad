#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""JupyterHub back end auth script for the PAAD project
Author: Ruslan Korniichuk <ruslan.korniichuk@gmail.com>
Version: 0.1a1

"""

import hashlib
import re
import time
from logging import basicConfig, DEBUG, error, info
from subprocess import check_output, CalledProcessError

from bottle import post, request, run
from fabric.api import local

host = "" # Enter host <172.20.60.12>
port = "" # Enter port <9797>
key = "" # Enter secret key
min_days = "99999" # Minimum number of days before user password change
log_abs_path = "/tmp/authscript_back_end.log" # Absolute path to log file

basicConfig(filename=log_abs_path, level=DEBUG, format='%(asctime)s %(levelname)s %(message)s')

@post("/api", method="POST")
def api():
    """"""

    def lock_check(USERNAME):
        """"""

        try:
            output = check_output("grep %s /etc/shadow" % USERNAME, shell=True)
            index = output.find(":")
            character = output[index+1]
            if character == '!':
                return True
            else:
                return False
        except CalledProcessError:
            return None

    ACTION = None
    USERNAME = None
    EMAIL = None
    PASSWD = None
    TIMESTAMP = None
    MD5 = None

    ACTION = request.forms.get("ACTION")
    USERNAME = request.forms.get("USERNAME")
    EMAIL = request.forms.get("EMAIL")
    PASSWD = request.forms.get("PASSWD")
    TIMESTAMP = request.forms.get("TIMESTAMP")
    MD5 = request.forms.get("MD5")

    clien_ip = request.environ.get('REMOTE_ADDR')

    # Verify vars
    if ((ACTION == None) or (USERNAME == None) or (EMAIL == None) or
            (PASSWD  == None) or (TIMESTAMP == None) or (MD5 == None)):
        info("%s 1;API takes exactly 6 arguments" % clien_ip)
        return "1;API takes exactly 6 arguments"
    # Verify MD5
    text = key + str(USERNAME) + key + str(TIMESTAMP) + key + str(PASSWD) + \
           key + str(ACTION) + key + str(EMAIL) + key
    md5 = hashlib.md5(text.encode()).hexdigest()
    if MD5 != md5:
        info("%s 1;MD5 is incorrect" % clien_ip)
        return "1;MD5 is incorrect"
    # Verify TIMESTAMP
    timestamp = time.time()
    try:
        TIMESTAMP = float(TIMESTAMP)
    except ValueError:
        error("%s 1;TIMESTAMP value error" % clien_ip)
        return "1;TIMESTAMP value error"
    if timestamp - TIMESTAMP > 5:
        info("%s 1;TIMESTAMP is incorrect" % clien_ip)
        return "1;TIMESTAMP is incorrect"
    # Verify ACTION value
    if ACTION == "":
        info("%s 1;ACTIONE is required" % clien_ip)
        return "1;ACTIONE is required"
    elif ACTION not in ("ENABLE", "DISABLE"):
        info("%s 1;ACTION is incorrect" % clien_ip)
        return "1;ACTION is incorrect"
    # Verify USERNAME value
    if USERNAME == "":
        info("%s 1;USERNAME is required" % clien_ip)
        return "1;USERNAME is required"
    elif re.search("[^a-zA-Z0-0._-]", USERNAME):
        info("%s 1;USERNAME is incorrect" % clien_ip)
        return "1;USERNAME is incorrect"
    if ACTION == "DISABLE":
        # Check user
        try:
            output = check_output("id %s" % USERNAME, shell=True)
        except CalledProcessError:
            pass # User doesn't exists
        else:
            lock_status = lock_check(USERNAME)
            if lock_status == False:
                # Disable user
                try:
                    local("passwd -l %s" % USERNAME)
                except BaseException:
                    error("%s 1;disable user error" % clien_ip)
                    return "1;disable user error"
            elif lock_status == True:
                pass # User already lock
            elif lock_status == None:
                error("%s 1;lock_check() error" % clien_ip)
                return "1;lock_check() error"
    elif ACTION == "ENABLE":
        # Check user
        try:
            output = check_output("id %s" % USERNAME, shell=True)
        except CalledProcessError:
            if EMAIL != "":
                if (PASSWD != "") and (PASSWD != "Ju61Hl0o747VY"):
                    # Add user
                    try:
                        local("useradd -c\"%s,%s\" -m -s /bin/bash %s" %
                                (USERNAME, EMAIL, USERNAME))
                        # Set user password
                        try:
                            local("echo \"%s:%s\" | chpasswd -e" %
                                    (USERNAME, PASSWD))
                            local("passwd -n %s %s" %
                                    (min_days, USERNAME))
                        except BaseException:
                            error("%s 1;set user password error" % clien_ip)
                            return "1;set user password error"
                    except BaseException:
                        error("%s 1;add user error" % clien_ip)
                        return "1;add user error"
                else:
                    info("%s 1;PASSWD is required" % clien_ip)
                    return "1;PASSWD is required"
            else:
               info("%s 1;EMAIL is required" % clien_ip)
               return "1;EMAIL is required"
        else:
            lock_status = lock_check(USERNAME)
            if lock_status == True:
                # Enable user
                try:
                    local("passwd -u %s" % USERNAME)
                except BaseException:
                    error("%s 1;enable user error" % clien_ip)
                    return "1;enable user error"
            elif lock_status == False:
                pass # User already unlock
            elif lock_status == None:
                error("%s 1;lock_check() error" % clien_ip)
                return "1;lock_check() error"
            # Check user e-mail
            try:
                output = check_output("grep %s /etc/passwd" %
                        USERNAME, shell=True)
            except CalledProcessError:
                error("%s 1;check user e-mail error" % clien_ip)
                return "1;check user e-mail error"
            else:
                gecos = output.split(':')[4]
                email = gecos.split(',')[1]
                if (EMAIL != "") and (email != EMAIL):
                    # Change user e-mail
                    try:
                        local("chfn -r \"%s\" %s" % (EMAIL, USERNAME))
                    except BaseException:
                        error("%s 1;change user e-mail error" % clien_ip)
                        return "1;change user e-mail error"
            # Check user password
            try:
                output = check_output("grep %s /etc/shadow" %
                        USERNAME, shell=True)
            except CalledProcessError:
                error("%s 1;check user password error" % clien_ip)
                return "1;check user password error"
            else:
                passwd = output.split(':')[1]
                if ((PASSWD != "") and (PASSWD != "Ju61Hl0o747VY") and
                        (passwd != PASSWD)):
                    # Change user password
                    try:
                        local("echo \"%s:%s\" | chpasswd -e" %
                                (USERNAME, PASSWD))
                    except BaseException:
                        error("%s 1;change user password error" % clien_ip)
                        return "1;change user password error"
    return "0"

run(host=host, port=port)
