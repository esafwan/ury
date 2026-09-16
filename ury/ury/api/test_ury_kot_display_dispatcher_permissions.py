"""Dispatcher-level negative permission coverage for five KOT endpoints.

This batch deliberately covers only the KOT display/reprint endpoints that
were not exercised through ``frappe.handler.execute_cmd`` by the existing
Guest, manager, or branch permission suites.  Each test uses a real
authenticated Employee user and the real dispatcher, so decorator routing,
HTTP-method validation, argument binding, and the endpoint's own permission
boundary all remain in the path under test.
"""

import frappe
from frappe.handler import execute_cmd
from frappe.tests.utils import FrappeTestCase

PLAIN_USER = "phase4-kot-dispatcher-plain-user@ury.test"
BRANCH_NAME = "Phase4 KOT Dispatcher Branch"


class TestKotDispatcherNegativePermissions(FrappeTestCase):
	"""An unprivileged authenticated caller is rejected by all five APIs."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")

		if not frappe.db.exists("Branch", BRANCH_NAME):
			branch = frappe.get_doc({"doctype": "Branch", "branch": BRANCH_NAME})
			branch.flags.ignore_mandatory = True
			branch.insert(ignore_permissions=True)
		if frappe.db.exists("User", PLAIN_USER):
			frappe.delete_doc("User", PLAIN_USER, force=True, ignore_permissions=True)
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": PLAIN_USER,
				"first_name": "Phase4 KOT Dispatcher",
				"send_welcome_email": 0,
				"enabled": 1,
			}
		).insert(ignore_permissions=True)
		if frappe.db.exists("Role", "Employee"):
			user.add_roles("Employee")
		branch = frappe.get_doc("Branch", BRANCH_NAME)
		if not any(row.user == user.name for row in branch.get("user") or []):
			branch.append("user", {"user": user.name})
			branch.save(ignore_permissions=True)

		cls.kot_name = frappe.db.get_value("URY KOT", {}, "name")
		if not cls.kot_name:
			kot = frappe.get_doc(
				{
					"doctype": "URY KOT",
					"naming_series": "KOT-PHASE4-DISPATCH-.####",
					"date": frappe.utils.nowdate(),
					"type": "New Order",
					"order_status": "Ready For Prepare",
					"branch": BRANCH_NAME,
				}
			)
			kot.flags.ignore_mandatory = True
			kot.insert(ignore_permissions=True)
			cls.kot_name = kot.name

		cls.invoice_name = frappe.db.get_value("POS Invoice", {}, "name")
		if not cls.invoice_name:
			raise AssertionError("A POS Invoice fixture is required for reprint_kot")

	@classmethod
	def tearDownClass(cls):
		frappe.set_user("Administrator")
		super().tearDownClass()

	def tearDown(self):
		frappe.set_user("Administrator")

	def _dispatch(self, method, **params):
		"""Execute a whitelisted API exactly as Frappe's request dispatcher does."""
		previous_form_dict = frappe.local.form_dict
		previous_request = getattr(frappe.local, "request", None)
		frappe.local.form_dict = frappe._dict(params)
		frappe.local.request = frappe._dict(method="POST")
		try:
			return execute_cmd(method)
		finally:
			frappe.local.form_dict = previous_form_dict
			frappe.local.request = previous_request

	def _as_plain_user(self):
		frappe.set_user(PLAIN_USER)

	def test_serve_kot_rejects_plain_employee_through_dispatcher(self):
		self._as_plain_user()
		with self.assertRaises(frappe.PermissionError):
			self._dispatch("ury.ury.api.ury_kot_display.serve_kot", name=self.kot_name)

	def test_confirm_cancel_kot_rejects_plain_employee_through_dispatcher(self):
		self._as_plain_user()
		with self.assertRaises(frappe.PermissionError):
			self._dispatch(
				"ury.ury.api.ury_kot_display.confirm_cancel_kot",
				name=self.kot_name,
			)

	def test_kot_list_rejects_plain_employee_through_dispatcher(self):
		self._as_plain_user()
		with self.assertRaises(frappe.PermissionError):
			self._dispatch("ury.ury.api.ury_kot_display.kot_list")

	def test_served_kot_list_rejects_plain_employee_through_dispatcher(self):
		self._as_plain_user()
		with self.assertRaises(frappe.PermissionError):
			self._dispatch("ury.ury.api.ury_kot_display.served_kot_list")

	def test_reprint_kot_rejects_plain_employee_through_dispatcher(self):
		self._as_plain_user()
		with self.assertRaises(frappe.PermissionError):
			self._dispatch(
				"ury.ury.api.ury_kot_reprint.reprint_kot",
				invoice_number=self.invoice_name,
			)
