from enum import Enum
import json
import time

class ResourceState(Enum):
    UNKNOWN = 0
    PENDING = 1
    CONFIGURING = 2
    CONFIGURED = 3
    UNCONFIGURED = 4
    STOPPED = 5
    FAILED = 6

class ResourceUtilizationState(Enum):
    UNKNOWN = 0
    IDLE = 1
    USED = 2
    FULL = 3

class Resource:
    
    '''
    def __init__(self, vmID='fake_vmID', ip='default_ip', nodename='default_name', available=False, alive=False, last_connection=0, timestamp_update_state=0, state=ResourceState.UNKNOWN, assigned_rdp_url='default_rdp_url'):
        self.vmID = vmID
        self.ip = ip
        self.nodename = nodename
        self.assigned_rdp_url = assigned_rdp_url
        self.available = bool(available)
        self.alive = bool(alive)
        self.last_connection = int(last_connection)
        self.timestamp_update_state = int(timestamp_update_state)
        self.state = state

    '''
    def __init__ (self, tuple_data):
        # tuple_data --> 'vmID, ip, nodename, assigned_rdp_url, timestamp_agent_connection, timestamp_update_state, state, utilization_state, cem_agent_data, timestamp_update_utilization_state', 'resources'
        self.vmID = tuple_data[0]
        self.ip = tuple_data[1]
        self.nodename = tuple_data[2]
        self.assigned_rdp_url = tuple_data[3]
        self.timestamp_agent_connection = int(tuple_data[4])
        self.timestamp_update_state = int(tuple_data[5])
        self.state = ResourceState(tuple_data[6])
        self.utilization_state = ResourceUtilizationState(tuple_data[7])
        self.cem_agent_data = json.loads(tuple_data[8].replace("'", '"'))
        self.timestamp_update_utilization_state = int(tuple_data[9])

    def to_tuple(self):
        return (self.vmID, self.ip, self.nodename ,self.assigned_rdp_url, self.timestamp_agent_connection, self.timestamp_update_state, self.state.value, self.utilization_state.value, json.dumps(self.cem_agent_data).replace('"', "'"), self.timestamp_update_utilization_state)

    def new_monitoring_info (self, timestamp, data ):
        self.timestamp_agent_connection = int(timestamp)
        self.cem_agent_data = data

    def set_assigned_rdp_url (self, new_url):
        self.assigned_rdp_url = new_url
        return True

    def set_state (self, new_state, timestamp=None):
        if not timestamp:
            timestamp = int(time.time())
        if self.state != new_state:
            if new_state.name in ResourceState.__members__:
                self.timestamp_update_state = timestamp
                self.state = new_state
                return True
        return False
    
    def set_utilization_state (self, new_state, timestamp=None):
        if not timestamp:
            timestamp = int(time.time())
        if self.utilization_state != new_state:
            if new_state.name in ResourceUtilizationState.__members__:
                self.utilization_state = new_state
                self.timestamp_update_utilization_state = timestamp
                return True
        return False

    def set_ip (self, new_ip):
        self.ip = new_ip
        return True

    def set_nodename (self, new_name, vmID):
        if '#N#' in new_name:
            new_name = new_name.replace('#N#', vmID)
        self.nodename = new_name
        return True

    def is_configured (self):
        return self.state in [ ResourceState.CONFIGURED ]

    def is_alive(self):
        return self.state in [ResourceState.CONFIGURED, ResourceState.CONFIGURING, ResourceState.UNCONFIGURED]
        #self.alive 
    
    def __str__(self):
        string = '( name=' + self.vmID + ', state' + self.state.name + ', utilization_state' + self.utilization_state.name + ')' 
        return string

    def transform_to_tuple_DB_SET (self):
        res = []
        res.append( ('vmID', '"'+self.vmID+'"') )
        res.append( ('ip', '"'+ self.ip + '"') )
        res.append( ('nodename', '"' + self.nodename + '"') )
        res.append( ('assigned_rdp_url', '"' + self.assigned_rdp_url + '"') )
        res.append( ('timestamp_agent_connection', int(self.timestamp_agent_connection) ) )
        res.append( ('timestamp_update_state', int(self.timestamp_update_state) ) )
        res.append( ('state', self.state.value ) )
        res.append( ('utilization_state', self.utilization_state.value) )
        res.append( ('cem_agent_data', '"' + json.dumps(self.cem_agent_data).replace('"', "'")  + '"' ) )
        res.append( ('timestamp_update_utilization_state', self.timestamp_update_utilization_state) )
        return res