import logging

class Plugin:

    def __init__(self,_name, plugin_configuration):
        self.name = _name
        self.LOG = logging.getLogger('PLUGIN - '+_name)
        self.plugin_configuration = plugin_configuration
    
    def check_utilization (self, data):
        print('Plugin - Dummy check_utilization')
        return False
