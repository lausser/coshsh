import sys
import os
import imp
import inspect
import logging

logger = logging.getLogger('coshsh')

class CoshshDatainterface(object):

    class_factory = []
    class_file_prefixes = []
    class_file_ident_function = ""
    my_type = ""

    @classmethod
    def init_class_factory(cls, classpath):
        print("XXX i am init_class_factory for "+cls.__name__)
        class_factory = []
        sys.dont_write_bytecode = True
        for p in [p for p in reversed(classpath) if os.path.exists(p) and os.path.isdir(p)]:
            #for module, path in [(item, p) for item in sorted(os.listdir(p), reverse=True) if item[-3:] == ".py" and item.startswith(cls.class_file_prefixes)]:
            for module, path in [(item, p) for item in sorted(os.listdir(p), reverse=True) if item[-3:] == ".py" and (item in cls.class_file_prefixes or [prefix for prefix in cls.class_file_prefixes if item.startswith(prefix)])]:
                try:
                    #print "try dr", module, path
                    path = os.path.abspath(path)
                    fp, filename, data = imp.find_module(module.replace('.py', ''), [path])
                    toplevel = imp.load_source(module.replace(".py", ""), filename)
                    for cl in inspect.getmembers(toplevel, inspect.isfunction):
                        if cl[0] ==  cls.class_file_ident_function:
                            class_factory.append([path, module, cl[1]])
                            print("found "+path+" "+module)
                except Exception as exp:
                    logger.critical("could not load %s %s from %s: %s" % (cls.my_type, module, path, exp))
                finally:
                    if fp:
                        fp.close()
        cls.update_class_factory(class_factory)
        return class_factory

    @classmethod
    def update_class_factory(cls, class_factory):
        print("XXX i am update_class_factory for "+cls.__name__)
        cls.class_factory = class_factory


    @classmethod
    def get_class(cls, params={}):
        print("LOOKING FOR "+str(params))
        #print "get_classhoho", cls, len(cls.class_factory), cls.class_factory
        for path, module, class_func in reversed(cls.class_factory):
            try:
                print("try", path, module, class_func)
                newcls = class_func(params)
                if newcls:
                    print("CHOOSING "+path+" "+module)
                    return newcls
            except Exception as exp:
                print(cls.__name__+".get_class exception", exp)
                pass
        logger.debug("found no matching class for this %s %s" % (cls.my_type, params))



