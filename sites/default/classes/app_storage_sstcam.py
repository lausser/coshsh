from application import Application
from templaterule import TemplateRule
from util import compare_attr

def __mi_ident__(params={}):
    if compare_attr("type", params, "sstcam"):
        return SSTCam


class SSTCam(Application):
    template_rules = [
        TemplateRule(
            template="app_storage_sstcam_logs", 
        )
    ]


    def __new__(cls, params={}):
        return object.__new__(cls)


    def __init__(self, params={}):
        print "i am SSTCAM.__init__"
        super(self.__class__, self).__init__(params)
        print "i am SSTCAM.__init__ called", super(self.__class__, self).__class__.__name__


