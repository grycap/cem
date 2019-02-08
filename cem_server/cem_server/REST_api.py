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


import requests
import time
import json

class REST():
    RETRY_SLEEP = 2
    MAX_RETRIES = 15

    def __init__(self, log):
        self.LOG=log
    
    def __get_Headers (self, extra_headers):
        headers = {}
        for k,v in extra_headers.items():
            headers[k] = v
        return headers    

    def do_request (self, method=None, url=None, body=None, params=None, extra_headers={}, verify=False):
        retries_cont = 1
        response = None
        ok = False
        myheaders = self.__get_Headers(extra_headers)
        #self.LOG.debug('method: ' + method)
        self.LOG.debug('url: ' + url)
        self.LOG.debug('myheaders: ' + json.dumps(myheaders))
        #self.LOG.debug('body: ' + str(body))
        while ( (self.MAX_RETRIES>retries_cont) and (not ok) ):
            retries_cont += 1
            try: 
                response = requests.request(method, url, verify=False, headers=myheaders, data=body, timeout=30)
                ok=True
            except requests.exceptions.ConnectionError as ex:
                self.LOG.warning(ex) 
                time.sleep(self.RETRY_SLEEP)
            except requests.exceptions.Timeout as ex:
                self.LOG.error(ex) 
            except requests.exceptions.HTTPError as ex:
                self.LOG.error(ex) 
                retries_cont = self.MAX_RETRIES
            except requests.exceptions.RequestException as ex:
                self.LOG.error(ex) 
                retries_cont = self.MAX_RETRIES

            
        if not ok:
            self.LOG.error('MAX_RETRIES reached, cannot connect to ' + url) 
            
        return response
