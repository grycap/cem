#!/usr/bin/python

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

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from cem_agent import __version__ as version
from cem_agent import __author__ as author


setup(name='cem_agent',
    version=version,
    description='CEM agent - Cluster Elasticity Manager',
    author=author,
    author_email='serlohu@upv.es',
    url='https://github.com/grycap/cem',
    packages = [ 'cem_agent' ],
    data_files = [
        ('/etc/cem-agent', [ 
            'etc/cem-agent.cfg',
            'etc/logging.cfg'
        ]),
        ('/etc/init.d', [
            'service/cem-agent'
        ]),
        ( '/usr/bin', [
            'cem_agent-service.py'
        ]),
        ( '/var/log/cem-agent', [])
    ],
    scripts=['cem_agent-service.py', 'service/cem-agent'],
    install_requires = [ "bottle", "cherrypy"]
)