#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""JupyterHub auth for the PAAD project
Author: Ruslan Korniichuk <ruslan.korniichuk@gmail.com>

"""

import hashlib
import time
from subprocess import check_output, CalledProcessError

from bottle import post, request, run
from fabric.api import local

host = "" # Enter host <172.20.60.12>
port = "" # Enter port <9797>

@post("/api", method="POST")
def api():
    """"""

    def lock_check(USERNAME):
        """"""

        try:
            output = check_output("grep %s /etc/shadow" % USERNAME, shell=True)
        except CalledProcessError:
            pass
        index = output.find(":")
        character = output[index+1]
        if character == '!':
            return True
        else:
            return False

    ACTION = None
    USERNAME = None
    EMAIL = None
    PASSWD = None
    TIMESTAMP = None
    MD5 = None
    key = "JupyterHub"

    ACTION = request.forms.get("ACTION")
    USERNAME = request.forms.get("USERNAME")
    EMAIL = request.forms.get("EMAIL")
    PASSWD = request.forms.get("PASSWD")
    TIMESTAMP = request.forms.get("TIMESTAMP")
    MD5 = request.forms.get("MD5")

    # Verufy vars
    if ((ACTION == None) or (USERNAME == None) or (EMAIL == None) or
            (PASSWD  == None) or (TIMESTAMP == None) or (MD5 == None)):
        return "1"
    # Verify MD5
    text = key + str(USERNAME) + key + str(TIMESTAMP) + key + str(PASSWD) + \
           key + str(ACTION) + key + str(EMAIL) + key
    md5 = hashlib.md5(text.encode()).hexdigest()
    if MD5 != md5:
        return "1"
    # Verify TIMESTAMP
    timestamp = time.time()
    if timestamp - float(TIMESTAMP) > 5:
        return "1"
    # Verify ACTION value
    if ACTION not in ("ENABLE", "DISABLE"):
        return "1"
    if ACTION == "DISABLE":
        # Check user
        try:
            output = check_output("id %s" % USERNAME, shell=True)
        except CalledProcessError:
            pass # User doesn't exists
        else:
            if lock_check(USERNAME) == False:
                try:
                    # Disable user
                    local("passwd -l %s" % USERNAME)
                except Exception:
                    pass
            else:
                pass # User already lock
    elif ACTION == "ENABLE":
        # Check user
        try:
            output = check_output("id %s" % USERNAME, shell=True)
        except CalledProcessError:
            # Add user
            pass # TODO
    return "0"

run(host=host, port=port)
