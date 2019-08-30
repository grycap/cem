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

import json
from cem_agent.REST import REST 
import time

class cem_server_api():

    __REGISTER_URL = '/cem_agent/register'
    __DEREGISTER_URL = '/cem_agent/deregister'
    __MONITORING_RESULT_URL = '/cem_agent/monitoring/<vmID>'
    __PLUGIN_CONFIGURATION_URL = '/cem_agent/monitoring/<vmID>'
    
    def __init__(self, log, url, auth_token=None, protocol='http'):
        self.rest = REST(log)
        self.__auth_token = auth_token
        self.protocol = protocol
        self.url = url
        self.LOG = log
        
    
    def __auth_header(self, token=None):
        if token:
            return { 'Authorization': token }
        elif self.__auth_token: 
             return { 'Authorization': self.__auth_token }
        return {}
        
    def register (self):
        myheaders = self.__auth_header()
        myheaders['Content-type'] = 'application/json'
        myheaders['Accept'] = 'application/json'

        url = self.protocol + '://' + self.url + self.__REGISTER_URL

        response = self.rest.do_request( method='GET', url=url, extra_headers=myheaders )
        if response:
            try:
                #self.LOG.debug(response.text)
                #self.LOG.debug( json.loads(response.text) )
                if response.status_code == 200:
                    return (json.loads(response.text))['vmID']
                self.LOG.error('CEM Agent register - Status code %d: %s'%(response.status_code, response.text))
            except: 
                self.LOG.error('CEM Agent register - Loading request body')

        return None

    def deregister (self):
        myheaders = self.__auth_header()
        url = self.protocol + '://' + self.url + self.__PLUGIN_CONFIGURATION_URL

        response = self.rest.do_request( method='GET', url=url, extra_headers=myheaders )
        if response:
            if response.status_code == 200:
                return True
            self.LOG.error('CEM Agent deregister - Status code %d: %s'%(response.status_code, response.text))
        return None

    def send_monitoring_info(self, vmID, info):
        myheaders = self.__auth_header()
        myheaders['Content-type'] = 'application/json'       
        data = json.dumps({ 'timestamp': time.time(), 'data': info})
        url = self.protocol + '://' + self.url + self.__MONITORING_RESULT_URL.replace('<vmID>', vmID)
        response = self.rest.do_request( method='POST', url=url, extra_headers=myheaders, body=data)
        if response:
            if response.status_code == 200:
                return response.text
            self.LOG.error('Sending info to CEM Server - Status code %d: %s'%(response.status_code, response.text))
        return None

    def get_plugins_configuration (self, vmID):
        myheaders = self.__auth_header()
        myheaders['Content-type'] = 'application/json'
        myheaders['Accept'] = 'application/json'

        url = self.protocol + '://' + self.url + self.__PLUGIN_CONFIGURATION_URL.replace('<vmID>', vmID)

        response = self.rest.do_request( method='GET', url=url, extra_headers=myheaders )
        if response:
            try:
                if response.status_code == 200:
                    return json.loads(response.text)
                self.LOG.error('Getting plugin configuration from CEM Server - Status code %d: %s'%(response.status_code, response.text))
            except: 
                self.LOG.error('Getting plugin configuration from CEM Server - Loading request body')

        return None
 
