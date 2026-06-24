"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  GRAVITY V16.0 PRO — TEST SUITE: strategic_memory                           ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import unittest
import tempfile

# Aislar el módulo en un DB temporal para tests
_orig_db = None


def setUpModule():
    """Redirige el DB a un archivo temporal antes de importar el módulo."""
    global _orig_db
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import core.strategic_memory as sm

    _orig_db = sm.DB_PATH
    sm.DB_PATH = os.path.join(tempfile.gettempdir(), "_gravity_test_memory.db")
    sm._init_db()


def tearDownModule():
    """Limpia el DB temporal."""
    import core.strategic_memory as sm

    try:
        if os.path.isfile(sm.DB_PATH):
            os.remove(sm.DB_PATH)
    except Exception:
        pass
    sm.DB_PATH = _orig_db


class TestRecordDecision(unittest.TestCase):
    def setUp(self):
        import core.strategic_memory as sm

        self.sm = sm

    def test_record_returns_positive_id(self):
        did = self.sm.record_decision(
            category=self.sm.CAT_SYSTEM,
            title="Test decision",
            description="desc",
        )
        self.assertGreater(did, 0)

    def test_record_and_retrieve(self):
        did = self.sm.record_decision(
            category=self.sm.CAT_CONTENT,
            title="Content test",
            description="testing content category",
        )
        row = self.sm.get_decision_by_id(did)
        self.assertIsNotNone(row)
        self.assertEqual(row["title"], "Content test")
        self.assertEqual(row["outcome"], self.sm.OUTCOME_PENDING)

    def test_update_outcome_success(self):
        did = self.sm.record_decision(self.sm.CAT_MONETIZE, "Monetize test")
        ok = self.sm.update_outcome(
            did, self.sm.OUTCOME_SUCCESS, "everything worked", impact_score=0.8
        )
        self.assertTrue(ok)
        row = self.sm.get_decision_by_id(did)
        self.assertEqual(row["outcome"], self.sm.OUTCOME_SUCCESS)
        self.assertAlmostEqual(row["impact_score"], 0.8, places=2)

    def test_update_outcome_invalid_rejected(self):
        did = self.sm.record_decision(self.sm.CAT_SYSTEM, "Invalid outcome test")
        ok = self.sm.update_outcome(did, "INVALID_OUTCOME")
        self.assertFalse(ok)

    def test_get_recent_decisions_limit(self):
        for i in range(5):
            self.sm.record_decision(self.sm.CAT_SECURITY, f"Batch decision {i}")
        rows = self.sm.get_recent_decisions(3)
        self.assertLessEqual(len(rows), 3)

    def test_get_recent_decisions_category_filter(self):
        self.sm.record_decision(self.sm.CAT_EVOLUTION, "Evolution decision")
        rows = self.sm.get_recent_decisions(10, category=self.sm.CAT_EVOLUTION)
        for r in rows:
            self.assertEqual(r["category"], self.sm.CAT_EVOLUTION)


class TestPatterns(unittest.TestCase):
    def setUp(self):
        import core.strategic_memory as sm

        self.sm = sm

    def test_upsert_pattern_creates(self):
        self.sm.upsert_pattern("test:module_error:bounty", "3")
        patterns = self.sm.get_patterns(prefix="test:module_error")
        self.assertTrue(
            any(p["pattern_key"] == "test:module_error:bounty" for p in patterns)
        )

    def test_upsert_pattern_increments_hits(self):
        key = "test:incr_pattern"
        self.sm.upsert_pattern(key, "v1")
        self.sm.upsert_pattern(key, "v2")
        self.sm.upsert_pattern(key, "v3")
        patterns = self.sm.get_patterns(prefix=key)
        match = next((p for p in patterns if p["pattern_key"] == key), None)
        self.assertIsNotNone(match)
        self.assertGreaterEqual(match["hits"], 3)


class TestSummary(unittest.TestCase):
    def setUp(self):
        import core.strategic_memory as sm

        self.sm = sm

    def test_summary_returns_dict(self):
        summary = self.sm.get_summary(30)
        self.assertIn("total_decisions", summary)
        self.assertIn("by_outcome", summary)
        self.assertIn("by_category", summary)

    def test_get_brain_snapshot_returns_string(self):
        snap = self.sm.get_brain_snapshot()
        self.assertIsInstance(snap, str)
        self.assertGreater(len(snap), 10)


if __name__ == "__main__":
    unittest.main(verbosity=2)
