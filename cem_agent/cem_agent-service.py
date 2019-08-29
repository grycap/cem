#! /usr/bin/env python
#
# CEM agent - Cluster Elasticity Manager
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
import json

from cem_agent.config import Config
from cem_agent import __version__ as cem_version
from cem_agent.cem_server_api import cem_server_api
from cem_agent.RepeatedTimer import RepeatedTimer
from cem_agent.plugins.check_commands import check_commands

LOGGER = logging.getLogger('CEM-agent')
CONFIG = Config()
CEM_MAIN_LOOP = None
vmID = None
CEM_SERVER_REST_API = None

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
        # First look at /etc/im/logging.conf file
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

        log = logging.getLogger('CEM-agent')
        log.setLevel(log_level)
        log.propagate = 0
        log.addHandler(fileh)

        log = logging.getLogger('Plugin')
        log.setLevel(log_level)
        log.propagate = 0
        log.addHandler(fileh)

    # Add the filter to add extra fields
    try:
        filt = ExtraInfoFilter()
        log = logging.getLogger('CEM-agent')
        log.addFilter(filt)
    except Exception as ex:
        print(ex)

        #sys.exit('Cannot read the logging configuration in '+ Config.LOG_CONF_FILE)

def cem_main():
    global CONFIG, LOGGER, vmID, CEM_SERVER_REST_API
    
    cem_server_url = CONFIG.CEM_SERVER_IP + ':' + CONFIG.CEM_SERVER_PORT
    CEM_SERVER_REST_API = cem_server_api(LOGGER, cem_server_url, auth_token=CONFIG.REST_API_SECRET)

    # Get my vmID
    if not vmID:
        vmID = CEM_SERVER_REST_API.register()
        LOGGER.info('Cem agent %s registered '%(vmID))
    
    if vmID:
        # Obtain plugin configuration
        plugins_configuration = CEM_SERVER_REST_API.get_plugins_configuration(vmID)

        if ('plugins' not in plugins_configuration) or ('users_list' not in plugins_configuration) or ('assigned_users' not in plugins_configuration):
            LOGGER.error('plugins, assigned_users or users_list not in plugins_configuration')
            return False
            
        LOGGER.info('Plugins configuration obtained successfully')
        LOGGER.debug(json.dumps(plugins_configuration))

        plugins_results = {}

        # Execute all plugins
        for p_name, p_config in plugins_configuration['plugins'].items():
            # Check if plugin exists and it is allowed 
            if p_name not in CONFIG.ALLOWED_PLUGINS:
                LOGGER.error('Plugin "%s" is not allowed or is not exists')
                plugins_results[p_name] = {}
                continue
            try:
                # Create plugin
                p = eval(p_name)(logging.getLogger('Plugin'), p_name, p_config)

                # Execute plugin
                plugins_results[p_name] = p.do_monitoring(plugins_configuration['users_list'], plugins_configuration['assigned_users'])
                LOGGER.debug('Plugin %s successfully executed' %(p_name))
            except:
                LOGGER.error('Something wrong during the execution of the plugin %s'%(p_name))
                plugins_results[p_name] = {}
        
        # Send plugins_results to CEM Server 
        CEM_SERVER_REST_API.send_monitoring_info(vmID, plugins_results)
        LOGGER.info('Monitoring infomation send it successfully to CEM Server')
        LOGGER.debug( json.dumps(plugins_results) )


def start_daemon():
    global CEM_MAIN_LOOP, CONFIG
    LOGGER.info( '------------- Starting Cluster Elasticity Manager - Agent %s -------------' % cem_version)
    CEM_MAIN_LOOP = RepeatedTimer(CONFIG.MONITORING_PERIOD, cem_main)
    CEM_MAIN_LOOP.start()
    CEM_MAIN_LOOP.wait_until_cancel()

def stop_daemon():
    global CEM_MAIN_LOOP, CEM_SERVER_REST_API
    CEM_MAIN_LOOP.stop()
    CEM_SERVER_REST_API.deregister()
    LOGGER.info('Cem agent %s deregistered '%(vmID))
    LOGGER.info( '------------- Cluster Elasticity Manager - Agent stopped -------------' )


def signal_int_handler(signal, frame):
    """
    Callback function to catch the system signals
    """
    stop_daemon()

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_int_handler)
    config_logger()
    start_daemon()
