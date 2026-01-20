import streamlit as st
import json
import os
import uuid
import base64
import zipfile
import io
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import hashlib

# Page configuration
st.set_page_config(
    page_title="Student Payment System",
    page_icon="🎓",
    layout="wide"
)

# File paths
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
STUDENTS_FILE = DATA_DIR / "students.json"
ADMIN_FILE = DATA_DIR / "admin.json"
INSTRUCTIONS_FILE = DATA_DIR / "instructions.json"
UPLOADS_DIR = DATA_DIR / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)

# Initialize data files with improved structure
def init_files():
    default_data = {
        "students": [],
        "admin": {
            "username": "admin",
            "password": "admin123",
            "payment_amount": 5000,
            "payment_accounts": [{"bank": "Bank Name", "account": "1234567890", "name": "Account Holder"}],
            "short_url_code": str(uuid.uuid4())[:8],
            "base_url": "https://payment-collection-form.streamlit.app",
            "instructions": "Default instructions for students.",
            "additional_instructions": "Please make payment to the given account and upload screenshot.",
            "form_published": True,
            "contact_email": "admin@example.com",
            "contact_phone": "+91 9876543210",
            "tab_visibility": {
                "account_details": True,
                "submit_payment": True,
                "payment_status": True,
                "student_list": True,
                "instructions": True
            },
            "screenshot_settings": {
                "allow_download": True,
                "allow_delete": True,
                "max_file_size_mb": 5
            },
            "security_settings": {
                "allow_future_dates": False,
                "require_screenshot_for_paid": True,
                "soft_delete_enabled": False
            }
        },
        "instructions": "Default instructions will appear here."
    }
    
    # Initialize students.json with improved structure
    if not STUDENTS_FILE.exists():
        with open(STUDENTS_FILE, 'w') as f:
            json.dump(default_data["students"], f, indent=2)
    
    # Initialize admin.json with hashed password
    if not ADMIN_FILE.exists():
        admin_data = default_data["admin"]
        admin_data["password"] = hash_password(admin_data["password"])
        with open(ADMIN_FILE, 'w') as f:
            json.dump(admin_data, f, indent=2)
    
    # Initialize instructions.json
    if not INSTRUCTIONS_FILE.exists():
        with open(INSTRUCTIONS_FILE, 'w') as f:
            json.dump(default_data["instructions"], f, indent=2)

# Password hashing
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Load and save data functions
def load_data(file_path, default=[]):
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except:
        return default

def save_data(file_path, data):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

# Query params handling for different Streamlit versions
def get_query_params():
    """Handle query parameters for both old and new Streamlit versions"""
    try:
        # Try Streamlit >= 1.28.0 method
        if hasattr(st, 'query_params'):
            params = st.query_params.to_dict()
            return params
    except:
        pass
    
    try:
        # Try Streamlit < 1.28.0 method
        if hasattr(st, 'experimental_get_query_params'):
            params = st.experimental_get_query_params()
            # Convert to dict format
            result = {}
            for key, value in params.items():
                if isinstance(value, list) and len(value) == 1:
                    result[key] = value[0]
                else:
                    result[key] = value
            return result
    except:
        pass
    
    # Return empty dict if both methods fail
    return {}

# Format date and time display
def format_datetime(dt_string):
    """Format datetime string to readable format"""
    try:
        if not dt_string:
            return "Not specified"
        dt = datetime.fromisoformat(dt_string)
        return dt.strftime("%d-%m-%Y %I:%M %p")
    except:
        return dt_string

def format_date_only(dt_string):
    """Format date only"""
    try:
        if not dt_string:
            return "Not specified"
        dt = datetime.fromisoformat(dt_string)
        return dt.strftime("%d-%m-%Y")
    except:
        return dt_string

# Admin authentication
def authenticate(username, password):
    admin_data = get_admin_data()
    if admin_data.get("username") == username:
        if admin_data.get("password") == hash_password(password):
            return True
    return False

def get_admin_data():
    return load_data(ADMIN_FILE, {})

def update_admin_data(data):
    save_data(ADMIN_FILE, data)

def get_payment_amount():
    admin_data = get_admin_data()
    return admin_data.get("payment_amount", 5000)

def get_payment_accounts():
    admin_data = get_admin_data()
    return admin_data.get("payment_accounts", [])

def get_screenshot_settings():
    admin_data = get_admin_data()
    return admin_data.get("screenshot_settings", {
        "allow_download": True,
        "allow_delete": True,
        "max_file_size_mb": 5
    })

def update_screenshot_settings(settings):
    admin_data = get_admin_data()
    admin_data["screenshot_settings"] = settings
    update_admin_data(admin_data)

def get_security_settings():
    admin_data = get_admin_data()
    return admin_data.get("security_settings", {
        "allow_future_dates": False,
        "require_screenshot_for_paid": True,
        "soft_delete_enabled": False
    })

def get_short_url():
    admin_data = get_admin_data()
    base_url = admin_data.get("base_url", "https://payment-collection-form.streamlit.app")
    short_url_code = admin_data.get("short_url_code", "")
    # Ensure no trailing slash
    base_url = base_url.rstrip('/')
    return f"{base_url}/?student={short_url_code}"

def get_base_url():
    admin_data = get_admin_data()
    base_url = admin_data.get("base_url", "https://payment-collection-form.streamlit.app")
    # Remove trailing slash for consistency
    return base_url.rstrip('/')

def update_base_url(base_url):
    admin_data = get_admin_data()
    # Remove trailing slash before saving
    admin_data["base_url"] = base_url.rstrip('/')
    update_admin_data(admin_data)

def is_form_published():
    admin_data = get_admin_data()
    return admin_data.get("form_published", True)

def toggle_form_publish(status):
    admin_data = get_admin_data()
    admin_data["form_published"] = status
    update_admin_data(admin_data)

def get_contact_info():
    admin_data = get_admin_data()
    return {
        "email": admin_data.get("contact_email", "admin@example.com"),
        "phone": admin_data.get("contact_phone", "+91 9876543210")
    }

def update_contact_info(email, phone):
    admin_data = get_admin_data()
    admin_data["contact_email"] = email
    admin_data["contact_phone"] = phone
    update_admin_data(admin_data)

def get_tab_visibility():
    admin_data = get_admin_data()
    return admin_data.get("tab_visibility", {
        "account_details": True,
        "submit_payment": True,
        "payment_status": True,
        "student_list": True,
        "instructions": True
    })

def update_tab_visibility(tab_visibility):
    admin_data = get_admin_data()
    admin_data["tab_visibility"] = tab_visibility
    update_admin_data(admin_data)

def get_additional_instructions():
    admin_data = get_admin_data()
    return admin_data.get("additional_instructions", "")

def update_additional_instructions(instructions):
    admin_data = get_admin_data()
    admin_data["additional_instructions"] = instructions
    update_admin_data(admin_data)

# Student deletion function with improved structure
def delete_student_by_id(student_id):
    """Delete a student and all associated data"""
    students = get_students()
    
    # Find student
    student_to_delete = None
    for student in students:
        if student.get("id") == student_id:
            student_to_delete = student
            break
    
    if not student_to_delete:
        return False
    
    # Check if soft delete is enabled
    security_settings = get_security_settings()
    if security_settings.get("soft_delete_enabled", False):
        # Soft delete - mark as deleted but keep data
        for student in students:
            if student.get("id") == student_id:
                student["deleted"] = True
                student["deleted_date"] = datetime.now().isoformat()
                break
        save_students(students)
        return True
    
    # Hard delete - remove completely
    # Delete student's screenshot files
    if student_to_delete.get("payments"):
        for payment in student_to_delete["payments"]:
            if payment.get("screenshot"):
                delete_screenshot_file(payment.get("screenshot"))
    
    # Remove student from students list
    updated_students = [s for s in students if s.get("id") != student_id]
    save_students(updated_students)
    
    return True

def delete_multiple_students(student_ids):
    """Delete multiple students and their associated data"""
    success_count = 0
    fail_count = 0
    
    for student_id in student_ids:
        if delete_student_by_id(student_id):
            success_count += 1
        else:
            fail_count += 1
    
    return success_count, fail_count

# Screenshot management
def delete_screenshot_file(filename):
    """Delete screenshot file from server"""
    try:
        if filename:
            file_path = UPLOADS_DIR / filename
            if file_path.exists():
                file_path.unlink()
                return True
    except Exception as e:
        st.error(f"Error deleting screenshot: {e}")
    return False

def remove_screenshot_from_student(student_id, payment_index=0):
    """Remove screenshot reference from student record"""
    students = get_students()
    for student in students:
        if student.get("id") == student_id:
            if "payments" in student and len(student["payments"]) > payment_index:
                student["payments"][payment_index]["screenshot"] = None
                student["payments"][payment_index]["screenshot_deleted"] = True
                student["payments"][payment_index]["screenshot_deleted_date"] = datetime.now().isoformat()
            break
    save_students(students)

def save_uploaded_file(uploaded_file, student_id):
    screenshot_settings = get_screenshot_settings()
    max_size_mb = screenshot_settings.get("max_file_size_mb", 5)
    max_size_bytes = max_size_mb * 1024 * 1024
    
    if uploaded_file.size > max_size_bytes:
        raise ValueError(f"File size exceeds maximum allowed size of {max_size_mb}MB")
    
    file_ext = uploaded_file.name.split('.')[-1]
    filename = f"{student_id}_{uuid.uuid4()}.{file_ext}"
    filepath = UPLOADS_DIR / filename
    
    with open(filepath, 'wb') as f:
        f.write(uploaded_file.getbuffer())
    
    return filename

def get_screenshot_download_button(student, payment_index=0):
    """Helper function to create a download button for student screenshot"""
    if student.get("payments") and len(student["payments"]) > payment_index:
        payment = student["payments"][payment_index]
        if payment.get("screenshot") and not payment.get("screenshot_deleted"):
            screenshot_path = UPLOADS_DIR / payment.get("screenshot")
            if screenshot_path.exists():
                with open(screenshot_path, "rb") as f:
                    screenshot_bytes = f.read()
                
                # Create download button
                st.download_button(
                    label="📥 Download Screenshot",
                    data=screenshot_bytes,
                    file_name=f"{student.get('roll_number')}_{student.get('name')}_payment.{screenshot_path.suffix}",
                    mime="image/png",
                    key=f"dl_{student['id']}_{payment_index}"
                )
                return True
    return False

# Student management with improved structure
def get_students():
    """Get all active students (filter out soft deleted if enabled)"""
    students = load_data(STUDENTS_FILE, [])
    security_settings = get_security_settings()
    
    if security_settings.get("soft_delete_enabled", False):
        # Filter out soft deleted students
        return [s for s in students if not s.get("deleted", False)]
    
    return students

def get_all_students():
    """Get all students including deleted ones"""
    return load_data(STUDENTS_FILE, [])

def save_students(students):
    save_data(STUDENTS_FILE, students)

def get_student_by_id(student_id):
    students = get_students()
    for student in students:
        if student.get("id") == student_id:
            return student
    return None

def get_student_by_roll(roll_number):
    students = get_students()
    for student in students:
        if student.get("roll_number") == roll_number:
            return student
    return None

def get_instructions():
    return load_data(INSTRUCTIONS_FILE, "")

def save_instructions(instructions):
    save_data(INSTRUCTIONS_FILE, instructions)

# Time validation functions
def validate_future_date(date_input, time_input=None, allow_future=False):
    """Validate that date/time is not in the future"""
    current_time = datetime.now()
    
    if time_input:
        # Combine date and time
        input_datetime = datetime.combine(date_input, time_input)
    else:
        # Just date
        input_datetime = datetime.combine(date_input, datetime.min.time())
    
    if not allow_future and input_datetime > current_time:
        return False, "Future dates are not allowed"
    
    return True, ""

def validate_time_components(hour, minute, am_pm):
    """Validate time components"""
    if hour < 1 or hour > 12:
        return False, "Hour must be between 1 and 12"
    
    if minute < 0 or minute > 59:
        return False, "Minute must be between 0 and 59"
    
    if am_pm not in ["AM", "PM"]:
        return False, "AM/PM must be either AM or PM"
    
    return True, ""

# Main app
def main():
    init_files()
    
    # Check if student panel should be shown
    query_params = get_query_params()
    
    # DEBUG: Show query params (set to False in production)
    DEBUG_MODE = False
    if DEBUG_MODE:
        st.sidebar.write("🔍 DEBUG INFO")
        st.sidebar.write("Query Params:", query_params)
        admin_data = get_admin_data()
        st.sidebar.write("Admin Code:", admin_data.get("short_url_code"))
        st.sidebar.write("Base URL:", get_base_url())
    
    if "student" in query_params:
        student_code = query_params["student"]
        admin_data = get_admin_data()
        
        if DEBUG_MODE:
            st.sidebar.write("Student Code from URL:", student_code)
            st.sidebar.write("Code Match:", student_code == admin_data.get("short_url_code"))
        
        if student_code == admin_data.get("short_url_code"):
            show_student_panel()
            return
        else:
            st.error("❌ Invalid student portal URL")
            # Show login option even if URL is invalid
            pass
    
    # Show login/register page
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    
    if not st.session_state.logged_in:
        show_login_page()
    else:
        show_admin_panel()

def show_login_page():
    st.title("🎓 Student Payment System - Admin Login")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            
            if submit:
                if authenticate(username, password):
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Invalid credentials")

def show_student_panel():
    # Check if form is published
    if not is_form_published():
        show_unpublished_message()
        return
    
    # If form is published, show student panel with visible tabs
    st.title("🎓 Student Payment Portal")
    
    # Get admin data
    admin_data = get_admin_data()
    payment_amount = admin_data.get("payment_amount", 5000)
    payment_accounts = get_payment_accounts()
    tab_visibility = get_tab_visibility()
    screenshot_settings = get_screenshot_settings()
    
    # Create tabs based on visibility
    tab_names = []
    tab_functions = []
    
    if tab_visibility.get("account_details", True):
        tab_names.append("Account Details")
        tab_functions.append(lambda: show_account_details_section(payment_accounts, payment_amount, admin_data))
    
    if tab_visibility.get("submit_payment", True):
        tab_names.append("Submit Payment")
        tab_functions.append(lambda: show_submit_payment_section(payment_amount, payment_accounts, screenshot_settings))
    
    if tab_visibility.get("payment_status", True):
        tab_names.append("Payment Status")
        tab_functions.append(lambda: show_payment_status_section())
    
    if tab_visibility.get("student_list", True):
        tab_names.append("Student List")
        tab_functions.append(lambda: show_student_list_section())
    
    if tab_visibility.get("instructions", True):
        tab_names.append("Instructions")
        tab_functions.append(lambda: show_instructions_section())
    
    # Create tabs
    if tab_names:
        tabs = st.tabs(tab_names)
        for i, tab in enumerate(tabs):
            with tab:
                tab_functions[i]()
    else:
        st.warning("No tabs are currently available. Please contact administrator.")

def show_unpublished_message():
    """Show only a message when form is unpublished"""
    contact_info = get_contact_info()
    
    st.markdown(
        """
        <style>
        .unpublished-container {
            text-align: center;
            padding: 50px 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 20px;
            margin: 50px auto;
            max-width: 800px;
        }
        .unpublished-icon {
            font-size: 100px;
            margin-bottom: 20px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown(
        f"""
        <div class="unpublished-container">
            <div class="unpublished-icon">⏸️</div>
            <h1>Payment Form Currently Unavailable</h1>
            <h3>The payment submission form is temporarily unavailable.</h3>
            <p>Please check back later or contact the administrator for more information.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Display contact information
    st.markdown("---")
    st.markdown("### Contact Information")
    st.markdown("If you have urgent queries, please contact:")
    
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"**📧 Email:** {contact_info['email']}")
    with col2:
        st.info(f"**📱 Phone:** {contact_info['phone']}")

def show_account_details_section(payment_accounts, payment_amount, admin_data):
    st.header("💰 Payment Account Details")
    
    if payment_accounts:
        st.success("Please make payment to one of the following accounts:")
        
        for i, account in enumerate(payment_accounts, 1):
            with st.container():
                st.markdown(f"### Account {i}")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.info(f"**Bank:** {account.get('bank', 'Not specified')}")
                with col2:
                    st.info(f"**Account Number:** {account.get('account', 'Not specified')}")
                with col3:
                    st.info(f"**Account Holder:** {account.get('name', 'Not specified')}")
                
                st.divider()
        
        # Payment amount
        st.warning(f"**IMPORTANT:** Payment amount is fixed at PKR {payment_amount}")
        
        # Additional instructions
        additional_instructions = get_additional_instructions()
        if additional_instructions:
            st.markdown("### Additional Instructions")
            st.info(additional_instructions)
    else:
        st.error("No payment account details available. Please contact administrator.")

def show_submit_payment_section(payment_amount, payment_accounts, screenshot_settings):
    st.header("Submit Payment Details")
    
    # Display payment amount reminder
    st.warning(f"Payment Amount: PKR {payment_amount} (fixed)")
    
    max_file_size = screenshot_settings.get("max_file_size_mb", 5)
    
    with st.form("student_payment_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Student Name*")
            roll_number = st.text_input("Roll Number*")
        
        with col2:
            transaction_id = st.text_input("Transaction ID*")
            if payment_accounts:
                payment_account = st.selectbox(
                    "Select Payment Account*",
                    options=[f"{acc.get('bank')} - {acc.get('account')} - {acc.get('name')}" for acc in payment_accounts]
                )
            else:
                payment_account = "No accounts available"
                st.error("No payment accounts available. Please contact administrator.")
        
        payment_screenshot = st.file_uploader(
            f"Upload Payment Screenshot* (Max: {max_file_size}MB)",
            type=['png', 'jpg', 'jpeg'],
            help=f"Maximum file size: {max_file_size}MB"
        )
        remarks = st.text_area("Remarks (Optional)")
        
        # Show current timestamp info
        current_time = datetime.now()
        formatted_time = current_time.strftime("%d-%m-%Y %I:%M %p")
        st.info(f"**Payment Timestamp will be automatically recorded as:** {formatted_time}")
        
        # Required fields note
        st.caption("* Required fields")
        
        submitted = st.form_submit_button("Submit Payment")
        
        if submitted:
            if not all([name, roll_number, transaction_id, payment_screenshot]):
                st.error("Please fill all required fields")
            elif not payment_accounts:
                st.error("No payment accounts available. Please contact administrator.")
            else:
                # Check if roll number already exists
                students = get_students()
                existing = any(s.get("roll_number") == roll_number for s in students)
                
                if existing:
                    st.error("This roll number has already submitted payment")
                else:
                    try:
                        # Auto-set payment datetime to current time
                        payment_datetime = datetime.now()
                        
                        # Create student record with improved structure
                        student_id = str(uuid.uuid4())
                        student_data = {
                            "id": student_id,
                            "name": name,
                            "roll_number": roll_number,
                            "payment_status": "Pending",
                            "admin_remarks": "",
                            "registration_date": datetime.now().isoformat(),
                            "student_remarks": remarks,
                            "added_by_admin": False,
                            "payment_datetime": payment_datetime.isoformat(),
                            "auto_timestamp": True,
                            "payments": [
                                {
                                    "id": str(uuid.uuid4()),
                                    "transaction_id": transaction_id,
                                    "amount": payment_amount,
                                    "screenshot": save_uploaded_file(payment_screenshot, student_id),
                                    "screenshot_deleted": False,
                                    "status": "Pending",
                                    "submission_date": datetime.now().isoformat(),
                                    "payment_datetime": payment_datetime.isoformat(),
                                    "student_remarks": remarks,
                                    "payment_account": payment_account,
                                    "added_by_admin": False,
                                    "auto_timestamp": True,
                                    "verified_by_admin": False
                                }
                            ]
                        }
                        
                        # Save data
                        students.append(student_data)
                        save_students(students)
                        
                        st.success("Payment submitted successfully! Your payment is under review.")
                        st.info(f"Submission timestamp: {formatted_time}")
                        
                    except ValueError as e:
                        st.error(str(e))
                    except Exception as e:
                        st.error(f"An error occurred: {e}")

def show_payment_status_section():
    st.header("Check Payment Status")
    
    roll_number = st.text_input("Enter your Roll Number to check status")
    if st.button("Check Status") and roll_number:
        student = get_student_by_roll(roll_number)
        
        if student:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Name", student.get("name"))
            with col2:
                st.metric("Roll Number", student.get("roll_number"))
            with col3:
                status = student.get("payment_status", "Pending")
                color = {"Paid": "green", "Unpaid": "red", "Pending": "orange"}.get(status, "gray")
                st.markdown(f"**Status:** <span style='color:{color};font-weight:bold'>{status}</span>", 
                          unsafe_allow_html=True)
            
            # Show payment account used
            if student.get("payments") and len(student["payments"]) > 0:
                payment_account = student["payments"][0].get("payment_account", "")
                if payment_account:
                    st.info(f"**Payment Account Used:** {payment_account}")
            
            # Show payment date and time
            if student.get("payment_datetime"):
                formatted_datetime = format_datetime(student.get("payment_datetime"))
                if student.get("auto_timestamp"):
                    st.info(f"**Payment Submission Timestamp:** {formatted_datetime} (Auto-recorded)")
                else:
                    st.info(f"**Payment Date & Time:** {formatted_datetime}")
            
            # Show payment history in list format
            if student.get("payments"):
                st.subheader("Payment History")
                for payment in student["payments"]:
                    payment_date = format_datetime(payment.get("payment_datetime", payment.get("submission_date")))
                    
                    # Create a container for each payment
                    with st.container():
                        col1, col2, col3, col4 = st.columns([3, 2, 2, 3])
                        
                        with col1:
                            st.write(f"**Transaction ID:** {payment.get('transaction_id')}")
                            st.write(f"**Amount:** PKR {payment.get('amount')}")
                        
                        with col2:
                            st.write(f"**Status:** {payment.get('status')}")
                            st.write(f"**Date:** {format_date_only(payment.get('payment_datetime'))}")
                        
                        with col3:
                            st.write(f"**Time:** {datetime.fromisoformat(payment.get('payment_datetime')).strftime('%I:%M %p') if payment.get('payment_datetime') else 'N/A'}")
                            st.write(f"**Account:** {payment.get('payment_account', 'N/A')[:20]}...")
                        
                        with col4:
                            # Screenshot section
                            if payment.get("screenshot_deleted"):
                                st.warning("📸 Screenshot deleted")
                            elif payment.get("screenshot"):
                                screenshot_settings = get_screenshot_settings()
                                if screenshot_settings.get("allow_download", True):
                                    screenshot_path = UPLOADS_DIR / payment.get("screenshot")
                                    if screenshot_path.exists():
                                        with open(screenshot_path, "rb") as f:
                                            img_bytes = f.read()
                                        
                                        # View button
                                        if st.button("👁️ View", key=f"view_{payment['id']}"):
                                            st.image(img_bytes, caption="Payment Screenshot", use_column_width=True)
                                        
                                        # Download button
                                        st.download_button(
                                            "📥 Download",
                                            img_bytes,
                                            file_name=payment.get("screenshot"),
                                            key=f"download_{payment['id']}"
                                        )
                                    else:
                                        st.warning("⚠️ File not found")
                                else:
                                    st.info("📸 Screenshot available")
                            else:
                                st.info("No screenshot")
                        
                        st.divider()
            else:
                st.info("No payment history available")
            
            if student.get("admin_remarks"):
                st.info(f"**Admin Remarks:** {student.get('admin_remarks')}")
        else:
            st.warning("No record found for this roll number")

def show_student_list_section():
    st.header("Student Payment List")
    
    students = get_students()
    if students:
        # Create DataFrames for paid and unpaid
        paid_students = [s for s in students if s.get("payment_status") == "Paid"]
        unpaid_students = [s for s in students if s.get("payment_status") in ["Unpaid", "Pending"]]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader(f"✅ Paid Students ({len(paid_students)})")
            if paid_students:
                df_paid = pd.DataFrame([
                    {
                        "Name": s["name"], 
                        "Roll Number": s["roll_number"],
                        "Status": "Paid",
                        "Payment Date": format_date_only(s.get("payment_datetime", "")),
                        "Registration Date": format_date_only(s.get("registration_date", ""))
                    } 
                    for s in paid_students
                ])
                st.dataframe(df_paid, use_container_width=True)
            else:
                st.info("No paid students yet")
        
        with col2:
            st.subheader(f"❌ Unpaid/Pending ({len(unpaid_students)})")
            if unpaid_students:
                df_unpaid = pd.DataFrame([
                    {
                        "Name": s["name"], 
                        "Roll Number": s["roll_number"],
                        "Status": s.get("payment_status", "Pending"),
                        "Payment Date": format_date_only(s.get("payment_datetime", "")),
                        "Registration Date": format_date_only(s.get("registration_date", ""))
                    } 
                    for s in unpaid_students
                ])
                st.dataframe(df_unpaid, use_container_width=True)
            else:
                st.info("No unpaid students")
    else:
        st.info("No student records available")

def show_instructions_section():
    st.header("Instructions")
    instructions = get_instructions()
    if instructions:
        st.markdown(instructions)
    else:
        st.info("No instructions available from admin")

def show_admin_panel():
    st.sidebar.title("Admin Panel")
    
    # Navigation
    page = st.sidebar.radio(
        "Navigation",
        ["Dashboard", "Student Management", "Payment Settings", "Reports", "Admin Settings", "Screenshot Management"]
    )
    
    # Logout button
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()
    
    # Student portal link
    st.sidebar.markdown("---")
    st.sidebar.subheader("Student Portal")
    short_url = get_short_url()
    st.sidebar.info(f"Student URL: \n{short_url}")
    
    if page == "Dashboard":
        show_admin_dashboard()
    elif page == "Student Management":
        show_student_management()
    elif page == "Payment Settings":
        show_payment_settings()
    elif page == "Reports":
        show_reports()
    elif page == "Admin Settings":
        show_admin_settings()
    elif page == "Screenshot Management":
        show_screenshot_management()

def show_admin_dashboard():
    st.title("📊 Admin Dashboard")
    
    # Statistics
    students = get_students()
    admin_data = get_admin_data()
    payment_accounts = get_payment_accounts()
    form_published = is_form_published()
    tab_visibility = get_tab_visibility()
    screenshot_settings = get_screenshot_settings()
    
    # Form status badge
    col_status, col1, col2, col3 = st.columns([1.5, 1, 1, 1])
    
    with col_status:
        status_color = "green" if form_published else "red"
        status_text = "🟢 PUBLISHED" if form_published else "🔴 UNPUBLISHED"
        st.markdown(f"<h3 style='color:{status_color};'>{status_text}</h3>", unsafe_allow_html=True)
        
        # Quick toggle button
        if form_published:
            if st.button("⏸️ Unpublish Form", type="secondary"):
                toggle_form_publish(False)
                st.success("Form has been unpublished! Students cannot access any tabs.")
                st.rerun()
        else:
            if st.button("▶️ Publish Form", type="primary"):
                toggle_form_publish(True)
                st.success("Form has been published! Students can now access enabled tabs.")
                st.rerun()
    
    with col1:
        st.metric("Total Students", len(students))
    with col2:
        paid_count = len([s for s in students if s.get("payment_status") == "Paid"])
        st.metric("Paid Students", paid_count)
    with col3:
        unpaid_count = len([s for s in students if s.get("payment_status") == "Unpaid"])
        st.metric("Unpaid Students", unpaid_count)
    
    # Form status message
    if not form_published:
        st.error("""
        ⚠️ **Student form is currently UNPUBLISHED.** 
        - Students cannot access any tabs
        - Students will only see an "unavailable" message
        - No student data or instructions will be visible
        """)
    else:
        st.success("""
        ✅ **Student form is PUBLISHED.** 
        - Students can access enabled tabs
        - Students can submit payments (if enabled)
        - Enabled student features are available
        """)
    
    # Short URL display without copy button
    st.divider()
    st.subheader("Student Portal URL")
    
    short_url = get_short_url()
    base_url = get_base_url()
    
    col1, col2 = st.columns([4, 1])
    with col1:
        st.code(short_url)
    with col2:
        st.markdown(f'<a href="{short_url}" target="_blank"><button style="background-color: #4CAF50; color: white; padding: 10px; border: none; border-radius: 5px; cursor: pointer; width: 100%;">🔗 Open Portal</button></a>', unsafe_allow_html=True)
    
    st.info(f"**Base URL:** {base_url}")
    
    # Show what tabs are visible
    if form_published:
        visible_tabs = []
        if tab_visibility.get("account_details"): visible_tabs.append("1. Account Details")
        if tab_visibility.get("submit_payment"): visible_tabs.append("2. Submit Payment")
        if tab_visibility.get("payment_status"): visible_tabs.append("3. Payment Status")
        if tab_visibility.get("student_list"): visible_tabs.append("4. Student List")
        if tab_visibility.get("instructions"): visible_tabs.append("5. Instructions")
        
        if visible_tabs:
            st.success(f"Students can access: {', '.join(visible_tabs)}")
        else:
            st.warning("No tabs are enabled for students")
    else:
        st.warning("Students can only see: 'Payment Form Currently Unavailable' message")
    
    # Current payment accounts
    st.divider()
    st.subheader("Current Payment Accounts")
    if payment_accounts:
        for i, account in enumerate(payment_accounts, 1):
            cols = st.columns(3)
            cols[0].write(f"**Bank {i}:** {account.get('bank')}")
            cols[1].write(f"**Account:** {account.get('account')}")
            cols[2].write(f"**Holder:** {account.get('name')}")
    else:
        st.warning("No payment accounts set up")
    
    # Screenshot settings info
    st.divider()
    st.subheader("Screenshot Settings")
    allow_download = screenshot_settings.get("allow_download", True)
    allow_delete = screenshot_settings.get("allow_delete", True)
    max_size = screenshot_settings.get("max_file_size_mb", 5)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        status = "✅ Enabled" if allow_download else "❌ Disabled"
        st.info(f"**Download:** {status}")
    with col2:
        status = "✅ Enabled" if allow_delete else "❌ Disabled"
        st.info(f"**Delete:** {status}")
    with col3:
        st.info(f"**Max Size:** {max_size}MB")
    
    # Recent submissions
    st.divider()
    st.subheader("Recent Payment Submissions")
    
    if students:
        # Get all payments from all students
        all_payments = []
        for student in students:
            if student.get("payments"):
                for payment in student["payments"]:
                    payment["student_name"] = student.get("name")
                    payment["student_roll"] = student.get("roll_number")
                    all_payments.append(payment)
        
        if all_payments:
            # Sort by payment datetime if available, otherwise by submission date
            recent_payments = sorted(
                all_payments, 
                key=lambda x: x.get("payment_datetime", x.get("submission_date", "")), 
                reverse=True
            )[:10]
            
            for payment in recent_payments:
                payment_date = format_datetime(payment.get("payment_datetime", payment.get("submission_date")))
                with st.expander(f"{payment.get('student_name')} - {payment_date}"):
                    cols = st.columns(4)
                    cols[0].write(f"**Roll:** {payment.get('student_roll')}")
                    cols[1].write(f"**Amount:** PKR {payment.get('amount')}")
                    cols[2].write(f"**Status:** {payment.get('status')}")
                    cols[3].write(f"**Txn ID:** {payment.get('transaction_id')}")
                    
                    # Show payment date and time
                    if payment.get("payment_datetime"):
                        formatted_datetime = format_datetime(payment.get("payment_datetime"))
                        if payment.get("auto_timestamp"):
                            st.write(f"**Submission Timestamp:** {formatted_datetime} (Auto-recorded)")
                        else:
                            st.write(f"**Payment Date & Time:** {formatted_datetime}")
                    
                    # Show submission date
                    submission_date = format_datetime(payment.get("submission_date"))
                    st.write(f"**Form Submission Date:** {submission_date}")
                    
                    if payment.get("payment_account"):
                        st.write(f"**Payment Account:** {payment.get('payment_account')}")
                    
                    # Show who submitted
                    submitted_by = "Admin" if payment.get("added_by_admin") else "Student"
                    st.write(f"**Submitted by:** {submitted_by}")
                    
                    # Show timestamp type
                    if payment.get("auto_timestamp"):
                        st.write("**Timestamp Type:** Auto-generated (Student submission)")
                    else:
                        st.write("**Timestamp Type:** Manually set by Admin")
        else:
            st.info("No payment submissions yet")
    else:
        st.info("No student records available")

def show_student_management():
    st.title("👥 Student Management")
    
    # Add some custom CSS for better button styling
    st.markdown("""
    <style>
    .download-btn {
        background-color: #4CAF50 !important;
        color: white !important;
        border: none !important;
        padding: 5px 10px !important;
        border-radius: 4px !important;
        cursor: pointer !important;
    }
    .download-btn:hover {
        background-color: #45a049 !important;
    }
    .screenshot-btn {
        display: inline-flex;
        align-items: center;
        gap: 5px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["Manage Students", "Add New Student", "Bulk Delete Students"])
    
    with tab1:
        students = get_students()
        
        if students:
            # Filter options
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                filter_status = st.selectbox("Filter by Status", ["All", "Paid", "Unpaid", "Pending"])
            with col2:
                search_term = st.text_input("Search by Name or Roll Number")
            with col3:
                filter_added_by = st.selectbox("Added By", ["All", "Admin", "Student"])
            with col4:
                date_filter = st.selectbox("Filter by Date", ["All", "Today", "Last 7 Days", "This Month"])
            
            # Apply filters
            filtered_students = students
            if filter_status != "All":
                filtered_students = [s for s in filtered_students if s.get("payment_status") == filter_status]
            if search_term:
                filtered_students = [s for s in filtered_students 
                                   if search_term.lower() in s.get("name", "").lower() 
                                   or search_term in s.get("roll_number", "")]
            if filter_added_by != "All":
                if filter_added_by == "Admin":
                    filtered_students = [s for s in filtered_students if s.get("added_by_admin") == True]
                else:
                    filtered_students = [s for s in filtered_students if s.get("added_by_admin") != True]
            
            # Date filter
            if date_filter != "All":
                today = datetime.now().date()
                filtered_by_date = []
                for student in filtered_students:
                    payment_datetime = student.get("payment_datetime")
                    if payment_datetime:
                        try:
                            payment_date = datetime.fromisoformat(payment_datetime).date()
                            if date_filter == "Today" and payment_date == today:
                                filtered_by_date.append(student)
                            elif date_filter == "Last 7 Days" and (today - payment_date).days <= 7:
                                filtered_by_date.append(student)
                            elif date_filter == "This Month" and payment_date.month == today.month and payment_date.year == today.year:
                                filtered_by_date.append(student)
                        except:
                            pass
                filtered_students = filtered_by_date
            
            # Display students in a list view - SINGLE ROW PER STUDENT
            st.subheader(f"Student List ({len(filtered_students)} students)")
            
            for student in filtered_students:
                with st.container():
                    # Create a single row with columns - UPDATED: Added col8 for Download
                    col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([3, 2, 2, 3, 2, 2, 2, 3])
                    
                    with col1:
                        st.write(f"**{student.get('name')}**")
                        st.write(f"Roll: {student.get('roll_number')}")
                    
                    with col2:
                        status = student.get("payment_status", "Pending")
                        color = {"Paid": "green", "Unpaid": "red", "Pending": "orange"}.get(status, "gray")
                        st.markdown(f"<span style='color:{color}; font-weight:bold'>{status}</span>", 
                                  unsafe_allow_html=True)
                    
                    with col3:
                        if student.get("payment_datetime"):
                            formatted_date = format_date_only(student.get("payment_datetime"))
                            st.write(f"**Date:** {formatted_date}")
                    
                    with col4:
                        # Screenshot View and Download buttons
                        if student.get("payments") and len(student["payments"]) > 0:
                            payment = student["payments"][0]
                            if payment.get("screenshot") and not payment.get("screenshot_deleted"):
                                screenshot_path = UPLOADS_DIR / payment.get("screenshot")
                                if screenshot_path.exists():
                                    # View button
                                    if st.button("👁️ View", key=f"view_{student['id']}", 
                                                help="View Screenshot", use_container_width=True):
                                        with open(screenshot_path, "rb") as f:
                                            img_bytes = f.read()
                                        st.image(img_bytes, caption=f"Screenshot for {student.get('name')}", 
                                                use_column_width=True)
                                else:
                                    st.write("File missing")
                            else:
                                st.write("No screenshot")
                        else:
                            st.write("No payments")
                    
                    with col5:
                        # Paid button
                        if student.get("payment_status") != "Paid":
                            if st.button("✅ Paid", key=f"paid_{student['id']}", type="primary", use_container_width=True):
                                student["payment_status"] = "Paid"
                                if student.get("payments"):
                                    for payment in student["payments"]:
                                        payment["status"] = "Paid"
                                save_students(students)
                                st.success(f"Marked {student.get('name')} as Paid")
                                st.rerun()
                    
                    with col6:
                        # Unpaid button
                        if student.get("payment_status") != "Unpaid":
                            if st.button("❌ Unpaid", key=f"unpaid_{student['id']}", type="secondary", use_container_width=True):
                                student["payment_status"] = "Unpaid"
                                if student.get("payments"):
                                    for payment in student["payments"]:
                                        payment["status"] = "Unpaid"
                                save_students(students)
                                st.success(f"Marked {student.get('name')} as Unpaid")
                                st.rerun()
                    
                    with col7:
                        # Delete Student button
                        if st.button("🗑️ Delete", key=f"delete_{student['id']}", type="secondary", use_container_width=True):
                            if delete_student_by_id(student.get("id")):
                                st.success(f"Deleted {student.get('name')}")
                                st.rerun()
                    
                    with col8:
                        # Download Screenshot button
                        if student.get("payments") and len(student["payments"]) > 0:
                            payment = student["payments"][0]
                            if payment.get("screenshot") and not payment.get("screenshot_deleted"):
                                screenshot_path = UPLOADS_DIR / payment.get("screenshot")
                                if screenshot_path.exists():
                                    with open(screenshot_path, "rb") as f:
                                        screenshot_data = f.read()
                                    
                                    # Main Download button with better styling
                                    st.download_button(
                                        label="📥 Download Screenshot",
                                        data=screenshot_data,
                                        file_name=f"{student.get('roll_number')}_{student.get('name')}_payment.{screenshot_path.suffix}",
                                        mime="image/png",
                                        key=f"download_main_{student['id']}",
                                        use_container_width=True
                                    )
                    
                    # Admin Controls expandable section
                    with st.expander(f"Admin Controls for {student.get('name')}"):
                        # Admin Controls Section
                        st.subheader("Admin Controls")
                        
                        col_control1, col_control2 = st.columns(2)
                        
                        with col_control1:
                            # Update payment date
                            st.write("**Update Payment Date & Time**")
                            
                            if student.get("payment_datetime"):
                                current_dt = datetime.fromisoformat(student.get("payment_datetime"))
                            else:
                                current_dt = datetime.now()
                            
                            # Date selection
                            new_payment_date = st.date_input(
                                "New Payment Date",
                                value=current_dt.date(),
                                key=f"date_{student['id']}"
                            )
                            
                            # Time selection with AM/PM
                            col_time1, col_time2, col_time3 = st.columns(3)
                            with col_time1:
                                hour_options = list(range(1, 13))
                                current_hour = current_dt.strftime("%I").lstrip("0")
                                current_hour = "12" if current_hour == "0" else current_hour
                                hour = st.selectbox("Hour", hour_options, index=hour_options.index(int(current_hour)), key=f"hour_{student['id']}")
                            with col_time2:
                                minute_options = [f"{m:02d}" for m in range(0, 60)]
                                current_minute = current_dt.minute
                                minute = st.selectbox("Minute", list(range(0, 60)), index=current_minute, key=f"minute_{student['id']}")
                            with col_time3:
                                am_pm_options = ["AM", "PM"]
                                current_am_pm = current_dt.strftime("%p")
                                am_pm = st.selectbox("AM/PM", am_pm_options, index=am_pm_options.index(current_am_pm), key=f"ampm_{student['id']}")
                            
                            # Convert 12-hour to 24-hour format
                            hour_24 = hour
                            if am_pm == "PM" and hour != 12:
                                hour_24 = hour + 12
                            elif am_pm == "AM" and hour == 12:
                                hour_24 = 0
                            
                            new_payment_datetime = datetime(
                                new_payment_date.year,
                                new_payment_date.month,
                                new_payment_date.day,
                                hour_24,
                                minute
                            )
                            
                            # Validate date/time
                            security_settings = get_security_settings()
                            allow_future = security_settings.get("allow_future_dates", False)
                            is_valid, error_msg = validate_future_date(new_payment_date, new_payment_datetime.time(), allow_future)
                            
                            if not is_valid:
                                st.error(error_msg)
                        
                        with col_control2:
                            # Update payment status
                            st.write("**Update Payment Status**")
                            current_status = student.get("payment_status", "Pending")
                            new_status = st.selectbox(
                                "Status",
                                ["Paid", "Unpaid", "Pending"],
                                index=["Paid", "Unpaid", "Pending"].index(current_status),
                                key=f"status_select_{student['id']}"
                            )
                            
                            # Update account type
                            st.write("**Update Payment Account**")
                            payment_accounts = get_payment_accounts()
                            if payment_accounts:
                                account_options = [f"{acc.get('bank')} - {acc.get('account')} - {acc.get('name')}" for acc in payment_accounts]
                                current_account = ""
                                if student.get("payments") and len(student["payments"]) > 0:
                                    current_account = student["payments"][0].get("payment_account", "")
                                
                                if current_account not in account_options and current_account:
                                    account_options.insert(0, current_account)
                                
                                new_account = st.selectbox(
                                    "Account",
                                    options=account_options,
                                    index=account_options.index(current_account) if current_account in account_options else 0,
                                    key=f"account_select_{student['id']}"
                                )
                            else:
                                new_account = ""
                                st.warning("No payment accounts configured")
                            
                            # Admin remarks
                            st.write("**Admin Remarks**")
                            admin_remarks = st.text_area(
                                "Remarks",
                                value=student.get("admin_remarks", ""),
                                height=100,
                                key=f"remarks_{student['id']}"
                            )
                        
                        # Save changes button
                        if st.button("💾 Save Changes", key=f"save_{student['id']}", type="primary"):
                            if is_valid:
                                # Update student data
                                student["payment_datetime"] = new_payment_datetime.isoformat()
                                student["payment_status"] = new_status
                                student["admin_remarks"] = admin_remarks
                                student["auto_timestamp"] = False
                                
                                # Update payment records
                                if student.get("payments"):
                                    for payment in student["payments"]:
                                        payment["payment_datetime"] = new_payment_datetime.isoformat()
                                        payment["status"] = new_status
                                        payment["auto_timestamp"] = False
                                        if new_account:
                                            payment["payment_account"] = new_account
                                
                                save_students(students)
                                st.success("Student data updated successfully!")
                                st.rerun()
                            else:
                                st.error("Cannot save changes due to validation errors")
                        
                        # Payment History & Screenshot Management in list format
                        st.subheader("Payment History & Screenshots")
                        
                        if student.get("payments"):
                            for idx, payment in enumerate(student["payments"]):
                                col_pay1, col_pay2, col_pay3, col_pay4 = st.columns([2, 2, 2, 3])
                                
                                with col_pay1:
                                    st.write(f"**Txn ID:** {payment.get('transaction_id')}")
                                    st.write(f"**Amount:** PKR {payment.get('amount')}")
                                
                                with col_pay2:
                                    st.write(f"**Status:** {payment.get('status')}")
                                    st.write(f"**Date:** {format_datetime(payment.get('payment_datetime'))}")
                                
                                with col_pay3:
                                    st.write(f"**Account:** {payment.get('payment_account', 'N/A')}")
                                
                                with col_pay4:
                                    # Screenshot management
                                    if payment.get("screenshot"):
                                        if payment.get("screenshot_deleted"):
                                            st.warning("Screenshot deleted")
                                        else:
                                            screenshot_path = UPLOADS_DIR / payment.get("screenshot")
                                            if screenshot_path.exists():
                                                # Create three columns for View, Download, Delete
                                                col_ss1, col_ss2, col_ss3 = st.columns(3)
                                                with col_ss1:
                                                    if st.button("👁️ View", key=f"view_payment_{payment['id']}", use_container_width=True):
                                                        with open(screenshot_path, "rb") as f:
                                                            img_bytes = f.read()
                                                        st.image(img_bytes, caption="Payment Screenshot", use_container_width=True)
                                                with col_ss2:
                                                    # Download button
                                                    if st.download_button(
                                                        "📥 Download",
                                                        data=open(screenshot_path, "rb").read(),
                                                        file_name=f"{student.get('roll_number')}_{payment.get('transaction_id')}.{screenshot_path.suffix}",
                                                        mime="image/png",
                                                        key=f"download_payment_{payment['id']}",
                                                        use_container_width=True
                                                    ):
                                                        st.success("Download started")
                                                with col_ss3:
                                                    if st.button("🗑️ Delete", key=f"del_ss_{payment['id']}", type="secondary", use_container_width=True):
                                                        if delete_screenshot_file(payment.get("screenshot")):
                                                            remove_screenshot_from_student(student["id"], idx)
                                                            st.success("Screenshot deleted")
                                                            st.rerun()
                                            else:
                                                st.error("File not found")
                                    else:
                                        st.info("No screenshot")
                                
                                st.divider()
                        else:
                            st.info("No payment history available")
                    
                    st.divider()
        else:
            st.info("No students found matching your criteria")
    
    # TAB 2: Add New Student
    with tab2:
        st.subheader("Add New Student Manually")
        
        # Load payment accounts for dropdown
        payment_accounts = get_payment_accounts()
        payment_amount = get_payment_amount()
        
        with st.form("add_student_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Student Name*", help="Full name of the student")
                roll_number = st.text_input("Roll Number*", help="Unique roll number")
                payment_status = st.selectbox(
                    "Payment Status*", 
                    ["Paid", "Unpaid", "Pending"],
                    help="Select current payment status"
                )
                
                # Payment date and time with auto-selected current time
                st.write("**Payment Date & Time**")
                col_date1, col_date2 = st.columns(2)
                with col_date1:
                    payment_date = st.date_input(
                        "Payment Date",
                        value=datetime.now().date(),
                        help="Select payment date"
                    )
                with col_date2:
                    # Auto-select current time
                    current_time = datetime.now()
                    col_time1, col_time2, col_time3 = st.columns(3)
                    with col_time1:
                        hour_options = list(range(1, 13))
                        current_hour = current_time.strftime("%I").lstrip("0")
                        current_hour = "12" if current_hour == "0" else current_hour
                        hour = st.selectbox("Hour", hour_options, index=hour_options.index(int(current_hour)))
                    with col_time2:
                        minute_options = list(range(0, 60))
                        current_minute = current_time.minute
                        minute = st.selectbox("Minute", minute_options, index=current_minute)
                    with col_time3:
                        am_pm_options = ["AM", "PM"]
                        current_am_pm = current_time.strftime("%p")
                        am_pm = st.selectbox("AM/PM", am_pm_options, index=am_pm_options.index(current_am_pm))
                
                # Convert 12-hour to 24-hour format
                hour_24 = hour
                if am_pm == "PM" and hour != 12:
                    hour_24 = hour + 12
                elif am_pm == "AM" and hour == 12:
                    hour_24 = 0
                
                payment_datetime = datetime(
                    payment_date.year,
                    payment_date.month,
                    payment_date.day,
                    hour_24,
                    minute
                )
                
                # Validate date/time
                security_settings = get_security_settings()
                allow_future = security_settings.get("allow_future_dates", False)
                is_valid_date, date_error = validate_future_date(payment_date, payment_datetime.time(), allow_future)
                
                if not is_valid_date:
                    st.error(date_error)
                
                # Payment account selection
                if payment_accounts:
                    account_options = [f"{acc.get('bank')} - {acc.get('account')} - {acc.get('name')}" for acc in payment_accounts]
                    account_options.insert(0, "Select Account")
                    
                    selected_account = st.selectbox(
                        "Payment Account Used",
                        options=account_options,
                        index=1 if payment_status == "Paid" and len(account_options) > 1 else 0,
                        help="Select which account the student paid to"
                    )
                else:
                    st.warning("No payment accounts configured. Please add accounts in Payment Settings.")
                    selected_account = None
            
            with col2:
                transaction_id = st.text_input(
                    "Transaction ID", 
                    help="Enter transaction ID if payment is made"
                )
                amount_paid = st.number_input(
                    "Amount Paid (PKR)*",
                    min_value=0,
                    value=payment_amount if payment_status == "Paid" else 0,
                    help="Enter the amount student actually paid"
                )
                
                # Screenshot upload for admin
                st.write("**Payment Screenshot (Optional)**")
                screenshot_settings = get_screenshot_settings()
                max_file_size = screenshot_settings.get("max_file_size_mb", 5)
                payment_screenshot = st.file_uploader(
                    f"Upload Payment Screenshot (Max: {max_file_size}MB)",
                    type=['png', 'jpg', 'jpeg'],
                    help=f"Maximum file size: {max_file_size}MB"
                )
                
                admin_remarks = st.text_area("Admin Remarks", help="Any remarks from admin", height=100)
                
                # Validation for paid without screenshot
                security_settings = get_security_settings()
                require_screenshot = security_settings.get("require_screenshot_for_paid", True)
                
                if payment_status == "Paid" and require_screenshot and not payment_screenshot:
                    st.warning("⚠️ Screenshot is required for paid status")
            
            submitted = st.form_submit_button("Add Student")
            
            if submitted:
                # Validation checks
                if not name or not roll_number:
                    st.error("Please fill all required fields (Name and Roll Number)")
                elif payment_status == "Paid" and amount_paid <= 0:
                    st.error("Please enter a valid amount for paid student")
                elif payment_status == "Paid" and require_screenshot and not payment_screenshot:
                    st.error("Screenshot is required for paid status")
                elif not is_valid_date:
                    st.error("Invalid date/time selected")
                else:
                    # Check for duplicate roll number
                    students = get_students()
                    if any(s.get("roll_number") == roll_number for s in students):
                        st.error("Roll number already exists")
                    else:
                        # Add student with details
                        add_student_with_details(
                            name, roll_number, payment_status, selected_account, 
                            transaction_id, amount_paid, admin_remarks, 
                            payment_datetime, "Admin", payment_screenshot
                        )
    
    # TAB 3: Bulk Delete Students
    with tab3:
        st.subheader("🗑️ Bulk Delete Students")
        st.warning("⚠️ **WARNING:** This action cannot be undone! All selected students and their data will be permanently deleted.")
        
        students = get_students()
        
        if students:
            # Filter options for bulk delete
            col1, col2 = st.columns(2)
            with col1:
                bulk_filter_status = st.selectbox("Filter by Status", ["All", "Paid", "Unpaid", "Pending"], key="bulk_filter")
            with col2:
                bulk_search = st.text_input("Search by Name or Roll Number", key="bulk_search")
            
            # Apply filters
            filtered_students = students
            if bulk_filter_status != "All":
                filtered_students = [s for s in filtered_students if s.get("payment_status") == bulk_filter_status]
            
            if bulk_search:
                filtered_students = [s for s in filtered_students 
                                   if bulk_search.lower() in s.get("name", "").lower() 
                                   or bulk_search in s.get("roll_number", "")]
            
            if filtered_students:
                st.info(f"Found {len(filtered_students)} students matching your criteria")
                
                # Create checkboxes for each student
                selected_students = []
                
                for student in filtered_students:
                    col1, col2, col3 = st.columns([1, 3, 2])
                    with col1:
                        selected = st.checkbox("", key=f"select_{student['id']}")
                        if selected:
                            selected_students.append(student["id"])
                    with col2:
                        st.write(f"**{student.get('name')}**")
                    with col3:
                        st.write(f"Roll: {student.get('roll_number')}")
                    
                    st.divider()
                
                # Summary of selected students
                if selected_students:
                    st.subheader(f"Selected {len(selected_students)} Students for Deletion")
                    
                    # Confirmation for deletion
                    st.error("""
                    **Deletion will permanently remove:**
                    - Student records
                    - All payment records
                    - Uploaded screenshots
                    - All associated data
                    """)
                    
                    # Double confirmation
                    confirm_text = st.text_input("Type 'DELETE' to confirm")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("🗑️ Delete Selected Students", type="secondary", disabled=confirm_text != "DELETE"):
                            if confirm_text == "DELETE":
                                with st.spinner("Deleting selected students..."):
                                    success_count, fail_count = delete_multiple_students(selected_students)
                                    
                                    if success_count > 0:
                                        st.success(f"Successfully deleted {success_count} students!")
                                        if fail_count > 0:
                                            st.warning(f"Failed to delete {fail_count} students")
                                        st.rerun()
                                    else:
                                        st.error("Failed to delete any students")
                            else:
                                st.warning("Please type 'DELETE' to confirm")
                    
                    with col2:
                        if st.button("Clear Selection"):
                            st.rerun()
                else:
                    st.info("Select students by checking the boxes to enable deletion")
            else:
                st.info("No students found matching your criteria")
        else:
            st.info("No students found to delete")

def add_student_with_details(name, roll_number, payment_status, selected_account, 
                            transaction_id, amount_paid, admin_remarks, 
                            payment_datetime, submitted_by, payment_screenshot=None):
    """Helper function to add student with all details"""
    students = get_students()
    
    student_id = str(uuid.uuid4())
    
    # Handle screenshot upload if provided
    screenshot_filename = None
    if payment_screenshot and payment_screenshot.size > 0:
        try:
            screenshot_filename = save_uploaded_file(payment_screenshot, student_id)
        except Exception as e:
            st.error(f"Error uploading screenshot: {e}")
            return
    
    # Create student data with improved structure
    student_data = {
        "id": student_id,
        "name": name,
        "roll_number": roll_number,
        "payment_status": payment_status,
        "admin_remarks": admin_remarks,
        "registration_date": datetime.now().isoformat(),
        "student_remarks": "",
        "added_by_admin": submitted_by == "Admin",
        "payment_datetime": payment_datetime.isoformat(),
        "auto_timestamp": False,  # Admin-added students have manual timestamps
        "payments": []
    }
    
    # Add payment record if status is Paid
    if payment_status == "Paid" and amount_paid > 0:
        payment_record = {
            "id": str(uuid.uuid4()),
            "transaction_id": transaction_id or f"ADMIN-{roll_number}",
            "amount": amount_paid,
            "screenshot": screenshot_filename,
            "screenshot_deleted": False,
            "status": "Paid",
            "submission_date": datetime.now().isoformat(),
            "payment_datetime": payment_datetime.isoformat(),
            "student_remarks": "",
            "admin_remarks": admin_remarks,
            "payment_account": selected_account if selected_account != "Select Account" else "Not specified",
            "added_by_admin": submitted_by == "Admin",
            "auto_timestamp": False,
            "verified_by_admin": True
        }
        student_data["payments"].append(payment_record)
    
    students.append(student_data)
    save_students(students)
    
    st.success("Student added successfully!")
    st.balloons()
    st.rerun()

def show_payment_settings():
    st.title("💰 Payment Settings")
    
    admin_data = get_admin_data()
    form_published = is_form_published()
    contact_info = get_contact_info()
    tab_visibility = get_tab_visibility()
    base_url = get_base_url()
    
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["Basic Settings", "Account Details", "Form Control", "Tab Visibility", "Contact Info", "Instructions", "Security"])
    
    with tab1:
        st.subheader("Payment Configuration")
        
        # Payment Amount and Base URL in a form
        with st.form("basic_settings_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                payment_amount = st.number_input(
                    "Payment Amount (PKR)*",
                    min_value=0,
                    value=admin_data.get("payment_amount", 5000),
                    help="Set the fixed payment amount for students"
                )
                
            with col2:
                # Base URL Configuration
                new_base_url = st.text_input(
                    "Base URL*",
                    value=base_url,
                    help="Your app URL (e.g., https://payment-collection-form.streamlit.app)"
                )
            
            # Generate new short URL code option
            generate_new_code = st.checkbox("Generate new student URL code", value=False)
            
            # Save button
            col1, col2 = st.columns([2, 1])
            with col1:
                save_button = st.form_submit_button("💾 Save Basic Settings", use_container_width=True)
            
            if save_button:
                if not payment_amount or not new_base_url:
                    st.error("Please fill all required fields (*)")
                else:
                    # Update payment amount
                    admin_data["payment_amount"] = payment_amount
                    
                    # Update base URL if changed
                    if new_base_url != base_url:
                        admin_data["base_url"] = new_base_url.strip().rstrip('/')
                        st.success(f"Base URL updated to: {new_base_url}")
                    
                    # Generate new short URL code if requested
                    if generate_new_code:
                        admin_data["short_url_code"] = str(uuid.uuid4())[:8]
                        st.success("New student URL code generated!")
                    
                    update_admin_data(admin_data)
                    st.success("Basic settings saved successfully!")
                    st.rerun()
        
        # Important note about Streamlit Cloud
        st.warning("""
        **Important for Streamlit Cloud:**
        1. Your Base URL should be: `https://payment-collection-form.streamlit.app`
        2. Make sure there's no trailing slash at the end
        3. Student portal URL format: `https://payment-collection-form.streamlit.app/?student=YOUR_CODE`
        """)
        
        # Test URL button
        if st.button("Test Student Portal URL"):
            test_url = f"{base_url}/?student={admin_data.get('short_url_code')}"
            st.info(f"**Test URL:** {test_url}")
            st.markdown(f'<a href="{test_url}" target="_blank">Open Test URL in New Tab</a>', unsafe_allow_html=True)
        
        # Current URL display without copy button
        st.divider()
        st.subheader("Current Student Portal URL")
        
        short_url = get_short_url()
        st.code(short_url)
        
        col1, col2 = st.columns(2)
        with col2:
            st.markdown(f'<a href="{short_url}" target="_blank"><button style="background-color: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; width: 100%;">🔗 Open Portal</button></a>', unsafe_allow_html=True)
    
    with tab2:
        st.subheader("Payment Account Details")
        st.info("These account details will be displayed to students in the payment portal")
        
        accounts = admin_data.get("payment_accounts", [])
        
        # Display current accounts in a form
        with st.form("account_details_form"):
            st.write("**Current Accounts:**")
            
            account_changes = []
            for i, account in enumerate(accounts):
                st.divider()
                st.write(f"**Account {i+1}**")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    bank = st.text_input("Bank Name", value=account.get("bank", ""), key=f"bank_{i}")
                with col2:
                    account_no = st.text_input("Account Number", value=account.get("account", ""), key=f"account_{i}")
                with col3:
                    account_name = st.text_input("Account Holder Name", value=account.get("name", ""), key=f"name_{i}")
                
                account_changes.append({"bank": bank, "account": account_no, "name": account_name})
            
            # Save button
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.form_submit_button("💾 Save Account Details", use_container_width=True):
                    admin_data["payment_accounts"] = account_changes
                    update_admin_data(admin_data)
                    st.success("Account details saved!")
                    st.rerun()
        
        # Add/Remove account buttons
        st.divider()
        st.write("**Quick Actions:**")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("➕ Add New Account"):
                accounts.append({"bank": "", "account": "", "name": ""})
                admin_data["payment_accounts"] = accounts
                update_admin_data(admin_data)
                st.success("New account added!")
                st.rerun()
        
        with col2:
            if len(accounts) > 1:
                if st.button("➖ Remove Last Account"):
                    accounts.pop()
                    admin_data["payment_accounts"] = accounts
                    update_admin_data(admin_data)
                    st.success("Last account removed!")
                    st.rerun()
            else:
                st.button("➖ Remove Last Account", disabled=True, help="Cannot remove the only account")
    
    with tab3:
        st.subheader("📋 Form Control Center")
        
        # Current status
        status_color = "green" if form_published else "red"
        status_icon = "✅" if form_published else "❌"
        status_text = "PUBLISHED" if form_published else "UNPUBLISHED"
        
        st.markdown(f"""
        <div style='background-color:{status_color}20; padding:20px; border-radius:10px; border-left:5px solid {status_color};'>
            <h3>{status_icon} Form Status: <span style='color:{status_color}'>{status_text}</span></h3>
            <p>When the form is unpublished, students see only an "unavailable" message.</p>
            <p>No tabs, no student list, no instructions - nothing is accessible.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Publish Form")
            st.info("Make the payment form available to students")
            if st.button("▶️ Publish Form Now", type="primary", use_container_width=True):
                toggle_form_publish(True)
                st.success("✅ Form has been published! Students can now access enabled tabs.")
                st.rerun()
        
        with col2:
            st.subheader("Unpublish Form")
            st.warning("Completely hide the student portal")
            if st.button("⏸️ Unpublish Form Now", type="secondary", use_container_width=True):
                toggle_form_publish(False)
                st.warning("⏸️ Form has been unpublished! Students will see only an 'unavailable' message.")
                st.rerun()
        
        st.divider()
        
        # Additional Instructions with save button
        st.subheader("Additional Instructions")
        st.info("These instructions appear in the Account Details tab for students")
        
        with st.form("additional_instructions_form"):
            additional_instructions = st.text_area(
                "Enter additional instructions for students",
                value=get_additional_instructions(),
                height=200
            )
            
            if st.form_submit_button("💾 Save Additional Instructions"):
                update_additional_instructions(additional_instructions)
                st.success("Additional instructions saved!")
                st.rerun()
        
        # Form statistics
        st.divider()
        st.subheader("Form Statistics")
        
        students = get_students()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            total_payments = sum(len(s.get("payments", [])) for s in students)
            st.metric("Total Submissions", total_payments)
        with col2:
            pending_count = len([s for s in students if s.get("payment_status") == "Pending"])
            st.metric("Pending Review", pending_count)
        with col3:
            today = datetime.now().date().isoformat()
            today_count = sum(1 for s in students if s.get("registration_date", "").startswith(today))
            st.metric("Today's Submissions", today_count)
    
    with tab4:
        st.subheader("📊 Tab Visibility Control")
        st.info("Control which tabs are visible to students in the payment portal")
        
        # Get current visibility
        tab_visibility = get_tab_visibility()
        
        # Tab visibility settings in a form
        with st.form("tab_visibility_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("### Enable/Disable Tabs")
                
                account_details = st.checkbox(
                    "Account Details Tab",
                    value=tab_visibility.get("account_details", True),
                    help="Shows payment account details and instructions"
                )
                
                submit_payment = st.checkbox(
                    "Submit Payment Tab",
                    value=tab_visibility.get("submit_payment", True),
                    help="Allows students to submit payment forms"
                )
                
                payment_status = st.checkbox(
                    "Payment Status Tab",
                    value=tab_visibility.get("payment_status", True),
                    help="Allows students to check their payment status"
                )
            
            with col2:
                st.write("### ")  # Empty header for alignment
                
                student_list = st.checkbox(
                    "Student List Tab",
                    value=tab_visibility.get("student_list", True),
                    help="Shows list of paid and unpaid students"
                )
                
                instructions = st.checkbox(
                    "Instructions Tab",
                    value=tab_visibility.get("instructions", True),
                    help="Shows general instructions from admin"
                )
            
            # Save button
            if st.form_submit_button("💾 Save Tab Visibility Settings"):
                new_visibility = {
                    "account_details": account_details,
                    "submit_payment": submit_payment,
                    "payment_status": payment_status,
                    "student_list": student_list,
                    "instructions": instructions
                }
                update_tab_visibility(new_visibility)
                st.success("Tab visibility settings saved!")
                st.rerun()
        
        # Preview what students see
        st.divider()
        st.subheader("Student View Preview")
        
        if form_published:
            visible_tabs = []
            if account_details: visible_tabs.append("1. Account Details - Payment accounts info")
            if submit_payment: visible_tabs.append("2. Submit Payment - Payment submission form")
            if payment_status: visible_tabs.append("3. Payment Status - Check payment status")
            if student_list: visible_tabs.append("4. Student List - View paid/unpaid students")
            if instructions: visible_tabs.append("5. Instructions - Admin instructions")
            
            if visible_tabs:
                st.success("**Students see:** Access to enabled tabs with complete functionality")
                st.code("\n".join(visible_tabs))
            else:
                st.error("**Students see:** No tabs available (all tabs are disabled)")
        else:
            st.error("**Students see:** Only an 'unavailable' message with contact info")
    
    with tab5:
        st.subheader("📞 Contact Information")
        st.info("This contact information will be shown to students when the form is unpublished")
        
        current_email = contact_info['email']
        current_phone = contact_info['phone']
        
        with st.form("contact_info_form"):
            email = st.text_input("Contact Email*", value=current_email)
            phone = st.text_input("Contact Phone Number*", value=current_phone)
            
            if st.form_submit_button("💾 Save Contact Information"):
                if email and phone:
                    update_contact_info(email, phone)
                    st.success("Contact information saved successfully!")
                    st.rerun()
                else:
                    st.error("Please fill all required fields (*)")
    
    with tab6:
        st.subheader("Instructions for Students")
        st.info("These instructions appear in the Instructions tab for students")
        
        with st.form("instructions_form"):
            instructions = st.text_area(
                "Enter instructions that will appear in the student panel",
                value=get_instructions(),
                height=300
            )
            
            if st.form_submit_button("💾 Save Instructions"):
                save_instructions(instructions)
                st.success("Instructions saved!")
                st.rerun()
    
    with tab7:
        st.subheader("🔒 Security Settings")
        st.info("Configure security and validation settings for the system")
        
        security_settings = get_security_settings()
        
        with st.form("security_settings_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                allow_future_dates = st.checkbox(
                    "Allow Future Dates",
                    value=security_settings.get("allow_future_dates", False),
                    help="Allow payment dates in the future"
                )
                
                require_screenshot = st.checkbox(
                    "Require Screenshot for Paid Status",
                    value=security_settings.get("require_screenshot_for_paid", True),
                    help="Block paid status without screenshot"
                )
            
            with col2:
                soft_delete_enabled = st.checkbox(
                    "Enable Soft Delete",
                    value=security_settings.get("soft_delete_enabled", False),
                    help="Mark records as deleted instead of permanent removal"
                )
            
            if st.form_submit_button("💾 Save Security Settings"):
                new_settings = {
                    "allow_future_dates": allow_future_dates,
                    "require_screenshot_for_paid": require_screenshot,
                    "soft_delete_enabled": soft_delete_enabled
                }
                admin_data["security_settings"] = new_settings
                update_admin_data(admin_data)
                st.success("Security settings saved!")
                st.rerun()

def show_screenshot_management():
    st.title("📸 Screenshot Management")
    
    screenshot_settings = get_screenshot_settings()
    
    tab1, tab2, tab3 = st.tabs(["Settings", "Bulk Operations", "Statistics"])
    
    with tab1:
        st.subheader("Screenshot Settings")
        
        with st.form("screenshot_settings_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                allow_download = st.checkbox(
                    "Allow Screenshot Download",
                    value=screenshot_settings.get("allow_download", True),
                    help="Enable/disable download option for screenshots"
                )
                
                allow_delete = st.checkbox(
                    "Allow Screenshot Deletion",
                    value=screenshot_settings.get("allow_delete", True),
                    help="Enable/disable delete option for screenshots"
                )
            
            with col2:
                max_file_size = st.number_input(
                    "Maximum File Size (MB)*",
                    min_value=1,
                    max_value=50,
                    value=screenshot_settings.get("max_file_size_mb", 5),
                    help="Maximum allowed file size for uploaded screenshots"
                )
            
            if st.form_submit_button("💾 Save Settings"):
                new_settings = {
                    "allow_download": allow_download,
                    "allow_delete": allow_delete,
                    "max_file_size_mb": max_file_size
                }
                update_screenshot_settings(new_settings)
                st.success("Screenshot settings saved!")
                st.rerun()
    
    with tab2:
        st.subheader("Bulk Screenshot Operations")
        st.warning("⚠️ These operations affect multiple records at once. Use with caution!")
        
        students = get_students()
        
        if students:
            # Get all payments with screenshots
            all_payments = []
            for student in students:
                if student.get("payments"):
                    for payment in student["payments"]:
                        if payment.get("screenshot") and not payment.get("screenshot_deleted"):
                            payment["student_name"] = student.get("name")
                            payment["student_id"] = student.get("id")
                            all_payments.append(payment)
            
            if all_payments:
                st.info(f"Found {len(all_payments)} screenshots")
                
                # Bulk delete option
                if st.button("🗑️ Delete All Screenshots", type="secondary"):
                    with st.spinner("Deleting screenshots..."):
                        deleted_count = 0
                        for payment in all_payments:
                            if delete_screenshot_file(payment.get("screenshot")):
                                # Find and update student record
                                for student in students:
                                    if student.get("id") == payment["student_id"]:
                                        for p in student.get("payments", []):
                                            if p.get("id") == payment.get("id"):
                                                p["screenshot"] = None
                                                p["screenshot_deleted"] = True
                                                p["screenshot_deleted_date"] = datetime.now().isoformat()
                                                break
                                        break
                                deleted_count += 1
                        
                        save_students(students)
                        st.success(f"Successfully deleted {deleted_count} screenshots!")
                        st.rerun()
                
                # Display screenshots
                for payment in all_payments[:10]:  # Show first 10
                    with st.expander(f"{payment.get('student_name')} - {payment.get('transaction_id')}"):
                        col_view, col_del = st.columns(2)
                        with col_view:
                            screenshot_path = UPLOADS_DIR / payment.get("screenshot")
                            if screenshot_path.exists():
                                if st.button("👁️ View", key=f"bulk_view_{payment['id']}"):
                                    with open(screenshot_path, "rb") as f:
                                        img_bytes = f.read()
                                    st.image(img_bytes, caption="Payment Screenshot", use_column_width=True)
                        with col_del:
                            if st.button("🗑️ Delete", key=f"bulk_delete_{payment['id']}", type="secondary"):
                                if delete_screenshot_file(payment.get("screenshot")):
                                    # Update student record
                                    for student in students:
                                        if student.get("id") == payment["student_id"]:
                                            for p in student.get("payments", []):
                                                if p.get("id") == payment.get("id"):
                                                    p["screenshot"] = None
                                                    p["screenshot_deleted"] = True
                                                    p["screenshot_deleted_date"] = datetime.now().isoformat()
                                                    break
                                            break
                                    save_students(students)
                                    st.success("Screenshot deleted!")
                                    st.rerun()
            else:
                st.info("No screenshots found")
        else:
            st.info("No students found")
    
    with tab3:
        st.subheader("Screenshot Analytics")
        
        students = get_students()
        
        if students:
            # Calculate statistics
            total_students = len(students)
            
            # Count screenshots
            total_screenshots = 0
            active_screenshots = 0
            deleted_screenshots = 0
            
            for student in students:
                if student.get("payments"):
                    for payment in student["payments"]:
                        if payment.get("screenshot"):
                            total_screenshots += 1
                            if payment.get("screenshot_deleted"):
                                deleted_screenshots += 1
                            else:
                                active_screenshots += 1
            
            # Display metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Students", total_students)
            with col2:
                st.metric("Active Screenshots", active_screenshots)
            with col3:
                st.metric("Deleted Screenshots", deleted_screenshots)
            
            # Calculate percentages
            if total_students > 0:
                col4, col5 = st.columns(2)
                with col4:
                    students_with_screenshots = sum(1 for s in students if any(p.get("screenshot") and not p.get("screenshot_deleted") for p in s.get("payments", [])))
                    percentage = (students_with_screenshots / total_students) * 100
                    st.metric("Students with Screenshots", f"{students_with_screenshots} ({percentage:.1f}%)")
                
                with col5:
                    if total_screenshots > 0:
                        active_percentage = (active_screenshots / total_screenshots) * 100
                        st.metric("Active Screenshot Rate", f"{active_percentage:.1f}%")
                    else:
                        st.metric("Active Screenshot Rate", "0%")
            
            # Status-based statistics
            st.divider()
            st.subheader("Screenshots by Payment Status")
            
            status_stats = {}
            for status in ["Paid", "Unpaid", "Pending"]:
                status_students = [s for s in students if s.get("payment_status") == status]
                status_screenshots = 0
                for student in status_students:
                    if student.get("payments"):
                        for payment in student["payments"]:
                            if payment.get("screenshot") and not payment.get("screenshot_deleted"):
                                status_screenshots += 1
                
                status_stats[status] = {
                    "students": len(status_students),
                    "screenshots": status_screenshots,
                    "percentage": (status_screenshots / len(status_students) * 100) if len(status_students) > 0 else 0
                }
            
            # Display status statistics
            for status, stats in status_stats.items():
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**{status} Students:** {stats['students']}")
                with col2:
                    st.write(f"**Screenshots:** {stats['screenshots']}")
                with col3:
                    st.write(f"**Coverage:** {stats['percentage']:.1f}%")
                st.divider()

def show_reports():
    st.title("📈 Reports & Analytics")
    
    students = get_students()
    
    tab1, tab2, tab3 = st.tabs(["Student Data", "Export Data", "Analytics"])
    
    with tab1:
        st.subheader("Student Data Summary")
        
        if students:
            # Create DataFrames for paid and unpaid
            paid_students = [s for s in students if s.get("payment_status") == "Paid"]
            unpaid_students = [s for s in students if s.get("payment_status") == "Unpaid"]
            pending_students = [s for s in students if s.get("payment_status") == "Pending"]
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Paid Students", len(paid_students))
            with col2:
                st.metric("Unpaid Students", len(unpaid_students))
            with col3:
                st.metric("Pending Students", len(pending_students))
            
            # Payment summary
            st.divider()
            st.subheader("Payment Summary")
            
            # Calculate total collected amount
            total_collected = 0
            expected_amount = 0
            payment_amount = get_payment_amount()
            
            for student in paid_students:
                if student.get("payments"):
                    for payment in student["payments"]:
                        if payment.get("status") == "Paid":
                            total_collected += payment.get("amount", 0)
                expected_amount += payment_amount
            
            # Calculate statistics
            total_students = len(students)
            paid_percentage = (len(paid_students) / total_students * 100) if total_students > 0 else 0
            collection_rate = (total_collected / expected_amount * 100) if expected_amount > 0 else 0
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Collected", f"PKR {total_collected:,}")
            with col2:
                st.metric("Expected Amount", f"PKR {expected_amount:,}")
            with col3:
                st.metric("Paid Percentage", f"{paid_percentage:.1f}%")
            with col4:
                st.metric("Collection Rate", f"{collection_rate:.1f}%")
            
            # Monthly trend
            st.divider()
            st.subheader("Monthly Collection Trend")
            
            # Group by month
            monthly_data = {}
            for student in students:
                if student.get("payment_datetime") and student.get("payment_status") == "Paid":
                    try:
                        payment_date = datetime.fromisoformat(student.get("payment_datetime"))
                        month_key = payment_date.strftime("%Y-%m")
                        if month_key not in monthly_data:
                            monthly_data[month_key] = {"count": 0, "amount": 0}
                        
                        # Get amount from payments
                        if student.get("payments"):
                            for payment in student["payments"]:
                                if payment.get("status") == "Paid":
                                    monthly_data[month_key]["amount"] += payment.get("amount", 0)
                                    monthly_data[month_key]["count"] += 1
                                    break
                        else:
                            monthly_data[month_key]["amount"] += payment_amount
                            monthly_data[month_key]["count"] += 1
                    except:
                        pass
            
            if monthly_data:
                monthly_df = pd.DataFrame([
                    {"Month": month, "Payments": data["count"], "Amount": data["amount"]}
                    for month, data in monthly_data.items()
                ]).sort_values("Month")
                
                st.line_chart(monthly_df.set_index("Month")[["Amount"]])
                
                # Show monthly table
                st.dataframe(monthly_df, use_container_width=True, hide_index=True)
            
            # Source analysis
            st.divider()
            st.subheader("Submission Source Analysis")
            
            admin_added = len([s for s in students if s.get("added_by_admin")])
            student_submitted = total_students - admin_added
            
            source_data = pd.DataFrame({
                'Source': ['Admin Added', 'Student Submitted'],
                'Count': [admin_added, student_submitted],
                'Percentage': [
                    (admin_added / total_students * 100) if total_students > 0 else 0,
                    (student_submitted / total_students * 100) if total_students > 0 else 0
                ]
            })
            
            st.bar_chart(source_data.set_index('Source')[['Count']])
            st.dataframe(source_data, use_container_width=True, hide_index=True)
            
        else:
            st.info("No student data available")
    
    with tab2:
        st.subheader("Export Student Data")
        
        # Export type selection
        export_type = st.radio(
            "Select Export Type",
            ["Payment Data (CSV/Excel)", "Complete Student Data", "Download All Screenshots"],
            horizontal=True
        )
        
        if export_type == "Payment Data (CSV/Excel)":
            col1, col2 = st.columns(2)
            with col1:
                export_format = st.selectbox("Select Format", ["CSV", "Excel"])
            with col2:
                filter_status = st.selectbox("Filter by Payment Status", ["All", "Paid", "Unpaid", "Pending"])
            
            if students:
                # Filter students
                filtered_students = students
                if filter_status != "All":
                    filtered_students = [s for s in students if s.get("payment_status") == filter_status]
                
                # Convert to DataFrame with Student Remarks
                export_data = []
                for student in filtered_students:
                    # Get payment info
                    payment_info = {}
                    if student.get("payments") and len(student["payments"]) > 0:
                        payment = student["payments"][0]
                        payment_info = {
                            "Transaction ID": payment.get("transaction_id", ""),
                            "Payment Amount": payment.get("amount", 0),
                            "Payment Account": payment.get("payment_account", ""),
                            "Screenshot": "Yes" if payment.get("screenshot") and not payment.get("screenshot_deleted") else "No"
                        }
                    
                    student_data = {
                        "Name": student.get("name"),
                        "Roll Number": student.get("roll_number"),
                        "Payment Status": student.get("payment_status"),
                        "Payment Date": format_datetime(student.get("payment_datetime", "")),
                        "Timestamp Type": "Auto" if student.get("auto_timestamp") else "Manual",
                        "Student Remarks": student.get("student_remarks", ""),  # Added this line
                        "Admin Remarks": student.get("admin_remarks", ""),
                        "Added By": "Admin" if student.get("added_by_admin") else "Student",
                        "Registration Date": format_datetime(student.get("registration_date", ""))
                    }
                    
                    # Merge payment info
                    student_data.update(payment_info)
                    export_data.append(student_data)
                
                if export_data:
                    df = pd.DataFrame(export_data)
                    
                    if export_format == "CSV":
                        csv = df.to_csv(index=False)
                        st.download_button(
                            "📥 Download CSV",
                            csv,
                            file_name=f"student_payments_{filter_status.lower()}_{datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                    else:
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            df.to_excel(writer, index=False, sheet_name='Student Payments')
                        excel_data = output.getvalue()
                        
                        st.download_button(
                            "📥 Download Excel",
                            excel_data,
                            file_name=f"student_payments_{filter_status.lower()}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                    
                    # Show preview
                    st.subheader("Data Preview")
                    st.dataframe(df.head(10), use_container_width=True)
                    
                    # Show statistics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Records", len(export_data))
                    with col2:
                        paid_count = sum(1 for s in filtered_students if s.get("payment_status") == "Paid")
                        st.metric("Paid Records", paid_count)
                    with col3:
                        total_amount = sum(s.get("payments", [{}])[0].get("amount", 0) if s.get("payments") else 0 for s in filtered_students)
                        st.metric("Total Amount", f"PKR {total_amount:,}")
                else:
                    st.info("No data to export for selected filter")
            else:
                st.info("No student data to export")
        
        elif export_type == "Complete Student Data":
            st.info("This export includes ALL student information including complete payment history")
            
            col1, col2 = st.columns(2)
            with col1:
                complete_format = st.selectbox("Select Format", ["Excel (Multiple Sheets)", "CSV (Single Sheet)"])
            with col2:
                include_deleted = st.checkbox("Include Deleted Students", value=False)
            
            if students:
                # Get all students data
                all_students = get_all_students() if include_deleted else students
                
                if complete_format == "Excel (Multiple Sheets)":
                    # Create detailed Excel with multiple sheets
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        # Sheet 1: Student Summary
                        summary_data = []
                        for student in all_students:
                            summary_data.append({
                                "ID": student.get("id"),
                                "Name": student.get("name"),
                                "Roll Number": student.get("roll_number"),
                                "Payment Status": student.get("payment_status"),
                                "Payment Date": format_datetime(student.get("payment_datetime", "")),
                                "Student Remarks": student.get("student_remarks", ""),
                                "Admin Remarks": student.get("admin_remarks", ""),
                                "Added By": "Admin" if student.get("added_by_admin") else "Student",
                                "Registration Date": format_datetime(student.get("registration_date", "")),
                                "Auto Timestamp": "Yes" if student.get("auto_timestamp") else "No",
                                "Deleted": "Yes" if student.get("deleted") else "No",
                                "Deleted Date": format_datetime(student.get("deleted_date", "")) if student.get("deleted_date") else "",
                                "Payment Count": len(student.get("payments", []))
                            })
                        
                        df_summary = pd.DataFrame(summary_data)
                        df_summary.to_excel(writer, sheet_name='Student Summary', index=False)
                        
                        # Sheet 2: Payment Details
                        payment_data = []
                        for student in all_students:
                            if student.get("payments"):
                                for payment in student["payments"]:
                                    payment_data.append({
                                        "Student ID": student.get("id"),
                                        "Student Name": student.get("name"),
                                        "Roll Number": student.get("roll_number"),
                                        "Payment ID": payment.get("id"),
                                        "Transaction ID": payment.get("transaction_id"),
                                        "Amount": payment.get("amount"),
                                        "Status": payment.get("status"),
                                        "Payment Account": payment.get("payment_account"),
                                        "Payment Date": format_datetime(payment.get("payment_datetime", "")),
                                        "Submission Date": format_datetime(payment.get("submission_date", "")),
                                        "Student Remarks": payment.get("student_remarks", ""),
                                        "Admin Remarks": payment.get("admin_remarks", ""),
                                        "Screenshot": payment.get("screenshot"),
                                        "Screenshot Deleted": "Yes" if payment.get("screenshot_deleted") else "No",
                                        "Added By Admin": "Yes" if payment.get("added_by_admin") else "No",
                                        "Auto Timestamp": "Yes" if payment.get("auto_timestamp") else "No",
                                        "Verified By Admin": "Yes" if payment.get("verified_by_admin") else "No"
                                    })
                        
                        if payment_data:
                            df_payments = pd.DataFrame(payment_data)
                            df_payments.to_excel(writer, sheet_name='Payment Details', index=False)
                        
                        # Sheet 3: Student-Payment Bridge (One row per student-payment)
                        bridge_data = []
                        for student in all_students:
                            if student.get("payments"):
                                for payment in student["payments"]:
                                    bridge_record = {
                                        "Student ID": student.get("id"),
                                        "Name": student.get("name"),
                                        "Roll Number": student.get("roll_number"),
                                        "Payment Status": student.get("payment_status"),
                                        "Student Remarks": student.get("student_remarks", ""),
                                        "Admin Remarks": student.get("admin_remarks", ""),
                                        "Added By": "Admin" if student.get("added_by_admin") else "Student",
                                        "Registration Date": format_datetime(student.get("registration_date", "")),
                                        "Payment ID": payment.get("id"),
                                        "Transaction ID": payment.get("transaction_id"),
                                        "Amount": payment.get("amount"),
                                        "Payment Status Detail": payment.get("status"),
                                        "Payment Account": payment.get("payment_account"),
                                        "Payment Date": format_datetime(payment.get("payment_datetime", "")),
                                        "Screenshot": "Yes" if payment.get("screenshot") and not payment.get("screenshot_deleted") else "No",
                                        "Auto Timestamp": "Yes" if payment.get("auto_timestamp") else "No"
                                    }
                                    bridge_data.append(bridge_record)
                            else:
                                # Student without payments
                                bridge_record = {
                                    "Student ID": student.get("id"),
                                    "Name": student.get("name"),
                                    "Roll Number": student.get("roll_number"),
                                    "Payment Status": student.get("payment_status"),
                                    "Student Remarks": student.get("student_remarks", ""),
                                    "Admin Remarks": student.get("admin_remarks", ""),
                                    "Added By": "Admin" if student.get("added_by_admin") else "Student",
                                    "Registration Date": format_datetime(student.get("registration_date", "")),
                                    "Payment ID": "",
                                    "Transaction ID": "",
                                    "Amount": "",
                                    "Payment Status Detail": "",
                                    "Payment Account": "",
                                    "Payment Date": "",
                                    "Screenshot": "",
                                    "Auto Timestamp": ""
                                }
                                bridge_data.append(bridge_record)
                        
                        df_bridge = pd.DataFrame(bridge_data)
                        df_bridge.to_excel(writer, sheet_name='Student-Payment Bridge', index=False)
                        
                        # Sheet 4: Statistics
                        stats_data = {
                            "Metric": ["Total Students", "Active Students", "Deleted Students", 
                                      "Paid Students", "Unpaid Students", "Pending Students",
                                      "Admin Added", "Student Added", "With Screenshots",
                                      "Total Payments", "Total Amount Collected"],
                            "Count": [
                                len(all_students),
                                len([s for s in all_students if not s.get("deleted", False)]),
                                len([s for s in all_students if s.get("deleted", False)]),
                                len([s for s in all_students if s.get("payment_status") == "Paid"]),
                                len([s for s in all_students if s.get("payment_status") == "Unpaid"]),
                                len([s for s in all_students if s.get("payment_status") == "Pending"]),
                                len([s for s in all_students if s.get("added_by_admin")]),
                                len([s for s in all_students if not s.get("added_by_admin")]),
                                len([s for s in all_students if any(p.get("screenshot") and not p.get("screenshot_deleted") 
                                                                  for p in s.get("payments", []))]),
                                sum(len(s.get("payments", [])) for s in all_students),
                                sum(p.get("amount", 0) for s in all_students for p in s.get("payments", []) if p.get("status") == "Paid")
                            ]
                        }
                        
                        df_stats = pd.DataFrame(stats_data)
                        df_stats.to_excel(writer, sheet_name='Statistics', index=False)
                    
                    excel_data = output.getvalue()
                    
                    st.download_button(
                        "📥 Download Complete Data (Excel)",
                        excel_data,
                        file_name=f"complete_student_data_{datetime.now().strftime('%Y%m%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                
                elif complete_format == "CSV (Single Sheet)":
                    # Create flattened CSV with all data in one sheet
                    flattened_data = []
                    
                    for student in all_students:
                        # Get all payments for this student
                        payments = student.get("payments", [])
                        
                        if payments:
                            # Create one row per payment
                            for payment in payments:
                                record = {
                                    "Student ID": student.get("id"),
                                    "Name": student.get("name"),
                                    "Roll Number": student.get("roll_number"),
                                    "Student Payment Status": student.get("payment_status"),
                                    "Student Remarks": student.get("student_remarks", ""),
                                    "Admin Remarks": student.get("admin_remarks", ""),
                                    "Added By": "Admin" if student.get("added_by_admin") else "Student",
                                    "Registration Date": format_datetime(student.get("registration_date", "")),
                                    "Auto Timestamp": "Yes" if student.get("auto_timestamp") else "No",
                                    "Deleted": "Yes" if student.get("deleted") else "No",
                                    "Deleted Date": format_datetime(student.get("deleted_date", "")) if student.get("deleted_date") else "",
                                    
                                    # Payment Details
                                    "Payment ID": payment.get("id"),
                                    "Transaction ID": payment.get("transaction_id"),
                                    "Payment Amount": payment.get("amount"),
                                    "Payment Status": payment.get("status"),
                                    "Payment Account": payment.get("payment_account"),
                                    "Payment Date": format_datetime(payment.get("payment_datetime", "")),
                                    "Payment Submission Date": format_datetime(payment.get("submission_date", "")),
                                    "Payment Student Remarks": payment.get("student_remarks", ""),
                                    "Payment Admin Remarks": payment.get("admin_remarks", ""),
                                    "Screenshot File": payment.get("screenshot"),
                                    "Screenshot Deleted": "Yes" if payment.get("screenshot_deleted") else "No",
                                    "Payment Added By Admin": "Yes" if payment.get("added_by_admin") else "No",
                                    "Payment Auto Timestamp": "Yes" if payment.get("auto_timestamp") else "No",
                                    "Payment Verified": "Yes" if payment.get("verified_by_admin") else "No"
                                }
                                flattened_data.append(record)
                        else:
                            # Student without payments
                            record = {
                                "Student ID": student.get("id"),
                                "Name": student.get("name"),
                                "Roll Number": student.get("roll_number"),
                                "Student Payment Status": student.get("payment_status"),
                                "Student Remarks": student.get("student_remarks", ""),
                                "Admin Remarks": student.get("admin_remarks", ""),
                                "Added By": "Admin" if student.get("added_by_admin") else "Student",
                                "Registration Date": format_datetime(student.get("registration_date", "")),
                                "Auto Timestamp": "Yes" if student.get("auto_timestamp") else "No",
                                "Deleted": "Yes" if student.get("deleted") else "No",
                                "Deleted Date": format_datetime(student.get("deleted_date", "")) if student.get("deleted_date") else "",
                                
                                # Empty payment fields
                                "Payment ID": "",
                                "Transaction ID": "",
                                "Payment Amount": "",
                                "Payment Status": "",
                                "Payment Account": "",
                                "Payment Date": "",
                                "Payment Submission Date": "",
                                "Payment Student Remarks": "",
                                "Payment Admin Remarks": "",
                                "Screenshot File": "",
                                "Screenshot Deleted": "",
                                "Payment Added By Admin": "",
                                "Payment Auto Timestamp": "",
                                "Payment Verified": ""
                            }
                            flattened_data.append(record)
                    
                    if flattened_data:
                        df_flat = pd.DataFrame(flattened_data)
                        csv_data = df_flat.to_csv(index=False)
                        
                        st.download_button(
                            "📥 Download Complete Data (CSV)",
                            csv_data,
                            file_name=f"complete_student_data_{datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                        
                        # Show preview
                        st.subheader("Data Preview (First 10 rows)")
                        st.dataframe(df_flat.head(10), use_container_width=True)
                        
                        # Show statistics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total Students", len(all_students))
                        with col2:
                            st.metric("Total Records", len(flattened_data))
                        with col3:
                            total_payments = sum(len(s.get("payments", [])) for s in all_students)
                            st.metric("Total Payments", total_payments)
                    else:
                        st.info("No data to export")
                
                # Show data preview for all formats
                st.divider()
                st.subheader("Data Preview")
                if all_students:
                    preview_df = pd.DataFrame([
                        {
                            "Name": s.get("name"),
                            "Roll": s.get("roll_number"),
                            "Status": s.get("payment_status"),
                            "Student Remarks": s.get("student_remarks", ""),
                            "Admin Remarks": s.get("admin_remarks", ""),
                            "Payments": len(s.get("payments", []))
                        } 
                        for s in all_students[:10]
                    ])
                    st.dataframe(preview_df, use_container_width=True)
                    if len(all_students) > 10:
                        st.caption(f"Showing 10 of {len(all_students)} students")
            else:
                st.info("No student data to export")
        
        else:  # Download All Screenshots
            st.subheader("Download All Screenshots as ZIP")
            st.warning("⚠️ This may take some time depending on the number of screenshots.")
            
            # Get all active screenshots
            all_screenshots = []
            for student in students:
                if student.get("payments"):
                    for payment in student["payments"]:
                        if payment.get("screenshot") and not payment.get("screenshot_deleted"):
                            screenshot_path = UPLOADS_DIR / payment.get("screenshot")
                            if screenshot_path.exists():
                                all_screenshots.append({
                                    "path": screenshot_path,
                                    "filename": payment.get("screenshot"),
                                    "student_name": student.get("name"),
                                    "roll_number": student.get("roll_number"),
                                    "transaction_id": payment.get("transaction_id")
                                })
            
            if all_screenshots:
                st.success(f"Found {len(all_screenshots)} screenshots available for download")
                
                # Show screenshot statistics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Screenshots", len(all_screenshots))
                with col2:
                    total_size_mb = sum(s["path"].stat().st_size for s in all_screenshots) / (1024 * 1024)
                    st.metric("Total Size", f"{total_size_mb:.2f} MB")
                with col3:
                    unique_students = len(set(s["roll_number"] for s in all_screenshots))
                    st.metric("Unique Students", unique_students)
                
                # Show sample list
                with st.expander("View Screenshot List"):
                    for i, ss in enumerate(all_screenshots[:20]):
                        col1, col2, col3 = st.columns([1, 3, 3])
                        col1.write(f"{i+1}.")
                        col2.write(f"📸 {ss['student_name']}")
                        col3.write(f"Roll: {ss['roll_number']}")
                    
                    if len(all_screenshots) > 20:
                        st.info(f"... and {len(all_screenshots) - 20} more screenshots")
                
                # Create ZIP file
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for ss in all_screenshots:
                        # Create meaningful filename
                        safe_name = ss['student_name'].replace(' ', '_').replace('/', '_')
                        safe_roll = ss['roll_number'].replace(' ', '_').replace('/', '_')
                        file_ext = ss['filename'].split('.')[-1]
                        new_filename = f"{safe_roll}_{safe_name}_{ss['transaction_id']}.{file_ext}"
                        
                        # Add file to zip
                        zip_file.write(ss['path'], new_filename)
                
                # Download button
                st.download_button(
                    "📦 Download All Screenshots as ZIP",
                    zip_buffer.getvalue(),
                    file_name=f"student_screenshots_{datetime.now().strftime('%Y%m%d_%H%M')}.zip",
                    mime="application/zip",
                    use_container_width=True
                )
            else:
                st.info("No screenshots found to download")
    
    with tab3:
        st.subheader("Analytics Dashboard")
        
        if students:
            # Status distribution
            status_counts = {}
            for student in students:
                status = student.get("payment_status", "Pending")
                status_counts[status] = status_counts.get(status, 0) + 1
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Payment Status Distribution**")
                status_df = pd.DataFrame(list(status_counts.items()), columns=['Status', 'Count'])
                st.bar_chart(status_df.set_index('Status'))
            
            with col2:
                st.write("**Screenshot Analysis**")
                
                # Calculate screenshot statistics
                with_screenshot = 0
                without_screenshot = 0
                
                for student in students:
                    has_screenshot = False
                    if student.get("payments"):
                        for payment in student["payments"]:
                            if payment.get("screenshot") and not payment.get("screenshot_deleted"):
                                has_screenshot = True
                                break
                    
                    if has_screenshot:
                        with_screenshot += 1
                    else:
                        without_screenshot += 1
                
                screenshot_data = pd.DataFrame({
                    'Category': ['With Screenshot', 'Without Screenshot'],
                    'Count': [with_screenshot, without_screenshot]
                })
                st.bar_chart(screenshot_data.set_index('Category'))
            
            # Real-time analytics
            st.divider()
            st.subheader("Real-time Analytics")
            
            # Today's activity
            today = datetime.now().date()
            today_students = []
            for student in students:
                try:
                    reg_date = datetime.fromisoformat(student.get("registration_date", "")).date()
                    if reg_date == today:
                        today_students.append(student)
                except:
                    pass
            
            # This week's activity
            week_ago = today - timedelta(days=7)
            recent_students = []
            for student in students:
                try:
                    reg_date = datetime.fromisoformat(student.get("registration_date", "")).date()
                    if reg_date >= week_ago:
                        recent_students.append(student)
                except:
                    pass
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Today's Registrations", len(today_students))
            with col2:
                st.metric("This Week's Registrations", len(recent_students))
            with col3:
                avg_daily = len(students) / max(1, (datetime.now().date() - datetime.fromisoformat(min(s.get("registration_date") for s in students if s.get("registration_date"))).date()).days)
                st.metric("Average Daily", f"{avg_daily:.1f}")
            
            # Performance metrics
            st.divider()
            st.subheader("Performance Metrics")
            
            # Calculate conversion rate (pending to paid)
            pending_to_paid = 0
            total_pending = len([s for s in students if s.get("payment_status") == "Pending"])
            for student in students:
                if student.get("payment_status") == "Paid":
                    # Check if was previously pending
                    if student.get("payments"):
                        for payment in student["payments"]:
                            if payment.get("status_history"):
                                # Check status changes
                                pass
                            pending_to_paid += 1
                            break
            
            conversion_rate = (pending_to_paid / total_pending * 100) if total_pending > 0 else 0
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Pending to Paid Conversion", f"{conversion_rate:.1f}%")
            with col2:
                # Calculate average processing time
                processing_times = []
                for student in students:
                    if student.get("payment_status") == "Paid" and student.get("payments"):
                        for payment in student["payments"]:
                            if payment.get("submission_date") and payment.get("verified_date"):
                                try:
                                    submit_date = datetime.fromisoformat(payment.get("submission_date"))
                                    verify_date = datetime.fromisoformat(payment.get("verified_date"))
                                    processing_times.append((verify_date - submit_date).total_seconds() / 3600)  # in hours
                                except:
                                    pass
                
                avg_processing = sum(processing_times) / len(processing_times) if processing_times else 0
                st.metric("Avg Processing Time", f"{avg_processing:.1f} hours")
            
            # Data quality metrics
            st.divider()
            st.subheader("Data Quality Metrics")
            
            complete_records = 0
            for student in students:
                has_name = bool(student.get("name"))
                has_roll = bool(student.get("roll_number"))
                has_status = bool(student.get("payment_status"))
                has_date = bool(student.get("payment_datetime"))
                
                if has_name and has_roll and has_status and has_date:
                    complete_records += 1
            
            data_quality = (complete_records / len(students) * 100) if students else 0
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Complete Records", f"{data_quality:.1f}%")
            with col2:
                # Screenshot quality
                valid_screenshots = 0
                total_screenshots = 0
                for student in students:
                    if student.get("payments"):
                        for payment in student["payments"]:
                            if payment.get("screenshot") and not payment.get("screenshot_deleted"):
                                total_screenshots += 1
                                # Check if file exists
                                screenshot_path = UPLOADS_DIR / payment.get("screenshot")
                                if screenshot_path.exists():
                                    valid_screenshots += 1
                
                screenshot_quality = (valid_screenshots / total_screenshots * 100) if total_screenshots > 0 else 0
                st.metric("Valid Screenshots", f"{screenshot_quality:.1f}%")
        else:
            st.info("No data available for analytics")

def show_admin_settings():
    st.title("⚙️ Admin Settings")
    
    admin_data = get_admin_data()
    
    tab1, tab2 = st.tabs(["Change Credentials", "System Info"])
    
    with tab1:
        st.subheader("Change Username and Password")
        
        with st.form("change_credentials"):
            current_password = st.text_input("Current Password*", type="password")
            new_username = st.text_input("New Username*", value=admin_data.get("username", ""))
            new_password = st.text_input("New Password*", type="password")
            confirm_password = st.text_input("Confirm New Password*", type="password")
            
            if st.form_submit_button("💾 Update Credentials"):
                if not current_password or not new_username or not new_password or not confirm_password:
                    st.error("Please fill all required fields (*)")
                elif not authenticate(admin_data.get("username"), current_password):
                    st.error("Current password is incorrect")
                elif new_password != confirm_password:
                    st.error("New passwords don't match")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters")
                else:
                    admin_data["username"] = new_username
                    admin_data["password"] = hash_password(new_password)
                    update_admin_data(admin_data)
                    st.success("Credentials updated successfully!")
                    st.rerun()
    
    with tab2:
        st.subheader("System Information")
        
        students = get_students()
        contact_info = get_contact_info()
        tab_visibility = get_tab_visibility()
        base_url = get_base_url()
        screenshot_settings = get_screenshot_settings()
        security_settings = get_security_settings()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.info(f"Total Students: {len(students)}")
            st.info(f"Payment Amount: PKR {admin_data.get('payment_amount', 5000)}")
            st.info(f"Form Status: {'Published' if is_form_published() else 'Unpublished'}")
            st.info(f"Base URL: {base_url}")
            st.info(f"Student URL Code: {admin_data.get('short_url_code')}")
            st.info(f"Contact Email: {contact_info['email']}")
            st.info(f"Contact Phone: {contact_info['phone']}")
        
        with col2:
            st.info(f"Upload Directory: {UPLOADS_DIR}")
            st.info(f"Data Directory: {DATA_DIR}")
            st.info(f"Payment Accounts: {len(get_payment_accounts())}")
            st.info(f"Admin Added Students: {len([s for s in students if s.get('added_by_admin')])}")
            st.info(f"Auto Timestamps: {len([s for s in students if s.get('auto_timestamp')])}")
            st.info(f"Screenshot Download: {'Enabled' if screenshot_settings.get('allow_download') else 'Disabled'}")
            st.info(f"Screenshot Delete: {'Enabled' if screenshot_settings.get('allow_delete') else 'Disabled'}")
            st.info(f"Soft Delete: {'Enabled' if security_settings.get('soft_delete_enabled') else 'Disabled'}")
        
        # Tab visibility status
        st.divider()
        st.subheader("Tab Visibility Status")
        
        visible_tabs = []
        if tab_visibility.get("account_details"): visible_tabs.append("Account Details")
        if tab_visibility.get("submit_payment"): visible_tabs.append("Submit Payment")
        if tab_visibility.get("payment_status"): visible_tabs.append("Payment Status")
        if tab_visibility.get("student_list"): visible_tabs.append("Student List")
        if tab_visibility.get("instructions"): visible_tabs.append("Instructions")
        
        st.success(f"Visible tabs for students: {', '.join(visible_tabs) if visible_tabs else 'None'}")
        
        # Full student URL without copy button
        st.divider()
        st.subheader("Full Student Portal URL")
        st.code(get_short_url())
        
        col1, col2 = st.columns(2)
        with col2:
            st.markdown(f'<a href="{get_short_url()}" target="_blank"><button style="background-color: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; width: 100%;">🔗 Open Student Portal</button></a>', unsafe_allow_html=True)
        
        # Data backup
        st.divider()
        st.subheader("Data Backup")
        
        if st.button("Export All Data as Backup", use_container_width=True):
            all_data = {
                "students": get_all_students(),  # Include deleted if soft delete enabled
                "admin": get_admin_data(),
                "instructions": get_instructions()
            }
            
            json_data = json.dumps(all_data, indent=2)
            st.download_button(
                "Download Backup",
                json_data,
                file_name=f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )

if __name__ == "__main__":
    main()
