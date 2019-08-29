import logging
from cem_server.Plugin import Plugin

class check_commands (Plugin):
    
    def check_utilization(self, data):
        target_commands = self.plugin_configuration['target_commands']
        return data['executing_target_cmd']
        