import json
import unittest
from unittest.mock import MagicMock, patch

import frappe

from ury.ury.api.ury_kot_item_execution_service import (
	ITEM_EXECUTION_DOCTYPE_NOT_FOUND,
	IN_PREPARATION,
	ItemExecutionError,
	QUEUED,
	READY,
	SERVED,
	get_kot_execution_state,
	mark_item_ready,
	seed_kot_item_executions,
	seed_kot_item_executions_on_submit,
	serve_item_execution,
	start_item_execution,
)

MODULE = "ury.ury.api.ury_kot_item_execution_service"


def _call(func, *args, **kwargs):
	return getattr(func, "__wrapped__", func)(*args, **kwargs)


def _exists(doctype, name=None):
	if doctype == "DocType":
		return True
	if doctype in {"URY KOT", "URY KOT Items"}:
		return True
	return False


def _kot_doc(name):
	if name == "URY KOT-1":
		items = [frappe._dict({"name": "KOTITEM-1"}), frappe._dict({"name": "KOTITEM-2"})]
		doc = frappe._dict({"name": name, "kot_items": items})
		doc.get = lambda key, default=None, _doc=doc: _doc[key] if key in _doc else default
		return doc
	raise AssertionError("unexpected get_doc lookup")


def _make_doc_recorder():
	created = []
	on_insert = None

	def _get_doc(*args, **kwargs):
		arg = args[0] if args else kwargs.get("arg1")
		name = args[1] if len(args) > 1 else None
		if isinstance(arg, dict):
			doc = frappe._dict(dict(arg))
			def insert(*_args, **_kwargs):
				if on_insert:
					on_insert(doc)

			doc.insert = MagicMock(side_effect=insert)
			doc.save = MagicMock()
			doc.set = lambda field, value, _doc=doc: _doc.__setitem__(field, value)
			doc.as_dict = lambda _doc=doc: dict(_doc)
			created.append(doc)
			return doc
		if arg == "URY KOT":
			return _kot_doc(name)
		if arg == "URY KOT Item Execution":
			for doc in created:
				if doc.get("name") == name:
					return doc
			doc = frappe._dict({"name": name})
			doc.save = MagicMock()
			doc.set = lambda field, value, _doc=doc: _doc.__setitem__(field, value)
			doc.as_dict = lambda _doc=doc: dict(_doc)
			created.append(doc)
			return doc
		raise AssertionError(f"unexpected get_doc lookup: {arg!r}")

	def set_on_insert(callback):
		nonlocal on_insert
		on_insert = callback

	return _get_doc, created, set_on_insert


class TestKotItemExecution(unittest.TestCase):
	def setUp(self):
		db_patcher = patch(f"{MODULE}.frappe.db", new=MagicMock())
		db_patcher.start()
		self.addCleanup(db_patcher.stop)

		session_patcher = patch(f"{MODULE}.frappe.session", new=MagicMock(user="chef@example.com"))
		session_patcher.start()
		self.addCleanup(session_patcher.stop)

		patcher = patch(f"{MODULE}.frappe.utils.now", return_value="2024-01-01 00:00:00")
		patcher.start()
		self.addCleanup(patcher.stop)

	def test_seed_creates_one_row_per_kot_item_and_is_idempotent(self):
		get_doc, created, set_on_insert = _make_doc_recorder()
		seen_kot_items = set()

		def exists(doctype, name=None):
			if doctype == "URY KOT Item Execution":
				return name and name.get("kot_item") in seen_kot_items
			return _exists(doctype, name)

		def remember_insert(doc):
			if doc.get("doctype") == "URY KOT Item Execution":
				seen_kot_items.add(doc["kot_item"])

		with patch(f"{MODULE}.frappe.db.exists", side_effect=_exists), patch(
			f"{MODULE}.frappe.get_doc", side_effect=get_doc
		), patch(f"{MODULE}.frappe.get_all", return_value=[]), patch(
			f"{MODULE}.frappe.db.get_value", return_value=frappe._dict({"branch": "BR-1", "production": "PU-1"})
		), patch(f"{MODULE}.frappe.session") as session:
			session.user = "chef@example.com"
			set_on_insert(remember_insert)
			with patch(f"{MODULE}.frappe.db.exists", side_effect=exists):
				rows = seed_kot_item_executions("URY KOT-1")
				rows_again = seed_kot_item_executions("URY KOT-1")
		self.assertEqual(len(rows), 2)
		self.assertEqual(len(rows_again), 0)
		self.assertEqual(len([doc for doc in created if doc.get("doctype") == "URY KOT Item Execution"]), 2)
		self.assertEqual(created[0]["state"], QUEUED)

	def test_submit_wrapper_only_ignores_missing_item_execution_doctype(self):
		kot = frappe._dict({"name": "URY KOT-1"})
		with patch(
			f"{MODULE}.seed_kot_item_executions",
			side_effect=ItemExecutionError(ITEM_EXECUTION_DOCTYPE_NOT_FOUND),
		), patch(f"{MODULE}.frappe.logger") as logger:
			self.assertEqual(seed_kot_item_executions_on_submit(kot), [])
		logger.assert_called_once_with("ury")

	def test_submit_wrapper_reraises_real_seed_errors(self):
		kot = frappe._dict({"name": "URY KOT-1"})
		with patch(
			f"{MODULE}.seed_kot_item_executions",
			side_effect=ItemExecutionError("REAL_ERROR"),
		):
			with self.assertRaises(ItemExecutionError):
				seed_kot_item_executions_on_submit(kot)

	def test_item_transitions_update_aggregate_state(self):
		get_doc, created, _set_on_insert = _make_doc_recorder()
		item_rows = [
			frappe._dict({"name": "ROW-1", "kot": "URY KOT-1", "kot_item": "KOTITEM-1", "state": QUEUED, "idempotency_key": "seed-1", "started_by": None, "started_at": None, "ready_by": None, "ready_at": None, "served_by": None, "served_at": None}),
			frappe._dict({"name": "ROW-2", "kot": "URY KOT-1", "kot_item": "KOTITEM-2", "state": QUEUED, "idempotency_key": "seed-2", "started_by": None, "started_at": None, "ready_by": None, "ready_at": None, "served_by": None, "served_at": None}),
		]
		for row in item_rows:
			row.save = MagicMock()
			row.set = lambda field, value, _doc=row: _doc.__setitem__(field, value)
			row.as_dict = lambda _doc=row: dict(_doc)
		created.extend(item_rows)

		def _get_all(doctype, filters=None, fields=None, order_by=None, limit=None):
			if doctype == "URY KOT Execution":
				return []
			if doctype != "URY KOT Item Execution":
				return []
			matches = item_rows
			for field, value in (filters or {}).items():
				matches = [row for row in matches if row.get(field) == value]
			return matches[:limit] if limit else matches

		with patch(f"{MODULE}.frappe.db.exists", side_effect=_exists), patch(
			f"{MODULE}.frappe.get_doc", side_effect=get_doc
		), patch(f"{MODULE}.frappe.get_all", side_effect=_get_all), patch(
			f"{MODULE}.frappe.db.sql", return_value=[item_rows[0]]
		), patch(f"{MODULE}.frappe.db.get_value", return_value=frappe._dict({"branch": "BR-1", "production": "PU-1"})), patch(
			f"{MODULE}._attach_ready_posting_intent", side_effect=lambda result, actor: result
		) as mock_ready_posting, patch(
			f"{MODULE}.frappe.session"
		) as session:
			session.user = "chef@example.com"
			seed_kot_item_executions("URY KOT-1")
			_call(start_item_execution, "KOTITEM-1", idempotency_key="start-1")
			_call(mark_item_ready, "KOTITEM-1", idempotency_key="ready-1")
			ready_state = get_kot_execution_state("URY KOT-1")
			_call(serve_item_execution, "KOTITEM-1", idempotency_key="serve-1")
			served_with_queued_peer_state = get_kot_execution_state("URY KOT-1")
		self.assertEqual(ready_state, READY)
		self.assertEqual(served_with_queued_peer_state, QUEUED)
		mock_ready_posting.assert_called_once()
		seeded = [doc for doc in created if doc.get("doctype") == "URY KOT Item Execution"]
		self.assertTrue(seeded)
		self.assertEqual(json.loads(seeded[0]["audit_log"])[0]["event"], "seed")
