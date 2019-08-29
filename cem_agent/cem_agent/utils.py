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

import logging
import subprocess
import shlex

def execute_cmd(LOG, cmd_string, fetch=True):
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



def user_processes (LOG, user, list_columns=None):
    
    command = 'ps --no-headers -U ' + user 
    if list_columns:
        command +=  ' -o '+ list_columns
    
    output, rc = execute_cmd(LOG, command)
    
    if rc == 0:
        return [ elem for elem in output if elem!='']
    elif rc != 1:
        LOG.error('Error code: %d. Output: %s' %(rc,output))
    return []

def kill_all (LOG, user=None, processes=None):
    if not processes:
        if not user:
            LOG.error('Cannot kill processes due to invalid args')
            return False
        processes = user_processes (LOG, user, list_columns='pid')
    
    ok = True
    for pid in processes:
        output, rc = execute_cmd( LOG, 'kill -9 ' + pid.replace(' ','')  )
        if rc != 0:
            LOG.warning('Cannot kill '+ pid.replace(' ','') + ': '+ str(output))
            ok = False

    return ok

