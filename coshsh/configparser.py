from configparser import RawConfigParser


class CoshshConfigParser(RawConfigParser, object):

    def read(self, files):
        super(self.__class__, self).read(files)
        for section in self._sections.values():
            if "isa" in section.keys() and section["isa"] in self._sections:
                    for key in self._sections[section["isa"]]:
                        if not key in section and not key == "isa":
                            section[key] = self._sections[section["isa"]][key]

