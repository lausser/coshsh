"""The constitutional performance benchmark: >= 60,000 services in <= 10 seconds.

Constitution Principle IV requires coshsh to generate a large configuration
within a fixed time budget.  This module is what turns that requirement from an
assumption into a measurement: run it before and after a change to the render
pipeline and compare, rather than reasoning about complexity and hoping.

WHY this is marked and deselected: it is a gate, not a per-run test.  It builds
a ~6,000-host fixture and runs the whole pipeline, which costs far more than the
rest of the suite put together, and a wall-clock assertion on a shared machine
is noisy enough that it should not be able to fail an ordinary test run.  Run it
deliberately:

    python -m pytest test_performance.py -m benchmark -q -s

and read the printed elapsed time.  The normal suite excludes it with
``-m "not benchmark"``.
"""

import os
import shutil
import sys
import tempfile
import time
import unittest

import pytest

sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

import coshsh
from coshsh.application import Application
from coshsh.contact import Contact
from coshsh.datarecipient import Datarecipient
from coshsh.datasource import Datasource
from coshsh.generator import Generator
from coshsh.monitoringdetail import MonitoringDetail
from coshsh.util import setup_logging

# WHY 6000: recipes/default/templates/os_linux_default.tpl renders 11 services
# per Red Hat application, so 6,000 hosts x 1 application yields 66,000 services
# -- comfortably over the constitutional 60,000 floor without making the fixture
# so large that building the CSV dominates the measurement.
HOST_COUNT = 6000
SERVICES_PER_APP = 11
REQUIRED_SERVICES = 60000
TIME_BUDGET_SECONDS = 10.0


@pytest.mark.benchmark
class PerformanceTest(unittest.TestCase):
    """Generate a large configuration and assert the constitutional time bound."""

    def setUp(self):
        # WHY the fixture is built here and not committed: a 6,000-row CSV is
        # generated data, not a test input anyone would read or edit, and
        # committing it would put ~1 MB of noise in every diff of this repo.
        # Building it costs milliseconds and is outside the timed region.
        self.called_from_dir = os.getcwd()
        self.tests_run_in_dir = os.path.dirname(os.path.realpath(__file__))
        os.chdir(self.tests_run_in_dir)

        Application.class_factory = []
        MonitoringDetail.class_factory = []
        Contact.class_factory = []
        Datasource.class_factory = []
        Datarecipient.class_factory = []

        self.tmp_dir = tempfile.mkdtemp(prefix="coshsh_perf_")
        self.data_dir = os.path.join(self.tmp_dir, "data")
        self.objects_dir = os.path.join(self.tmp_dir, "objects")
        os.makedirs(self.data_dir)
        os.makedirs(self.objects_dir)
        self._write_csv()
        self.cookbook = os.path.join(self.tmp_dir, "perf.cfg")
        self._write_cookbook()

        setup_logging(logdir=self.tmp_dir, scrnloglevel=50)
        self.generator = Generator()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)
        os.chdir(self.called_from_dir)

    def _write_csv(self):
        """Write the hosts/applications CSV pair in the csv10.* column layout."""
        # Column layout copied from tests/recipes/test10/data/csv10.1_hosts.csv
        # and csv10.1_applications.csv so the stock "csv" datasource reads it.
        hosts = ["host_name,address,type,os,hardware,virtual,notification_period,location,department"]
        apps = ["host_name,name,type,component,version,check_period"]
        for i in range(HOST_COUNT):
            hosts.append("perf_host_%d,127.0.0.1,server,,Proliant DL380 G6,ps,7x24,rack1,perf" % i)
            apps.append("perf_host_%d,os,Red Hat,,6.2,7x24" % i)
        with open(os.path.join(self.data_dir, "perfcsv_hosts.csv"), "w") as f:
            f.write("\n".join(hosts) + "\n")
        with open(os.path.join(self.data_dir, "perfcsv_applications.csv"), "w") as f:
            f.write("\n".join(apps) + "\n")

    def _write_cookbook(self):
        # WHY git_init = no: the constitutional bound is about generating a
        # configuration, not about committing it.  "git init" plus an add/commit
        # over 6,000 host directories is dominated by git process time and would
        # measure git rather than coshsh.
        with open(self.cookbook, "w") as f:
            f.write(
                "[defaults]\n"
                "recipes = perf\n"
                "log_dir = %s\n"
                "pid_dir = %s\n"
                "\n"
                "[datasource_PERFCSV]\n"
                "type = csv\n"
                "dir = %s\n"
                "\n"
                "[recipe_perf]\n"
                "objects_dir = %s\n"
                "datasources = PERFCSV\n"
                "git_init = no\n" % (self.tmp_dir, self.tmp_dir, self.data_dir, self.objects_dir)
            )

    def test_60000_services_in_10_seconds(self):
        """The full pipeline generates >= 60,000 services within 10 seconds."""
        self.generator.set_default_log_level("info")
        self.generator.read_cookbook([self.cookbook], None, False, False)

        tic = time.time()
        self.generator.run()
        elapsed = time.time() - tic

        recipe = self.generator.get_recipe("perf")
        self.assertIsNotNone(recipe, "the perf recipe was not created")
        host_count = len(recipe.objects["hosts"])
        app_count = len(recipe.objects["applications"])
        service_count = app_count * SERVICES_PER_APP

        print(
            "\nBENCHMARK: %d hosts, %d applications, %d services in %.3f seconds"
            % (host_count, app_count, service_count, elapsed)
        )

        self.assertEqual(host_count, HOST_COUNT)
        self.assertGreaterEqual(
            service_count, REQUIRED_SERVICES,
            "fixture too small: %d services, need at least %d" % (service_count, REQUIRED_SERVICES),
        )
        self.assertLessEqual(
            elapsed, TIME_BUDGET_SECONDS,
            "constitutional bound exceeded: %d services took %.3f s, budget is %.1f s"
            % (service_count, elapsed, TIME_BUDGET_SECONDS),
        )


if __name__ == '__main__':
    unittest.main()
