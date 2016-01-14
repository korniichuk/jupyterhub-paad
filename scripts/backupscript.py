#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""JupyterHub backup for the PAAD project
Author: Ruslan Korniichuk <ruslan.korniichuk@gmail.com>

"""

import time
from datetime import datetime, timedelta
from subprocess import check_output, CalledProcessError
from threading import Timer

from fabric.api import local

username = "" # Enter Docker Hub USERNAME <paad>
password = "" # Enter Docker Hub user PASSWORD
email = "" # Enter Docker Hub user EMAIL <paad.jupyterhub@gmail.com>
docker_hub_repo_name = "" # Enter Docker Hub repository name <jupyterhub>
docker_container_name = "" # Enter Docker container name <all_jupyterhub_1>

def backup():
    """Backup from running container to Docker Hub repository"""

    def login():
        """Automatic Docker login"""
        
        try:
            local("docker login --username=%s --password=%s --email=%s" %
                    (username, password, email))
        except Exception:
            pass

    docker_hub_repo = username + '/' + docker_hub_repo_name            
    # Check Docker image id
    try:
        image_id = check_output("docker images -q %s" % docker_hub_repo,
                                shell=True)
        image_id = image_id.strip()
    except CalledProcessError:
        image_id = None
    # Docker commit
    try:
        local("docker commit %s %s" % (docker_container_name, docker_hub_repo))
    except Exception:
        pass
    # Delete previous Docker image
    if image_id != None:
        try:
            local("docker rmi %s" % image_id)
        except Exception:
            pass
    # Docker push
    try:
        local("docker push %s" % docker_hub_repo)
    except Exception:
        login()

while True:
    date_time_current = datetime.now()
    date_time_action = date_time_current + timedelta(hours=12, minutes=0,
                                                     seconds=0, microseconds=0)
    delta_date_time = date_time_action - date_time_current
    seconds_delta_date_time = delta_date_time.seconds
    t = Timer(seconds_delta_date_time, backup)
    t.start()
    time.sleep(seconds_delta_date_time)
