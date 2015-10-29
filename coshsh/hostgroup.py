import os
import coshsh


class HostGroup(coshsh.item.Item):

    id = 1 #0 is reserved for host (primary node for parents)
    template_rules = [
        coshsh.templaterule.TemplateRule(needsattr=None, 
            template="hostgroup", 
            self_name="hostgroup",
            unique_attr="hostgroup_name", unique_config="hostgroup_%s",
        ),
    ]


    def __init__(self, params={}):
        self.members = []
        self.contacts = []
        self.contactgroups = []
        self.templates = []
        superclass = super(HostGroup, self)
        superclass.__init__(params)
        

    def is_correct(self):
        return True


    def write_config(self, target_dir):
        my_target_dir = os.path.join(target_dir, "hostgroups", self.hostgroup_name)
        if not os.path.exists(my_target_dir):
            os.mkdir(my_target_dir)
        for file in self.config_files:
            content = self.config_files[file]
            with open(os.path.join(my_target_dir, file), "w") as f:
                f.write(content)


    def create_members(self):
        pass


    def create_contacts(self):
        pass


    def create_templates(self):
        pass

