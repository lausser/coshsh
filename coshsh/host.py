import os
from item import Item
from templaterule import TemplateRule

class Host(Item):

    id = 1 #0 is reserved for host (primary node for parents)
    template_rules = [
        TemplateRule(needsattr=None, 
            template="host", 
            self_name="host",
        ),
    ]
    lower_columns = ['address', 'type', 'os', 'hardware', 'virtual', 'location', 'department']


    def __init__(self, params={}):
        for c in self.__class__.lower_columns:
            try:
                params[c] = params[c].lower()
            except Exception:
                if c in params:
                    params[c] = None
        self.hostgroups = []
        self.contacts = []
        self.contact_groups = []
        self.ports = [22] # can be changed with a PORT detail
        super(Host, self).__init__(params)
        self.alias = getattr(self, 'alias', self.host_name)
        

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

