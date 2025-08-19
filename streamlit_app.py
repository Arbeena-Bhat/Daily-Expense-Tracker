import streamlit as st
from streamlit import json
import json
import requests
import pandas as pd
from datetime import datetime, timedelta
import re

API_BASE = "http://127.0.0.1:8000"

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="Daily Expense Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Hide Streamlit default UI elements
# hide_streamlit_style = """
#     <style>
#     #MainMenu {visibility: hidden;}
#     footer {visibility: hidden;}
#     header {visibility: hidden;}
#     </style>
# """
# st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# =========================
# ENSURE SIDEBAR TOGGLE IS ALWAYS VISIBLE
# =========================
show_sidebar_toggle = """
<style>
[data-testid="collapsedControl"] {
    display: block !important;   /* 👈 always show expand/collapse button */
}
</style>
"""
st.markdown(show_sidebar_toggle, unsafe_allow_html=True)

# =========================
# SESSION STATE
# =========================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user" not in st.session_state:
    st.session_state.user = {}
if "email_id" not in st.session_state:
    st.session_state.email_id = None
if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "login"

# =========================
# API HELPERS
# =========================
def get_roles():
    try:
        res = requests.get(f"{API_BASE}/roles/")
        if res.status_code == 200:
            return res.json()
        else:
            st.warning(f"⚠ Could not load roles: Server responded with status {res.status_code}")
    except Exception as e:
        st.warning(f"⚠ Could not load roles: {e}")
    return []

# =====================
# USER HELPERS
# =====================
def login_user(email, password):
    params = {"email": email, "password": password}
    try:
        res = requests.get(f"{API_BASE}/users/login", params=params)
        if res.status_code == 200:
            return res.json(), None
        else:
            return None, res.json().get("detail", "Login failed")
    except Exception as e:
        return None, str(e)

def register_user(first_name, middle_name, last_name, email, password, role_name):
    payload = {
        "first_name": first_name,
        "middle_name": middle_name,
        "last_name": last_name,
        "email_id": email,
        "password": password,
        "role_name": role_name
    }
    try:
        res = requests.post(f"{API_BASE}/users/register", json=payload)
        if res.status_code == 200:
            return True, None
        else:
            return False, res.json().get("detail", "Registration failed")
    except Exception as e:
        return False, str(e)
    
def get_all_users():
    try:
        res = requests.get(f"{API_BASE}/users/")
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        st.error(f"⚠ Could not fetch users: {e}")
    return []


def update_user(user_id: str, updated_data: dict):
    """Update user details."""
    try:
        resp = requests.put(f"{API_BASE}/users/{user_id}", json=updated_data)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def delete_user(user_id: str):
    """Delete a user by their ID."""
    try:
        resp = requests.delete(f"{API_BASE}/users/{user_id}")
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}
# --------------------
# FUNDS HELPERS
# --------------------
# ✅ Funds
def add_user_funds(email_id, amount):
    """Allocate funds for a user."""
    try:
        res = requests.post(
            f"{API_BASE}/funds/allocate",
            json={"email_id": email_id, "amount": amount},
        )
        return res.json()
    except Exception as e:
        return {"error": str(e)}


def get_user_funds(email_id):
    """Fetch current funds info (total, spent, balance)."""
    try:
        res = requests.get(f"{API_BASE}/funds", params={"email_id": email_id})
        if res.status_code == 200:
            data = res.json()
            return {
                "total_funds": data.get("total_funds", 0),
                "spent": data.get("spent", 0),
                "balance": data.get("balance", 0),
            }
        return {"error": res.text}
    except Exception as e:
        return {"error": str(e)}


def update_user_funds(email_id, new_total):
    """Update user’s total funds directly."""
    try:
        res = requests.put(
            f"{API_BASE}/funds/update",
            json={"email_id": email_id, "total_funds": new_total},
        )
        return res.json()
    except Exception as e:
        return {"error": str(e)}


def reset_user_funds(email_id):
    """Delete user funds record (reset)."""
    try:
        res = requests.delete(f"{API_BASE}/funds/{email_id}")
        return res.json()
    except Exception as e:
        return {"error": str(e)}
    
# =====================
# CATEGORY HELPERS
# =====================

def get_categories():
    try:
        resp = requests.get(f"{API_BASE}/categories/")
        if resp.status_code == 200:
            categories = resp.json()
            # Ensure _id is always a string
            for cat in categories:
                if "_id" in cat:
                    cat["_id"] = str(cat["_id"])
            return categories
        else:
            return []
    except Exception as e:
        st.error(f"Error fetching categories: {e}")
        return []

def get_top_categories(email_id):
    """Fetch top spending categories for a user."""
    params = {"email_id": email_id}
    try:
        res = requests.get(f"{API_BASE}/summary/top-categories", params=params)
        if res.status_code == 200:
            try:
                data = res.json()
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict) and "top_categories" in data:
                    return data["top_categories"]
                else:
                    return []
            except Exception as e:
                st.error(f"⚠ Error parsing top categories: {e}")
                return []
        else:
            st.warning(f"⚠ Could not fetch top categories (status {res.status_code})")
            return []
    except Exception as e:
        st.error(f"⚠ Could not load top categories: {e}")
        return []


# def get_summary_by_category(email_id):
#     """Fetch summary of expenses grouped by category."""
#     params = {"email_id": email_id}
#     try:
#         res = requests.get(f"{API_BASE}/summary/by-category", params=params)
#         if res.status_code == 200:
#             try:
#                 data = res.json()
#                 if isinstance(data, list):
#                     return data
#                 elif isinstance(data, dict) and "category_summary" in data:
#                     return data["category_summary"]
#                 else:
#                     return []
#             except Exception as e:
#                 st.error(f"⚠ Error parsing category summary: {e}")
#                 return []
#         else:
#             st.warning(f"⚠ Could not fetch category summary (status {res.status_code})")
#             return []
#     except Exception as e:
#         st.error(f"⚠ Could not load category summary: {e}")
#         return []
def get_summary_by_category(email_id):
    """Fetch summary of expenses grouped by category."""
    params = {"email_id": email_id}
    try:
        res = requests.get(f"{API_BASE}/summary/by-category", params=params)
        if res.status_code == 200:
            try:
                data = res.json()
                # Handle different possible formats
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict):
                    # If backend returns category_summary key
                    if "category_summary" in data and isinstance(data["category_summary"], list):
                        return data["category_summary"]
                    # If backend returns categories as keys with spent amounts
                    elif all(isinstance(v, (int, float)) for v in data.values()):
                        return [{"category": k, "spent": v} for k, v in data.items()]
                    else:
                        return []
                else:
                    return []
            except Exception as e:
                st.error(f"⚠ Error parsing category summary: {e}")
                return []
        else:
            st.warning(f"⚠ Could not fetch category summary (status {res.status_code})")
            return []
    except Exception as e:
        st.error(f"⚠ Could not load category summary: {e}")
        return []


# def add_category(name):
#     payload = {"name": name}
#     try:
#         res = requests.post(f"{API_BASE}/categories/", json=payload)
#         return res.status_code in [200, 201]
#     except Exception as e:
#         st.error(f"⚠ Error connecting to backend: {e}")
#     return False

def add_category(name):
    payload = {"name": name}
    try:
        res = requests.post(f"{API_BASE}/categories/", json=payload)
        if res.status_code in [200, 201]:
            return True, f"Category '{name}' added successfully!"
        else:
            # Extract backend error message if available
            try:
                error_msg = res.json().get("detail", "Unknown error occurred.")
            except Exception:
                error_msg = res.text or "Unknown error occurred."
            return False, error_msg
    except Exception as e:
        return False, f"Error connecting to backend: {e}"


def update_category(category_id: str, updated_data: dict):
    """Update a category name."""
    try:
        resp = requests.put(f"{API_BASE}/categories/{category_id}", json=updated_data)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def delete_category(category_id: str):
    """Delete a category by ID."""
    try:
        resp = requests.delete(f"{API_BASE}/categories/{category_id}")
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}
    
  # =====================
# EXPENSE HELPERS
# =====================
 
def get_expenses(email_id, start_date=None, end_date=None, category=None):
    params = {"email_id": email_id}
    if start_date:
        params["start"] = start_date
    if end_date:
        params["end"] = end_date
    if category:
        params["category"] = category

    try:
        res = requests.get(f"{API_BASE}/expenses/", params=params)
        if res.status_code == 200:
            data = res.json()
            expenses = data.get("expenses", [])
            funds = data.get("funds", {"total_funds": 0, "spent": 0, "balance": 0})
            return expenses, funds
        else:
            st.warning(f"⚠ Could not fetch expenses (status {res.status_code})")
            return [], {"total_funds": 0, "spent": 0, "balance": 0}
    except Exception as e:
        st.error(f"⚠ Error connecting to backend: {e}")
        return [], {"total_funds": 0, "spent": 0, "balance": 0}

def add_expense(email_id, amount, category, date, description=""):
    """Add a new expense entry."""
    payload = {
        "amount": amount,
        "category": category,
        "date": date,
        "description": description or "",
        "email_id": email_id,
    }
    try:
        res = requests.post(
            f"{API_BASE}/expenses/",
            params={"email_id": email_id},
            json=payload
        )
        if res.status_code in [200, 201]:
            return True, res.json() if res.content else {"message": "Expense added."}
        else:
            return False, {"error": res.text}
    except Exception as e:
        return False, {"error": f"⚠ Error connecting to backend: {e}"}

def update_expense(expense_id: str, updated_data: dict, email_id: str):
    """Update an existing expense by ID."""
    try:
        res = requests.put(
            f"{API_BASE}/update/expenses/{expense_id}",
            params={"email_id": email_id},
            json=updated_data
        )
        if res.status_code == 200:
            return res.json()
        return {"error": res.text}
    except Exception as e:
        return {"error": f"⚠ Error updating expense: {e}"}

def get_monthly_summary(email_id):
    params = {"email_id": email_id}
    try:
        res = requests.get(f"{API_BASE}/summary/monthly", params=params)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        st.error(f"⚠ Could not load monthly summary: {e}")
    # return []
    # Always return dict with same structure
    # return {"monthly_summary": [], "funds": {}}
    return {"monthly_summary": [], "funds": {"total_funds": 0, "spent": 0, "balance": 0}}


# =========================
# AUTH SCREENS
# =========================
if not st.session_state.authenticated:
    st.title("💰 Daily Expense Tracker")

    if st.session_state.auth_mode == "login":
        st.subheader("🔑 Login")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if st.button("Sign In"):
            if not email or not password:
                st.warning("Please enter both email and password.")
            else:
                user_data, error = login_user(email, password)
                if user_data:
                    st.session_state.authenticated = True
                    st.session_state.user = user_data.get("user", {})
                    st.session_state.email_id = st.session_state.user.get("email_id")
                    st.success("✅ Login successful! Redirecting...")
                    st.rerun()
                else:
                    st.error(f"❌ {error}")

        if st.button("Create an account"):
            st.session_state.auth_mode = "register"
            st.rerun()

    else:  # Register
        st.subheader("📝 Register New Account")
        first_name = st.text_input("First Name")
        middle_name = st.text_input("Middle Name")
        last_name = st.text_input("Last Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        role_name = st.selectbox("Role", ["User", "Admin"])

        if st.button("Register"):
            if not first_name or not last_name or not email or not password:
                st.warning("Please fill in all required fields.")
            else:
                success, message = register_user(first_name, middle_name, last_name, email, password, role_name)
                if success:
                    st.success("✅ Registration successful! Please login.")
                    st.session_state.auth_mode = "login"
                    st.rerun()
                else:
                    st.error(f"❌ {message}")

        if st.button("Already have an account?"):
            st.session_state.auth_mode = "login"
            st.rerun()

# =========================
# MAIN APP (LOGGED IN)
# =========================
else:
    st.title("💰 Daily Expense Tracker")
    st.sidebar.write(f"👋 Welcome, {st.session_state.user.get('first_name', '')}!")
    if st.sidebar.button("🚪 Logout"):
        st.session_state.authenticated = False
        st.session_state.user = {}
        st.session_state.email_id = None
        st.rerun()

    role = st.session_state.user.get("role_name", "user").lower()
    tabs_to_show = []

    if role == "admin":
        tabs_to_show = [
            "📂 View Categories",
            "➕ Add Categories",
            "👥 View Users",
            "✏️ Update User",
            "❌ Delete User",
            "✏️ Update Category",
            "❌ Delete Category"
        ]
    else:
        tabs_to_show = [
            "💵 Manage Funds",
            "💳 Category Funds Overview",
            "📜 View & Filter Expenses",
            "➕ Add Expenses",
            "📅 Monthly Summary",
            "🏆 Top Categories",
            # "📊 Summary by Category",
            "✏️ Update My Expense"
        ]

    tab_objects = st.tabs(tabs_to_show)
    tab_mapping = {tabs_to_show[i]: tab_objects[i] for i in range(len(tabs_to_show))}
    if role=="admin":
        # ------------------------
        # Admin only: View Categories
        # ------------------------
        if "📂 View Categories" in tab_mapping:
            with tab_mapping["📂 View Categories"]:
                st.subheader("📂 All Categories")
                categories = get_categories()
                if categories:
                    # Extract only category names
                    category_names = [cat.get("name", "") for cat in categories]
                    st.dataframe(pd.DataFrame(category_names, columns=["Category Name"]))    
                    # st.dataframe(pd.DataFrame(categories)) 
                else:
                    st.warning("No categories found.")

        # -------------------
        # VIEW USERS (Admin)
        # -------------------
        if "👥 View Users" in tab_mapping:  
            with tab_mapping["👥 View Users"]:    
                st.subheader("👥 All Registered Users")  
                users = get_all_users()
                if users:
                    st.dataframe(pd.DataFrame(users))
                else:
                    st.warning("No users found.")
        # ------------------------
        # (  Update User Admin)
        # ------------------------
        if "✏️ Update User" in tab_mapping:
            with tab_mapping["✏️ Update User"]:
                st.subheader("✏️ Update User")
                users = get_all_users()
                # st.write(users)
                if users:
                    user_df = pd.DataFrame(users)
                    # Build mapping: display label -> user_id
                    user_options = {
                    f"{row['first_name']} {row.get('last_name', '')} ({row['email_id']})": row["id"]
                    for _, row in user_df.iterrows()
                    }
                    # # Select user
                    # selected_user_id = st.selectbox("Select User to Update", user_df["id"])
                    # Dropdown with name + email shown, id stored
                    selected_label = st.selectbox("Select User to Update", list(user_options.keys()))
                    selected_user_id = user_options[selected_label]
                    # Get selected user data
                    selected_user_data = user_df[user_df["id"] == selected_user_id].iloc[0].to_dict()
                    # Input fields with correct dict access
                    first_name = st.text_input("First Name", selected_user_data.get("first_name", ""))
                    middle_name = st.text_input("Middle Name", selected_user_data.get("middle_name", ""))
                    last_name = st.text_input("Last Name", selected_user_data.get("last_name", ""))
                    email_id = st.text_input("Email", selected_user_data.get("email_id", ""))  # <-- Editable email
                    role_name = st.selectbox("Role", ["User", "Admin"], index=0 if selected_user_data.get("role_name", "").lower() == "user" else 1)
                    password = st.text_input("Password (leave blank to keep unchanged)", type="password")

                    # Update button
                    if st.button("Update User"):
                        updated_data = {
                            "first_name": (first_name or "").strip().title(),
                            "middle_name": (middle_name or "").strip().title(),
                            "last_name": (last_name or "").strip().title(),
                            "email_id": (email_id or "").strip().lower(),
                            "role_name": role_name
                            
                        }
                        # Only include password if entered
                        if password.strip():
                            updated_data["password"] = password.strip()
                        
                        # ✅ Email validation
                        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
                        if not re.match(email_pattern, updated_data["email_id"]):
                            st.error("⚠ Please enter a valid email address.")
                        else:
                            resp = update_user(selected_user_id, updated_data)
                        
                            if "error" not in resp:
                                st.success("✅ User updated successfully!")
                            
                            else:
                                st.error(f"⚠ {resp['error']}")
                            
                else:
                    st.warning("No users found to update.")
                
    # ------------------------
    # Admin only: Delete User
    # ------------------------
        if "❌ Delete User" in tab_mapping:
            with tab_mapping["❌ Delete User"]:
                st.subheader("❌ Delete User")

                users = get_all_users()
                if users:
                    user_df = pd.DataFrame(users)

                    # Remove the currently logged-in user (prevent self-deletion)
                    if "email_id" in st.session_state:
                        user_df = user_df[user_df["email_id"] != st.session_state["email_id"]]
                    
                    if not user_df.empty:
                        # Create display label: "Full Name (Email)"
                        # user_df["label"] = user_df["first_name"] + " (" + user_df["email_id"] + ")"
                        user_df["label"] = (user_df["first_name"] + " " + user_df["last_name"] + " (" + user_df["email_id"] + ")")
                    
                        # Sort alphabetically by display name
                        user_df = user_df.sort_values(by="label")

                        # Create mapping from label -> id
                        label_to_id = dict(zip(user_df["label"], user_df["id"]))

                        # Show selectbox with labels
                        selected_label = st.selectbox("Select User to Delete", user_df["label"])

                        # Get the selected user_id
                        selected_user_id = label_to_id[selected_label]

                        if st.button("Delete User"):
                            resp = delete_user(selected_user_id)

                            if "error" not in resp:
                                st.success("✅ User deleted successfully!")
                            else:
                                st.error(f"⚠ {resp['error']}")
                    else:
                        st.error(f"⚠ {resp['error']}")            
                else:
                    st.warning("No users found to delete.")
                    
        # ------------------------
        # Admin only: Update Category
        # ------------------------
        if "✏️ Update Category" in tab_mapping:
            with tab_mapping["✏️ Update Category"]:
                st.subheader("✏️ Update Category")
                categories = get_categories()
                # st.write("Debug: categories raw response →", categories)  # see what's coming
                if categories and isinstance(categories, list):
                    cat_df = pd.DataFrame(categories)
                    # st.write("Debug: cat_df →", cat_df)  # see actual table
                    # Check columns directly
                    if "id" in cat_df.columns and "name" in cat_df.columns:
                        # Ensure IDs are non-empty strings (likely Mongo ObjectIds)
                        valid_mask = cat_df["id"].apply(lambda x: isinstance(x, str) and len(x) > 10)
                        valid_cats = cat_df[valid_mask]

                        if not valid_cats.empty:
                            cat_ids = valid_cats["id"].tolist()
                            cat_names = valid_cats["name"].tolist()

                            selected_index = st.selectbox(
                                "Select Category to Update",
                                range(len(cat_ids)),
                                format_func=lambda i: cat_names[i]
                            )

                            selected_cat_id = cat_ids[selected_index]
                            selected_cat_name = cat_names[selected_index]
                            new_name = st.text_input("New Category Name", selected_cat_name)

                            if st.button("Update Category"):
                                resp = update_category(selected_cat_id, {"name": new_name})
                                if "error" not in resp:
                                    st.success("✅ Category updated successfully!")  
                                else:
                                    st.error(f"⚠ {resp['error']}")
                        else:
                            st.warning("No valid category IDs found in backend response.")
                    else:
                        st.warning("No valid category data available.")
                else:
                    st.warning("No categories found to update.")                   
        # ------------------------
        # Admin only: Delete Category
        # ------------------------
        if "❌ Delete Category" in tab_mapping:
            with tab_mapping["❌ Delete Category"]:
                st.subheader("❌ Delete Category")
                categories = get_categories()
                if categories:
                    cat_df = pd.DataFrame(categories)    
                    # st.write("Debug: cat_df columns", cat_df.columns)  # optional for debugging
                    # Only continue if 'id' and 'name' exist
                    if "id" in cat_df.columns and "name" in cat_df.columns:  
                        selected_index = st.selectbox("Select Category to Delete",range(len(cat_df)),format_func=lambda i: cat_df["name"].iloc[i])
                        selected_cat_id = cat_df["id"].iloc[selected_index]
                        if st.button("Delete Category"):
                            resp = delete_category(selected_cat_id)
                            if "error" not in resp:
                                st.success("✅ Category deleted successfully!")
                            else:
                                st.error(f"⚠ {resp['error']}")
                    else:
                        st.warning("No valid category IDs found.")    
                else:
                    st.warning("No categories found to delete.")  
  
            # ------------------------
    # Admin only: Add Categories
    # ------------------------
        if "➕ Add Categories" in tab_mapping:
            with tab_mapping["➕ Add Categories"]:
                st.subheader("➕ Add New Category")
                with st.form("category_form"):
                    category_name = st.text_input("Category Name")
                    submitted = st.form_submit_button("Add Category")
                    if submitted:
                        if not category_name.strip():
                            st.warning("⚠ Please enter a valid category name.")
                        else:
                            success, message = add_category(category_name.strip())
                            if success:
                                st.success(f"✅ {message}")
                            else:
                                st.error(f"⚠ {message}")
        
    else:
    # ------------------------
    # Manage Funds Tab
    # ------------------------
        if "💵 Manage Funds" in tab_mapping:
            with tab_mapping["💵 Manage Funds"]:
                st.subheader("💵 Manage Your Funds")
                user_funds = get_user_funds(st.session_state.email_id)

                col1, col2, col3 = st.columns(3)
                col1.metric("💰 Total Funds", f"₹{user_funds.get('total_funds', 0):.2f}")
                col2.metric("💸 Spent", f"₹{user_funds.get('spent', 0):.2f}")
                col3.metric("💵 Balance", f"₹{user_funds.get('balance', 0):.2f}")

                st.markdown("---")
                st.subheader("➕ Add Funds to Your Account")
                with st.form("add_funds_form"):
                    new_funds = st.number_input("Amount to Add", min_value=0.0, format="%.2f")
                    submitted = st.form_submit_button("Add Funds")
                    if submitted:
                        if new_funds <= 0:
                            st.warning("⚠ Enter a positive amount to add.")
                        else:
                            if add_user_funds(st.session_state.email_id, new_funds):
                                st.success(f"✅ ₹{new_funds:.2f} added successfully!")
                                st.rerun()
                            else:
                                st.error("⚠ Could not add funds. Try again later.")  

        if "💳 Category Funds Overview" in tab_mapping:
            with tab_mapping["💳 Category Funds Overview"]:
                st.subheader("💳 Category-Wise Funds Overview")

                # 1️⃣ Fetch expenses and funds
                all_expenses, funds = get_expenses(st.session_state.email_id)  # now returns (expenses, funds)
                categories = get_categories()
                category_names = [cat["name"] for cat in categories] if categories else []

                if not category_names:
                    st.warning("No categories available. Add categories first.")
                else:
                    # 2️⃣ Aggregate spent per category
                    spent_per_category = {cat: 0 for cat in category_names}
                    if all_expenses and isinstance(all_expenses, list):
                        for exp in all_expenses:
                            if isinstance(exp, dict):
                                cat = exp.get("category")
                                amt = exp.get("amount", 0)
                                if cat in spent_per_category:
                                    spent_per_category[cat] += amt

                    # 3️⃣ Display allocated funds per category
                    st.info(f"💰 Total Funds: ₹{funds.get('total_funds', 0):.2f}")
                    st.info(f"💸 Total Spent: ₹{funds.get('spent', 0):.2f}")
                    st.info(f"💵 Balance: ₹{funds.get('balance', 0):.2f}")

                    # 4️⃣ Build a dataframe
                    df_cat = pd.DataFrame({
                        "Category": category_names,
                        "Spent": [spent_per_category[cat] for cat in category_names],
                    })
                    df_cat["Remaining"] = df_cat["Spent"].apply(
                        lambda x: max(funds.get("total_funds", 0) / len(category_names) - x, 0)
                    )
                    st.dataframe(df_cat)

                    # 5️⃣ Visualize category-wise spending
                    st.bar_chart(df_cat.set_index("Category")[["Spent", "Remaining"]])

        # ------------------------
        # View & Filter Expenses
        # ------------------------
        if "📜 View & Filter Expenses" in tab_mapping:
            with tab_mapping["📜 View & Filter Expenses"]:
                st.subheader("📜 View & Filter Expenses")

                categories = get_categories()
                category_names = [cat["name"] for cat in categories] if categories else []

                start_date = st.date_input("Start Date", value=datetime.today() - timedelta(days=30))
                end_date = st.date_input("End Date", value=datetime.today())
                category_filter = st.selectbox("Filter by Category", ["All"] + category_names)

                if category_filter == "All":
                    category_filter = None

                expenses, funds = get_expenses(
                    st.session_state.email_id,
                    str(start_date),
                    str(end_date),
                    category_filter
                )

                if expenses:
                    st.dataframe(pd.DataFrame(expenses))
                    # ✅ Show funds info directly from API response
                    st.metric("💰 Total Funds", f"₹{funds.get('total_funds', 0):,.2f}")
                    st.metric("📉 Spent", f"₹{funds.get('spent', 0):,.2f}")
                    st.metric("💵 Balance", f"₹{funds.get('balance', 0):,.2f}")
                else:
                    st.info("No expenses found.")


        # ------------------------
        # Add Expenses
        # ------------------------
        if "➕ Add Expenses" in tab_mapping:
            with tab_mapping["➕ Add Expenses"]:
                st.subheader("➕ Add New Expense")
                categories = get_categories()
                category_names = [cat["name"] for cat in categories] if categories else []
                
                # user_funds = get_user_funds(st.session_state.email_id)
                # balance = user_funds.get("balance", 0)
                user_funds: dict = get_user_funds(st.session_state.email_id)
                balance: float = float(user_funds.get("balance", 0) or 0)

                st.info(f"💵 Available Balance: ₹{balance:.2f}")

                with st.form("expense_form"):
                    col1, col2 = st.columns(2)
                    amount = col1.number_input("Amount", min_value=0.0, format="%.2f")
                    category_name = col2.selectbox("Category", category_names if category_names else ["No categories available"])
                    date = st.date_input("Date", value=datetime.today())
                    description = st.text_area("Description")
                    submitted = st.form_submit_button("Add Expense")
                    if submitted:
                        if amount <= 0:
                            st.warning("⚠ Please enter a valid amount.")
                        #new line added
                        elif amount > balance:
                            st.error("⚠ Insufficient balance. Add funds to continue.")
                        elif category_name == "No categories available":
                            st.warning("⚠ Please add categories first.")
                        else:
                            if add_expense(st.session_state.email_id, amount, category_name, date.strftime("%Y-%m-%d"), description):
                                st.success(f"✅ Expense of ₹{amount:.2f} added successfully!")
                            else:
                                st.error("⚠ Could not add expense.")

        # ------------------------
        # Monthly Summary
        # ------------------------
        # if "📅 Monthly Summary" in tab_mapping:s
        #     with tab_mapping["📅 Monthly Summary"]:
        #         st.subheader("📅 Monthly Expense Summary")
        #         monthly_data = get_monthly_summary(st.session_state.email_id)
                
        #         if monthly_data:
        #             df_monthly = pd.DataFrame(monthly_data)
        #             if 'month' in df_monthly.columns:
        #                 df_monthly['month'] = pd.to_datetime(df_monthly['month'])
        #                 df_monthly = df_monthly.sort_values(by='month')
        #                 st.dataframe(df_monthly)
        #                 st.line_chart(df_monthly.set_index('month')['total_expense'])
        #             else:
        #                 st.warning("Monthly data format is invalid.")
        #         else:
        #             st.warning("No monthly summary data found.")
        # ------------------------
    # Monthly Summary
    # ------------------------
        if "📅 Monthly Summary" in tab_mapping:
            with tab_mapping["📅 Monthly Summary"]:
                st.subheader("📅 Monthly Expense Summary")

                monthly_data = get_monthly_summary(st.session_state.email_id)

                if monthly_data:
                    # ------------------------
                    # Handle Monthly Summary
                    # ------------------------
                    summary_list = monthly_data.get("monthly_summary", [])
                    if summary_list:
                        df_monthly = pd.DataFrame(summary_list)
                        if 'month' in df_monthly.columns:
                            df_monthly['month'] = pd.to_datetime(df_monthly['month'])
                            df_monthly = df_monthly.sort_values(by='month')
                            st.dataframe(df_monthly)
                            st.line_chart(df_monthly.set_index('month')['total_expense'])
                        else:
                            st.warning("Monthly data format is invalid.")
                    else:
                        st.warning("No monthly summary data found.")

                    # ------------------------
                    # Handle Funds
                    # ------------------------
                    funds = monthly_data.get("funds", {})
                    if funds:
                        st.subheader("💵 Funds Overview")
                        col1, col2, col3 = st.columns(3)
                        col1.metric("💰 Total Funds", f"₹{funds.get('total_funds', 0):,.0f}")
                        col2.metric("💸 Spent", f"₹{funds.get('spent', 0):,.0f}")
                        col3.metric("🏦 Balance", f"₹{funds.get('balance', 0):,.0f}")
                else:
                    st.warning("No monthly summary data found.")

        if "🏆 Top Categories" in tab_mapping:
            with tab_mapping["🏆 Top Categories"]:
                st.subheader("🏆 Top Spending Categories")
                top_cats = get_top_categories(st.session_state.email_id)

                if not top_cats:
                    st.warning("No top categories data found.")
                else:
                    # Ensure it's always a list of dicts
                    if isinstance(top_cats, dict):
                        top_cats = [top_cats]
                    elif isinstance(top_cats, list) and all(isinstance(x, list) for x in top_cats):
                        # Convert list of lists into dicts
                        top_cats = [{"category": x[0], "total": x[1]} for x in top_cats]

                    try:
                        df_top = pd.DataFrame(top_cats)
                        if "category" in df_top.columns and "total" in df_top.columns:
                            st.dataframe(df_top)
                            st.bar_chart(df_top.set_index("category")["total"])
                        else:
                            st.warning("Top categories data format is invalid.")
                    except Exception as e:
                        st.error(f"⚠ Could not display top categories: {e}")


    # # ------------------------
    # # Summary by Category
    # # ------------------------
    #     if "📊 Summary by Category" in tab_mapping:
    #         with tab_mapping["📊 Summary by Category"]:
    #             st.subheader("📊 Expense Summary by Category")
    #             summary_data = get_summary_by_category(st.session_state.email_id)
    #             if summary_data:
    #                 df_summary = pd.DataFrame(summary_data)
    #                 if 'category' in df_summary.columns:
    #                     st.dataframe(df_summary)
    #                     st.bar_chart(df_summary.set_index('category')['total'])
    #                 else:
    #                     st.warning("Invalid category summary data format.")
    #             else:
    #                 st.warning("No category summary data found.")
    # ------------------------
    # Summary by Category
    # ------------------------
        if "📊 Summary by Category" in tab_mapping:
            with tab_mapping["📊 Summary by Category"]:
                st.subheader("📊 Expense Summary by Category")
                summary_data = get_summary_by_category(st.session_state.email_id)

                if summary_data:
                    df_summary = pd.DataFrame(summary_data)

                    # Handle different key names for amount
                    if "total" in df_summary.columns:
                        value_column = "total"
                    elif "spent" in df_summary.columns:
                        value_column = "spent"
                    else:
                        st.warning("Invalid category summary data format.")
                        value_column = None

                    if value_column:
                        if "category" in df_summary.columns:
                            st.dataframe(df_summary)
                            st.bar_chart(df_summary.set_index("category")[value_column])
                        else:
                            st.warning("Category field not found in summary data.")
                else:
                    st.warning("No category summary data found.")


        if "✏️ Update My Expense" in tab_mapping:
            with tab_mapping["✏️ Update My Expense"]:
                st.subheader("✏️ Update My Expense")

                # Fetch user's expenses (unpack expenses and funds)
                expenses, _ = get_expenses(st.session_state.email_id)

                if expenses and isinstance(expenses, list):
                    # Convert to DataFrame safely
                    expense_df = pd.DataFrame(expenses)

                    if not expense_df.empty:
                        # Select expense to update
                        selected_expense_id = st.selectbox(
                            "Select Expense to Update",
                            expense_df["id"],
                            # format_func=lambda x: f"{expense_df.loc[expense_df['id'] == x, 'category'].values[0]} | ₹{expense_df.loc[expense_df['id'] == x, 'amount'].values[0]} | {expense_df.loc[expense_df['id'] == x, 'date'].values[0]}"
                            format_func=lambda x: (
                            f"{expense_df.loc[expense_df['id'] == x].iloc[0]['category']} | "
                            f"₹{expense_df.loc[expense_df['id'] == x].iloc[0]['amount']} | "
                            f"{expense_df.loc[expense_df['id'] == x].iloc[0]['date']}")
                        )

                        selected_expense = expense_df.loc[expense_df["id"] == selected_expense_id].iloc[0]

                        # Input fields to update
                        col1, col2 = st.columns(2)
                        new_amount = col1.number_input(
                            "Amount",
                            value=float(selected_expense.get("amount", 0.0)),
                            min_value=0.0,
                            format="%.2f"
                        )

                        categories = get_categories()
                        category_names = [cat["name"] for cat in categories] if categories else []
                        new_category = col2.selectbox(
                            "Category",
                            category_names,
                            index=category_names.index(selected_expense.get("category", category_names[0])) if selected_expense.get("category") in category_names else 0
                        )

                        new_date = st.date_input(
                            "Date",
                            value=pd.to_datetime(selected_expense.get("date", pd.Timestamp.today())).date()
                        )

                        new_description = st.text_area(
                            "Description",
                            value=selected_expense.get("description", "")
                        )

                        # Update button
                        if st.button("Update Expense ✅"):
                            if not st.session_state.email_id:
                                st.error("⚠ You are not logged in!")
                            else:
                                updated_data = {
                                    "amount": new_amount,
                                    "category": new_category,
                                    "date": new_date.strftime("%Y-%m-%d"),
                                    "description": new_description
                                }

                                try:
                                    res = requests.put(
                                        f"{API_BASE}/update/expenses/{selected_expense_id}",
                                        params={"email_id": st.session_state.email_id},
                                        json=updated_data
                                    )

                                    if res.status_code == 200:
                                        st.success("✅ Expense updated successfully!")
                                    else:
                                        st.error(f"❌ Failed: {res.json().get('detail', res.text)}")
                                except Exception as e:
                                    st.error(f"⚠ Error updating expense: {e}")
                    else:
                        st.info("No expenses found to update.")
                else:
                    st.info("No expenses found to update.")

