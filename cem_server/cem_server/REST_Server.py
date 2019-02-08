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

LOG = logging.getLogger('RESTServer')
app = bottle.Bottle()
bottle_server = None
REQUEST_QUEUE = None


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

def run(host, port, request_queue):
    global bottle_server,LOG, REQUEST_QUEUE
    REQUEST_QUEUE = request_queue
    bottle_server = RESTServer(host=host, port=port)
    bottle.run(app, server=bottle_server, quiet=True)

def stop():
    if bottle_server:
        bottle_server.shutdown()

def run_in_thread(host, port, request_queue):
    bottle_thr = threading.Thread(target=run, args=(host, port,request_queue))
    bottle_thr.daemon = True
    bottle_thr.start()
    return bottle_thr
    
def check_auth (token):
    return True #token == CONFIG.REST_API_SECRET

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
