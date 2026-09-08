import unittest

from fabops.optimization.signature_algorithm import ablation, select_release_slot, sensitivity


class SignatureAlgorithmTests(unittest.TestCase):
    def setUp(self):
        self.lot = {"due_slot": 1, "queue_risk": 5}
        self.slots = [0, 1, 2]
        self.scenarios = [{"queue": 1}, {"queue": 4}, {"queue": 8}]

    def test_cvar_release_is_deterministic(self):
        self.assertEqual(select_release_slot(self.lot, self.slots, self.scenarios), select_release_slot(self.lot, self.slots, self.scenarios))

    def test_invalid_alpha_raises(self):
        with self.assertRaises(ValueError):
            select_release_slot(self.lot, self.slots, self.scenarios, alpha=1.0)

    def test_risk_ablation_is_executable(self):
        self.assertIn("slot", ablation(self.lot, self.slots, self.scenarios))

    def test_alpha_sensitivity_is_executable(self):
        self.assertIn("cvar", sensitivity(self.lot, self.slots, self.scenarios, 0.75))


if __name__ == "__main__":
    unittest.main()
