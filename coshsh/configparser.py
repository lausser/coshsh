import ConfigParser

class CoshshConfigParser(ConfigParser.ConfigParser, object):

    def read(self, files):
        print "now superconfig"
        superclass = super(CoshshConfigParser, self)
        print "i am super", superclass
        super(CoshshConfigParser, self).read(files)
        print "<<<now superconfig"
        superclass.read('etc/coshsh2.cfg')
        print "CONF", self._sections
        for section in self._sections.values():
            #print "section", section
            if "isa" in section.keys():
                #print "wants to inherit from", section["isa"]
                if section["isa"] in self._sections:
                    #print "inherits"
                    for key in self._sections[section["isa"]]:
                        if not key in section and not key == "isa":
                            #print "inherits", key, self._sections[section["isa"]][key]
                            section[key] = self._sections[section["isa"]][key]


