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
from REST_api import REST 

class CEM_Agent_client():

    __STATE_URL = '/status'
    
    def __init__(self, log, auth_token=None, protocol='http'):
        self.rest = REST(log)
        self.__auth_token = auth_token
        self.protocol = protocol
        
    
    def __auth_header(self, token=None):
        if token:
            return { 'Authorization': token }
        elif self.__auth_token: 
             return { 'Authorization': self.__auth_token }
        return {}
    def get_status (self, host, port, headers=None ):
        myheaders = self.__auth_header()
        myheaders['Content-type'] = 'application/json'
        myheaders['Accept'] = 'application/json'
        if headers:
            for k,v in headers.items():
                myheaders[k] = v
        url = self.protocol + '://' + host + ':' + port + self.__STATE_URL
        return self.rest.do_request( method='GET', url=url, extra_headers=myheaders )

    def post_status (self, host, port, data, headers=None):
        myheaders = self.__auth_header()
        myheaders['Content-type'] = 'application/json'
        myheaders['Accept'] = 'application/json'
        if headers:
            for k,v in headers.items():
                myheaders[k] = v

        url = self.protocol + '://' + host + ':' + port + self.__STATE_URL
        return self.rest.do_request( method='POST', url=url, extra_headers=myheaders, body=data )

 