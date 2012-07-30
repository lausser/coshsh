import unittest
from optparse import OptionParser
import ConfigParser
import sys
import os
import shutil

sys.path.append("..")
sys.path.append("../coshsh")
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'recipes', 'default', 'classes'))
from generator import Generator
from datasource import Datasource
from recipe import Recipe

class CoshshTest(unittest.TestCase):
    def setUp(self):
        #shutil.rmtree('var/objects/test1')
        self.config = ConfigParser.ConfigParser()
        self.config.read('etc/coshsh.cfg')
        self.generator = Generator()


    def test_create_recipe(self):
        self.assert_(self.config._sections != {})
        print self.config._sections
        print [section for section in self.config.sections() if section.startswith('recipe_')]
        recipe = 'recipe_TEST1'
        self.generator.add_recipe(name=recipe.replace("recipe_", "", 1).lower(), **dict(self.config.items(recipe)))
        print self.generator.recipes
        self.assert_(len(self.generator.recipes) == 1)
        self.assert_('test1' in self.generator.recipes)
        self.assert_(self.generator.recipes['test1'].name == 'test1')
        print self.generator.recipes['test1'].datasources
        self.generator.recipes['test1'].init_class_cache()

    def test_create_datasource(self):
        cfg = self.config.items("datasource_SIMPLESAMPLE")
        self.generator.add_recipe(name='test1', **dict(self.config.items('recipe_TEST1')))
        self.generator.recipes['test1'].add_datasource(**dict(cfg))
        print self.generator.recipes['test1'].datasources

    def test_custom_create_datasource(self):
        cfg = self.config.items("datasource_SIMPLESAMPLE")
        print "add recipe test2"
        self.generator.add_recipe(name='test2', **dict(self.config.items('recipe_TEST2')))
        print "add recipe test2 ds simplesample"
        self.generator.recipes['test2'].add_datasource(**dict(cfg))
        ds2 = self.generator.recipes['test2'].datasources[0]
        print "add recipe test3"
        self.generator.add_recipe(name='test3', **dict(self.config.items('recipe_TEST3')))
        print "add recipe test3 ds simplesample"
        self.generator.recipes['test3'].add_datasource(**dict(cfg))
        ds3 = self.generator.recipes['test3'].datasources[0]
        self.assert_(not hasattr(ds2, "only_the_test_simplesample"))
        self.assert_(hasattr(ds3, "only_the_test_simplesample"))

    def test_create_datasource_with_myhost(self):
        dscfg = self.config.items("datasource_SIMPLESAMPLE")
        sicfg = self.config.items('recipe_TEST4')
        recipe = Recipe(**dict(sicfg))
        print recipe
        print "add recipe test4 ds simplesample"
        self.generator.recipes['test4'].add_datasource(**dict(cfg))
        ds4 = self.generator.recipes['test4'].datasources[0]

    def test_create_config(self):
        self.generator.add_recipe(name='test3', **dict(self.config.items('recipe_TEST3')))
        self.generator.recipes['test3'].add_datasource(**dict(self.config.items("datasource_SIMPLESAMPLE") + [('name', 'simplesample')]))
        self.generator.run()

if __name__ == '__main__':
    unittest.main()


