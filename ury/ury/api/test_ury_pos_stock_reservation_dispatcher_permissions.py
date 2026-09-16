"""Dispatcher-level negative permission coverage for POS, stock, and reservations.

These tests deliberately use the real Frappe command dispatcher rather than
calling endpoint functions directly.  The caller is authenticated but has no
custom URY roles, so each endpoint must reject the request at its permission
boundary before touching the requested resource.
"""

import frappe
from frappe.handler import execute_cmd
from frappe.tests.utils import FrappeTestCase


PLAIN_USER = "phase4-pos-stock-reservation-plain@ury.test"


class TestPosStockReservationDispatcherPermissions(FrappeTestCase):
	"""A logged-in user without the relevant DocType permissions is rejected."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		if frappe.db.exists("User", PLAIN_USER):
			frappe.delete_doc("User", PLAIN_USER, force=True, ignore_permissions=True)
		frappe.get_doc(
			{
				"doctype": "User",
				"email": PLAIN_USER,
				"first_name": "Phase 4 Permission Test",
				"send_welcome_email": 0,
				"enabled": 1,
			}
		).insert(ignore_permissions=True)

	@classmethod
	def tearDownClass(cls):
		frappe.set_user("Administrator")
		if frappe.db.exists("User", PLAIN_USER):
			frappe.delete_doc("User", PLAIN_USER, force=True, ignore_permissions=True)
		frappe.db.commit()
		super().tearDownClass()

	def tearDown(self):
		frappe.set_user("Administrator")

	def _dispatch(self, method, **params):
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

	def test_pos_customer_creation_rejects_plain_user_through_dispatcher(self):
		self._as_plain_user()
		with self.assertRaises(frappe.PermissionError):
			self._dispatch(
				"ury.ury_pos.api.create_customer",
				customer_name="Phase 4 Unauthorized Customer",
			)

	def test_stock_transfer_rejects_plain_user_through_dispatcher(self):
		self._as_plain_user()
		with self.assertRaises(frappe.PermissionError):
			self._dispatch(
				"ury.ury.api.ury_stock_service.transfer_to_department",
				issue_authorization="missing",
				qty=1,
				branch="missing",
				company="missing",
			)

	def test_stock_receipt_rejects_plain_user_through_dispatcher(self):
		self._as_plain_user()
		with self.assertRaises(frappe.PermissionError):
			self._dispatch(
				"ury.ury.api.ury_stock_service.receive_at_department",
				transfer_movement="missing",
				qty=1,
				branch="missing",
				company="missing",
			)

	def test_stock_return_rejects_plain_user_through_dispatcher(self):
		self._as_plain_user()
		with self.assertRaises(frappe.PermissionError):
			self._dispatch(
				"ury.ury.api.ury_stock_service.return_to_central_store",
				issue_authorization="missing",
				qty=1,
				branch="missing",
				company="missing",
			)

	def test_reservation_creation_rejects_plain_user_through_dispatcher(self):
		self._as_plain_user()
		with self.assertRaises(frappe.PermissionError):
			self._dispatch(
				"ury.ury.api.ury_reservation_service.create_reservation",
				item_code="missing",
				qty=1,
				warehouse="missing",
				branch="missing",
				company="missing",
				order_ref="missing",
			)
