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

import bottle
import threading
import logging
import json

from Request import Request
from db import DataBase 
from Resource import Resource, ResourceState, ResourceUtilizationState

LOG = logging.getLogger('RESTServer')
app = bottle.Bottle()
bottle_server = None
REQUEST_QUEUE = None
DB = None
REST_API_SECRET = None
CEM = None
class RESTServer(bottle.ServerAdapter):

    def run(self, handler):
        try:
            # First try to use the new version
            from cheroot import wsgi
            server = wsgi.Server((self.host, self.port), handler, request_queue_size=32)
        except:
            from cherrypy import wsgiserver
            server = wsgiserver.CherryPyWSGIServer((self.host, self.port), handler, request_queue_size=32)

        self.srv = server
        try:
            server.start()
        finally:
            server.stop()

    def shutdown(self):
        self.srv.stop()

def run(host, port, request_queue, db, rest_api_secret, cem):
    global bottle_server,LOG, REQUEST_QUEUE, DB, REST_API_SECRET, CEM
    CEM = cem
    REQUEST_QUEUE = request_queue
    DB = db
    REST_API_SECRET = rest_api_secret
    bottle_server = RESTServer(host=host, port=port)
    bottle.run(app, server=bottle_server, quiet=True)

def stop():
    if bottle_server:
        bottle_server.shutdown()

def run_in_thread(host, port, request_queue, db, rest_api_secret, cem):
    bottle_thr = threading.Thread(target=run, args=(host, port,request_queue, db, rest_api_secret, cem))
    bottle_thr.daemon = True
    bottle_thr.start()
    return bottle_thr
    
def check_auth (token):
    return token == REST_API_SECRET

''' Returns None or the Resource object ''' 
def check_client_ip (client_ip):
    resources = {}
    if DB.connect():
        aux = DB.select('vmID, ip, nodename, assigned_rdp_url, timestamp_agent_connection, timestamp_update_state, state, utilization_state, cem_agent_data, timestamp_update_utilization_state', 'resources') 
        if aux:
            for tuple_data in aux:
                r = Resource(tuple_data)
                resources[r.ip] = r
    if client_ip in resources:
        return resources[client_ip]
    return None

def get_media_type(header):
    """
    Function to get specified the header media type.
    Returns a List of strings.
    """
    res = []
    accept = bottle.request.headers.get(header)
    if accept:
        media_types = accept.split(",")
        for media_type in media_types:
            pos = media_type.find(";")
            if pos != -1:
                media_type = media_type[:pos]
            if media_type.strip() in ["text/yaml", "text/x-yaml"]:
                res.append("text/yaml")
            else:
                res.append(media_type.strip())

    return res



@app.route('/hello', method='GET')
def RESTGetInfrastructureInfo():
    global REQUEST_QUEUE
    LOG.debug("Received /hello")
    r = Request( request_type='hello', data={}, auth={} )
    REQUEST_QUEUE.put(item=r, block=True, timeout=None)
    bottle.response.content_type = "text/plain"
    return "Added to queue: "+ str(r)

# Requests by USER
@app.route('/demand_resources', method='POST')
def demand_resources():
    global REQUEST_QUEUE
    LOG.debug("Received /demand_resources")
    r_data = {}
    content_type = get_media_type('Content-Type')
    LOG.debug("content_type_: "+str(content_type))
    if content_type:
        if 'application/json' in content_type:
            read_data = str(bottle.request.body.read() )
            try:
                r_data = json.loads( read_data )
            except:
                LOG.error("Cannot read the body of the request")    
                
    r = Request( request_type='demand_resources', data=r_data, auth={} )
    LOG.debug("r: "+str(r))
    REQUEST_QUEUE.put(item=r, block=True, timeout=None)
    bottle.response.content_type = "text/plain"
    bottle.response.status = 200
    return "Added to queue: "+ str(r)

@app.route('/asking_deallocate', method='POST')
def demand_resources():
    global REQUEST_QUEUE
    LOG.debug("Received /asking_deallocate")
    r_data = {}
    content_type = get_media_type('Content-Type')
    LOG.debug("content_type_: "+str(content_type))
    if content_type:
        if 'application/json' in content_type:
            read_data = str(bottle.request.body.read() )
            try:
                r_data = json.loads( read_data )
            except:
                LOG.error("Cannot read the body of the request")    
                
    r = Request( request_type='asking_deallocate', data=r_data, auth={} )
    LOG.debug("r: "+str(r))
    REQUEST_QUEUE.put(item=r, block=True, timeout=None)
    bottle.response.content_type = "text/plain"
    bottle.response.status = 200
    return "Added to queue: "+ str(r)

# Requests by PRIVILEGED_USER
@app.route('/remove_resources', method='POST')
def remove_resource():
    global REQUEST_QUEUE
    LOG.debug("Received /remove_resources")
    
    r_data = {}
    r_auth = {}
    content_type = get_media_type('Content-Type')
    LOG.debug("content_type_: "+str(content_type))
    if content_type:
        if 'application/json' in content_type:
            read_data = str(bottle.request.body.read() )
            #LOG.debug("read: "+ read_data)
            try:
                read_json = json.loads( read_data )
                r_data = { 'vmID': read_json['vmID'] }
                r_auth = { 'user': read_json['user'], 'password': read_json['password'] }
            except:
                LOG.error("Cannot read the body of the request")    

    r = Request( request_type='remove_resources', data=r_data, auth=r_auth )
    LOG.debug("r: "+str(r))
    REQUEST_QUEUE.put(item=r, block=True, timeout=None)
    bottle.response.content_type = "text/plain"
    bottle.response.status = 200
    return "Added to queue: "+ str(r)

@app.route('/add_resources', method='POST')
def add_resources():
    global REQUEST_QUEUE
    LOG.debug("Received /add_resources")
    
    r_data = {}
    r_auth = {}
    content_type = get_media_type('Content-Type')
    LOG.debug("content_type_: "+str(content_type))
    if content_type:
        if 'application/json' in content_type:
            read_data = str(bottle.request.body.read() )
            #LOG.debug("read: "+ read_data)
            try:
                read_json = json.loads( read_data )
                r_data = {  }
                r_auth = { 'user': read_json['user'], 'password': read_json['password'] }
            except:
                LOG.error("Cannot read the body of the request")
    
    r = Request( request_type='add_resources', data=r_data, auth=r_auth )
    LOG.debug("r: "+str(r))
    REQUEST_QUEUE.put(item=r, block=True, timeout=None)
    bottle.response.content_type = "text/plain"
    bottle.response.status = 200
    return "Added to queue: "+ str(r)

@app.route('/restart_resources', method='POST')
def restart_resources():
    global REQUEST_QUEUE
    LOG.debug("Received /restart_resources") 
    r_data = {}
    r_auth = {}
    content_type = get_media_type('Content-Type')
    LOG.debug("content_type_: "+str(content_type))
    if content_type:
        if 'application/json' in content_type:
            read_data = str(bottle.request.body.read() )
            #LOG.debug("read: "+ read_data)
            try:
                read_json = json.loads( read_data )
                r_data = { 'vmID': read_json['vmID']  }
                r_auth = { 'user': read_json['user'], 'password': read_json['password'] }
            except:
                LOG.error("Cannot read the body of the request")
    
    r = Request( request_type='restart_resources', data=r_data, auth=r_auth )
    LOG.debug("r: "+str(r))
    REQUEST_QUEUE.put(item=r, block=True, timeout=None)
    bottle.response.content_type = "text/plain"
    bottle.response.status = 200
    return "Added to queue: "+ str(r)

@app.route('/stop_resources', method='POST')
def stop_resources():
    global REQUEST_QUEUE
    LOG.debug("Received /stop_resources")
    r_data = {}
    r_auth = {}
    content_type = get_media_type('Content-Type')
    LOG.debug("content_type_: "+str(content_type))
    if content_type:
        if 'application/json' in content_type:
            read_data = str(bottle.request.body.read() )
            #LOG.debug("read: "+ read_data)
            try:
                read_json = json.loads( read_data )
                r_data = { 'vmID': read_json['vmID'] }
                r_auth = { 'user': read_json['user'], 'password': read_json['password'] }
            except:
                LOG.error("Cannot read the body of the request")
    
    r = Request( request_type='stop_resources', data=r_data, auth=r_auth )
    LOG.debug("r: "+str(r))
    REQUEST_QUEUE.put(item=r, block=True, timeout=None)
    bottle.response.content_type = "text/plain"
    bottle.response.status = 200
    return "Added to queue: "+ str(r)

@app.route('/remove_assignation', method='POST')
def remove_assignation():
    global REQUEST_QUEUE
    LOG.debug("Received /remove_assignation")
    
    r_data = {}
    r_auth = {}
    content_type = get_media_type('Content-Type')
    LOG.debug("content_type_: "+str(content_type))
    if content_type:
        if 'application/json' in content_type:
            read_data = str(bottle.request.body.read() )
            #LOG.debug("read: "+ read_data)
            try:
                read_json = json.loads( read_data )
                r_data = { 'vmID': read_json['vmID'], 'username': read_json['username'], 'alloc_id': read_json['alloc_id'] }
                r_auth = { 'user': read_json['user'], 'password': read_json['password'] }
            except:
                LOG.error("Cannot read the body of the request")
    
    r = Request( request_type='remove_assignation', data=r_data, auth=r_auth )
    LOG.debug("r: "+str(r))
    REQUEST_QUEUE.put(item=r, block=True, timeout=None)
    bottle.response.content_type = "text/plain"
    bottle.response.status = 200
    return "Added to queue: "+ str(r)

# Request by CEM Agent
@app.route('/cem_agent/register', method='GET')
def cem_agent_register():
    global REQUEST_QUEUE
    LOG.debug("Received /cem_agent/register")

    if 'Authorization' in bottle.request.headers:
        token = bottle.request.headers['Authorization']

    bottle.response.content_type = "application/json"
    bottle.response.status = 403
    result = {}
    resource = check_client_ip(bottle.request.environ.get('HTTP_X_FORWARDED_FOR') or bottle.request.environ.get('REMOTE_ADDR'))
    if check_auth(token):
        # Check if it is an IP from our clients
        bottle.response.status = 200
        if resource:
            result['vmID'] = resource.vmID
    return json.dumps(result)

@app.route('/cem_agent/deregister', method='GET')
def cem_agent_deregister():
    global REQUEST_QUEUE
    LOG.debug("Received /cem_agent/deregister")

    if 'Authorization' in bottle.request.headers:
        token = bottle.request.headers['Authorization']

    bottle.response.content_type = "plain/text"
    bottle.response.status = 403
    result = {}
    resource = check_client_ip(bottle.request.environ.get('HTTP_X_FORWARDED_FOR') or bottle.request.environ.get('REMOTE_ADDR'))
    if check_auth(token):
        # Check if it is an IP from our clients
        bottle.response.status = 200
    return ""

@app.route('/cem_agent/monitoring/<vmID>', method='POST')
def cem_agent_monitoring(vmID):
    global REQUEST_QUEUE
    LOG.debug("Received /cem_agent/monitoring/<vmID>")
    content_type = get_media_type('Content-Type')
    LOG.debug("content_type_: "+str(content_type))
    r = None
    resource = None

    if 'Authorization' in bottle.request.headers:
        token = bottle.request.headers['Authorization']

   
    if content_type:
        if 'application/json' in content_type:
            read_data = bottle.request.body.read() 
            LOG.debug("read_data: "+ read_data)
            try:
                read_json = json.loads( read_data )
                r_data = read_json['data']
                timestamp = read_json['timestamp']
                resource = check_client_ip(bottle.request.environ.get('HTTP_X_FORWARDED_FOR') or bottle.request.environ.get('REMOTE_ADDR'))
                r = Request(request_type='agent_monitoring', data={ 'data': r_data, 'resource': resource.to_tuple(), 'timestamp': timestamp }, auth={} )
            except:
                LOG.error("Cannot read the body of the request")
    
    bottle.response.content_type = "application/json"
    bottle.response.status = 403
    # Check token
    if check_auth(token) and resource:
        if (vmID == resource.vmID):
            REQUEST_QUEUE.put(item=r, block=True, timeout=None)
            bottle.response.content_type = "text/plain"
            bottle.response.status = 200
            return "Added to queue: "+ str(r)

@app.route('/cem_agent/monitoring/<vmID>', method='GET')
def cem_agent_plugin_info(vmID):
    global CEM, DB
    
    if 'Authorization' in bottle.request.headers:
        token = bottle.request.headers['Authorization']

    bottle.response.content_type = "application/json"
    bottle.response.status = 403
    result = {}
    resource = check_client_ip(bottle.request.environ.get('HTTP_X_FORWARDED_FOR') or bottle.request.environ.get('REMOTE_ADDR'))
    if check_auth(token):
        # Check if it is an IP from our clients
        bottle.response.status = 200
        result = { 'plugins': CEM.plugins_configuration, 'users_list': CEM.get_all_users(DB) , 'assigned_users': CEM.get_users_assigned_to_node(vmID, DB) }

    return json.dumps(result)