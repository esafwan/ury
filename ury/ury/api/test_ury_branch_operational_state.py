import unittest
from datetime import datetime
from unittest.mock import patch

import frappe

from ury.ury.api.ury_branch_operational_state import resolve_branch_operational_state


class TestBranchOperationalState(unittest.TestCase):
	def setUp(self):
		patcher = patch("ury.ury.api.ury_branch_operational_state._", side_effect=lambda message, *args, **kwargs: message)
		patcher.start()
		self.addCleanup(patcher.stop)

	@patch("ury.ury.api.ury_branch_operational_state.getBranch", return_value="Main")
	@patch("ury.ury.api.ury_branch_operational_state.frappe")
	def test_missing_schedule_fails_closed(self, frappe_mock, _get_branch):
		frappe_mock.db.get_value.return_value = None
		result = resolve_branch_operational_state(at=datetime(2026, 9, 7, 12))
		frappe_mock.db.get_value.assert_called_once_with(
			"URY Branch Operating Schedule",
			{"branch": "Main"},
			["name", "enabled"],
			as_dict=True,
		)
		self.assertEqual(result["primary_phase"], "NOT_CONFIGURED")
		self.assertEqual(result["health"], "WARNING")

	@patch("ury.ury.api.ury_branch_operational_state.getBranch", return_value="Main")
	@patch("ury.ury.api.ury_branch_operational_state.frappe")
	def test_requested_branch_schedule_lookup_uses_branch_field(self, frappe_mock, _get_branch):
		frappe_mock.get_roles.return_value = ["System Manager"]
		frappe_mock.db.get_value.side_effect = [None, None]
		result = resolve_branch_operational_state(branch="Downtown", at=datetime(2026, 9, 7, 12))
		frappe_mock.db.get_value.assert_any_call(
			"URY Branch Operating Schedule",
			{"branch": "Downtown"},
			["name", "enabled"],
			as_dict=True,
		)
		self.assertEqual(result["branch"], "Downtown")
		self.assertEqual(result["primary_phase"], "NOT_CONFIGURED")

	@patch("ury.ury.api.ury_branch_operational_state.getBranch", return_value="Main")
	@patch("ury.ury.api.ury_branch_operational_state.frappe")
	def test_all_branch_is_rejected_for_single_branch_state(self, frappe_mock, _get_branch):
		frappe_mock.PermissionError = frappe.PermissionError
		frappe_mock.throw.side_effect = frappe.PermissionError
		with self.assertRaises(frappe.PermissionError):
			resolve_branch_operational_state(branch="all", at=datetime(2026, 9, 7, 12))
		frappe_mock.db.get_value.assert_not_called()

	@patch("ury.ury.api.ury_branch_operational_state.getBranch", return_value="Main")
	@patch("ury.ury.api.ury_branch_operational_state.frappe")
	def test_active_service_is_open(self, frappe_mock, _get_branch):
		frappe_mock.db.get_value.side_effect = [{"name": "Main", "enabled": 1}, None]
		frappe_mock.get_all.return_value = [{"service_name": "Lunch", "open_time": "10:00:00", "close_time": "14:00:00", "enabled": 1}]
		result = resolve_branch_operational_state(at=datetime(2026, 9, 7, 12))
		self.assertTrue(result["is_open"])
		self.assertEqual(result["active_services"], ["Lunch"])
		self.assertEqual(result["primary_phase"], "SERVICE_OPEN")

	@patch("ury.ury.api.ury_branch_operational_state.getBranch", return_value="Main")
	@patch("ury.ury.api.ury_branch_operational_state.frappe")
	def test_closed_exception_wins(self, frappe_mock, _get_branch):
		frappe_mock.db.get_value.side_effect = [{"name": "Main", "enabled": 1}, {"is_closed": 1, "reason": "Holiday"}]
		result = resolve_branch_operational_state(at=datetime(2026, 9, 7, 12))
		self.assertEqual(result["state"], "CLOSED")
		self.assertEqual(result["reason"], "Holiday")
