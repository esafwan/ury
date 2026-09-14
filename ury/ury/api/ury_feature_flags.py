# Copyright (c) 2026, Tridz Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""V3-73: POS stock authority feature flag.

This module is the SOLE read path used by `ury_order.py` to decide whether a
POS Invoice's stock authority is handled by ERPNext's native
`update_stock=1` posting (the current, always-on-by-default behavior) or by
the fulfilment services from V3-71/V3-72. The replacement path remains
feature-flagged and operationally gated until its runtime accounting and
deployment evidence is accepted.

Governing contract:
tracks/sa-v3_nxt/outputs/V3-70-fulfilment-accounting-transition-checklist.md

HARD RULES this module exists to enforce:

1. The flag defaults to False/off in every circumstance: unset field, a
   missing "URY Feature Flags" doctype/table (e.g. before migration), a
   database error, or any other unexpected condition. This function FAILS
   CLOSED -- any exception is caught here and treated as "flag is off". It
   must never fail open to the new, less-battle-tested code path.
2. Nothing in this module, or anywhere else in the shipped application code,
   sets this flag to True. The only way the flag becomes True in a real
   deployment is a human deliberately editing the "URY Feature Flags" single
   doctype (Desk UI or a direct, out-of-band data change) -- an explicit,
   auditable, out-of-band admin action, not a code default.
3. Per-branch/per-company overrides are accepted as optional future-proofing
   (the checklist recommends per-branch scoping) but the current
   implementation only reads the single global flag; `company`/`branch`
   arguments are accepted so callers don't need to change their call sites
   later, and are currently unused. Document any future per-scope storage
   choice here when it's built.

DO NOT set this flag to True anywhere in this codebase. If you are looking
for how to enable the new fulfilment path in a live environment, that is an
operational decision requiring the evidence and sign-off described in the
governing contract above -- not a code change.
"""

import frappe
from frappe import _

FLAG_DOCTYPE = "URY Feature Flags"
FLAG_FIELD = "pos_stock_authority_v2"
RESERVATION_DOCTYPE = "URY Stock Reservation"


def is_pos_stock_authority_flag_enabled(company=None, branch=None):
	"""Return True only if a human has explicitly enabled the V3-73 flag.

	Fails CLOSED (returns False) on any error, including a missing doctype
	(e.g. before this app's migration has run), an unset field, or any other
	unexpected condition. Never raises.

	`company` and `branch` are accepted for forward compatibility with a
	future per-scope override but are not currently used to vary the result
	-- the single global "URY Feature Flags" value is authoritative today.
	"""

	try:
		value = frappe.db.get_single_value(FLAG_DOCTYPE, FLAG_FIELD)
	except Exception:
		# Fail closed: doctype missing, DB error, not yet migrated, etc.
		# Never let a read failure be interpreted as "flag on".
		return False

	return bool(value)


def maybe_wire_fulfilment_on_submit(doc, method=None):
	"""B02/V3-73 flag-on integration point, called from POS Invoice's
	on_submit doc_event (additive: appended alongside the existing on_submit
	handler, never replacing it).

	Flag OFF (default in every real environment): no-op, returns immediately.
	`_apply_pos_stock_authority` already left `update_stock=1` in this case,
	so ERPNext's native POS deduction is the sole authority and there is
	nothing here to verify.

	Flag ON: this is the real stock-authority gate. Real Stock Entries are
	NOT posted here -- they are already posted (or in flight) by
	`ury_fulfilment_posting_service.py`, triggered earlier in the order's
	life whenever a KOT item transitioned to READY/SERVED via
	`ury_kot_item_execution_service.mark_item_ready`/`serve_item_execution`
	(Captain app, and Mosaic's `kot.vue` since the B01 fix). This function's
	job is narrower and safety-critical: for every KOT item on this invoice
	that reached READY/SERVED, confirm a `URY Fulfilment Posting Intent`
	exists and has reached POSTED (i.e. carries a real, submitted `Stock
	Entry`) before letting the invoice, submitted with
	`invoice.update_stock=0`, go through. Posting is normally processed
	asynchronously by a background worker within seconds of READY/SERVED; if
	it has not caught up yet by the time the invoice is submitted, this
	function gives it one synchronous attempt (`process_posting_intent`,
	itself idempotent/safe to replay) rather than failing purely on a race.
	If a produced item still has no POSTED intent after that, or has no
	intent at all, submission is refused -- update_stock is 0, so letting the
	invoice through unverified would silently create unvalued sales and
	inventory drift, exactly the failure mode `_apply_pos_stock_authority`
	used to fail closed against unconditionally.
	"""
	if not is_pos_stock_authority_flag_enabled(branch=doc.get("branch")):
		return

	_verify_fulfilment_posted_for_invoice(doc)


ITEM_EXECUTION_DOCTYPE = "URY KOT Item Execution"
POSTING_INTENT_DOCTYPE = "URY Fulfilment Posting Intent"
PRODUCED_STATES = ("READY", "SERVED")


def _verify_fulfilment_posted_for_invoice(doc):
	kots = frappe.get_all("URY KOT", filters={"invoice": doc.name}, fields=["name"])
	if not kots:
		return

	if not frappe.db.exists("DocType", ITEM_EXECUTION_DOCTYPE) or not frappe.db.exists(
		"DocType", POSTING_INTENT_DOCTYPE
	):
		# Cannot verify real posting on this site at all -- fail closed rather
		# than let an unverifiable invoice submit with update_stock=0.
		frappe.throw(
			_(
				"POS Stock Authority V2 is enabled but this site is missing the "
				"fulfilment posting infrastructure ({0}/{1}); cannot verify stock "
				"was posted for invoice {2}."
			).format(ITEM_EXECUTION_DOCTYPE, POSTING_INTENT_DOCTYPE, doc.name),
			frappe.ValidationError,
		)

	from ury.ury.api.ury_fulfilment_posting_service import process_posting_intent, POSTED

	for kot in kots:
		item_execution_rows = frappe.get_all(
			ITEM_EXECUTION_DOCTYPE,
			filters={"kot": kot.name},
			fields=["name", "kot_item", "state"],
		)
		for row in item_execution_rows:
			if row.state not in PRODUCED_STATES:
				# Never produced (e.g. cancelled before READY) -- nothing was
				# ever supposed to be deducted for it, so there is nothing to
				# verify here.
				continue

			intent_name = frappe.db.get_value(
				POSTING_INTENT_DOCTYPE,
				{"kot_item": row.kot_item},
				"name",
				order_by="creation desc",
			)
			if not intent_name:
				frappe.throw(
					_(
						"KOT item {0} reached {1} but no fulfilment posting intent "
						"was ever created for it; stock cannot be authoritatively "
						"deducted for invoice {2}."
					).format(row.kot_item, row.state, doc.name),
					frappe.ValidationError,
				)

			status = frappe.db.get_value(POSTING_INTENT_DOCTYPE, intent_name, "status")
			if status != POSTED:
				# Give the (normally async) posting pipeline one synchronous
				# chance to catch up before failing the submit on a timing
				# race -- process_posting_intent is idempotent/safe to replay.
				process_posting_intent(intent_name)
				status = frappe.db.get_value(POSTING_INTENT_DOCTYPE, intent_name, "status")

			if status != POSTED:
				frappe.throw(
					_(
						"Stock has not been posted yet for KOT item {0} (fulfilment "
						"posting intent {1} is {2}, not POSTED); cannot submit "
						"invoice {3} under POS Stock Authority V2."
					).format(row.kot_item, intent_name, status, doc.name),
					frappe.ValidationError,
				)


