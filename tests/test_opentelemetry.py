import unittest
from unittest import mock

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider, ReadableSpan
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SimpleSpanProcessor, SpanExporter, SpanExportResult
from opentelemetry.sdk.resources import Resource
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

# In-memory exporter for testing
class InMemorySpanExporter(SpanExporter):
    """Implementation of :class:`SpanExporter` that stores spans in memory."""

    def __init__(self):
        self._finished_spans = []
        self._stopped = False

    def export(self, spans: tuple[ReadableSpan, ...]) -> SpanExportResult:
        if self._stopped:
            return SpanExportResult.FAILURE
        self._finished_spans.extend(spans)
        return SpanExportResult.SUCCESS

    def shutdown(self) -> None:
        self._stopped = True

    def get_finished_spans(self) -> tuple[ReadableSpan, ...]:
        return tuple(self._finished_spans)

    def clear(self) -> None:
        self._finished_spans = []


class OpenTelemetryTestCase(unittest.TestCase):
    def setUp(self):
        self.resource = Resource.create({"service.name": "coshsh-test"})
        self.memory_exporter = InMemorySpanExporter()

        # Using SimpleSpanProcessor for tests to ensure spans are processed immediately
        # BatchSpanProcessor might delay processing, making assertions harder.
        self.span_processor = SimpleSpanProcessor(self.memory_exporter)

        self.tracer_provider = TracerProvider(resource=self.resource)
        self.tracer_provider.add_span_processor(self.span_processor)

        # Store the original tracer provider to restore it in tearDown
        self.original_tracer_provider = trace.get_tracer_provider()
        trace.set_tracer_provider(self.tracer_provider)

        self.tracer = trace.get_tracer("coshsh.test_tracer")

    def tearDown(self):
        # Shutdown the processor and provider
        # For SimpleSpanProcessor, shutdown might not be strictly necessary for flushing
        # but it's good practice. For BatchSpanProcessor, it's crucial.
        self.span_processor.shutdown()
        # No explicit shutdown for TracerProvider in SDK, processor shutdown handles exporter.

        # Restore the original tracer provider
        trace.set_tracer_provider(self.original_tracer_provider)

        self.memory_exporter.clear()

    def get_finished_spans(self) -> tuple[ReadableSpan, ...]:
        # Force flush if using BatchSpanProcessor, not strictly needed for SimpleSpanProcessor
        # self.tracer_provider.force_flush()
        return self.memory_exporter.get_finished_spans()


# Example of how to import Generator for testing
# This will likely require adjustments based on actual project structure and imports
from coshsh.generator import Generator
from coshsh.configparser import CoshshConfigParser # Assuming this is the correct import

class TestGeneratorInstrumentation(OpenTelemetryTestCase):

    @mock.patch('coshsh.configparser.CoshshConfigParser')
    @mock.patch('coshsh.util.setup_logging') # Mock logging setup
    def test_read_cookbook_creates_span(self, mock_setup_logging, MockCoshshConfigParser):
        # Arrange
        mock_parser_instance = MockCoshshConfigParser.return_value
        mock_parser_instance._sections = {'recipe_test': []} # Simulate some content
        mock_parser_instance.sections.return_value = ['recipe_test']
        mock_parser_instance.items.return_value = [('name', 'test_recipe_item')]

        generator = Generator()

        # Act
        # Minimal valid inputs. Actual file paths not needed due to mocking.
        # The method itself has quite a bit of logic, so more mocking might be needed
        # for deeper parts of it, or if it tries to access attributes of the mocked items.
        try:
            generator.read_cookbook(
                cookbook_files=["mock_cookbook.cfg"],
                default_recipe="test_recipe_item",
                force=False,
                safe_output=False
            )
        except Exception as e:
            # Catch exceptions during the call to understand failures better
            # print(f"Error during generator.read_cookbook: {e}")
            pass # Allow test to proceed to span assertions, or fail if critical

        # Assert
        finished_spans = self.get_finished_spans()

        self.assertGreater(len(finished_spans), 0, "No spans were created.")

        read_cookbook_span = next((s for s in finished_spans if s.name == "Generator.read_cookbook"), None)
        self.assertIsNotNone(read_cookbook_span, "Span 'Generator.read_cookbook' not found.")

        if read_cookbook_span:
            self.assertEqual(read_cookbook_span.resource.attributes["service.name"], "coshsh-test")

            # Check for some expected events
            expected_events = [
                "Read cookbook files",
                "Processed mappings",
                "Processed datarecipient_configs",
                "Processed datasource_configs",
                "Processed recipe_configs"
            ]
            actual_event_names = [event.name for event in read_cookbook_span.events]
            for event_name in expected_events:
                self.assertIn(event_name, actual_event_names, f"Event '{event_name}' not found in span.")

# Need to import Recipe and potentially other classes for mocking
from coshsh.recipe import Recipe
# Datasource might be needed if Recipe.collect interacts with it directly
# from coshsh.datasource import Datasource

class TestRecipeInstrumentation(OpenTelemetryTestCase):

    @mock.patch('coshsh.util.switch_logging') # Called in Recipe.__init__
    @mock.patch('coshsh.recipe.Recipe.set_recipe_sys_path') # Called in Recipe.__init__
    @mock.patch('coshsh.recipe.Recipe.unset_recipe_sys_path') # Called in Recipe.__del__ potentially
    @mock.patch('coshsh.recipe.Recipe.init_ds_dr_class_factories') # Called in Recipe.__init__
    @mock.patch('coshsh.recipe.Recipe.init_item_class_factories') # Called in Recipe.__init__
    @mock.patch('coshsh.jinja2_extensions.global_environ') # For Jinja2 env setup in Recipe
    def test_recipe_collect_creates_span(self, mock_j2_glob_env, mock_init_item_cf, mock_init_ds_dr_cf, mock_unset_sys_path, mock_set_sys_path, mock_switch_logging):
        # Arrange
        # Basic kwargs for Recipe constructor. Many are path-related and might not need
        # to exist if methods that use them are mocked or not called.
        recipe_kwargs = {
            "name": "test_recipe",
            "force": False,
            "safe_output": False,
            "pid_dir": "/tmp",
            "templates_dir": "mock_templates/",
            "classes_dir": "mock_classes/",
            "coshsh_config_mappings": {},
            # Add other minimal required kwargs for Recipe.__init__
        }

        # Mocking datasources for the collect method
        mock_datasource = mock.MagicMock()
        mock_datasource.name = "mock_ds"
        # Mock methods called on datasource instance within Recipe.collect
        mock_datasource.open.return_value = None
        mock_datasource.read.return_value = None # Simulate no new objects
        mock_datasource.close.return_value = None

        # Instantiate the recipe
        # We mock many __init__ internal calls to simplify setup
        recipe = Recipe(**recipe_kwargs)
        recipe.datasources = [mock_datasource] # Assign the mocked datasource
        recipe.datasource_filters = {} # Initialize datasource_filters
        recipe.objects = { # Initialize objects dictionary
            'hosts': {}, 'applications': {}, 'details': {},
            # Add other keys as accessed by Recipe.collect if any
        }


        # Act
        try:
            recipe.collect()
        except Exception as e:
            # print(f"Error during recipe.collect: {e}")
            pass

        # Assert
        finished_spans = self.get_finished_spans()
        self.assertGreater(len(finished_spans), 0, "No spans were created by Recipe.collect.")

        recipe_collect_span = next((s for s in finished_spans if s.name == "Recipe.collect"), None)
        self.assertIsNotNone(recipe_collect_span, "Span 'Recipe.collect' not found.")

        if recipe_collect_span:
            self.assertEqual(recipe_collect_span.resource.attributes["service.name"], "coshsh-test")
            # Verify it's a child of some other span if we were to create a parent span in test
            # For now, just check its own properties.
            # Check parent_id if a parent span was created explicitly in the test.
            # Here, it would be a root span unless Recipe.collect is called within another traced function.

if __name__ == '__main__':
    unittest.main()
