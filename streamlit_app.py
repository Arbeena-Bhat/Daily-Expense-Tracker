import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

# Backend API base URL
API_BASE = "http://127.0.0.1:8000"

# --- Utility Functions ---
# @st.cache_data  # Caches the result to speed up repeated calls
def get_categories():
    try:
        res = requests.get(f"{API_BASE}/categories/")
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        st.warning(f"⚠ Could not load categories: {e}")
    return []

def get_expenses(start_date=None, end_date=None, category=None):
    params = {}
    if start_date:
        params["start"] = start_date
    if end_date:
        params["end"] = end_date
    if category:
        params["category"] = category
    try:
        res = requests.get(f"{API_BASE}/expenses/", params=params)
        if res.status_code == 200:
            return res.json()
    except:
        pass
    return []

def add_expense(amount, category, date, description):
    payload = {
        "amount": amount,
        "category": category,
        "date": date,
        "description": description
    }
    try:
        res = requests.post(f"{API_BASE}/expenses/", json=payload)
        if res.status_code in [200, 201]:
            return True
        else:
            # Log actual backend error if available
            try:
                detail = res.json().get("detail", "")
                st.warning(f"⚠ Could not add expense: {detail}")
            except:
                st.warning(f"⚠ Could not add expense. Status: {res.status_code}")
    except Exception as e:
        st.error(f"⚠ Error connecting to backend: {e}")
    return False

def get_monthly_summary():
    try:
        res = requests.get(f"{API_BASE}/summary/monthly")
        if res.status_code == 200:
            return res.json()
    except:
        pass
    return []

def get_top_categories():
    try:
        res = requests.get(f"{API_BASE}/summary/top-categories")
        if res.status_code == 200:
            return res.json()
    except:
        pass
    return []

def add_category(name):
    payload = {"name": name}
    try:
        res = requests.post(f"{API_BASE}/categories/", json=payload)
        if res.status_code in [200, 201]:
            return True
        else:
            try:
                detail = res.json().get("detail", "")
                st.warning(f"⚠ Could not add category: {detail}")
            except:
                st.warning(f"⚠ Could not add category. Status: {res.status_code}")
    except Exception as e:
        st.error(f"⚠ Error connecting to backend: {e}")
    return False

# --- Streamlit UI ---
st.set_page_config(page_title="Daily Expense Tracker", layout="wide", page_icon="💰",initial_sidebar_state="expanded")
st.title("💰 Daily Expense Tracker")

# Create 6 tabs
# tab1, tab2, tab3, tab4, tab5 = st.tabs([
#     "📂 View Categories",
#     "📜 View & Filter Expenses",
#     "➕ Add Expenses",
#     "📅 Monthly Summary",
#     "🏆 Top Categories"
# ])
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📂 View Categories",
    "📜 View & Filter Expenses",
    "➕ Add Expenses",
    "📅 Monthly Summary",
    "🏆 Top Categories",
    "➕ Add Categories"
])

# --- Tab 1: View Categories ---
with tab1:
    st.subheader("📂 All Categories")
    categories = get_categories()
    if categories:
        df = pd.DataFrame(categories)
        st.dataframe(df)
    else:
        st.warning("No categories found.")

# --- Tab 2: View & Filter Expenses ---
with tab2:
    st.subheader("📜 View & Filter Expenses")
    categories = get_categories()
    category_names = [cat["name"] for cat in categories]
    
    start_date = st.date_input("Start Date", value=datetime.today() - timedelta(days=30))
    end_date = st.date_input("End Date", value=datetime.today())
    category_filter = st.selectbox("Filter by Category", ["All"] + category_names)

    if category_filter == "All":
        category_filter = None

    expenses = get_expenses(str(start_date), str(end_date), category_filter)

    if expenses:
        df = pd.DataFrame(expenses)
        st.dataframe(df)
    else:
        st.info("No expenses found.")

# --- Tab 3: Add Expenses ---
with tab3:
    st.subheader("➕ Add New Expense")
    categories = get_categories()
    category_names = [cat["name"] for cat in categories] if categories else []

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
            elif category_name == "No categories available":
                st.warning("⚠ Please add categories first.")
            else:
                # Convert date to string format that backend expects
                date_str = date.strftime("%Y-%m-%d")
                
                success = add_expense(amount, category_name, date_str, description)
                if success:
                    st.success("✅ Expense added successfully!")
                else:
                    st.error("⚠ Could not add expense. Please try again.")



# --- Tab 4: Monthly Summary ---
with tab4:
    st.subheader("📅 Monthly Expense Summary")
    monthly_data = get_monthly_summary()

    if monthly_data:
        df_monthly = pd.DataFrame(monthly_data)
        if 'month' in df_monthly.columns:
            df_monthly['month'] = pd.to_datetime(df_monthly['month'])
            df_monthly = df_monthly.sort_values(by='month')
            st.dataframe(df_monthly)
            st.line_chart(df_monthly.set_index('month')['total_expense'])
        else:
            st.warning("Monthly data format is invalid.")
    else:
        st.warning("No monthly summary data found.")

# --- Tab 5: Top Categories ---
with tab5:
    st.subheader("🏆 Top Spending Categories")
    top_cats = get_top_categories()
    if top_cats:
        df_top = pd.DataFrame(top_cats)
        if 'category' in df_top.columns:
            st.dataframe(df_top)
            st.bar_chart(df_top.set_index('category')['total'])
        else:
            st.warning("Invalid top categories data format.")
    else:
        st.warning("No top categories data found.")

# --- Tab 6: Add Categories ---
with tab6:
    st.subheader("➕ Add New Category")
    with st.form("category_form"):
        category_name = st.text_input("Category Name")
        submitted = st.form_submit_button("Add Category")
        if submitted:
            if not category_name.strip():
                st.warning("⚠ Please enter a valid category name.")
            else:
                success = add_category(category_name.strip())
                if success:
                    st.success(f"✅ Category '{category_name}' added successfully!")
                else:
                    st.error("⚠ Could not add category. Please try again.")