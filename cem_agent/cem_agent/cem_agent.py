# CEM agent - Cluster Elasticity Manager
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
import subprocess 
import time
import shlex 

LOG = logging.getLogger('CEM-agent')
CONFIG = None
app = bottle.Bottle()
bottle_server = None

TARGET_COMMANDS = ['/opt/Xilinx/Vivado/2018.2/bin/vivado', 'vivado']

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

def run(host, port):
    global bottle_server, LOG
    bottle_server = RESTServer(host=host, port=port)
    bottle.run(app, server=bottle_server, quiet=True)

def stop():
    if bottle_server:
        bottle_server.shutdown()

def run_in_thread(host, port, config):
    global CONFIG
    CONFIG = config
    bottle_thr = threading.Thread(target=run, args=(host, port))
    bottle_thr.daemon = True
    bottle_thr.start()
    return bottle_thr

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

def check_auth (token):
    return token == CONFIG.REST_API_SECRET

def get_response_content_type(content_type):
    if "application/json" in content_type:
        return "application/json"
    else:
        return 'text/plain'
       
@app.route('/status', method='GET')
def GetStatus():
    global LOG
    LOG.debug("Received GET /status")

    code = 404
    msg = json.dumps({'message': 'Not found', 'code': code})

    bottle.response.content_type = get_response_content_type (get_media_type('Accept'))

    if (check_auth (bottle.request.headers['Authorization']) ):
        code = 200
        msg = json.dumps({'message': 'OK', 'code': code, 'data': {'alive': True} } )
    else:
        code = 401
        msg = json.dumps({'message': 'Authentication error', 'code': code})

    bottle.response.status = code
    return msg

@app.route('/status', method='POST')
def PostStatus():
    global LOG
    LOG.debug("Received POST /status")

    code = 404
    msg = json.dumps({'message': 'Not found', 'code': code})

    bottle.response.content_type = get_response_content_type (get_media_type('Accept'))

    if (check_auth (bottle.request.headers['Authorization']) ):
        content_type = get_media_type('Content-Type')
        LOG.debug("content_type_: "+str(content_type))
        if content_type:
            if 'application/json' in content_type:
                data = None
                try:
                    body = str(bottle.request.body.read() )
                    LOG.debug("body: "+ body)
                    data = json.loads( body )
                except (ValueError):
                    LOG.error('Loading request body')
                    code = 406
                    msg = json.dumps({'message': 'Error loading body', 'code': code})
                if data:    
                    code, msg = __get_status(data)
            else:
                code = 415
                msg = json.dumps({'message': 'Unsupported Accept Media type: '+content_type, 'code': code})


    else:
        code = 401
        msg = json.dumps({'message': 'Authentication error', 'code': code})


    bottle.response.status = code
    return msg


def __execute_cmd( cmd_string, fetch=True):
    global LOG
    '''
    fetch: if True, return a list. Otherwise, return string
    '''
    #str_cmd = []
    #for e in cmd:
    #    str_cmd.append( str(e) )
    LOG.debug ('Executing "' + cmd_string + '"' )
    args = shlex.split(cmd_string)

    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    rc = p.returncode

    output = err
    if rc == 0:
        output= out

    if fetch:
        output = output.split('\n')

    return output, rc 



def __user_processes (user, list_columns=None):
    global LOG
    command = 'ps --no-headers -U ' + user 

    if list_columns:
        command +=  ' -o '+ list_columns
    
    output, rc = __execute_cmd(command)
    
    if rc == 0:
        return [ elem for elem in output if elem!='']
    elif rc != 1:
        LOG.error('Error code: %d. Output: %s' %(rc,output))
    return []

def __kill_all (user=None, processes=None):
    global LOG
    if not processes:
        if not user:
            LOG.error('Cannot kill processes due to invalid args')
            return False
        processes = __user_processes (user, list_columns='pid')
    
    ok = True
    for pid in processes:
        output, rc = __execute_cmd(  'kill -9 ' + pid.replace(' ','')  )
        if rc != 0:
            LOG.warning('Cannot kill '+ pid.replace(' ','') + ': '+ str(output))
            ok = False

    return ok


def __get_status(data):
    global LOG
    code = 200
    msg = { 'alive':  True, 'state': {}, 'timestamp': time.time() } 

    
    if  ('users_list' not in data) or ('assigned_users' not in data):
        code = 404  
        msg['message'] = 'users_list or assigned_users not in body'
    else:
        users = data['users_list']
        ok_users = data['assigned_users']

        kill_all_processes = []
        if 'kill_all' in data:
            kill_all_processes = data['kill_all']

        for user in users:
            processes = __user_processes (user, list_columns='%p;%a')
            msg['state'][user] = {}
            msg['state'][user]['number_processes'] = len(processes)
            msg['state'][user]['processes'] = processes
            msg['state'][user]['executing_target_cmd'] = False

            if (len(processes)>0) and (user not in ok_users):
                LOG.info ('Unauthorized user "'+user+'" has '+ str(len(processes)) + ' processes. ' )
                
                if user in kill_all_processes:
                    pids = [ pr.split(';')[0].replace(' ','') for pr in processes if pr.split(';')[0]!= '']
                    if not __kill_all( user, pids ):
                        LOG.warning ('Some process was not killed for user ' + user) 
                    else:
                        LOG.info ('All processes were killed for user ' + user) 
            else:
                LOG.info ('User "'+user+'" has '+ str(len(processes)) + ' processes. ' )
                
                # Check if user is doing things
                #commands = [ pr.split(';')[1] for pr in processes if pr.split(';')[1]!= '']

                for pr in processes:            
                    #LOG.debug ('pr: ' + pr) 
                    #LOG.debug ('split p: ' + str( pr.split(';') ) )
                    cmd = pr.split(';')[1]
                    for target_cmd in TARGET_COMMANDS:
                        if target_cmd in cmd:
                            LOG.debug (user + ' is executing "' + cmd+"'" ) 
                            msg['state'][user]['executing_target_cmd'] = True
                            break
    #LOG.info ('msg: ' + json.dumps(msg)) 
    return code, json.dumps(msg)