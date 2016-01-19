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

docker_hub_username = "" # Enter Docker Hub USERNAME <paad>
docker_hub_password = "" # Enter Docker Hub user PASSWORD
docker_hub_email = "" # Enter Docker Hub user EMAIL <paad.jupyterhub@gmail.com>
docker_hub_repo_name = "" # Enter Docker Hub repository name <jupyterhub>
docker_container_name = "" # Enter Docker container name <all_jupyterhub_1>

def backup():
    """Backup from running container to Docker Hub repository"""

    docker_hub_repo = docker_hub_username + '/' + docker_hub_repo_name
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
        pass

def login():
    """Automatic Docker login"""

    try:
        local("docker login --username=%s --password=%s --email=%s" %
                (docker_hub_username, docker_hub_password, docker_hub_email))
    except Exception:
        pass

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
