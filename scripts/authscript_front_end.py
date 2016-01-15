#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""JupyterHub front end auth script for the PAAD project
Author: Ruslan Korniichuk <ruslan.korniichuk@gmail.com>

"""

import hashlib
import time

from urllib.parse import urlencode
from urllib.request import urlopen

key = "" # Enter secret key
url = "" # Enter API URL <172.20.60.12:9797/api>

ACTION = "" # Choise action: ENABLE |DISABLE
USERNAME = "" # Enter PAAD USERNAME
EMAIL = "" # Enter PAAD user EMAIL
PASSWD = "" # Enter PAAD user PASSWD

def request(url, params={}, timeout=5):
    """ GET/POST method"""

    if params:
        params = urlencode(params)
        params_bytes = params.encode()
        html = urlopen(url, params_bytes, timeout)
    else:
        html = urlopen(url)
    return html.read()

TIMESTAMP = time.time()
text = key + str(USERNAME) + key + str(TIMESTAMP) + key + str(PASSWD) + \
       key + str(ACTION) + key + str(EMAIL) + key
MD5 = hashlib.md5(text.encode()).hexdigest()
params = {"ACTION": ACTION, "USERNAME": USERNAME, "EMAIL": EMAIL,
          "PASSWD": PASSWD, "TIMESTAMP": TIMESTAMP, "MD5": MD5}
request(url, params)
