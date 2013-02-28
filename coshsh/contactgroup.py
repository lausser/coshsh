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
            self_name="contactgroup",
            unique_attr="contactgroup_name", unique_config="contactgroup_%s",
        )
    ]


    def __init__(self, params={}):
        self.members = []
        super(ContactGroup, self).__init__(params)
        self.fingerprint = lambda s=self:s.__class__.fingerprint(params)

    @classmethod
    def fingerprint(self, params):
        return "%s" % (params["contactgroup_name"], )

    def __str__(self):
        return "contactgroup %s" % self.contactgroup_name

