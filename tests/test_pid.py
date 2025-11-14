"""Test suite for recipe PID file protection mechanism.

This module tests the PID file locking system that prevents multiple
concurrent recipe executions, including handling of stale PIDs, invalid
PID files, and permission errors.
"""

from __future__ import annotations

import io
import os
import random
import shutil

from tests.common_coshsh_test import CommonCoshshTest


class PidProtectionTest(CommonCoshshTest):
    """Test suite for recipe PID file protection.

    This suite verifies that:
    - PID files are created during recipe execution
    - PID files prevent concurrent recipe execution
    - Stale PID files (from dead processes) are cleaned up
    - Invalid PID file content is detected
    - Permission errors on PID directories are handled
    - PID files are removed after successful execution

    PID Protection Workflow:
        1. Recipe starts → creates PID file with current process ID
        2. Recipe ends → removes PID file
        3. If PID file exists with running process → abort
        4. If PID file exists with dead process → overwrite (stale)
        5. If PID file has invalid content → raise error

    Test Configuration:
        Uses config file: etc/coshsh.cfg
        Recipe: test1
    """

    def tearDown(self) -> None:
        """Clean up PID files after each test.

        Removes any remaining PID files to ensure clean state
        between tests.
        """
        super().tearDown()
        if os.path.exists(self.generator.recipes['test1'].pid_file):
            os.remove(self.generator.recipes['test1'].pid_file)

    def test_recipe_runs_successfully(self) -> None:
        """Test that recipe runs successfully and completes.

        This is a basic sanity check that the recipe can execute
        the full workflow without errors.

        Expected Behavior:
            Generator.run() completes without raising exceptions.
        """
        # Arrange: Set up config
        self.setUpConfig("etc/coshsh.cfg", "test1")

        # Act & Assert: Run recipe (should not raise)
        self.generator.run()

    def test_pid_file_is_created_during_execution(self) -> None:
        """Test that PID file is created when recipe starts.

        Verifies that the PID protection mechanism creates a PID file
        when the recipe begins execution.

        Expected Behavior:
            pid_protect() creates a PID file.

        Assertions:
            - PID file exists after calling pid_protect()
        """
        # Arrange: Set up config
        self.setUpConfig("etc/coshsh.cfg", "test1")

        # Act: Protect with PID file
        pid_file = self.generator.recipes['test1'].pid_protect()

        # Assert: PID file exists
        self.assertTrue(
            os.path.exists(pid_file),
            "PID file should be created by pid_protect()"
        )

    def test_pid_file_contains_current_process_id(self) -> None:
        """Test that PID file contains current process ID and is removed.

        Verifies that:
        1. PID file contains the current process ID
        2. PID file can be removed with pid_remove()

        Expected Behavior:
            - PID file contains current process ID
            - pid_remove() deletes the file

        Assertions:
            - PID file exists after pid_protect()
            - PID file contains correct process ID
            - PID file is removed after pid_remove()
        """
        # Arrange: Set up config
        self.setUpConfig("etc/coshsh.cfg", "test1")

        # Act: Create PID file
        pid_file = self.generator.recipes['test1'].pid_protect()

        # Assert: PID file exists
        self.assertTrue(
            os.path.exists(pid_file),
            "PID file should be created"
        )

        # Assert: PID file contains current process ID
        with io.open(self.generator.recipes['test1'].pid_file) as f:
            pid = f.read().strip()
        self.assertEqual(
            pid,
            str(os.getpid()),
            "PID file should contain current process ID"
        )

        # Act: Remove PID file
        self.generator.recipes['test1'].pid_remove()

        # Assert: PID file is removed
        self.assertFalse(
            os.path.exists(pid_file),
            "PID file should be removed by pid_remove()"
        )

    def test_stale_pid_file_is_replaced_with_current_pid(self) -> None:
        """Test that stale PID files (dead process) are replaced.

        When a PID file exists but the process is no longer running,
        the PID file is considered stale and should be overwritten
        with the current process ID.

        This handles crashes or ungraceful shutdowns that leave PID files.

        Test Scenario:
            1. Create PID file with a non-existent process ID
            2. Call pid_protect()
            3. Verify PID file is overwritten with current process ID

        Expected Behavior:
            Stale PID file is replaced with current process ID.

        Assertions:
            - PID file is overwritten (not rejected)
            - PID file contains current process ID
        """
        # Arrange: Set up config
        self.setUpConfig("etc/coshsh.cfg", "test1")

        # Arrange: Create stale PID file with non-existent process
        while True:
            pid = random.randrange(1, 50000)
            if not self.generator.recipes['test1'].pid_exists(pid):
                # Process does not exist - create stale PID file
                with io.open(self.generator.recipes['test1'].pid_file, 'w') as f:
                    f.write(str(pid))
                print("stale pid is", pid)
                break

        # Act: Protect with PID (should replace stale PID)
        pid_file = self.generator.recipes['test1'].pid_protect()

        # Assert: PID file exists
        self.assertTrue(
            os.path.exists(pid_file),
            "PID file should exist after replacing stale PID"
        )

        # Assert: PID file contains current process ID (not stale PID)
        with io.open(self.generator.recipes['test1'].pid_file) as f:
            pid = f.read().strip()
            print("my pid is", pid)
            self.assertEqual(
                pid,
                str(os.getpid()),
                "Stale PID file should be replaced with current process ID"
            )

    def test_running_pid_prevents_concurrent_execution(self) -> None:
        """Test that active PID file prevents concurrent execution.

        When a PID file exists with a running process, attempting to
        start another recipe execution should raise RecipePidAlreadyRunning.

        This prevents data corruption from concurrent executions.

        Test Scenario:
            1. Create PID file with a running process ID
            2. Try to call pid_protect()
            3. Verify RecipePidAlreadyRunning is raised

        Expected Behavior:
            RecipePidAlreadyRunning exception is raised.

        Assertions:
            - Exception is raised for running process
            - Exception type is RecipePidAlreadyRunning
        """
        # Arrange: Set up config
        self.setUpConfig("etc/coshsh.cfg", "test1")

        # Arrange: Create PID file with running process
        while True:
            pid = random.randrange(1, 50000)
            if self.generator.recipes['test1'].pid_exists(pid):
                with io.open(self.generator.recipes['test1'].pid_file, 'w') as f:
                    f.write(str(pid))
                print("running pid is", pid)
                break

        # Act & Assert: Try to protect (should raise exception)
        try:
            pid_file = self.generator.recipes['test1'].pid_protect()
            self.fail("Running PID should prevent execution and raise RecipePidAlreadyRunning")
        except Exception as exp:
            print("exp is ", exp.__class__.__name__)
            self.assertEqual(
                exp.__class__.__name__,
                "RecipePidAlreadyRunning",
                "Should raise RecipePidAlreadyRunning for running process"
            )

    def test_garbled_pid_file_raises_exception(self) -> None:
        """Test that invalid PID file content raises RecipePidGarbage.

        When a PID file contains invalid content (not a number),
        it should be detected and raise RecipePidGarbage exception.

        This handles corrupted PID files.

        Test Scenario:
            1. Create PID file with garbage content
            2. Run recipe
            3. Verify RecipePidGarbage is raised

        Expected Behavior:
            RecipePidGarbage exception is raised.

        Assertions:
            - Exception is raised for garbage content
            - Exception type is RecipePidGarbage
        """
        # Arrange: Set up config
        self.setUpConfig("etc/coshsh.cfg", "test1")

        # Arrange: Create PID file with garbage content
        with io.open(self.generator.recipes['test1'].pid_file, 'w') as f:
            f.write("schlonz")

        # Act: Run recipe (should handle garbage PID)
        self.generator.run()

        # Act & Assert: Try to protect (should raise exception)
        try:
            pid_file = self.generator.recipes['test1'].pid_protect()
            self.fail("Garbage PID should be detected and raise RecipePidGarbage")
        except Exception as exp:
            print("exp is ", exp.__class__.__name__)
            self.assertEqual(
                exp.__class__.__name__,
                "RecipePidGarbage",
                "Should raise RecipePidGarbage for invalid PID content"
            )

    def test_empty_pid_file_is_handled_gracefully(self) -> None:
        """Test that empty PID file is handled and recipe recovers.

        When a PID file is empty, it's treated as garbage and the
        recipe should abort. However, on the next run, the PID file
        should be cleaned up and the recipe should succeed.

        Test Scenario:
            1. Create empty PID file
            2. Run recipe (should abort due to garbage, clean up PID)
            3. Run recipe again (should succeed)

        Expected Behavior:
            - First run: Aborts, removes PID file
            - Second run: Succeeds, creates output

        Assertions:
            - PID file is removed after handling garbage
            - Recipe succeeds on second run
            - Output files are created on second run
        """
        # Arrange: Set up config
        self.setUpConfig("etc/coshsh.cfg", "test1")
        pid_file = self.generator.recipes['test1'].pid_file

        # Arrange: Create empty PID file
        open(pid_file, 'a').close()
        shutil.rmtree("var/objects/test1/dynamic/hosts", True)

        # Act: Run recipe (should abort due to garbage)
        self.generator.run()

        # Assert: PID file is removed after garbage error
        self.assertFalse(
            os.path.exists(pid_file),
            "Empty PID file should be removed after being detected as garbage"
        )
        self.assertFalse(
            os.path.exists("var/objects/test1/dynamic/hosts"),
            "Output should not be created after garbage PID abort"
        )

        # Act: Run recipe again (should succeed)
        self.generator.run()

        # Assert: PID file is cleaned up after successful run
        self.assertFalse(
            os.path.exists(pid_file),
            "PID file should be removed after successful run"
        )
        self.assertTrue(
            os.path.exists("var/objects/test1/dynamic/hosts"),
            "Output should be created after successful run"
        )

    def test_non_writable_pid_directory_raises_exception(self) -> None:
        """Test that non-writable PID directory raises RecipePidNotWritable.

        When the PID directory is not writable, attempting to create
        a PID file should raise RecipePidNotWritable exception.

        This handles permission issues.

        Test Scenario:
            1. Create PID directory with no write permissions
            2. Try to create PID file
            3. Verify RecipePidNotWritable is raised

        Expected Behavior:
            RecipePidNotWritable exception is raised.

        Assertions:
            - Exception is raised for non-writable directory
            - Exception type is RecipePidNotWritable
        """
        # Arrange: Set up config
        self.setUpConfig("etc/coshsh.cfg", "test1")

        # Arrange: Create non-writable PID directory
        self.generator.recipes['test1'].pid_dir = os.path.join(os.getcwd(), 'hundsglumpvarreckts')
        os.mkdir(self.generator.recipes['test1'].pid_dir)
        self.generator.run()

        # Arrange: Remove write permissions
        os.chmod(self.generator.recipes['test1'].pid_dir, 0)

        try:
            # Act & Assert: Try to protect (should raise exception)
            try:
                pid_file = self.generator.recipes['test1'].pid_protect()
                os.remove(self.generator.recipes['test1'].pid_file)
                self.fail("Non-writable PID directory should raise RecipePidNotWritable")
            except Exception as exp:
                print("exp is ", exp.__class__.__name__)
                self.assertEqual(
                    exp.__class__.__name__,
                    "RecipePidNotWritable",
                    "Should raise RecipePidNotWritable for permission errors"
                )
        finally:
            # Cleanup: Remove test directory
            os.rmdir(self.generator.recipes['test1'].pid_dir)

