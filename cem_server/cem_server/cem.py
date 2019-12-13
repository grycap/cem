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
import queue
import threading
import json
import sys 
import time
import subprocess 
import uuid
import math
import shlex 

from cem_server.db import DataBase 
from cem_server.Request import Request
from cem_server.IM_api import IMRestAPI
from cem_server.IptRest_api import IptRest
from cem_server.Resource import Resource, ResourceState, ResourceUtilizationState
from cem_server.User import UserState
from cem_server.IM_api import read_radl

from cem_server.plugins.check_commands import check_commands

def sort_by_usage( resource_list  ) :
    res_list = []
    sorted_list = sorted( resource_list, key= lambda resource: resource['slots_free'], reverse=True)
    for element in sorted_list:
        res_list +=  [ element['vmID'] ] * element['slots_free']
    return res_list


def execute_cmd( cmd_string, LOG, fetch=True):
    '''
    fetch: if True, return a list. Otherwise, return string
    '''
    LOG.debug ('Executing "' + cmd_string + '"' )
    args = shlex.split(cmd_string)

    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    rc = p.returncode

    output = err.decode('UTF-8') 

    if rc == 0:
        output= out.decode('UTF-8') 

    if fetch:
        output = output.split('\n')

    return output, int(rc)



def parse_im_state (im_state):
    if im_state == 'stopped':
        return ResourceState.STOPPED
    elif im_state == 'unconfigured':
        return ResourceState.UNCONFIGURED
    elif im_state == 'configured':
        return ResourceState.CONFIGURED
    elif im_state == 'pending':
        return ResourceState.PENDING
    elif im_state == 'running':
        return ResourceState.CONFIGURING
    return ResourceState.FAILED

def get_property_radl( data, im_property ):
    if type(data) == list:
        for elem in data:
            if type(elem) == dict:
                if im_property in elem:
                    return elem[im_property]
    elif type(data) == dict:
        if im_property in data:
            return data[im_property]
                
    return None


class ClusterElasticityManager():

    LOG = logging.getLogger('CEM')
    main_loop = False
    monitoring_loop = False
    manager_loop = False

    

    def __init__(self, config, request_queue, _db):
        self.__Config = config
        self._db = _db
        self.request_queue = request_queue
        self.threads = []
        self.__im_rest = IMRestAPI(self.__Config.IM_INFRASTRUCTURE_ID, self.__Config.IM_REST_ENDPOINT, self.__Config.IM_CREDENTIALS)
        self.__iprtest = IptRest(host=self.__Config.IPTREST_HOST, port=self.__Config.IPTREST_PORT)
        self.plugins_configuration = {'check_commands': { 'target_commands': ['/opt/Xilinx/Vivado/2018.2/bin/vivado', 'vivado'] }}

        self.init_db()

    def get_active_plugins(self):
        return ['check_commands']

    def check_db(self):
        
        if self._db.connect():
            res = self._db.execute('SELECT * FROM users')
            if len(res) > 0:
                #for row in res:
                #    ClusterElasticityManager.LOG.info(row)
                ClusterElasticityManager.LOG.debug('Database has users')
            else:
                ClusterElasticityManager.LOG.warning('Database is empty')
            self._db.close()

            return True
        return False

    def init_db (self):
        ok = True
        for table in ['users', 'allocations', 'resources']:
            if not self._db.table_exists(table):
                ok = False
        if not ok:
            self.__create_db_tables()
            
    def __create_db_tables(self):
        self.LOG.info('Creating database tables...')
        try: 
            with open('/etc/cem/db_config.db') as f:
                content = f.readlines()
            
            for line in content:
                if self._db.connect():
                    self._db.execute(line)
                    self._db.close()

            self.LOG.info('Database tables created successfully')
        except:
            self.LOG.error('Error creating datables tables')
            sys.exit(2)

    def start (self):
        self.main_loop = True
        self.LOG.debug('Start to process requests from queue')
        self.__loop_process_requests() 
        self.LOG.debug('__loop_process_requests finished')

    def start_monitoring (self):
        self.monitoring_loop = True
        self.LOG.debug('Starting monitoring..')
        self.__monitoring_loop() 
        self.LOG.debug('__monitoring_loop finished')

    def start_manager (self):
        self.manager_loop = True
        self.LOG.debug('Starting Manager..')
        self.__manager_loop() 
        self.LOG.debug('__manager_loop finished')

    def run_in_thread(self):
        th_monitoring = threading.Thread(target=self.start_monitoring, args=())
        th_monitoring.daemon = True
        th_monitoring.start()
        self.threads.append(th_monitoring)

        th_main = threading.Thread(target=self.start, args=())
        th_main.daemon = True
        th_main.start()
        self.threads.append(th_main)

        th_manager = threading.Thread(target=self.start_manager, args=())
        th_manager.daemon = True
        th_manager.start()
        self.threads.append(th_manager)

        self.LOG.debug('CEM threads: '+str(self.threads))

    def stop (self):
        self.main_loop = False
        self.monitoring_loop = False
        self.manager_loop = False
        #self.LOG.debug('Loop to false')

    def __mysleep(self, seconds, thread_name=None):
        counter = 0
        while counter < seconds:
            if thread_name == 'monitoring' and self.monitoring_loop == False:
                return False
            elif thread_name == 'manager' and self.manager_loop == False:
                return False
            time.sleep(1)
            counter += 1
        return True

    '''
        Return vmIDs that are stopped 
        INPUT: 
            - None
        OUTPUT:
            - List(str:vmID)
    '''
    def get_stopped_resources(self, DB):
        res = []
        if DB.connect():
            aux = DB.select('vmID', 'resources', where='state == "'+str(ResourceState.STOPPED.value)+'"')
            if aux:
                for resource in aux:
                    res.append(resource[0])
            DB.close()
        return res

    '''
        Return vmIDs that can be assigned to users. If the resource has more than one slot available, the vmID is repeated many times as slots free.
        INPUT: 
            - None
        OUTPUT:
            - List(str:vmID)
    '''
    def get_free_resources(self, DB):
        free_resources = []      
        sql_resources_max_slots_ok= 'SELECT vmID_assigned,COUNT(vmID_assigned) FROM users GROUP BY vmID_assigned HAVING COUNT(vmID_assigned) < ' + str(self.__Config.CEM_MAX_SLOTS_NODE)
        sql_alloc = 'SELECT * FROM ('+ sql_resources_max_slots_ok +') WHERE vmID_assigned != "-1" AND current_alloc_id != "-1" '
        if DB.connect():
            aux = DB.execute(sql_alloc) 
            if aux:
                for tuple_res in aux:
                    free_resources += tuple_res[0] * (self.__Config.CEM_MAX_SLOTS_NODE - tuple_res[1])
        
            aux = DB.select('vmID', 'resources', where= 'utilization_state == '+ str(ResourceUtilizationState.IDLE.value) +' AND state == '+str(ResourceState.CONFIGURED.value) )
            if aux:
                for resource in aux:
                    free_resources += resource[0] * self.__Config.CEM_MAX_SLOTS_NODE  

            DB.close()     
            
        if len(free_resources) > 0:
            self.LOG.debug('There are '+str(len(free_resources)) + ' nodes that can be reserved by users' )
        else:
            self.LOG.debug('There are not resources available')

        
        return free_resources

    '''
        Use IPTRest for creating a port redirection between front-end port and RDP wn port 
        INPUT:
            - Destination port
            - Destination IP
        OUTPPUT:
            - Redirection created, using the format --> IP:PORT
    '''  
    def __obtain_rdp_url (self, d_ip, d_port, DB):
        rdp_url = 'default_rdp_url'
        s_port = self.__obtain_src_port(DB)
        self.LOG.debug('s_port: ' + str(s_port))
        res = self.__iprtest.create_redirection(source_port=s_port, dest_ip=d_ip, dest_port=d_port)
        if res:
            if len(res) == 1:
                rdp_url = self.__Config.PUBLIC_IP + ':' + s_port
                self.LOG.debug('New rdp_url = ' + rdp_url + ' for ' + d_ip+':'+d_port)
        return rdp_url
    
    '''
        Check the database for getting the smallest port free between the range of ports that can be used 
        INPUT:
            - None
        OUTPUT:
            - Valid port
    '''
    def __obtain_src_port(self, DB):
        min_port= int( str(self.__Config.IPTREST_RANGE_SOURCE_PORTS.split(',')[0]).replace(' ', '') )
        max_port= int( str(self.__Config.IPTREST_RANGE_SOURCE_PORTS.split(',')[1]).replace(' ', '') )
        s_port = min_port
        used_ports = []
        if DB.connect():
            aux = DB.select('assigned_rdp_url', 'resources')
            if aux:
                for url in aux:
                    if url[0] != 'default_rdp_url':
                        used_ports.append( int( url[0].split(':')[1] ) )

            DB.close()

        for p in range(min_port, max_port):
            if p not in used_ports:
                s_port = p
                break

        return str(s_port)

    '''
        Obtains the "name" parameter for users assigned to a certain node
        INPUT:
            - vmID: IM ID of the node
        OUTPUT:
            - List(str:username)
    '''   
    def get_users_assigned_to_node(self, vmID, DB):
        res = []
        if DB.connect():
            aux = DB.select('name', 'users', where='vmID_assigned == "'+vmID+'"')
            if aux:
                res = [ elem[0] for elem in aux ]
            DB.close()
        return res

    '''
        Obtains the "name" parameter for all STUDENT users 
        INPUT:
            - None
        OUTPUT:
            - List. Default: List(str:username)
    '''   
    def get_all_users(self, DB, columns='name', role='student'):
        res = []
        if DB.connect():
            aux =DB.select(columns, 'users', where=' role == "'+role+'"')
            if aux:
                for user_data in aux:
                    if len(user_data) == 1:
                        res.append(user_data[0])
                    else:
                        res.append(user_data)
            DB.close()
        return res

    '''
        Obtains the "name" parameter for users that are WAITING_RESOURCES 
        INPUT:
            - None
        OUTPUT:
            - List(str:username)
    '''   
    def get_users_waiting_resources(self, DB):
        res = [] 
        if DB.connect():
            aux = DB.select ('name', 'users', where='state == '+str(UserState.WAITING_RESOURCES.value) )
            if aux:
                res = [ elem[0] for elem in aux ]
            DB.close()
        return res

    '''
        Obtains the resources that are CONFIGURED and the users that are assigned to the resource
        INPUT:
            - None
        OUTPUT:
            - Dict( str:vmID, {Resource:resource , List(str:username):users } )
    '''   
    def get_dict_with_configured_resources(self, DB):
        resources = {}
        if DB.connect():
            aux = DB.select('vmID, ip, nodename, assigned_rdp_url, timestamp_agent_connection, timestamp_update_state, state, utilization_state, cem_agent_data, timestamp_update_utilization_state', 'resources', where='state == '+str(ResourceState.CONFIGURED.value)) 
            if aux:
                for tuple_data in aux:
                    r = Resource(tuple_data)
                    resources[r.vmID] = { 'resource': r, 'users': [] }

            aux2 = DB.select('vmID_assigned, name' , 'users', where='vmID_assigned != "-1" AND current_alloc_id != "-1"')
            if aux2:
                for tuple_data in aux2:
                    vmID = tuple_data[0].replace(' ', '')
                    username = tuple_data[1].replace(' ', '')
                    if vmID in resources:
                        resources[vmID]['users'].append(username)
                    else:
                        self.LOG.error('get_dict_with_configured_resources: resources_vmID (obtained in allocations table) not in resources (obtained in resources table)')
            DB.close()
        return resources

    '''
        Updates the DB:
            - user state is RESOURCES_ASSIGNED and vmID_assigned is vmID and current_alloc_id is alloc_id
            - create new allocation
        INPUT:
            - vmID: IM ID of the node
            - username: user that reserve one slot on the vmID
            - alloc_id: random identification
        OUTPUT:
            - Boolean

    '''
    def new_resource_assignation_for_user(self, vmID, username, alloc_id):
        sql_new_alloc = ''' INSERT INTO allocations (alloc_id, resources_vmID, username, timestamp_start) VALUES ( ? , ? , ?, ?) ''' 
        result = False
        if self._db.connect():
            if self._db.execute(sql_new_alloc, args= (alloc_id, vmID, username, int(time.time())), fetch=False ) and self._db.update( table='users', set_tuple_list=[('state', UserState.RESOURCES_ASSIGNED.value), ('vmID_assigned', vmID), ('current_alloc_id', '"'+alloc_id+'"'), ('timestamp_update_state', int(time.time()) ) ], where='name=="'+username+'"' ): 
                self.LOG.info('Node '+vmID+' reserved for '+username)
                result = True
            else:
                self.LOG.error('Node '+vmID+ ' cannot be reserved for '+username)
            self._db.close()
        return result        

    '''
        Updates the DB:
            - user state is NOTHING_RESERVED and vmID_assigned="-1" and current_alloc_id="-1"
            - update timestamp_finish of the allocation
        INPUT:
            - vmID: IM ID of the node
            - username: user that reserve one slot on the vmID
            - alloc_id: random identification
        OUTPUT:
            - Boolean

    '''
    def remove_resource_assignation_for_user(self, vmID, username, alloc_id, __by):
        result = False
        if self._db.connect():
            if self._db.update( table='users', set_tuple_list=[('state', UserState.NOTHING_RESERVED.value), ('vmID_assigned', '-1'), ('current_alloc_id', '-1'), ('timestamp_update_state', int(time.time()) )], where='name=="'+username+'"' ) and self._db.update( table='allocations', set_tuple_list=[('timestamp_finish',  int(time.time()) )], where='alloc_id=="'+alloc_id+'"' ): 
                self.LOG.info('Resource '+vmID+' has been deallocated for user '+username + ' by '+__by)
                result = True
            else:
                self.LOG.error('Resource '+vmID+ ' cannot be deallocated for user '+username+ ' by '+__by)
            self._db.close()
        return result        

    '''
        Updates the DB:
            - Insert new Resource from Resources
        INPUT:
            - vmID: IM ID of the node
        OUTPUT:
            - Boolean

    '''
    def add_resource_db (self, vmID ):
        sql = ''' INSERT INTO resources (vmID, ip, nodename, assigned_rdp_url, timestamp_agent_connection, timestamp_update_state, state, utilization_state, cem_agent_data, timestamp_update_utilization_state) VALUES ( ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''' 
        result = False
        if self._db.connect():
            if self._db.execute(sql, args=(vmID, 'default_ip', 'default_name', 'default_rdp_url', -1, int(time.time()), ResourceState.PENDING.value, ResourceUtilizationState.UNKNOWN.value, "{}", int(time.time())), fetch=False ) : 
                self.LOG.info('Node '+vmID+' added to DB')
                result = True
            else:
                self.LOG.error('Node '+vmID+' not added to DB')
            self._db.close()
        return result   

    '''
        Updates the DB:
            - Remove Resource from Resources if it is not assigned to any user
        INPUT:
            - vmID: IM ID of the node
        OUTPUT:
            - Boolean

    '''
    def remove_resource_db(self, vmID):
        result = False
        # Check if some user is using the vmID  
        assigned_users = self.get_users_assigned_to_node(vmID, self._db) 
        if len( assigned_users )>0:
            self.LOG.error('Trying to remove node '+vmID+' but, it is assigned to users'+str(assigned_users) +'. Skipping...')
        else:
            sql = 'DELETE FROM resources WHERE vmID == "'+vmID+'"'
            if self._db.connect():
                if self._db.execute(sql, args= (), fetch=False):
                    self.LOG.info('Node '+vmID+' removed from DB')
                    result = True
                else:
                    self.LOG.error('Node '+vmID+' not removed from DB')
                self._db.close()
        return result      

    def update_state_resource (self, vmID, newstate, timestamp=None):
        if not timestamp:
            timestamp = int(time.time())
        result = False
        if self._db.connect():
            if self._db.update( table='resources', set_tuple_list=[('state', newstate.value), ('timestamp_update_state', timestamp) ], where='vmID=="'+vmID+'"' ): 
                self.LOG.info('New state for resource '+vmID+' is '+newstate.name)
                result = True
            else:
                self.LOG.error('Cannot change the state ('+ newstate.name+') for node '+vmID)
            self._db.close()
        return result    

    def __delete_rdp_url(self, vmID, __DB):
        result = False
        rdp_url = 'default_rdp_url'
        if __DB.connect():
            aux = __DB.select( 'assigned_rdp_url', 'resources' , where='vmID == "' + vmID +'"'  )
            if aux:
                rdp_url = aux[0][0]
            
            if rdp_url != 'default_rdp_url':
                port = rdp_url.split(':')[1]
                if self.__iprtest.delete_redirection( source_port=port ) != None:
                    result = True
            __DB.close()
        return result

    ''' ---------------------------------- MAIN THREAD ---------------------------------- '''
    '''
        Loop that processes the requests obtained from REQUEST_QUEUE
            - 1 Thread dedicated - MAIN_THREAD
            - Only this thread can write to the DB
            - The loop is stopped by cem-service.py
    ''' 
    def __loop_process_requests(self):
        while self.main_loop == True:
            if not self.request_queue.empty():
                r = self.request_queue.get( block=True, timeout=1)
                self.LOG.debug('Request obtained from queue')
                # Requests by CEM AGENT
                if r.request_type == 'agent_monitoring':
                    self.LOG.debug('agent_monitoring: '+str(r))
                    self.__process_agent_monitoring(r)
                # Requests by USERS
                elif r.request_type == 'demand_resources':
                    self.LOG.debug('demand_resources: '+str(r))
                    self.__process_demand_resources(r)
                elif r.request_type == 'asking_deallocate':
                    self.LOG.debug('asking_deallocate: '+str(r))
                    self.__process_asking_deallocate(r)
                # Requests by PRIVILEGED_USER (that call to update_resource_assignation and im_requests)
                elif r.request_type == 'remove_resources':
                    self.LOG.debug('remove_resources: '+str(r))
                    self.__process_remove_resource(r)
                elif r.request_type == 'add_resources':
                    self.LOG.debug('add_resources: '+str(r))
                    self.__process_add_resource(r)
                elif r.request_type == 'restart_resources':
                    self.LOG.debug('restart_resources: '+str(r))
                    self.__process_restart_resource(r)
                elif r.request_type == 'stop_resources':
                    self.LOG.debug('stop_resources: '+str(r))
                    self.__process_stop_resource (r)                
                elif r.request_type == 'remove_assignation':
                    self.LOG.debug('remove_assignation: '+str(r))
                    self.__process_remove_assignation(r)
                # Requests by MONITORING_THREAD
                elif r.request_type == 'server_monitoring':
                    self.LOG.debug('server_monitoring: '+str(r))
                    self.__process_server_monitoring(r)
                elif r.request_type == 'iptrest_info':
                    self.LOG.debug('iptrest_info: '+str(r))
                    self.__process_iptrest_info(r)
                # Requests by MANAGER_THREAD or PRIVILEGED_USER
                elif r.request_type == 'update_resource_assignation':
                    self.LOG.debug('update_resource_assignation: '+str(r))
                    self.__process_update_resource_assignation(r)
                elif r.request_type == 'im_requests':
                    self.LOG.debug('im_requests: '+str(r))
                    self.__process_im_requests(r)
                else:
                    self.LOG.error('request_type is not valid: '+str(r))
                self.request_queue.task_done()


    '''
        Check if there are any resources that can be assigned to user and, in that case, assign it to him. In the other case, the user go to state WAITING_RESOURCES. 
    '''
    def __process_demand_resources(self, request):  
        username = None
        try:
            data = request.data  #json.loads( request.data )
            username = data['user']
        except (ValueError):
            self.LOG.error("Data received invalid: " + str(request))
            return False

        '''
        free_resources = self.get_free_resources()
        if len (free_resources) > 0: 
            vmID = free_resources[0]
            alloc_id = uuid.uuid4()
            if not self.new_resource_assignation_for_user( vmID, username, alloc_id):
                self.LOG.error('Error in new_resource_assignation_for_user')                
                self.request_queue.put(item=request, block=True, timeout=None)
        else:
        '''
        # User state is set to waiting resources
        if self._db.connect():
            if not self._db.update(table='users',set_tuple_list=[('state', UserState.WAITING_RESOURCES.value), ('timestamp_update_state', int(time.time()) )], where='name=="'+username+'"'):
                self.LOG.error('Cannot set state to WAITING_RESOURCES for user ' + username)
                self._db.close()
        
        self.LOG.debug('End of __demand_resources ')
        return True

    def __process_asking_deallocate(self, request):  
        username = None
        try:
            data = request.data  #json.loads( request.data )
            username = data['user']
        except (ValueError):
            self.LOG.error("Data received invalid: " + str(request))
            return False
        vmID_assigned = None
        current_alloc_id = None
        # Obtain the vmID and the alloc_id
        if self._db.connect():
            aux = self._db.select('vmID_assigned,current_alloc_id', 'users', where='name=="'+username+'"'  )
            if aux:
                vmID_assigned = aux[0][0]
                current_alloc_id = aux[0][1]
            self._db.close()

        

        if not vmID_assigned or not current_alloc_id:
            return False
        
        self.remove_resource_assignation_for_user(vmID_assigned, username, current_alloc_id, username)

        
        self.LOG.debug('End of __asking_deallocate')
        return True

    '''
        Use the monitoring information sent by the CEM AGENT in a node 
            - Update the users state 
    '''
    def __process_agent_monitoring(self, request):
        r = Resource(request.data['resource'])
        vmID = r.vmID
        agent_data = request.data['data']
        timestamp = request.data['timestamp']
        
        # Due to the CEM-Agent response,  the contextualization was completed at least one time in the past. So, the Resource State is set to Configured
        r.set_state(ResourceState.CONFIGURED)
        r.new_monitoring_info(timestamp, agent_data )
        # Store the agent monitoring info in the DB
        if self._db.connect():
            if not self._db.update(table='resources', set_tuple_list=r.transform_to_tuple_DB_SET(), where='vmID=="'+vmID+'"'):
                self.LOG.error('Cannot update the monitoring information of node ' + vmID)
                res = False
            self._db.close()
        
        users_assigned_to_node = self.get_users_assigned_to_node(vmID, self._db) 
        # Check if users are executing_cmd_commands
        for username in users_assigned_to_node:
            # Obtain the old state
            db_data_user = None
            if self._db.connect():
                aux = self._db.select('state', 'users', where='name=="'+username+'"'  )
                if aux:
                    db_data_user = UserState(aux[0][0])
                self._db.close()

            old_state = UserState.UNKNOWN
            if db_data_user:
                old_state = db_data_user

            new_state = old_state
            self.LOG.debug('old_state: %s' % ( old_state.name ) ) 

            # Use the agent monitoring information to update the user state
            plugins_result = None
            for plugin_name in self.get_active_plugins():
                p = eval(plugin_name)(plugin_name, self.plugins_configuration[plugin_name])
                # OR between all activated plugin results
                plugins_result = plugins_result or p.check_utilization(agent_data[plugin_name][username])

            if plugins_result:
                new_state = UserState.ACTIVE
            else:
                new_state = UserState.RESOURCES_ASSIGNED

            self.LOG.debug('new_state: %s' % ( new_state.name ) ) 

            if new_state != old_state:
                self.LOG.debug('new_state: '+new_state.name + ', old_state: '+old_state.name)
                # Store the new user state to DB
                if self._db.connect():
                    if not self._db.update(table='users', set_tuple_list=[('state', new_state.value), ('timestamp_update_state', int(r.timestamp_agent_connection))], where='name=="'+username+'"'): 
                        self.LOG.error('Cannot update the state of user '+username)
                        res = False
                    else:
                        self.LOG.debug('New state of user '+username+' is '+new_state.name)
                    self._db.close()    

    '''
        Use the monitoring information obtained by MONITORING_THREAD for:
        - Computing the utilization_state for each node 
        - Check if users are using the node 
        - Update DB
        - Update (if required) the RDP url

        
    '''
    def __process_server_monitoring(self, request):
        res = True
        for vmID, resource_tuple in request.data.items():
            r= Resource(resource_tuple)
            if self.__Config.IPTREST_ENABLED and r.is_configured() and r.assigned_rdp_url == 'default_rdp_url':
                r.set_assigned_rdp_url( self.__obtain_rdp_url(r.ip, self.__Config.RDP_DEST_PORT, self._db ) )
                self.LOG.info('The RDP URL for node '+vmID +' is '+r.assigned_rdp_url)
            
            # Compute utilization_state
            utilization_state = ResourceUtilizationState.UNKNOWN
            users_assigned_to_node = self.get_users_assigned_to_node(vmID, self._db) 
            if r.is_configured():
                if len(users_assigned_to_node) == 0:
                    utilization_state = ResourceUtilizationState.IDLE
                elif len(users_assigned_to_node) < self.__Config.CEM_MAX_SLOTS_NODE:
                    utilization_state = ResourceUtilizationState.USED
                else:
                    utilization_state = ResourceUtilizationState.FULL
            r.set_utilization_state(utilization_state)

            # Store the resource information to DB
            if self._db.connect():
                if not self._db.update(table='resources', set_tuple_list=r.transform_to_tuple_DB_SET(), where='vmID=="'+vmID+'"'):
                    self.LOG.error('Cannot update the monitoring information of node ' + vmID)
                    res = False
                self._db.close()

            self.LOG.debug('vmID=%s --> users_assigned_to_node: %s' %(vmID, str(users_assigned_to_node) ) )
            

        return res

    '''
        Allocate or deallocate resources to users:
        - Users and vmIDs are provided in the request.data by the MANAGER_THREAD 
        - Update DB
        
    '''
    def __process_update_resource_assignation(self, request):
        __by = 'CEM-Manager'
        if 'by' in request.data:
            __by = request.data['by']

        if 'free' in request.data:
            for username, info in request.data['free'].items():
                vmID = info['vmID']
                alloc_id = info['alloc_id']
                if not self.remove_resource_assignation_for_user(vmID,username, alloc_id, __by):
                    self.LOG.error('Error deallocating resource '+vmID+' to user '+username )                   
        if 'assign' in request.data:
            for username, info in request.data['assign'].items():
                vmID = info['vmID']
                alloc_id = info['alloc_id']
                if not self.new_resource_assignation_for_user( vmID, username, alloc_id):
                    self.LOG.error('Error allocating resource '+vmID+' to user '+username )    
        return True

    ''' 
        Perform (add, remove, start or stop) actions throuth IM REST API and update DB 
    ''' 
    def __process_im_requests(self, request):
        result = True
        __by = 'CEM-Manager'
        if 'by' in request.data:
            __by = request.data['by']

        if 'add' in request.data:
            wn_radl = read_radl( self.__Config.WN_RADL_FILE, self.LOG )
            wn_radl = wn_radl.replace('<<N_WN>>', str(request.data['add']) )
            new_VMs = self.__im_rest.add_resources( radl=wn_radl  )
            if not new_VMs:
                result= False
                self.LOG.error ('Something wrong when ' + __by +' was trying to add %d new resources' % ( request.data['add'] ))
            else:
                if len(new_VMs) != request.data['add']:
                    self.LOG.error ('Only %d new resources added  by ' + __by +' instead of %d' % (len(new_VMs), request.data['add'] ))
                else:
                    self.LOG.info ('All VMs added successfully by ' + __by)  
                # Update DB
                for vmID in new_VMs:
                    if not self.add_resource_db(vmID):
                        self.LOG.error (__by + ' cannot add resource %s to Resources table' % ( vmID ))

        if 'restart' in request.data:
            if not self.__im_rest.start_resources( request.data['restart'] ):
                result= False
                self.LOG.error ('Something wrong when ' + __by + ' was trying to restart the VMs: '+str( request.data['restart'] ))
            else:
                self.LOG.info ('All VMs restarted successfully by ' + __by)

        if 'suspend' in request.data:
            if not self.__im_rest.stop_resources( request.data['suspend'] ):
                result = False
                self.LOG.error ('Something wrong when ' + __by +' was trying to stop the VMs: '+str( request.data['suspend'] ) )
            else:
                self.LOG.info ('All VMs stopped successfully by ' + __by)
                for vmID in request.data['suspend']:
                    if not self.update_state_resource (vmID, ResourceState.STOPPED):
                        self.LOG.error ('Cannot change node ' + vmID + ' to STOPPED by ' + __by )
                    
        
        if 'remove' in request.data:
            removed_vms = []
            if not self.__im_rest.remove_resources( request.data['remove'] ):
                result= False
                self.LOG.error ('Something wrong when ' +__by + ' was trying to remove the VMs: '+str( request.data['remove'] ))
                im_nodes = self.__im_rest.get_infrastructure_state()
                for vmID in request.data['remove']:
                    if vmID not in im_nodes['state']['vm_states']:
                        removed_vms.append(vmID)
            else:
                self.LOG.info ('All VMs removed successfully by ' + __by)      
                removed_vms = request.data['remove']
            
            # Update DB
            for vmID in removed_vms:
                if self.__Config.IPTREST_ENABLED:
                    if not self.__delete_rdp_url(vmID, self._db):
                        self.LOG.error (__by + ' cannot remove rdp_url for resource %s' % ( vmID ))
                if not self.remove_resource_db(vmID):
                    self.LOG.error (__by + ' cannot remove resource %s from the Resources table' % ( vmID ))
                
                
        return result
    
    def __process_remove_resource(self, request):
        users = self.get_users_assigned_to_node( request.data['vmID'], self._db )
        VM_USED = ( len(users) != 0 )
        if self.__user_is_privileged(request.auth['user'], request.auth['password']) and not VM_USED:
            data_im_request = { 'by': request.auth['user'] }
            data_im_request['remove'] = [ request.data['vmID'] ]
            self.request_queue.put(item= Request('im_requests', data=data_im_request, auth = {} ), block=True, timeout=None)
            return True
        return False

    def __process_add_resource (self, request):
        if self.__user_is_privileged(request.auth['user'], request.auth['password']):
            data_im_request = { 'by': request.auth['user'] }
            data_im_request['add'] = 1
            self.request_queue.put(item= Request('im_requests', data=data_im_request, auth = {} ), block=True, timeout=None)
            return True
        return False

    def __process_stop_resource (self, request):
        users = self.get_users_assigned_to_node( request.data['vmID'], self._db )
        VM_USED = ( len(users) != 0 )
        if self.__user_is_privileged(request.auth['user'], request.auth['password']) and not VM_USED:
            data_im_request = { 'by': request.auth['user'] }
            data_im_request['suspend'] = [ request.data['vmID'] ]
            self.request_queue.put(item= Request('im_requests', data=data_im_request, auth = {} ), block=True, timeout=None)
            return True
        return False
    
    def __process_restart_resource(self, request):
        if self.__user_is_privileged(request.auth['user'], request.auth['password']):
            data_im_request = { 'by': request.auth['user'] }
            data_im_request['restart'] = [ request.data['vmID'] ]
            self.request_queue.put(item= Request('im_requests', data=data_im_request, auth = {} ), block=True, timeout=None)
            return True
        return False

    def __process_remove_assignation(self, request):
        if self.__user_is_privileged(request.auth['user'], request.auth['password']):
            data_im_request = { 'by': request.auth['user'] }
            data_im_request['free'] = { }
            data_im_request['free'][ request.data['username'] ] = { 'vmID': request.data['vmID'], 'alloc_id': request.data['alloc_id'] }
            self.request_queue.put(item= Request('update_resource_assignation', data=data_im_request, auth = {} ), block=True, timeout=None)
            return True
        return False 

    def __process_iptrest_info (self, request):

        iptrest_active_redir = []
        aux = self.__iprtest.get_redirections()
        if aux:
            iptrest_active_redir = aux

        for redir in iptrest_active_redir:
            delete = True
            for cem_redir in request.data['redirections']:
                if redir['s_port'] == cem_redir['source_port'] and redir['ip'] == cem_redir['dest_ip'] and redir['d_port'] == cem_redir['dest_port']:
                    delete = False
                    break
            
            if delete:
                if not self.__iprtest.delete_redirection(source_port=redir['s_port'] ):
                    self.LOG.error('Cannot delete IptRest redirection: '+json.dumps(redir))
                else:
                    self.LOG.info('Redirection deleted: %s '%(json.dumps(redir)))

        iptrest_active_redir = []
        aux = self.__iprtest.get_redirections()
        if aux:
            iptrest_active_redir = aux

        for cem_redir in request.data['redirections']:
            create = True
            for redir in iptrest_active_redir:
                if redir['s_port'] == cem_redir['source_port'] and redir['ip'] == cem_redir['dest_ip'] and redir['d_port'] == cem_redir['dest_port']:
                    create = False
                    break
            if create:
                if not self.__iprtest.create_redirection(source_port=cem_redir['source_port'], dest_ip=cem_redir['dest_ip'], dest_port=cem_redir['dest_port']):
                    self.LOG.error('Cannot create IptRest redirection: '+json.dumps(cem_redir))
                else:
                    self.LOG.info('Redirection created: %s'%(json.dumps(cem_redir)))

        # Check if -A FORWARD_direct -m conntrack --ctstate NEW,RELATED -j ACCEPT is in iptables-save           
        output, rc = execute_cmd( 'iptables-save', self.LOG)
        if rc == 0:
            if not "-A FORWARD_direct -m conntrack --ctstate NEW,RELATED -j ACCEPT" in output:
                #self.LOG.warn('iptables forwarding is not configured: exit_code= %d, output=%s' % (rc, output))
                output2, rc2 = execute_cmd( 'iptables -t filter -A FORWARD_direct -m conntrack --ctstate NEW,RELATED -j ACCEPT', self.LOG)
                if rc2 != 0:
                    self.LOG.warn('Cannot configure iptables: exit_code= %d, output=%s' % (rc2, output2))
                else:
                    self.LOG.info('iptables forwarding is now configured ')
        else:
            self.LOG.error( 'iptables-save returns error_code=%d, output=%s'%(rc, output))


            



    def __user_is_privileged(self, username, password):
        role = 'student'
        if self._db.connect():
            aux = self._db.select('role', 'users', where='name=="'+username+'" AND password=="'+password+'"'  )
            if aux:
                role = str(aux[0][0])
                self._db.close()
        return role == 'teacher' 
    ''' ---------------------------------- MONITORING THREAD ---------------------------------- '''

    '''
        Loop that obtains information about the CEM-AGENTS running of the infrastructure and send it to the MAIN_THREAD using the REQUEST_QUEUE
            - 1 Thread dedicated - MONITORING_THREAD
            - The loop is stopped by cem-service.py
    ''' 
    def __monitoring_loop(self):
        __DB = DataBase(self.__Config.DB)
        while self.monitoring_loop:
            self.LOG.info('-- Starting monitoring loop iteration -- ')
            # Get nodes from DB
            all_nodes = {}
            db_nodes = []
            iptrest_info = []

            if __DB.connect():
                aux = __DB.select('vmID, ip, nodename, assigned_rdp_url, timestamp_agent_connection, timestamp_update_state, state, utilization_state, cem_agent_data, timestamp_update_utilization_state', 'resources')
                if aux:
                    db_nodes = aux
                __DB.close()

            self.LOG.debug(db_nodes)
            
            
            # Check im_state from that nodes
            im_states = self.__im_rest.get_infrastructure_state()

            if im_states == None:
                self.LOG.error('No VMs in the infrastructure')
            else:
                if len(im_states['state']['vm_states'])-1 != len(db_nodes): 
                    self.LOG.warning( "len(im_states['state']['vm_states']) != len(db_nodes) --> %d , %d " % ( len(im_states['state']['vm_states'])-1, len(db_nodes)  ) )

                users_list =  self.get_all_users(__DB) 

                for node_tuple_info in db_nodes:
                    __resource = Resource(node_tuple_info)
                    #__resource.set_state(ResourceState.UNKNOWN)
                    #__resource.set_utilization_state(ResourceUtilizationState.UNKNOWN)
                    vmID = __resource.vmID
                    
                    # IPTRest INFO
                    if self.__Config.IPTREST_ENABLED and __resource.assigned_rdp_url != 'default_rdp_url':
                        iptrest_info.append ( { 'source_port':  __resource.assigned_rdp_url.split(':')[1], 'dest_port': self.__Config.RDP_DEST_PORT, 'dest_ip': __resource.ip } )

                    if vmID in im_states['state']['vm_states']:
                        # Change state
                        __resource.set_state(  parse_im_state(im_states['state']['vm_states'][vmID]) )  
                        
                        # Due to the CEM-Agent response,  the contextualization was completed at least one time in the past. So, the Resource State is set to Configured
                        if __resource.cem_agent_data:                        
                            __resource.set_state(ResourceState.CONFIGURED)
                        
                        if __resource.nodename == 'default_name' or __resource.ip == 'default_ip':
                            node_info = self.__im_rest.get_node_info(vmID)
                            # Obtain ip and nodename
                            if node_info:
                                if 'radl' in node_info:
                                    new_ip = get_property_radl(node_info['radl'], 'net_interface.0.ip')
                                    if new_ip != None:
                                        __resource.set_ip(new_ip)
                                        self.LOG.info('New IP for resource ' + vmID+': ' + new_ip )  
                                    
                                    new_name = get_property_radl(node_info['radl'], 'net_interface.0.dns_name')
                                    if new_name != None:
                                        __resource.set_nodename(new_name, vmID)
                                        self.LOG.info('New name for resource ' + vmID+': ' +new_name ) 
                    
                    else:
                        self.LOG.warning( 'Node ' + vmID + ' not exists for IM')

                    all_nodes[ vmID ] = __resource.to_tuple()

                if self.__Config.IPTREST_ENABLED:
                    self.request_queue.put(item=Request(request_type='iptrest_info', data={ 'redirections': iptrest_info }, auth={} ) , block=True, timeout=None)
                self.request_queue.put(item=Request(request_type='server_monitoring', data=all_nodes, auth={} ), block=True, timeout=None)

            self.LOG.info (' -- Monitoring loop iteration complete -- ')
            if not self.__mysleep (self.__Config.CEM_MONITORING_PERIOD, 'monitoring'):
                break
            #time.sleep(self.__Config.CEM_MONITORING_PERIOD)

        return True

    ''' ---------------------------------- MANAGER THREAD ---------------------------------- '''

    '''
        Loop that assigns users to resources, wake up/suspend resources and add/remove resources.
            - 1 Thread dedicated - MANAGER
            - The loop is stopped by cem-service.py
            - It interacts with IM for wake up/suspend OR add/remove
            - Sends to the MAIN_THREAD the DB modifications usign the REQUEST_QUEUE

    ''' 
    def __manager_loop(self):
        __DB = DataBase(self.__Config.DB)
        while self.manager_loop:
            self.LOG.info ('-- Starting Manager loop iteration -- ')
            __demanding_slots = 0
            RESOURCE_ASSIGNATIONS = {}
            RESOURCE_UNASSIGNATIONS = {}
            RESTART_RESOURCES = []
            SUSPEND_RESOURCES = []
            ADD_RESOURCES = 0
            REMOVE_RESOURCES = []

            configured_resources_dict = self.get_dict_with_configured_resources( __DB )
            users_dict = {}
            for elem in self.get_all_users(__DB, columns='name, role, state, timestamp_update_state, vmID_assigned, current_alloc_id'):
                #self.LOG.debug( ' --------------> ' + str(UserState.NOTHING_RESERVED  == elem[2]) )
                users_dict[ elem[0] ] = {'role': elem[1], 'state': UserState(elem[2]), 'timestamp_update_state': int(elem[3]), 'vmID': elem[4], 'current_alloc_id': elem[5]}
        
            # Check if users are not active in order to free their resources
            for username, user_info in users_dict.items():
                same_state_seconds = int(time.time()) - int(user_info['timestamp_update_state']) 
                # If user is not ACTIVE during more than ALLOW_SLOTS_INACTIVE_TIME_SECONDS seconds, CEM-Manager will free its resource.
                if (user_info['state'] == UserState.RESOURCES_ASSIGNED)  and same_state_seconds > self.__Config.ALLOW_SLOTS_INACTIVE_TIME_SECONDS:
                    self.LOG.info('Assigned resources to user '+username +' will be released due to INACTIVITY PERIOD ('+str(same_state_seconds) + ' seconds)' )
                    RESOURCE_UNASSIGNATIONS[username] = { 'alloc_id': user_info['current_alloc_id'], 'vmID': user_info['vmID'] } # To update DB
                    configured_resources_dict[ user_info['vmID'] ]['users'].remove(username)
                    
            
            users_waiting_resources_list = self.get_users_waiting_resources(__DB)
            '''
            free_resources_list = []
            for vmID, resource_data in configured_resources_dict.items():
                slots_free = self.__Config.CEM_MAX_SLOTS_NODE - len(resource_data['users'])
                while slots_free>0:
                    free_resources_list.append(vmID)
                    slots_free -= 1
            free_resources_list.sort()
            '''
            aux_list = []
            aux_list = [ { 'vmID': vmID, 'slots_free': self.__Config.CEM_MAX_SLOTS_NODE - len(resource_data['users']) } for vmID, resource_data in configured_resources_dict.items() ]

            free_resources_list = sort_by_usage( aux_list)

            stopped_resources_list = self.get_stopped_resources(__DB)

            self.LOG.info ( ('The system will free %d resource reservations: %s') % (len(RESOURCE_UNASSIGNATIONS) , str(RESOURCE_UNASSIGNATIONS.keys()) ) )
            self.LOG.info ( ('There are %d users in state WAITING_RESOURCES: %s') % (len(users_waiting_resources_list) , str(users_waiting_resources_list)) )
            self.LOG.info ( ('There are %d slots availables for allocating users: %s') % (len(free_resources_list) , str(free_resources_list)) ) 
            self.LOG.info ( ('There are %d resources STOPPED: %s ') % (len(stopped_resources_list), str(stopped_resources_list) ) ) 

            while len(users_waiting_resources_list)>0:
                user = users_waiting_resources_list.pop(0)

                if len(free_resources_list) > 0: # ¿Free resources?
                    # Assign vmID to the user (the request will be sent later)
                    vmID = free_resources_list.pop(0)
                    RESOURCE_ASSIGNATIONS[user] = { 'vmID': vmID, 'alloc_id': str(uuid.uuid4()).replace('-','') } # To update DB
                    configured_resources_dict[vmID]['users'].append(user)

                elif len(stopped_resources_list)>0: #¿Stopped resources?
                    RESTART_RESOURCES.append(stopped_resources_list.pop(0))

                else: # Create new resources 
                    __demanding_slots += 1   

            self.LOG.info ( ('After the new resource assignations, there are %d users in state WAITING_RESOURCES: %s') % (len(users_waiting_resources_list) , str(users_waiting_resources_list)) )

            # Obtain ADD_RESOURCES using __demanding_slots
            ADD_RESOURCES = int( math.ceil ( float(__demanding_slots)/float( self.__Config.CEM_MAX_SLOTS_NODE ) ) )    

            # Obtain IDLE resources
            idle_resources = { }
            for vmID, resource_data in configured_resources_dict.items():
                if len(resource_data['users']) == 0:
                    idle_resources[vmID] = resource_data['resource']
            
           
            required_stopped_resources = self.__Config.MIN_RESOURCES_STOPPED  - len(stopped_resources_list)  # x<0 -> x resources more than required ;  x>0 -> x resources required ;
            idle_resources_wasted = len(idle_resources) - self.__Config.MIN_RESOURCES_IDLE 
            
            # Check if the infrastructure will have the minimum number of resources suspended
            if required_stopped_resources > 0: 
                self.LOG.info('The infrastructure has not the required number of resources Stopped (%d / %d). Stopping IDLE resources that are wasted' % ( len(stopped_resources_list), required_stopped_resources ) )   
                
                # if the infrastructure has idle resources wasted, we can stop them
                while (idle_resources_wasted > 0) and (required_stopped_resources>0):
                    vmID = list(idle_resources.keys())[0]
                    del idle_resources[vmID]
                    SUSPEND_RESOURCES.append(vmID)
                    idle_resources_wasted -= 1
                    required_stopped_resources -=1
                
                # Still needing stopped resources?
                if required_stopped_resources>0:
                    ADD_RESOURCES += required_stopped_resources
                    self.LOG.info('Finally, the infrastructure has not the required number of resources Stopped (%d), %d new resources will be powered on.' % ( required_stopped_resources , required_stopped_resources )  )

            # Check if the infrastructure has the minimum number of resources IDLE
            idle_resources_wasted = len(idle_resources) - self.__Config.MIN_RESOURCES_IDLE 
            while idle_resources_wasted < 0:
                self.LOG.info('The infrastructure has not the required number of resources IDLE (%d, %d)' % ( len(idle_resources), self.__Config.MIN_RESOURCES_IDLE) )   
                
                # Check if the infrastructure has resources STOPPED that can be powered on
                if required_stopped_resources < 0:
                    vmID = stopped_resources_list.pop(0)
                    RESTART_RESOURCES.append(vmID)
                    required_stopped_resources += 1
                    idle_resources_wasted += 1 # As the stopped resource will be powered on, the infrastructure will be have one resource more IDLE
                    self.LOG.info('%s will be powered on for getting the required number of resources IDLE (%d)' % ( vmID, self.__Config.MIN_RESOURCES_IDLE) ) 
                else:
                    self.LOG.info('There are not resources stopped for getting the required number of resources IDLE, adding %d to ADD_RESOURCES' % ( idle_resources_wasted*(-1) ) ) 
                    # Check if the infrastructure has resources STOPPED that can be used!!! --> WIP 
                    ADD_RESOURCES += (idle_resources_wasted*(-1))
                    idle_resources_wasted = 0

            self.LOG.info ( ('There are %d resources IDLE where %d are wasted: %s') % (len(idle_resources) , idle_resources_wasted, str(idle_resources)) ) 

            


            # Check if some user with privileged role wants something (destroy / create NODES)  



            # If there are some resources in state CONFIGURING / PENDING / UNCONFIGURED means that some previous ADD_RESOURCE request was done, so CEM-Manager does not attend it again
            future_resources = 0
            if __DB.connect():
                aux = __DB.select ('vmID', 'resources', where='( (state == '+str(ResourceState.PENDING.value)+') OR '+ '(state == '+str(ResourceState.CONFIGURING.value)+') )' ) #') OR '+ '(state == '+str(ResourceState.UNCONFIGURED.value)+ 
                if aux:
                    future_resources = len(aux)
                __DB.close()
                

            self.LOG.info ( ('Required resources %d, resources that will be powered on %d') % ( ADD_RESOURCES , ADD_RESOURCES-future_resources ) ) 

            ADD_RESOURCES -= future_resources

            # Any node can be removed? (state FAILED,IDLE during too much time or many resources STOPPED)

            # IDLE
            for vmID, r in idle_resources.items():
                self.LOG.debug('Node '+vmID+' is IDLE since '+str(r.timestamp_update_utilization_state) + ' and idle_resources_wasted = '+str(idle_resources_wasted) )
                if idle_resources_wasted > 0:     
                    same_state_seconds = int(time.time()) - int( r.timestamp_update_utilization_state ) 
                    if r.utilization_state == ResourceUtilizationState.IDLE and same_state_seconds > self.__Config.RESOURCE_IDLE_TIME_SECONDS:
                        self.LOG.info ('Node '+vmID+' will be removed due to it is IDLE too much time (%d)' % (same_state_seconds) )
                        REMOVE_RESOURCES.append(vmID)
                        idle_resources_wasted-=1                    
                else: # If not exists removable IDLE resources 
                    break 

            # FAILED
            failed_resources = []
            if __DB.connect():
                aux = __DB.select ('vmID', 'resources', where='state == '+str(ResourceState.FAILED.value) ) 
                if aux:
                    failed_resources = aux
            for r_info in failed_resources:
                REMOVE_RESOURCES.append(r_info[0])
                self.LOG.info ('Node '+r_info[0]+' will be removed due to its state is FAILED' )            
            self.LOG.info ( ('There are %d resources FAILED: %s') % ( len(failed_resources) , str(failed_resources) ) ) 


            # STOPPED
            while len(stopped_resources_list)>self.__Config.MIN_RESOURCES_STOPPED:
                vmID = stopped_resources_list.pop(0)
                self.LOG.info ('Node '+vmID+' will be removed because there are %d resources stopped (only %d is required))' % (len(stopped_resources_list), self.__Config.MIN_RESOURCES_STOPPED ) )
                REMOVE_RESOURCES.append(vmID)
            
            # Send decisions to MAIN_THREAD            
            # Update allocations
            data_update_assignation = {}
            if len(RESOURCE_ASSIGNATIONS) > 0:
                data_update_assignation['assign'] = RESOURCE_ASSIGNATIONS
            if len(RESOURCE_UNASSIGNATIONS) > 0:
                data_update_assignation['free'] = RESOURCE_UNASSIGNATIONS
            if len(data_update_assignation) > 0:
                self.LOG.debug (' CEM-Manager sends "update_resource_assignation": ' + str(data_update_assignation) )
                self.request_queue.put(item= Request('update_resource_assignation', data=data_update_assignation, auth = {} ), block=True, timeout=None)

            data_im_request = {}
            # Restart resources - Request
            if len(RESTART_RESOURCES) > 0:
                data_im_request['restart'] = RESTART_RESOURCES

            # Suspend resources - Request
            if len(SUSPEND_RESOURCES) > 0:
                data_im_request['suspend'] = SUSPEND_RESOURCES           
            
            # Add resources - Request
            if ADD_RESOURCES > 0:
                data_im_request['add'] = ADD_RESOURCES  

            # Remove resources - Request
            if len(REMOVE_RESOURCES) > 0:
                data_im_request['remove'] = REMOVE_RESOURCES

            if len(data_im_request)>0:
                self.LOG.debug (' CEM-Manager sends "im_requests": ' + json.dumps(data_im_request) )
                self.request_queue.put(item= Request('im_requests', data=data_im_request, auth = {} ), block=True, timeout=None)

            self.LOG.info ('-- Manager loop iteration complete -- ')
            if not self.__mysleep (self.__Config.CEM_MANAGER_PERIOD, 'manager'):
                break
            
        return True
