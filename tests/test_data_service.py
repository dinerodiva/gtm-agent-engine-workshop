import unittest

from gtm_agent import data_service


class UpdateProspectInfoTests(unittest.TestCase):
    prospect_id = "LEAD-39002"

    def setUp(self):
        self.record = data_service.PROSPECTS[self.prospect_id]
        self.original_tech_stack = list(self.record["tech_stack"])
        self.original_profile = data_service._PROFILES.get(self.prospect_id)

    def tearDown(self):
        self.record["tech_stack"] = self.original_tech_stack
        if self.original_profile is None:
            data_service._PROFILES.pop(self.prospect_id, None)
        else:
            data_service._PROFILES[self.prospect_id] = self.original_profile

    def test_update_persists_and_invalidates_cached_profile(self):
        data_service._PROFILES[self.prospect_id] = {"tech_stack": self.original_tech_stack}

        result = data_service.update_prospect_info(self.prospect_id, "Terraform")

        self.assertTrue(result["updated"])
        self.assertIn("Terraform", data_service.fetch_tech_stack(self.prospect_id))
        self.assertNotIn(self.prospect_id, data_service._PROFILES)

        repeated = data_service.update_prospect_info(self.prospect_id, "Terraform")

        self.assertEqual(repeated["tech_stack"].count("Terraform"), 1)


if __name__ == "__main__":
    unittest.main()
