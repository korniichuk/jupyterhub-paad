# Name: korniichuk/jupyterhub-paad
# Short Description: JupyterHub for the PAAD project
# Full Description: The korniichuk/jupyterhub Docker image for the PAAD project.
# Version: 0.1a1

FROM korniichuk/jupyterhub:0.1

MAINTAINER Ruslan Korniichuk <ruslan.korniichuk@gmail.com>

USER root

# Change the login.html file
COPY login.html /usr/local/share/jupyter/hub/templates/login.html 

# Add logos for footer
COPY logos/ig_logo_150x50px.png /usr/local/share/jupyter/hub/static/images/ig_logo_150x50px.png
COPY logos/us_plus_intibs_logo_81x50px.png /usr/local/share/jupyter/hub/static/images//us_plus_intibs_logo_81x50px.png
COPY logos/efrr_logo_204x50px.png /usr/local/share/jupyter/hub/static/images/efrr_logo_204x50px.png
