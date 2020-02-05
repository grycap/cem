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

from cem_agent.Plugin import Plugin
from cem_agent.utils import user_processes, kill_all 
class check_commands(Plugin):

    def do_monitoring (self, users_list, assigned_users):
        result = {}
        if 'target_commands' not in self.plugin_configuration:
            self.LOG.error('"target_commands list not defined in plugin configuration')
            return result

        kill_all_processes = []
        if 'kill_all' in self.plugin_configuration:
            kill_all_processes = self.plugin_configuration['kill_all']

        for username in users_list:
            processes = user_processes (self.LOG, username, list_columns='%p;%a')
            result[username] = {}
            result[username]['number_processes'] = len(processes)
            result[username]['processes'] = processes
            result[username]['executing_target_cmd'] = False

            if (len(processes)>0) and (username not in assigned_users):
                self.LOG.info ('Unauthorized user "'+username+'" has '+ str(len(processes)) + ' processes. ' )
                
                if username in kill_all_processes:
                    pids = [ pr.split(';')[0].replace(' ','') for pr in processes if pr.split(';')[0]!= '']
                    if not kill_all(self.LOG, username, pids ):
                        self.LOG.warning ('Some process was not killed for user ' + username) 
                    else:
                        self.LOG.info ('All processes were killed for user ' + username) 
            else:
                if len(processes)>0:
                    self.LOG.info ('User "'+username+'" has '+ str(len(processes)) + ' processes. ' )

                for pr in processes:
                    cmd = pr.split(';')[1]
                    for target_cmd in self.plugin_configuration['target_commands']:
                        if target_cmd in cmd:
                            self.LOG.debug(username + ' is executing "' + cmd+"'" ) 
                            result[username]['executing_target_cmd'] = True
                            break

        return result