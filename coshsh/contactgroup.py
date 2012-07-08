import os
from item import Item
from templaterule import TemplateRule

class ContactGroup(Item):

    id = 1 #0 is reserved for host (primary node for parents)
    my_type = 'contact_group'
    app_template = "app.tpl"

    template_rules = [
        TemplateRule(
            template="contactgroup",
            unique_attr="contactgroup_name", unique_config="contactgroup_%s",
        )
    ]


    def __init__(self, params={}):
        self.members = []
        super(ContactGroup, self).__init__(params)


    def __str__(self):
        return "contactgroup %s" % self.contactgroup_name


    def write_config(self, target_dir):
        my_target_dir = os.path.join(target_dir, "contactgroups")
        if not os.path.exists(my_target_dir):
            os.mkdir(my_target_dir)
        for file in self.config_files:
            content = self.config_files[file]
            with open(os.path.join(my_target_dir, file), "w") as f:
                f.write(content)
