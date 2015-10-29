import os

class Dependency(object):

    def __init__(self, params={}):
        self.host_name = params["host_name"]
        self.parent_host_name = params["parent_host_name"]
        
