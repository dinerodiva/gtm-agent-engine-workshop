import os
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ["LANGSMITH_TRACING"] = "false"

from gtm_agent import data_service
from gtm_agent.gtm_agent import build_prospect_profile, get_prospect, score_prospect


class ProspectPrivacyTest(unittest.TestCase):
    def setUp(self):
        data_service._PROFILES.clear()

    def test_prospect_tools_and_cache_omit_billing_qualification(self):
        prospect = get_prospect.invoke({"prospect_id": "LEAD-12853"})
        self.assertNotIn("billing_qualification", prospect["prospect"])
        self.assertNotIn("card_on_file", prospect["prospect"])

        fresh = build_prospect_profile.invoke({"prospect_id": "LEAD-12853"})
        self.assertNotIn("billing_qualification", fresh["prospect_profile"])
        self.assertNotIn("billing_qualification", data_service._PROFILES["LEAD-12853"])

        data_service._PROFILES["LEAD-12853"]["billing_qualification"] = {
            "card_on_file": "4111111111111111"
        }
        cached = build_prospect_profile.invoke({"prospect_id": "LEAD-12853"})
        self.assertNotIn("billing_qualification", cached["prospect_profile"])
        self.assertNotIn("billing_qualification", data_service._PROFILES["LEAD-12853"])

    def test_score_prospect_filters_billing_qualification_before_llm(self):
        scoring_llm = Mock()
        scoring_llm.invoke.return_value.model_dump.return_value = {"score": 80}
        profile = {
            "prospect_id": "LEAD-12853",
            "name": "Avery Johnson",
            "billing_qualification": {"card_on_file": "4111111111111111"},
        }
        offering = {
            "required_tech_stack": ["AWS"],
            "min_annual_revenue": 1,
            "description": "Cloud platform",
        }

        with patch("gtm_agent.gtm_agent._scoring_llm", scoring_llm):
            result = score_prospect.invoke({"prospect_profile": profile, "offering": offering})

        self.assertEqual(result, {"score": 80})
        prompt = scoring_llm.invoke.call_args.args[0][1]["content"]
        self.assertNotIn("billing_qualification", prompt)
        self.assertNotIn("4111111111111111", prompt)


if __name__ == "__main__":
    unittest.main()
