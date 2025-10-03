import frappe
from frappe.utils import today
from frappe.utils import now
from datetime import date, datetime, timedelta




def update_daily_checklists(doc, event):
    # Initialize quality checklist
    doc.quality_checklist = []

    # Retrieve POS profile details
    pos_profile = frappe.get_doc("POS Profile", doc.pos_profile)
    branch = pos_profile.branch
    checklist = pos_profile.custom_dependent_checklist

    # Retrieve quality reviews for the specified branch and date
    quality_reviews = frappe.get_all(
        "Quality Review",
        fields=["goal"],
        filters={"branch": branch, "date": doc.posting_date},
    )

    # Identify pending checklists for POS Opening Entry
    non_completed_checklists = [
        qc.quality_checklist
        for qc in checklist
        if qc.select_2 == "POS Opening Entry"
        and not any(qr.goal == qc.quality_checklist for qr in quality_reviews)
    ]

    # Raise an exception if there are pending checklists
    if non_completed_checklists:
        frappe.throw(
            title="Daily Checklists not completed",
            msg=("Pending:  {0}").format(",  ".join(non_completed_checklists)),
        )


def validate_pos_opening(doc, event):
    branch = frappe.db.get_value("POS Profile", doc.pos_profile, "branch")
    multiple_cashier = frappe.db.get_value("POS Profile",doc.pos_profile,"custom_enable_multiple_cashier")
    if multiple_cashier:
        pos_openings = frappe.get_all(
            "POS Opening Entry",
            fields=["name"],
            filters={"branch": branch, "status": "Open", "docstatus": 1, "user": doc.user},
        )
        if len(pos_openings) >= 1:
            frappe.throw("Close Pending Opening Entries for the Cashier")
    else:
        branch = frappe.db.get_value("POS Profile", doc.pos_profile, "branch")
        pos_openings = frappe.get_all(
            "POS Opening Entry",
            fields=["name"],
            filters={"branch": branch, "status": "Open", "docstatus": 1},
        )
        if len(pos_openings) >= 1:
            frappe.throw("Close Pending Opening Entries")
    
    enable_shift_open= frappe.db.get_value('POS Profile', doc.pos_profile, 'custom_enable_shift_open')
    if enable_shift_open:
        if not doc.custom_shift_type:
            frappe.throw("Please Select shift")
    
    
    check_stock_correction = frappe.db.get_value('POS Profile', doc.pos_profile, 'custom_check_stock_correction')
    if check_stock_correction:
        yesterday = (datetime.now() - timedelta(days=1)).date()
        latest_correction = frappe.get_all(
            "Stock Correction",
            filters={
            'posting_date': yesterday
            },
            fields=["name", "status", "modified"],
            order_by="modified desc",
            limit=1
        )
        if latest_correction and latest_correction[0].status == "Failed":
            frappe.throw(
                f"Stock correction ({latest_correction[0].name}) has failed. "
                "Please resolve it before proceeding."
            )
    
    check_daily_p_and_l = frappe.db.get_value('POS Profile', doc.pos_profile, 'custom_check_ury_daily_p_and_l')
    if check_daily_p_and_l:
        yesterday = (datetime.now() - timedelta(days=1)).date()
        latest_p_and_l = frappe.get_all(
            "URY Daily P and L",
            filters={
            'date': yesterday
            },
            fields=["name", "custom_status", "modified"],
            order_by="modified desc",
            limit=1
        )
        if latest_p_and_l and latest_p_and_l[0].custom_status == "Failed":
            frappe.throw(
                f"URY Daily P and L ({latest_p_and_l[0].name}) has failed. "
                "Please resolve it before proceeding."
            )


@frappe.whitelist()
def get_shift(shift_type):
    employee= frappe.db.get_value('Shift Assignment', {'shift_type':shift_type}, ['employee_name'])
    shift_details={
        "employee":employee
    }
    return shift_details
    

def create_shift_open(doc,event):
    enable_shift_open= frappe.db.get_value('POS Profile', doc.pos_profile, 'custom_enable_shift_open')
    if enable_shift_open:
        shift_opening = frappe.new_doc("Shift Opening")
        shift_opening.period_start_date = doc.period_start_date
        shift_opening.posting_date = doc.posting_date
        shift_opening.company = doc.company
        shift_opening.user = doc.user
        shift_opening.pos_profile = doc.pos_profile
        shift_opening.shift_type=doc.custom_shift_type
        shift_opening.employee=doc.custom_employee
        for item in doc.balance_details:
            shift_opening.append("balance_details", {
                "mode_of_payment": item.mode_of_payment,
                "opening_amount": item.opening_amount
            })
    
        shift_opening.insert()
        shift_opening.submit()
        doc.custom_shift_opening=shift_opening.name
        doc.save()
        
def shift_open_cancel(doc,event):
    enable_shift_open= frappe.db.get_value('POS Profile', doc.pos_profile, 'custom_enable_shift_open')
    if not frappe.db.get_value("POS Profile", doc.pos_profile, "custom_enable_shift_open"):
        return
    if doc.custom_shift_opening:    
        shift_open = frappe.get_doc("Shift Opening", doc.custom_shift_opening)
        shift_open.cancel()

@frappe.whitelist()
def get_current_date():
    today_date=today()
    date_time=now()
    date_details={
        "today":today_date,
        "date_time":date_time
    }
    
    return date_details
