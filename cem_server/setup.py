#!/usr/bin/python

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

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from cem_server import __version__ as version
from cem_server import __author__ as author


setup(name='cem',
    version=version,
    description='CEM - Cluster Elasticity Manager',
    author=author,
    author_email='serlohu@upv.es',
    url='https://github.com/grycap/cem',
    packages = [ 'cem_server', 'cem_server/plugins' ],
    platforms=["any"],
    data_files = [
        ('/etc/cem', [ 
            'etc/cem.cfg',
            'etc/logging.cfg'
        ]),
        ('/etc/init.d', [
            'service/cem'
        ]),
        ( '/usr/bin', [
            'cem-service.py'
        ]),
        ( '/var/log/cem', [

        ])
    ],
    scripts=['cem-service.py', 'service/cem'],
    install_requires = [ "bottle", "requests" , "cherrypy", "enum34"]
)