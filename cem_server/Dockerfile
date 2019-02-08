FROM ubuntu:18.04
MAINTAINER serlohu@upv.es
LABEL version = '0.0.1'

RUN apt-get update && apt-get install --no-install-recommends -y python-pip sqlite3 iputils

RUN pip install setuptools

#&&  pip install bottle cherrypy requests

EXPOSE 8080
