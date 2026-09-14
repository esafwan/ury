# Copyright (c) 2026, Tridz Technologies Pvt. Ltd. and contributors
# See license.txt

"""V3-73/B02 tests: POS stock authority feature flag read path, and the
submit-time verification gate that lets a flag-on invoice through only once
every produced KOT item on it has a real, POSTED fulfilment posting intent
(a submitted Stock Entry) behind it.

These are static/unit tests using mocks -- no bench/site required to reason
about them, but they follow this repo's existing FrappeTestCase + mock
pattern (see ury/ury/doctype/ury_order/test_ury_order.py) so they run
under `bench run-tests` in a real environment.
"""

from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from ury.ury.api.ury_feature_flags import (
    is_pos_stock_authority_flag_enabled,
    maybe_wire_fulfilment_on_submit,
)


class TestPosStockAuthorityFlagDefaultsSafe(FrappeTestCase):
    """The single most important test in this task: the flag must default
    to False/off whenever it is unset, or whenever reading it fails for any
    reason (missing doctype, DB error, etc). It must never fail open."""

    @patch("ury.ury.api.ury_feature_flags.frappe.db.get_single_value")
    def test_flag_defaults_false_when_unset(self, mock_get_single_value):
        mock_get_single_value.return_value = 0
        self.assertFalse(is_pos_stock_authority_flag_enabled())

    @patch("ury.ury.api.ury_feature_flags.frappe.db.get_single_value")
    def test_flag_defaults_false_when_field_missing_none(self, mock_get_single_value):
        # get_single_value returns None if the field/doctype doesn't resolve
        mock_get_single_value.return_value = None
        self.assertFalse(is_pos_stock_authority_flag_enabled())

    @patch("ury.ury.api.ury_feature_flags.frappe.db.get_single_value")
    def test_flag_fails_closed_on_missing_doctype_or_db_error(self, mock_get_single_value):
        # Simulate the doctype not existing yet / any DB-level error.
        mock_get_single_value.side_effect = Exception("DocType URY Feature Flags not found")
        self.assertFalse(is_pos_stock_authority_flag_enabled())

    @patch("ury.ury.api.ury_feature_flags.frappe.db.get_single_value")
    def test_flag_true_only_when_explicitly_enabled(self, mock_get_single_value):
        # This is the ONLY case that should return True -- proves the
        # function is capable of reporting "on" so the flag-on branch is
        # reachable and testable, without that capability implying it is
        # ever true by default anywhere in shipped code.
        mock_get_single_value.return_value = 1
        self.assertTrue(is_pos_stock_authority_flag_enabled())

    @patch("ury.ury.api.ury_feature_flags.frappe.db.get_single_value")
    def test_flag_accepts_optional_scope_args_without_changing_default(self, mock_get_single_value):
        mock_get_single_value.return_value = 0
        self.assertFalse(
            is_pos_stock_authority_flag_enabled(company="Acme Co", branch="Main Branch")
        )


class TestMaybeWireFulfilmentOnSubmit(FrappeTestCase):
    """B02: flag-on submit-time verification that real Stock Entries were
    posted for every produced KOT item on the invoice, added on top of the
    accepted flag-read path."""

    @patch("ury.ury.api.ury_feature_flags.is_pos_stock_authority_flag_enabled")
    @patch("ury.ury.api.ury_feature_flags._verify_fulfilment_posted_for_invoice")
    def test_noop_when_flag_off(self, mock_verify, mock_flag):
        mock_flag.return_value = False
        doc = {"name": "POS-INV-001", "branch": "Main Branch"}
        maybe_wire_fulfilment_on_submit(doc)
        mock_verify.assert_not_called()

    @patch("ury.ury.api.ury_feature_flags.is_pos_stock_authority_flag_enabled")
    @patch("ury.ury.api.ury_feature_flags._verify_fulfilment_posted_for_invoice")
    def test_calls_verification_when_flag_on(self, mock_verify, mock_flag):
        mock_flag.return_value = True
        doc = {"name": "POS-INV-001", "branch": "Main Branch"}
        maybe_wire_fulfilment_on_submit(doc)
        mock_verify.assert_called_once_with(doc)

    @patch("ury.ury.api.ury_feature_flags.is_pos_stock_authority_flag_enabled")
    @patch("ury.ury.api.ury_feature_flags._verify_fulfilment_posted_for_invoice")
    def test_verification_failure_is_propagated(self, mock_verify, mock_flag):
        mock_flag.return_value = True
        mock_verify.side_effect = Exception("boom")
        doc = {"name": "POS-INV-001", "branch": "Main Branch"}
        with self.assertRaises(Exception):
            maybe_wire_fulfilment_on_submit(doc)

    @patch("ury.ury.api.ury_feature_flags.frappe.get_all")
    def test_verify_noop_when_no_kots(self, mock_get_all):
        from ury.ury.api.ury_feature_flags import _verify_fulfilment_posted_for_invoice

        mock_get_all.return_value = []
        doc = frappe._dict({"name": "POS-INV-001"})
        # Must not raise, and must not proceed past the KOT lookup (no
        # doctype-existence or item-execution queries either).
        _verify_fulfilment_posted_for_invoice(doc)
        mock_get_all.assert_called_once()

    @patch("ury.ury.api.ury_feature_flags.frappe.db.exists")
    @patch("ury.ury.api.ury_feature_flags.frappe.get_all")
    def test_verify_fails_closed_when_posting_infrastructure_missing(
        self, mock_get_all, mock_exists
    ):
        from ury.ury.api.ury_feature_flags import _verify_fulfilment_posted_for_invoice

        mock_get_all.return_value = [frappe._dict({"name": "KOT-001"})]
        mock_exists.return_value = False
        doc = frappe._dict({"name": "POS-INV-001"})

        with self.assertRaises(frappe.ValidationError):
            _verify_fulfilment_posted_for_invoice(doc)

    @patch("ury.ury.api.ury_feature_flags.frappe.db.exists", return_value=True)
    @patch("ury.ury.api.ury_feature_flags.frappe.db.get_value")
    @patch("ury.ury.api.ury_feature_flags.frappe.get_all")
    def test_verify_skips_items_never_produced(self, mock_get_all, mock_get_value, mock_exists):
        from ury.ury.api.ury_feature_flags import _verify_fulfilment_posted_for_invoice

        mock_get_all.side_effect = [
            [frappe._dict({"name": "KOT-001"})],
            [frappe._dict({"name": "IE-1", "kot_item": "KI-1", "state": "QUEUED"})],
        ]
        doc = frappe._dict({"name": "POS-INV-001"})

        # Must not raise, and must never look up a posting intent for an
        # item that was never produced.
        _verify_fulfilment_posted_for_invoice(doc)
        mock_get_value.assert_not_called()

    @patch("ury.ury.api.ury_feature_flags.frappe.db.exists", return_value=True)
    @patch("ury.ury.api.ury_feature_flags.frappe.db.get_value")
    @patch("ury.ury.api.ury_feature_flags.frappe.get_all")
    def test_verify_rejects_produced_item_with_no_posting_intent(
        self, mock_get_all, mock_get_value, mock_exists
    ):
        from ury.ury.api.ury_feature_flags import _verify_fulfilment_posted_for_invoice

        mock_get_all.side_effect = [
            [frappe._dict({"name": "KOT-001"})],
            [frappe._dict({"name": "IE-1", "kot_item": "KI-1", "state": "READY"})],
        ]
        mock_get_value.return_value = None  # no posting intent found
        doc = frappe._dict({"name": "POS-INV-001"})

        with self.assertRaises(frappe.ValidationError):
            _verify_fulfilment_posted_for_invoice(doc)

    @patch("ury.ury.api.ury_feature_flags.frappe.db.exists", return_value=True)
    @patch("ury.ury.api.ury_feature_flags.frappe.db.get_value")
    @patch("ury.ury.api.ury_feature_flags.frappe.get_all")
    def test_verify_accepts_already_posted_intent(self, mock_get_all, mock_get_value, mock_exists):
        from ury.ury.api.ury_feature_flags import _verify_fulfilment_posted_for_invoice

        mock_get_all.side_effect = [
            [frappe._dict({"name": "KOT-001"})],
            [frappe._dict({"name": "IE-1", "kot_item": "KI-1", "state": "SERVED"})],
        ]
        # First get_value: posting-intent name lookup. Second: its status.
        mock_get_value.side_effect = ["INTENT-1", "POSTED"]
        doc = frappe._dict({"name": "POS-INV-001"})

        # Must not raise.
        _verify_fulfilment_posted_for_invoice(doc)

    @patch("ury.ury.api.ury_feature_flags.frappe.db.exists", return_value=True)
    @patch("ury.ury.api.ury_feature_flags.frappe.db.get_value")
    @patch("ury.ury.api.ury_feature_flags.frappe.get_all")
    def test_verify_retries_pending_intent_then_rejects_if_still_not_posted(
        self, mock_get_all, mock_get_value, mock_exists
    ):
        from ury.ury.api.ury_feature_flags import _verify_fulfilment_posted_for_invoice

        mock_get_all.side_effect = [
            [frappe._dict({"name": "KOT-001"})],
            [frappe._dict({"name": "IE-1", "kot_item": "KI-1", "state": "READY"})],
        ]
        # Name lookup, then status before retry, then status after retry.
        mock_get_value.side_effect = ["INTENT-1", "PENDING", "PENDING"]

        with patch(
            "ury.ury.api.ury_fulfilment_posting_service.process_posting_intent",
            return_value=None,
        ) as mock_process:
            doc = frappe._dict({"name": "POS-INV-001"})
            with self.assertRaises(frappe.ValidationError):
                _verify_fulfilment_posted_for_invoice(doc)
            mock_process.assert_called_once_with("INTENT-1")
