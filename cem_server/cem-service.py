#! /usr/bin/env python3
#
# CEM - Cluster Elasticity Manager 
# Copyright (C) 2011 - GRyCAP - Universitat Politecnica de Valencia
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import logging
import logging.handlers
import logging.config
import sys
import threading
import signal
import time
import queue

import cem_server.REST_Server as REST_Server
from cem_server.config import Config
from cem_server.cem import ClusterElasticityManager 
from cem_server import __version__ as cem_version
from cem_server.db import DataBase 

LOGGER = logging.getLogger('CEM')
CEM = None
REST_SERVER = None
CONFIG = Config()
REQUEST_QUEUE = queue.Queue()
DB = DataBase(CONFIG.DB)

class ExtraInfoFilter(logging.Filter):
    """
    This is a filter which injects extra attributes into the log.
      * hostname
    """
    def filter(self, record):
        import socket
        record.hostname = socket.gethostname()
        return True

def config_logger():
    try:
        # First look at /etc/im/logging.cfg file
        logging.config.fileConfig(Config.LOG_CONF_FILE)
    except Exception as ex:
        print(ex)
        log_dir = os.path.dirname(Config.LOG_FILE)
        if not os.path.isdir(log_dir):
            os.makedirs(log_dir)

        fileh = logging.handlers.RotatingFileHandler(filename=Config.LOG_FILE, maxBytes=Config.LOG_FILE_MAX_SIZE, backupCount=3)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fileh.setFormatter(formatter)

        if Config.LOG_LEVEL == "DEBUG":
            log_level = logging.DEBUG
        elif Config.LOG_LEVEL == "INFO":
            log_level = logging.INFO
        elif Config.LOG_LEVEL in ["WARN", "WARNING"]:
            log_level = logging.WARN
        elif Config.LOG_LEVEL == "ERROR":
            log_level = logging.ERROR
        elif Config.LOG_LEVEL in ["FATAL", "CRITICAL"]:
            log_level = logging.FATAL
        else:
            log_level = logging.WARN

        logging.RootLogger.propagate = 0
        logging.root.setLevel(logging.ERROR)

        log = logging.getLogger('DB')
        log.setLevel(log_level)
        log.propagate = 0
        log.addHandler(fileh)

        log = logging.getLogger('RESTServer')
        log.setLevel(log_level)
        log.propagate = 0
        log.addHandler(fileh)

        log = logging.getLogger('CEM')
        log.setLevel(log_level)
        log.propagate = 0
        log.addHandler(fileh)

        log = logging.getLogger('IM')
        log.setLevel(log_level)
        log.propagate = 0
        log.addHandler(fileh)

        log = logging.getLogger('IPTrest')
        log.setLevel(log_level)
        log.propagate = 0
        log.addHandler(fileh)

        

    # Add the filter to add extra fields
    try:
        filt = ExtraInfoFilter()
        log = logging.getLogger('DB')
        log.addFilter(filt)
        log = logging.getLogger('RESTServer')
        log.addFilter(filt)
        log = logging.getLogger('CEM')
        log.addFilter(filt)
        log = logging.getLogger('IM')
        log.addFilter(filt)
        log = logging.getLogger('IPTrest')
        log.addFilter(filt)

        
    except Exception as ex:
        print(ex)

        #sys.exit('Cannot read the logging configuration in '+ Config.LOG_CONF_FILE)

def start_daemon():
    global CEM, REQUEST_QUEUE, DB
    LOGGER.info( '------------- Starting Cluster Elasticity Manager %s -------------' % cem_version)

    CEM = ClusterElasticityManager( CONFIG, REQUEST_QUEUE, DB )
    
    bottle_thr = REST_Server.run_in_thread(host=CONFIG.CEM_API_REST_HOST, port=CONFIG.CEM_API_REST_PORT, request_queue=REQUEST_QUEUE, db=DB, rest_api_secret=CONFIG.REST_API_SECRET, cem=CEM)
    
    CEM.run_in_thread()

    while bottle_thr.is_alive() and CEM.threads[0].is_alive() and CEM.threads[1].is_alive() and CEM.threads[2].is_alive():
        pass

    

def stop_daemon( ):
    global CEM
    REST_Server.stop()
    CEM.stop()
    while CEM.threads[0].is_alive() or CEM.threads[1].is_alive() or CEM.threads[2].is_alive():
        pass
    LOGGER.info( '------------- Cluster Elasticity Manager stopped -------------' )

    

def signal_int_handler(signal, frame):
    """
    Callback function to catch the system signals
    """
    stop_daemon()


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_int_handler)
    config_logger()
    start_daemon()