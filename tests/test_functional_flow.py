import asyncio
import unittest
import json
from unittest.mock import patch, AsyncMock
import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Import the Flask app instance
from app import app
from models.data_models import BridgeRequest # For payload structure reference

class TestAPIIntegrationFlow(unittest.TestCase):

    def setUp(self):
        self.app = app # The Flask app instance
        self.client = self.app.test_client()
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        # Test case input based on "设计一座100米跨度的预应力混凝土连续梁桥"
        self.test_user_requirements = "设计一座100米跨度的预应力混凝土连续梁桥，双向四车道，位于8度抗震区"
        self.test_project_conditions = {
            "seismic_intensity": "8度",
            "road_lanes": "双向四车道"
        }
        self.test_design_constraints = {
            # "bridge_type_preference": "预应力混凝土连续梁桥", # Removed to test LLM refinement path
            "span_preference_meters": 100
        }
        self.api_payload = {
            "user_requirements": self.test_user_requirements,
            "project_conditions": self.test_project_conditions,
            "design_constraints": self.test_design_constraints # Now without bridge_type_preference
        }

        # Expected values based on our BridgeService logic for this input
        self.expected_span_m = 100.0
        # BridgeService.refine_parameters_with_knowledge will produce this for the mocked LLM output
        self.expected_bridge_type_after_refinement = "Prestressed Concrete Continuous Girder Bridge"
        self.expected_bridge_type_keywords = ["prestressed", "concrete", "continuous", "girder"]
        self.expected_min_bridge_width = 15.0 # For dual 4 lanes

    def tearDown(self):
        self.loop.close()

    @patch('services.llm_service.LLMService.analyze_text_with_failover', new_callable=AsyncMock)
    def test_e2e_api_flow(self, mock_llm_analyze):
        print(f"\n--- TestAPIIntegrationFlow: test_e2e_api_flow ---")

        # --- Step 1: Mock LLM Response ---
        mock_llm_output = {
            "bridge_type_preference": "prestressed concrete continuous beam bridge", # LLM might say "beam"
            "span_length_description": "a 100m crossing",
            "estimated_span_meters": 100.0,
            "load_requirements": "highway traffic",
            "site_terrain": "generic",
            "specific_materials": "prestressed concrete", # Important for refinement
            "budget_constraints": "medium",
            "aesthetic_preferences": "functional",
            "environmental_factors": "seismic zone 8",
            "road_lanes_description": "双向四车道"
        }
        mock_llm_analyze.return_value = (mock_llm_output, "MockLLMProvider")

        # --- Step 2: Call /api/v1/generate_design ---
        print("\nAction: Calling /api/v1/generate_design...")
        response_design = self.client.post('/api/v1/generate_design', json=self.api_payload)
        print(f"Response Status: {response_design.status_code}")
        response_design_data = response_design.get_json()

        self.assertEqual(response_design.status_code, 200, f"generate_design failed: {response_design_data.get('error', {}).get('details', response_design_data)}")
        self.assertIn("design_id", response_design_data)
        self.assertIn("design_data", response_design_data)

        actual_design_data = response_design_data["design_data"]
        self.assertIsNotNone(actual_design_data)

        # Validate that BridgeService used the refined LLM output for bridge_type
        self.assertEqual(actual_design_data.get("bridge_type"), self.expected_bridge_type_after_refinement)
        # Check with keywords as well, as the exact string might vary slightly with future refactorings of refine_parameters
        self.assertTrue(all(keyword.lower() in actual_design_data.get("bridge_type", "").lower() for keyword in self.expected_bridge_type_keywords),
                        f"Bridge type '{actual_design_data.get('bridge_type')}' doesn't match all keywords {self.expected_bridge_type_keywords}")

        self.assertAlmostEqual(actual_design_data.get("span_lengths", [0])[0], self.expected_span_m, delta=1.0)
        self.assertGreaterEqual(actual_design_data.get("bridge_width", 0), self.expected_min_bridge_width)

        materials_str_lower = str(actual_design_data.get("materials", {})).lower()
        self.assertTrue("prestressed" in materials_str_lower or "prestressing" in materials_str_lower,
                        f"Materials should mention prestressing/prestressed. Got: {materials_str_lower}")
        self.assertIn("concrete", materials_str_lower, "Materials should mention concrete")

        # --- Step 3: Call /api/v1/generate_2d_drawing ---
        print("\nAction: Calling /api/v1/generate_2d_drawing...")
        payload_2d = {"design_data": actual_design_data}
        response_2d = self.client.post('/api/v1/generate_2d_drawing', json=payload_2d)
        print(f"Response Status: {response_2d.status_code}")
        response_2d_data = response_2d.get_json()

        self.assertEqual(response_2d.status_code, 200, f"generate_2d_drawing failed: {response_2d_data.get('error')}")
        self.assertIn("drawing_id", response_2d_data)
        self.assertIn("svg_content", response_2d_data)
        self.assertTrue(response_2d_data["svg_content"].startswith("<svg"))
        self.assertIn(f"Span: {self.expected_span_m:.2f} m", response_2d_data["svg_content"])

        # --- Step 4: Call /api/v1/generate_3d_model_data ---
        print("\nAction: Calling /api/v1/generate_3d_model_data...")
        payload_3d = {"design_data": actual_design_data}
        response_3d = self.client.post('/api/v1/generate_3d_model_data', json=payload_3d)
        print(f"Response Status: {response_3d.status_code}")
        response_3d_data = response_3d.get_json()

        self.assertEqual(response_3d.status_code, 200, f"generate_3d_model_data failed: {response_3d_data.get('error')}")
        self.assertIn("model_id", response_3d_data)
        self.assertIn("model_data", response_3d_data)
        self.assertEqual(response_3d_data["format"], "json_scene_description")

        model_json = response_3d_data["model_data"]
        self.assertIn("scene_setup", model_json)
        self.assertIn("materials", model_json)
        self.assertIn("components", model_json)
        self.assertGreater(len(model_json["components"]), 0, "3D model should have components")

        found_deck = any(
            comp.get("geometry", {}).get("type") == "BoxGeometry" and
            abs(comp["geometry"].get("args", [0,0,0])[2] - self.expected_span_m) < 1.0
            for comp in model_json["components"] if comp.get("type") == "deck_box"
        ) or any (
            comp.get("geometry", {}).get("type") == "BoxGeometry" and
            abs(comp["geometry"].get("args", [0,0,0])[2] - self.expected_span_m) < 1.0
            for comp in model_json["components"] if "girder" in comp.get("type","")
        )
        self.assertTrue(found_deck, f"Could not find a main deck/girder component with span approx {self.expected_span_m}m in 3D model data.")

        print("\n--- TestAPIIntegrationFlow: test_e2e_api_flow completed successfully ---")


    @patch('services.llm_service.LLMService.analyze_text_with_failover', new_callable=AsyncMock)
    def test_llm_failure_graceful_degradation(self, mock_llm_analyze):
        print(f"\n--- TestAPIIntegrationFlow: test_llm_failure_graceful_degradation ---")
        mock_llm_analyze.return_value = ({"error": "Simulated LLM provider failure", "details": "All LLM providers down"}, "none")

        response_design = self.client.post('/api/v1/generate_design', json=self.api_payload)
        response_design_data = response_design.get_json()

        self.assertEqual(response_design.status_code, 500, "Expected 500 error due to LLM failure")
        self.assertIn("error", response_design_data)
        self.assertEqual(response_design_data.get("error"), "Failed to generate design")

        details_raw = response_design_data.get("details")
        self.assertIsNotNone(details_raw, "Details field should be present in error response")

        details_data_dict = None
        if isinstance(details_raw, str):
            try:
                details_data_dict = json.loads(details_raw)
            except json.JSONDecodeError as e:
                self.fail(f"The 'details' field was a string but not valid JSON: {details_raw}. Error: {e}")
        elif isinstance(details_raw, dict):
            details_data_dict = details_raw
        else:
            self.fail(f"The 'details' field was neither a string nor a dict. Type: {type(details_raw)}, Value: {details_raw}")

        self.assertIsInstance(details_data_dict, dict, f"Details field, after potential parsing, should be a dict. Got {type(details_data_dict)}")
        self.assertEqual(details_data_dict.get("bridge_type"), "Error - Analysis Failed",
                         f"Details.bridge_type should indicate analysis failure. Got: {details_data_dict.get('bridge_type')}")

        main_girder_details = details_data_dict.get("main_girder", {})
        self.assertIsInstance(main_girder_details, dict, f"main_girder in details should be a dict, got {type(main_girder_details)}")
        self.assertIn("Analysis failed", main_girder_details.get("error", ""),
                      "main_girder.error message missing or incorrect in details")

        print("Graceful degradation test for LLM failure passed.")


if __name__ == '__main__':
    # To run tests using PyTest:
    # 1. Ensure pytest and pytest-asyncio are installed: pip install pytest pytest-asyncio
    # 2. Navigate to the project root directory in the terminal.
    # 3. Run the command: pytest
    # Pytest will automatically discover and run tests in files named test_*.py or *_test.py.

    # To run with unittest directly (less common for async, PyTest is preferred):
    # This setup is primarily for PyTest. For `python -m unittest`, you might need a different runner for async tests.
    # However, Flask test_client handles the async nature of the endpoint when called this way.
    print("Running tests with unittest.main(). For better async support, consider using PyTest with pytest-asyncio.")
    unittest.main()

# Developer Notes:
# - This test class now uses Flask's test_client to interact with the API endpoints.
# - LLMService.analyze_text_with_failover is mocked to provide controlled outputs.
# - The e2e_api_flow test checks the sequence of API calls and validates key parts of their responses.
# - The llm_failure_graceful_degradation test ensures the system handles LLM failures by returning appropriate error responses.
# - This moves away from testing BridgeService internals directly and focuses on API contract and integration.
