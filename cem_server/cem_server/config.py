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
import logging

try:
    from ConfigParser import ConfigParser
except ImportError:
    from configparser import ConfigParser

def parse_options(config, section_name, config_class):
    options = config.options(section_name)
    for option in options:
        option = option.upper()
        if option in config_class.__dict__ and not option.startswith("__"):
            if isinstance(config_class.__dict__[option], bool):
                setattr(config_class, option, config.getboolean(section_name, option))
            elif isinstance(config_class.__dict__[option], int):
                setattr(config_class, option, config.getint(section_name, option))
            elif isinstance(config_class.__dict__[option], list):
                str_value = config.get(section_name, option)
                setattr(config_class, option, str_value.split(','))
            else:
                setattr(config_class, option, config.get(section_name, option))
        else:
            logger = logging.getLogger('CEM')
            logger.warn( 'Unknown option in the CEM config file. Ignoring it: ' + option)

class Config:
    # General parameters
    CEM_MAX_SLOTS_NODE = 3
    CEM_PATH = '/etc/cem'
    CEM_API_REST_HOST = '0.0.0.0'
    CEM_API_REST_PORT = '10000'
    CEM_MONITORING_PERIOD = 30
    CEM_MANAGER_PERIOD = 30
    MIN_RESOURCES_STOPPED = 0
    MIN_RESOURCES_IDLE = 0
    ALLOW_SLOTS_INACTIVE_TIME_SECONDS = 1200
    RESOURCE_IDLE_TIME_SECONDS = 1800
    PUBLIC_IP = 'localhost'

    REST_API_SECRET = '6f0b387e-865c-4ac3-9ae1-6170b5fbcd79'
    RDP_DEST_PORT = '3389'

    # IM parameters
    IM_CREDENTIALS = CEM_PATH + '/auth.dat'
    IM_REST_ENDPOINT = 'https://....'
    IM_INFRASTRUCTURE_ID = 'fake_id'
    WN_RADL_FILE = '/etc/cem/wn.radl'

    # Database parameters
    DB = CEM_PATH + '/cem.db'
    
    # Logging parameters
    LOG_CONF_FILE = CEM_PATH + '/logging.cfg'
    LOG_LEVEL = 'WARNING'
    LOG_FILE = '/var/log/cem/cem.log'
    LOG_FILE_MAX_SIZE = 10485760
    

    # Cem_agent
    REST_AGENT_API_SECRET = '6f0b387e-865c-4ac3-9ae1-6170b5fbcd79'
    CEM_AGENT_PORT = '10000'
    
    # IPT Rest
    IPTREST_HOST = 'localhost'
    IPTREST_PORT = '8080'
    IPTREST_RANGE_SOURCE_PORTS = 9000, 9050
  
config = ConfigParser()
config.read([ Config.CEM_PATH + '/cem.cfg'])


section_name = 'cem'
if config.has_section(section_name):
    parse_options(config, section_name, Config)

section_name = 'cem_agent'
if config.has_section(section_name):
    parse_options(config, section_name, Config)

section_name = 'log'
if config.has_section(section_name):
    parse_options(config, section_name, Config)