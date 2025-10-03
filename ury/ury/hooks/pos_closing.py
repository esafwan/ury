import frappe
from frappe import _, scrub
from datetime import datetime, timedelta
from frappe.utils import flt, get_datetime,today,now

def validate_current_time(doc, method):
    fetch_current_time = frappe.db.get_value("POS Profile", doc.pos_profile, "custom_current_time")
    if fetch_current_time:
        # Update to current time
        today_date = today()
        date_time = now()

        if isinstance(date_time, str):
            # Split at the dot to remove microseconds, if present
            formatted_date_time = date_time.split('.')[0]
        else:
            # If it's a datetime object, format it
            formatted_date_time = date_time.strftime('%Y-%m-%d %H:%M:%S')
        doc.period_end_date = date_time

        # Extract just the time part
        time_part = formatted_date_time.split(' ')[1]
        doc.posting_time = time_part
        
        invoices = frappe.get_all(
            "POS Invoice",
            filters={
                "docstatus": 1,
                "status":"Paid",
                "posting_date": ["between", [doc.period_start_date, doc.period_end_date]]
            },
            fields=["name", "posting_date", "customer", "grand_total", "base_grand_total"]
        )
        
        # Clear existing transactions
        doc.set("pos_transactions", [])
        
        # Add all found invoices with the required fields
        for invoice in invoices:
            doc.append("pos_transactions", {
                "pos_invoice": invoice.name,
                "posting_date": invoice.posting_date,
                "customer": invoice.customer,
                "grand_total": invoice.grand_total,
                "base_grand_total": invoice.base_grand_total
            })


def validate_daily_checklists(doc, method):
    # Retrieve POS profile details
    pos_profile = frappe.get_doc("POS Profile", doc.pos_profile)
    branch = pos_profile.branch
    checklist = pos_profile.custom_dependent_checklist
    try:
        enable_ury_offline = frappe.db.get_value("POS Profile", doc.pos_profile, "enable_ury_offline")
        site_status = frappe.db.get_value("POS Profile", doc.pos_profile, "site_status")
    except:
        enable_ury_offline = 0
        site_status = ""
    
    # Parse start date
    start_date = doc.period_start_date
    endDate = doc.period_end_date
    if isinstance(start_date, str):
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S.%f")
        except ValueError:
            start_date = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")
    if isinstance(endDate, str):
        try:
            endDate = datetime.strptime(endDate, "%Y-%m-%d %H:%M:%S.%f")
        except ValueError:
            endDate = datetime.strptime(endDate, "%Y-%m-%d %H:%M:%S")

    # Check for draft invoices
    draft_invoices = frappe.get_all(
        "POS Invoice",
        fields=["name"],
        filters={"branch": branch, "status": "Draft", "docstatus": "0"},
    )
    if draft_invoices:
        frappe.throw("Submit/Delete Draft Invoices")

    # Check for expected amount
    expected_amount = sum(
        payment.expected_amount for payment in doc.payment_reconciliation
    )
    if expected_amount == 0.0:
        frappe.throw("Expected Amount not loaded. Please reload the page")

    # Initialize quality checklist and non-completed checklist
    doc.quality_checklist = []
    non_completed_checklists = []
    errors = []

    def validate_and_throw(error_messages):
        if error_messages != []:
            error_list = [_("{}".format(msg)) for msg in error_messages]
            frappe.throw(error_list, title=_("Validation Error"), as_list=True)

    # Check for POS Closing Entry in the checklist
    for qc in checklist:
        if qc.select_2 == "POS Closing Entry":
            quality_reviews = frappe.db.sql(
                """
                SELECT goal
                FROM `tabQuality Review`
                WHERE branch = %s 
                    AND `creation` >= %s
                """,
                (branch, start_date),
                as_dict=True,
            )
            have = any(qr.goal == qc.quality_checklist for qr in quality_reviews)
            if have:
                doc.append(
                    "quality_checklist",
                    {"checklist": qc.quality_checklist, "check_2": 1},
                )
            elif not have:
                non_completed_checklists.append(
                    _("Pending checklist: {} ").format(
                        frappe.bold(qc.quality_checklist)
                    )
                )
    # if enable_ury_offline == 0 or enable_ury_offline == None or site_status != "Online":
     
    start_time = datetime.now().replace(hour=5, minute=0, second=0, microsecond=0)
    end_time = start_time + timedelta(days=1)
    if isinstance(doc.period_start_date, str):
        try:
            period_start_date = datetime.strptime(doc.period_start_date, "%Y-%m-%d %H:%M:%S.%f").date()
        except ValueError:
            period_start_date = datetime.strptime(doc.period_start_date, "%Y-%m-%d %H:%M:%S").date()
    else:
        period_start_date = doc.period_start_date.date()
    material_requests = wastage = bulk_production = daily_p_and_l = []
    if pos_profile.validate_mr == 1:
        # # Construct the SQL query
        mr_query = """
                SELECT name, transaction_date, status
                FROM `tabMaterial Request`
                WHERE 
                branch =%s  
                AND docstatus = 1 AND
                modified >= %s AND modified <= %s
        """

        # Execute the query using frappe.db.sql
        material_requests = frappe.db.sql(
            mr_query, (branch, start_time, end_time), as_dict=True
        )

    if pos_profile.validate_wd == 1:
        wtg_query = """
                SELECT name
                FROM `tabWastage`
                WHERE 
                docstatus = 1 AND
                branch =%s AND posting_datetime >= %s AND posting_datetime <= %s
        """
        
        # Execute the query using frappe.db.sql
        wastage = frappe.db.sql(wtg_query, (branch, doc.period_start_date, doc.period_end_date), as_dict=True)

    if pos_profile.validate_bp == 1:
        pr_query = """
                SELECT name
                FROM `tabBulk Production`
                WHERE 
                docstatus = 1 AND
                branch =%s AND modified >= %s AND modified <= %s
        """

        # Execute the query using frappe.db.sql
        bulk_production = frappe.db.sql(
            pr_query, (branch, start_time, end_time), as_dict=True
        )
    if pos_profile.daily_p_and_l_validation == 1:
        pr_query = """
                SELECT name
                FROM `tabURY Daily P and L`
                WHERE 
                docstatus = 0 AND
                branch =%s AND date = %s
        """

        # Execute the query using frappe.db.sql
        daily_p_and_l = frappe.db.sql(
            pr_query, (branch, period_start_date), as_dict=True
        )
    if pos_profile.validate_attendance == 1:    
        attnd_query = """
                SELECT a.name
                FROM `tabAttendance` a
                INNER JOIN `tabEmployee` b ON b.name = a.employee
                WHERE b.branch = %s AND a.docstatus = 1 AND a.attendance_date = %s
            """

        # Execute the query using frappe.db.sql
        attendance = frappe.db.sql(
            attnd_query, (branch, period_start_date), as_dict=True
        )

    if pos_profile.validate_mr == 1 and not material_requests:
        errors.append(_("Material Request: not generated"))

    if pos_profile.validate_wd == 1 and not wastage:
        errors.append(_("Wastage: No recording for today"))

    if pos_profile.validate_bp == 1 and not bulk_production:
        errors.append(_("Bulk Production: No entries today"))

    if pos_profile.daily_p_and_l_validation == 1 and not daily_p_and_l:
        errors.append(_("Daily P and L: No entries today"))

    if pos_profile.validate_attendance == 1 and not attendance:
        errors.append(_("Attendance: Not marked for today"))

    errors.extend(non_completed_checklists)

    validate_and_throw(errors)
# else:
#     errors.extend(non_completed_checklists)

#     validate_and_throw(errors)



def create_shift_closing(doc, event):
    # Check if shift closing is enabled for the POS profile
    if not frappe.db.get_value("POS Profile", doc.pos_profile, "custom_enable_shift_open"):
        return

    # Fetch the open shift details
    open_shift = frappe.get_all(
        "Shift Opening",
        fields=["period_start_date", "name", "shift_type", "employee"],
        filters={"status": "Open", "docstatus": 1},
        limit=1
    )

    if not open_shift:
        frappe.throw("No open shift found to close.")

    open_shift = open_shift[0]

    # Create a new Shift Closing document
    shift_closing = frappe.new_doc("Shift Closing")
    shift_closing.update({
        "period_start_date": open_shift["period_start_date"],
        "shift_opening_entry": open_shift["name"],
        "posting_date": doc.posting_date,
        "company": doc.company,
        "user": doc.user,
        "period_end_date": doc.period_end_date,
        "pos_profile": doc.pos_profile,
        "shift_type": open_shift["shift_type"],
        "employee": open_shift["employee"],
    })

    # Get opening balances for the shift
    opening_balances = frappe.get_all(
        "Shift Opening Entry Detail",
        fields=["opening_amount", "mode_of_payment"],
        filters={"parent": open_shift["name"]}
    )
        
    invoices = frappe.db.sql(
        """
        SELECT name, timestamp(posting_date, posting_time) AS timestamp
        FROM `tabPOS Invoice`
        WHERE owner = %s AND docstatus = 1 AND pos_profile = %s
        """,
        (doc.user, doc.pos_profile),
        as_dict=True
    )

    invoices = [
        frappe.get_doc("POS Invoice", inv["name"])
        for inv in invoices
        if get_datetime(open_shift["period_start_date"]) <= get_datetime(inv["timestamp"]) <= get_datetime(doc.period_end_date)
    ]
    
    # Calculate totals
    shift_closing.grand_total = sum(inv.grand_total for inv in invoices)
    shift_closing.net_total = sum(inv.net_total for inv in invoices)
    shift_closing.total_quantity = sum(inv.total_qty for inv in invoices)
    for invoice in invoices:
        shift_closing.append("pos_transactions", {
                    "pos_invoice": invoice.name,
                    "grand_total": invoice.grand_total,
                    "posting_date": invoice.posting_date
                })
    # Get the last Shift Closing for reconciliation
    last_shift_closing = frappe.get_last_doc(
        "Shift Closing",
        filters={"docstatus": 1},
        order_by="creation desc"
    )

    # Reconcile payments
    for item in doc.payment_reconciliation:
        open_balance = next((bal for bal in opening_balances if bal.mode_of_payment == item.mode_of_payment), None)
        last_balance = next((bal for bal in getattr(last_shift_closing, "payment_reconciliation", []) if bal.mode_of_payment == item.mode_of_payment), None)

        if open_balance and last_balance:
            expected_amount = (
                item.expected_amount - last_balance.expected_amount + open_balance["opening_amount"]
            )
            closing_amount = item.closing_amount - open_balance["opening_amount"]
            difference = closing_amount - expected_amount

            shift_closing.append("payment_reconciliation", {
                "mode_of_payment": item.mode_of_payment,
                "opening_amount": open_balance["opening_amount"],
                "expected_amount": expected_amount,
                "closing_amount": closing_amount,
                "difference": difference
            })

    # Save and submit the shift closing
    shift_closing.insert()
    shift_closing.submit()
    doc.custom_shift_closing=shift_closing.name
    # doc.save()
        
def shift_close_cancel(doc,event):
    enable_shift_open= frappe.db.get_value('POS Profile', doc.pos_profile, 'custom_enable_shift_open')
    if not frappe.db.get_value("POS Profile", doc.pos_profile, "custom_enable_shift_open"):
        return
    if doc.custom_shift_closing:    
        shift_open = frappe.get_doc("Shift Closing", doc.custom_shift_closing)
        shift_open.cancel()
    

def payment_reconciliation(doc,event):
    enable_payment_reconciliation = frappe.db.get_value("POS Profile", doc.pos_profile, "enable_payment_reconciliation")
    if enable_payment_reconciliation == 1:
        short_excess_account = frappe.db.get_value("POS Profile", doc.pos_profile, "short_excess_account")
        branch = frappe.db.get_value("POS Profile", doc.pos_profile, "branch")
        cost_center = frappe.db.get_value("POS Profile", doc.pos_profile, "cost_center")
        cash_diff = bank_diff = cash_expected = bank_expected = cash_closing = bank_closing = 0
        for payment in doc.payment_reconciliation:
            if 'Cash' in str(payment.mode_of_payment):
                cash_mop = frappe.get_doc("Mode of Payment", payment.mode_of_payment)
                for account in cash_mop.accounts:
                    if account.company == doc.company:
                        cash_account = account.default_account
                cash_expected = payment.expected_amount
                cash_closing = payment.closing_amount
                cash_diff = payment.difference
            if 'Card' in str(payment.mode_of_payment) or 'UPI' in str(payment.mode_of_payment):
                bank_mop = frappe.get_doc("Mode of Payment", payment.mode_of_payment)
                for account in bank_mop.accounts:
                    if account.company == doc.company:
                        bank_account = account.default_account
                bank_expected += payment.expected_amount
                bank_closing += payment.closing_amount
                bank_diff += payment.difference
        cash_company = frappe.db.get_value("Company", doc.company, "default_cash_account")
        bank_company = frappe.db.get_value("Company", doc.company, "default_bank_account")
        journal_entry = frappe.get_doc({ 
            'doctype': 'Journal Entry',
            'company': doc.company,
            'custom_branch': branch,
            'posting_date': doc.posting_date,
            'user_remark':"Payment Reconciliation"
        })
        if cash_expected !=0:
            journal_entry.append("accounts", {
                "account": cash_account,
                "credit_in_account_currency": cash_expected,
                "cost_center": cost_center,
            })
        if cash_closing != 0:
            journal_entry.append("accounts", {
                "account": cash_company,
                "debit_in_account_currency": cash_closing,
                "cost_center": cost_center
            })
        if bank_expected !=0:
            journal_entry.append("accounts", {
                "account": bank_account,
                "credit_in_account_currency": bank_expected,
                "cost_center": cost_center,
            })
        if bank_closing != 0:
            journal_entry.append("accounts", {
                "account": bank_company,
                "debit_in_account_currency": bank_closing,
                "cost_center": cost_center
            })
        diff = cash_diff + bank_diff
        if diff < 0:
            diff = abs(diff)
            journal_entry.append("accounts", {
                "account": short_excess_account,
                "debit_in_account_currency": diff,
                "cost_center": cost_center
            })
        elif diff > 0:
            diff = abs(diff)
            journal_entry.append("accounts", {
                "account": short_excess_account,
                "credit_in_account_currency": diff,
                "cost_center": cost_center,
            })
        journal_entry.save()


@frappe.whitelist()
def get_draft_stock_reconciliation(pos_profile,period_end_date,period_start_date,closing_entry = None):
    # Fetching branch from POS profile
    branch = frappe.get_value("POS Profile", pos_profile, "branch")
    if not branch:
        frappe.throw("Branch not found for the given POS profile")
    
    submit_stock_correction = frappe.get_value("POS Profile", pos_profile, "submit_stock_reconciliation")
    warehouse = frappe.get_value("POS Profile", pos_profile, "warehouse")
    
    start_date = period_start_date
    
    end_date = period_end_date

    # Getting the last created stock reconciliation document for the branch
    stock_correction = None
    try:
        stock_correction = frappe.get_last_doc(
            "Stock Correction", filters={"docstatus": 0, "branch": branch, "set_warehouse": warehouse, "period_end_date": ["between", [start_date, end_date]]}
        )
    except:
       pass

    if submit_stock_correction == 1:
        if stock_correction:
            return stock_correction.name
        else:
            return False
    else:
        return True

@frappe.whitelist()
def get_draft_daily_p_and_l(pos_profile, closing_entry = None):
    branch = frappe.get_value("POS Profile", pos_profile, "branch")
    submit_daily_p_and_l = frappe.get_value("POS Profile", pos_profile, "submit_daily_p_and_l")
    period_start_date = frappe.get_value("POS Closing Entry", closing_entry,"period_start_date")
    period_end_date = frappe.get_value("POS Closing Entry", closing_entry,"period_end_date")

    if not branch:
        frappe.throw("Branch not found for the given POS profile")
        
    daily_p_and_l = None
    try:
        daily_p_and_l = frappe.get_last_doc(
            "URY Daily P and L", filters={"docstatus": 0, "branch": branch, "date": ["between", [period_start_date, period_end_date]]}
        )
    except:
       pass

    if submit_daily_p_and_l == 1:
        if daily_p_and_l:
            return daily_p_and_l.name
        else:
            return False
    else:
        return True

@frappe.whitelist()
def get_draft_wastage(pos_profile,period_end_date,period_start_date,closing_entry = None):
    # Fetching branch from POS profile
    branch = frappe.get_value("POS Profile", pos_profile, "branch")
    if not branch:
        frappe.throw("Branch not found for the given POS profile")
    
    submit_wastage = frappe.get_value("POS Profile", pos_profile, "custom_submit_wastage_and_damage")
    warehouse = frappe.get_value("POS Profile", pos_profile, "warehouse")
    
    start_date = period_start_date
    
    end_date = period_end_date

    # Getting the last created wastage document for the branch
    wastage = None
    try:
        wastage = frappe.get_last_doc(
            "Wastage", filters={"docstatus": 0, "branch": branch, "warehouse": warehouse, "posting_datetime": ["between", [start_date, end_date]]}
        )
    except:
       pass

    if submit_wastage == 1:
        if wastage:
            return wastage.name
        else:
            return False
    else:
        return True