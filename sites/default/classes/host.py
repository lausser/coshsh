from jinja2 import Template, FileSystemLoader, Environment
import os
from coshsh.item import Item
from templaterule import TemplateRule

class Host(Item):

    id = 1 #0 is reserved for host (primary node for parents)
    template_rules = [
        TemplateRule(needsattr=None, 
            template="host", 
            self_name="host",
        ),
    ]


    def __init__(self, params={}):
        self.hostgroups = []
        self.contacts = []
        self.contact_groups = []
        self.ports = [22] # can be changed with a PORT detail
        super(Host, self).__init__(params)
        

    def is_correct(self):
        return hasattr(self.host_name) and self.host_name != None


    def fingerprint(self):
        return "%s" % (self.host_name, )


    def write_config(self, target_dir):
        my_target_dir = os.path.join(target_dir, "hosts", self.host_name)
        if not os.path.exists(my_target_dir):
            os.mkdir(my_target_dir)
        super(Host, self).write_config(target_dir)


    def create_hostgroups(self):
        pass


    def create_contacts(self):
        pass


    def create_templates(self):
        pass

