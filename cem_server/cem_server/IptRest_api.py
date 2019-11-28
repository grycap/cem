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
import json
from cem_server.REST_api import REST

class IptRest():

    LOG = logging.getLogger('IPTrest')

    GET_REDIR_URL = '/'
    CREATE_REDIR_URL = '/<SOURCE_PORT>/<DEST_IP>/<DEST_PORT>'
    DELETE_REDIR_1_URL = '/<SOURCE_PORT>'
    DELETE_REDIR_2_URL = '/<DEST_IP>/<DEST_PORT>'

    def __init__(self, host, port, protocol='http'):
        self.url = host + ':' + str(port) 
        self.protocol = protocol
        

    def create_redirection (self, dest_ip, dest_port, source_port=None):
        if source_port == None:
            source_port = '0'
        request_url = self.protocol + '://' + self.url + self.CREATE_REDIR_URL.replace('<SOURCE_PORT>', source_port).replace('<DEST_IP>', dest_ip).replace('<DEST_PORT>', dest_port)
        try:
            response = REST(self.LOG).do_request( method='PUT', url=request_url)
            if response.status_code == 200:
                return response.json()
            else:
                self.LOG.error('Something wrong creating the redirection: '+response.text)
        except (ValueError):
            self.LOG.error('Cannot connect with IPTRest')  
        return None


    def delete_redirection (self, source_port=None, dest_ip=None, dest_port=None):
        if (not source_port and not dest_ip and not dest_port):
            self.LOG.error('Invalid parameters for delete_dir')
            return None

        request_url = self.protocol + '://' + self.url + self.DELETE_REDIR_1_URL.replace('<SOURCE_PORT>', source_port)

        if not source_port and (dest_ip and dest_port):
            request_url = self.protocol + '://' + self.url + self.DELETE_REDIR_2_URL.replace('<DEST_IP>', dest_ip).replace('<DEST_PORT>', dest_port)

        try:
            response = REST(self.LOG).do_request( method='DELETE', url=request_url)
            if response.status_code == 200:
                return response.json()
            else:
                self.LOG.error('Something wrong removing the redirection: '+response.text)
        except (ValueError):
            self.LOG.error('Cannot connect with IPTRest')  
        return None

    def get_redirections(self):
        request_url = self.protocol + '://' + self.url + self.GET_REDIR_URL
        try:
            response = REST(self.LOG).do_request( method='GET', url=request_url)
            if response.status_code == 200:
                return response.json()
            else:
                self.LOG.error('Something wrong getting redirections: '+response.text)
        except (ValueError):
            self.LOG.error('Cannot connect with IPTRest')  
        return None