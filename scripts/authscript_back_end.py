#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""JupyterHub back end auth script for the PAAD project
Author: Ruslan Korniichuk <ruslan.korniichuk@gmail.com>
Version: 0.1a2

"""

import hashlib
import re
import time
from crypt import crypt
from logging import basicConfig, debug, DEBUG, error, info
from subprocess import check_output, CalledProcessError

from bottle import post, request, run
from fabric.api import local
from netifaces import AF_INET, ifaddresses

host = "" # Enter host IP or "" value for eth0 address
port = "" # Enter port <9797>
key = "" # Enter secret key
min_days = "99999" # Minimum number of days before user password change
log_abs_path = "/tmp/authscript_back_end.log" # Absolute path to log file

basicConfig(filename=log_abs_path, level=DEBUG,
            format='%(asctime)s %(levelname)s %(message)s')

@post("/api", method="POST")
def api():
    """Auth API"""

    def lock_check(USERNAME):
        """Checking user lock status
        Input: USERNAME -- username.
        Output:
          True -- user lock,
          False -- user unlock,
          None -- lock_check() error.

        """

        try:
            outputs = check_output("grep %s: /etc/shadow" %
                    USERNAME, shell=True)
            outputs = outputs.split("\n")
            for output in outputs:
                if output.startswith("%s:" % USERNAME):
                    break
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

    client_ip = request.environ.get('REMOTE_ADDR')
    empty_passwd = crypt("", key)

    # Verify vars
    if ((ACTION == None) or (USERNAME == None) or (EMAIL == None) or
            (PASSWD  == None) or (TIMESTAMP == None) or (MD5 == None)):
        info("%s 1;API takes exactly 6 arguments" % client_ip)
        return "1;API takes exactly 6 arguments"
    debug("%s vars verified" % client_ip)
    # Verify MD5
    text = key + str(USERNAME) + key + str(TIMESTAMP) + key + str(PASSWD) + \
           key + str(ACTION) + key + str(EMAIL) + key
    md5 = hashlib.md5(text.encode()).hexdigest()
    if MD5 != md5:
        info("%s 1;MD5 is incorrect" % client_ip)
        return "1;MD5 is incorrect"
    debug("%s MD5 verified" % client_ip)
    # Verify TIMESTAMP
    timestamp = time.time()
    try:
        TIMESTAMP = float(TIMESTAMP)
    except ValueError:
        error("%s 1;TIMESTAMP value error" % client_ip)
        return "1;TIMESTAMP value error"
    if timestamp - TIMESTAMP > 5:
        info("%s 1;TIMESTAMP is incorrect" % client_ip)
        return "1;TIMESTAMP is incorrect"
    debug("%s TIMESTAMP verified" % client_ip)
    # Verify ACTION value
    if ACTION == "":
        info("%s 1;ACTION is required" % client_ip)
        return "1;ACTION is required"
    elif ACTION not in ("ENABLE", "DISABLE"):
        info("%s 1;ACTION is incorrect" % client_ip)
        return "1;ACTION is incorrect"
    debug("%s ACTION value verified" % client_ip)
    # Verify USERNAME value
    if USERNAME == "":
        info("%s 1;USERNAME is required" % client_ip)
        return "1;USERNAME is required"
    elif re.search("[^a-zA-Z0-0._-]", USERNAME):
        info("%s 1;USERNAME is incorrect" % client_ip)
        return "1;USERNAME is incorrect"
    debug("%s USERNAME value verified" % client_ip)
    # DISABLE
    if ACTION == "DISABLE":
        debug("%s start DISABLE" % client_ip)
        # Check user
        try:
            output = check_output("id %s" % USERNAME, shell=True)
        except CalledProcessError:
            info("%s '%s' user doesn't exists" % (client_ip, USERNAME))
        else:
            debug("%s user checked" % client_ip)
            lock_status = lock_check(USERNAME)
            if lock_status == False:
                # Disable user
                try:
                    local("passwd -l %s" % USERNAME)
                except BaseException:
                    error("%s 1;disable user error" % client_ip)
                    return "1;disable user error"
                else:
                    info("%s '%s' user disabled" % (client_ip, USERNAME))
            elif lock_status == True:
                info("%s '%s' user already lock" % (client_ip, USERNAME))
            elif lock_status == None:
                error("%s 1;lock_check() error" % client_ip)
                return "1;lock_check() error"
    # ENABLE
    elif ACTION == "ENABLE":
        debug("%s start ENABLE" % client_ip)
        # Check user
        try:
            output = check_output("id %s" % USERNAME, shell=True)
        except CalledProcessError:
            if EMAIL != "":
                if (PASSWD != "") and (PASSWD != empty_passwd):
                    # Add user
                    try:
                        local("useradd -c\"%s,%s\" -m -s /bin/bash %s" %
                                (USERNAME, EMAIL, USERNAME))
                    except BaseException:
                        error("%s 1;add user error" % client_ip)
                        return "1;add user error"
                    else:
                        info("%s '%s' user added" % (client_ip, USERNAME))
                        # Set user password
                        try:
                            local("echo \"%s:%s\" | chpasswd -e" %
                                    (USERNAME, PASSWD))
                            local("passwd -n %s %s" %
                                    (min_days, USERNAME))
                        except BaseException:
                            error("%s 1;set user password error" % client_ip)
                            return "1;set user password error"
                        else:
                            info("%s '%s' user password set" %
                                    (client_ip, USERNAME))
                else:
                    info("%s 1;PASSWD is required" % client_ip)
                    return "1;PASSWD is required"
            else:
               info("%s 1;EMAIL is required" % client_ip)
               return "1;EMAIL is required"
        else:
            debug("%s user checked" % client_ip)
            lock_status = lock_check(USERNAME)
            if lock_status == True:
                # Enable user
                try:
                    local("passwd -u %s" % USERNAME)
                except BaseException:
                    error("%s 1;enable user error" % client_ip)
                    return "1;enable user error"
                else:
                    info("%s '%s' user enabled" % (client_ip, USERNAME))
            elif lock_status == False:
                info("%s '%s' user already unlock" % (client_ip, USERNAME))
            elif lock_status == None:
                error("%s 1;lock_check() error" % client_ip)
                return "1;lock_check() error"
            # Check user e-mail
            try:
                outputs = check_output("grep %s: /etc/passwd" %
                        USERNAME, shell=True)
            except CalledProcessError:
                error("%s 1;check user e-mail error" % client_ip)
                return "1;check user e-mail error"
            else:
                outputs = outputs.split("\n")
                for output in outputs:
                    if output.startswith("%s:" % USERNAME):
                        break
                gecos = output.split(':')[4]
                email = gecos.split(',')[1]
                debug("%s user e-mail got" % client_ip)
                if (EMAIL != "") and (email != EMAIL):
                    # Change user e-mail
                    try:
                        local("chfn -r \"%s\" %s" % (EMAIL, USERNAME))
                    except BaseException:
                        error("%s 1;change user e-mail error" % client_ip)
                        return "1;change user e-mail error"
                    else:
                        info("%s '%s' user e-mail changed" %
                                (client_ip, USERNAME))
            # Check user password
            try:
                outputs = check_output("grep %s: /etc/shadow" %
                        USERNAME, shell=True)
            except CalledProcessError:
                error("%s 1;check user password error" % client_ip)
                return "1;check user password error"
            else:
                outputs = outputs.split("\n")
                for output in outputs:
                    if output.startswith("%s:" % USERNAME):
                        break
                passwd = output.split(':')[1]
                debug("%s user password got" % client_ip)
                if ((PASSWD != "") and (PASSWD != empty_passwd) and
                        (passwd != PASSWD)):
                    # Change user password
                    try:
                        local("echo \"%s:%s\" | chpasswd -e" %
                                (USERNAME, PASSWD))
                    except BaseException:
                        error("%s 1;change user password error" % client_ip)
                        return "1;change user password error"
                    else:
                        info("%s '%s' user password changed" %
                                (client_ip, USERNAME))
    return "0"

if host == "":
    host = ifaddresses('eth0')[AF_INET][0]["addr"]
run(host=host, port=port)
