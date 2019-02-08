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
            logger = logging.getLogger('CEM-agent')
            logger.warn( 'Unknown option in the CEM config file. Ignoring it: ' + option)

class Config:
    # General parameters
    CEM_PATH = '/etc/cem-agent'
    CEM_API_REST_HOST = '0.0.0.0'
    CEM_API_REST_PORT = '9988'
    REST_API_SECRET = '6f0b387e-865c-4ac3-9ae1-6170b5fbcd79'
    
    # Logging parameters
    LOG_CONF_FILE = CEM_PATH + '/logging.cfg'
    LOG_LEVEL = 'WARNING'
    LOG_FILE = '/var/log/cem-agent/cem-agent.log'
    LOG_FILE_MAX_SIZE = 10485760
    


config = ConfigParser()
config.read([ Config.CEM_PATH + '/cem-agent.cfg'])


section_name = 'cem-agent'
if config.has_section(section_name):
    parse_options(config, section_name, Config)

section_name = 'log'
if config.has_section(section_name):
    parse_options(config, section_name, Config)