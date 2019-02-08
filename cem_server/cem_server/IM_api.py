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
import sys

from REST_api import REST

def read_radl (filename, LOG):
    radl = None
    try: 
        f = open(filename, "r")
        radl = f.read()     
        f.close()        
        #LOG.debug('IM will create a VM with the RADL: \n' + radl)
    except:
        LOG.error('Cannot read the RALD '+filename)
        sys.exit()
    return radl

class IMRestAPI () :

    LOG = logging.getLogger('IM')

    GET_INFRASTRUCTURE_STATE_URL = '/infrastructures/<INF_ID>/state'
    ADD_RESOURCE_URL =  '/infrastructures/<INF_ID>' 
    REMOVE_RESOURCE_URL =  '/infrastructures/<INF_ID>/vms/<VM_ID>' 
    GET_NODE_INFO_URL =  '/infrastructures/<INF_ID>/vms/<VM_ID>'
    STOP_VM_URL =  '/infrastructures/<INF_ID>/vms/<VM_ID>/stop' 
    START_VM_URL =  '/infrastructures/<INF_ID>/vms/<VM_ID>/start'

    def __init__(self, infrastructure_id, rest_endpoint, im_credentials_filename ):
        self.im_credentials_filename = im_credentials_filename
        self.infrastructure_id = infrastructure_id
        self.endpoint = rest_endpoint
        self.auth = self.__obtain_auth()
        

    def __obtain_auth (self, im_credentials_filename=None):
        auth = ''
        try: 
            f = open(self.im_credentials_filename, "r")
            auth = f.read().replace("\n", "\\n")    
            f.close()        
            self.LOG.debug('IM_CREDENTIALS = ' + auth)
        except:
            self.LOG.error('Cannot read the IM credentials in '+self.im_credentials_filename)
            sys.exit()
        return auth

    def __get_Headers(self, extra_headers):
        headers = {}
        headers ["Authorization"] = self.auth
        for k,v in extra_headers.items():
            headers[k] = v
        return headers

    def do_request (self, method='GET', url=None, body=None, params=None, extra_headers={}, verify=False):
        myheaders = self.__get_Headers(extra_headers)
        request_url = self.endpoint + url
        return REST(self.LOG).do_request( method=method, url=request_url, body=body, params=params, extra_headers=myheaders, verify=verify)

    def get_infrastructure_state (self):
        self.LOG.debug ('Getting infrastructure state...' )
        state = None
        headers = { "Accept":  "application/json"}
        url = self.GET_INFRASTRUCTURE_STATE_URL.replace('<INF_ID>', self.infrastructure_id )
        response = self.do_request(method='GET', url=url, extra_headers=headers)
        if response:
            if response.status_code == 200:
                try:
                    self.LOG.debug ('response.text: ' + response.text)
                    state = response.json()
                    self.LOG.debug ('State was obtained successfully')
                except:
                    self.LOG.error('Loading the response of ' + url)  
            else:
                self.LOG.error('Response status_code: ' + response.status_code)               
        else:
            self.LOG.error('No response obtained getting the infrastructure state from IM')
        return state

    def add_resources (self, radl=None, radl_filename=None):
        result = None

        if radl_filename:
            radl = read_radl( radl_filename, self.LOG )
        
        if not radl:
            self.LOG.error ('RADL is None' )
            return result

        self.LOG.debug ('Adding new VM(s) to the infrastructure ...' )
             
        url = self.ADD_RESOURCE_URL.replace('<INF_ID>', self.infrastructure_id )

        headers = { 'Content-type': 'text/plain', "Accept": "application/json"}

        response = self.do_request(method='POST', url=url, extra_headers=headers, body=radl)
        if response:
            if response.status_code == 200:
                try:
                    self.LOG.debug (response.text)
                    data = response.json()
                    result = []
                    for vm_uri in data['uri-list']:
                        new_vm_id = vm_uri['uri'].split('/')[-1]
                        result.append(new_vm_id)
                        self.LOG.debug ('The VM '+ new_vm_id +' was added successfully to the infrastructure')
                except:
                    self.LOG.error('Loading the response of ' + url)  
            else:
                self.LOG.error('Response status_code: ' + response.status_code)               
        else:
            self.LOG.error('No response obtained adding a new VM to the infrastructure')
        return result        

    def remove_resources (self, list_vmIDs=[]):
        result = None

        self.LOG.info ('Removing the VM(s) '+str(list_vmIDs)+' from the infrastructure ...' )
        
        url = self.REMOVE_RESOURCE_URL.replace('<INF_ID>', self.infrastructure_id ).replace('<VM_ID>', ','.join(list_vmIDs)  )

        headers = { "Accept": "text/plain" }
        response = self.do_request(method='DELETE', url=url, extra_headers=headers)
        if response:
            if response.status_code == 200:
                self.LOG.info ('VMs removed successfully from the infrastructure')
                result = True
            else:
                self.LOG.error('Response status_code: ' + response.status_code)               
        else:
            self.LOG.error('No response obtained removing the VMs from the infrastructure')
        return result        

    def stop_resources (self, list_vmIDs=[]):
        result = True
        self.LOG.info ('Stopping the VM(s) '+str(list_vmIDs)+' of the infrastructure ...' )
        
        headers = { "Accept": "text/plain" }
        
        for vmID in list_vmIDs:
            url = self.STOP_VM_URL.replace('<INF_ID>', self.infrastructure_id ).replace('<VM_ID>', vmID  )
            response = self.do_request(method='PUT', url=url, extra_headers=headers)
            if response:
                if response.status_code == 200:
                    self.LOG.info ('VM ' + vmID + ' stopped successfully')
                else:
                    result = False
                    self.LOG.error('Response status_code: ' + response.status_code)               
            else:
                result = False
                self.LOG.error('No response obtained when performs the VM stop')
        return result   

    def start_resources (self, list_vmIDs=[]):
        result = True
        self.LOG.info ('Restarting the VM(s) '+str(list_vmIDs)+' of the infrastructure ...' )
        
        headers = { "Accept": "text/plain" }
        for vmID in list_vmIDs:
            url = self.START_VM_URL.replace('<INF_ID>', self.infrastructure_id ).replace('<VM_ID>', vmID  )
            response = self.do_request(method='PUT', url=url, extra_headers=headers)
            if response:
                if response.status_code == 200:
                    self.LOG.info ('VM ' + vmID + ' started successfully')
                else:
                    result = False
                    self.LOG.error('Response status_code: ' + response.status_code)               
            else:
                result = False
                self.LOG.error('No response obtained when performs the VM restart')
        return result 

    '''
        Obtain information of a node querying to IM 
        INPUT:
            - vmID: IM ID of the node
            - (optional) im_property: specific IM property
        OUTPUT:
            - OK: Dict with the data
            - NOT: None
    '''
    def get_node_info (self, vmID, im_property=None):
        self.LOG.debug ('Getting VM info for node with ID=' + vmID)
        node_info = None
        url = self.GET_NODE_INFO_URL.replace('<INF_ID>', self.infrastructure_id ).replace('<VM_ID>', vmID  )
        headers = { "Accept": "application/json" }
        response = self.do_request(method='GET', url=url,extra_headers=headers)
        if response:
            if response.status_code == 200:
                try:
                    self.LOG.debug (response.text)
                    node_info = response.json()
                    if im_property:
                        if im_property in node_info:
                            node_info = node_info[im_property]
                    self.LOG.debug ('Node info with vmID ' + vmID + ' was obtained successfully')
                except:
                    self.LOG.error('Loading the response of ' + url)  
            else:
                self.LOG.error('Response status_code: ' + response.status_code)               
        else:
            self.LOG.error('No response obtained getting VM information')
        return node_info
    