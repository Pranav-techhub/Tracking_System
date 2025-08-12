import streamlit as st
import pandas as pd
import os
import re
import matplotlib.pyplot as plt
import requests  # You use requests in summary tab, so import it

# Point to backend\data folder (adjust as needed)
DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend', 'data'))

CUSTOMERS_CSV = os.path.join(DATA_PATH, 'customers.csv')
DUES_CSV = os.path.join(DATA_PATH, 'dues.csv')

ADDED_CUSTOMERS_CSV = os.path.join(DATA_PATH, 'added_customers.csv')
UPDATED_CUSTOMERS_CSV = os.path.join(DATA_PATH, 'updated_customers.csv')
PARTIAL_CUSTOMERS_CSV = os.path.join(DATA_PATH, 'partial_customers.csv')
DELETED_CUSTOMERS_CSV = os.path.join(DATA_PATH, 'deleted_customers.csv')

st.set_page_config(layout="wide")
st.title("Customer Due Tracker System")

def append_row_to_csv(file_path, new_row_dict):
    new_row_df = pd.DataFrame([new_row_dict])
    if os.path.exists(file_path):
        existing_df = pd.read_csv(file_path)
        updated_df = pd.concat([existing_df, new_row_df], ignore_index=True)
    else:
        updated_df = new_row_df
    updated_df.to_csv(file_path, index=False)

# Sidebar Menu: (internal key, display label with emoji)
tabs = [
    ("add_customer", "➕ Add Customer"),
    ("update_due", "✏️ Update Due"),
    ("partial_payment", "💰 Partial Payment"),
    ("delete_customer", "🗑️ Delete Customer"),
    ("view_all", "📋 View All"),
    ("summary", "📊 Summary"),
    ("recent_activity", "🕒 Recent Activity")
]

st.sidebar.markdown("## 📂 Menu")

if "selected_tab" not in st.session_state:
    st.session_state.selected_tab = tabs[0][0]  # default key, not label

for key, label in tabs:
    if st.sidebar.button(label, use_container_width=True, key=key):
        st.session_state.selected_tab = key

choice = st.session_state.selected_tab

# -- Your helper functions unchanged --
def load_csv(file_path, default_cols=None):
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        return df
    else:
        if default_cols:
            return pd.DataFrame(columns=default_cols)
        return pd.DataFrame()

def load_customers():
    default_cols = ['id', 'name', 'phone', 'email', 'address', 'due', 'last_update', 'status']
    df = load_csv(CUSTOMERS_CSV, default_cols)
    if 'id' in df.columns:
        df['id'] = pd.to_numeric(df['id'], errors='coerce').astype('Int64')
    if 'due' in df.columns:
        df['due'] = pd.to_numeric(df['due'], errors='coerce').fillna(0)
    return df

def save_customers(df):
    os.makedirs(DATA_PATH, exist_ok=True)
    df.to_csv(CUSTOMERS_CSV, index=False)

def validate_email_format(email):
    if not email:
        return False
    email = str(email).strip().lower()
    pattern = r'^[a-z0-9._%+\-]+@gmail\.com$'
    return re.match(pattern, email) is not None

def validate_phone_format(phone):
    phone_str = str(phone).strip()
    return phone_str.isdigit() and len(phone_str) == 10

def validate_customer(name, phone, email, customers_list):
    name = str(name).strip()
    phone = str(phone).strip()
    email = str(email).strip()

    if not name:
        st.error("Name cannot be empty")
        return False
    if not phone:
        st.error("Phone cannot be empty")
        return False
    if not email:
        st.error("Email cannot be empty")
        return False

    if not validate_phone_format(phone):
        st.error("Phone number is invalid. Must be exactly 10 digits.")
        return False
    if not validate_email_format(email):
        st.error("Email must be a valid Gmail address (ends with '@gmail.com').")
        return False

    name_lower = name.lower()
    phone_clean = phone
    email_lower = email.lower()

    for cust in customers_list:
        cust_name = str(cust.get('name', '')).strip().lower()
        cust_phone = str(cust.get('phone', '')).strip()
        cust_email = str(cust.get('email', '')).strip().lower() if cust.get('email') else ""

        if cust_name == name_lower:
            st.error("Name already exists.")
            return False
        if cust_phone == phone_clean:
            st.error("Phone number already exists.")
            return False
        if cust_email == email_lower and email_lower != "":
            st.error("Email already exists.")
            return False

    return True

# --- Tabs content ---

if choice == "add_customer":
    st.header("Add Customer")
    name = st.text_input("Name *").strip()
    phone = st.text_input("Phone *").strip()
    email = st.text_input("Email (must be Gmail) *").strip()
    address = st.text_input("Address").strip()
    due = st.number_input("Due Amount", min_value=0.0, format="%.2f")

    if st.button("Add Customer"):
        df = load_customers()
        customers_list = df.to_dict(orient="records")

        # Validations
        if not name:
            st.error("Name cannot be empty.")
        elif not phone or not phone.isdigit() or len(phone) != 10:
            st.error("Phone must be exactly 10 digits.")
        elif not email or not email.lower().endswith("@gmail.com"):
            st.error("Email must be a valid Gmail address (ends with '@gmail.com').")
        elif not validate_customer(name, phone, email, customers_list):
            pass
        else:
            new_id = int(df['id'].max()) + 1 if not df.empty else 1
            new_customer = {
                "id": new_id,
                "name": name,
                "phone": phone,
                "email": email,
                "address": address,
                "due": float(due),
                "last_update": pd.Timestamp.now(),
                "status": "active"
            }
            df = pd.concat([df, pd.DataFrame([new_customer])], ignore_index=True)
            save_customers(df)
            append_row_to_csv(ADDED_CUSTOMERS_CSV, new_customer)
            st.success(f"Customer '{name}' added successfully!")

elif choice == "update_due":
    st.header("Update Due")
    df = load_customers()
    if df.empty:
        st.info("No customers available.")
    else:
        cust_id = st.number_input("Enter Customer ID", min_value=1, step=1)
        if cust_id not in df['id'].values:
            st.warning("Customer ID not found.")
        else:
            customer = df[df["id"] == cust_id].iloc[0]
            st.write(f"Customer Name: {customer['name']}")
            st.write(f"Current Due: ₹{customer['due']:.2f}")
            new_due = st.number_input("New Due Amount", min_value=0.0, value=float(customer['due']), format="%.2f")
            if st.button("Update Due"):
                df.loc[df["id"] == cust_id, "due"] = new_due
                df.loc[df["id"] == cust_id, "last_update"] = pd.Timestamp.now()
                save_customers(df)
                updated_log = {
                    "id": cust_id,
                    "name": customer['name'],
                    "updated_due": new_due,
                    "updated_at": pd.Timestamp.now()
                }
                append_row_to_csv(UPDATED_CUSTOMERS_CSV, updated_log)
                st.success("Due updated successfully!")

elif choice == "partial_payment":
    st.header("Partial Payment")
    df = load_customers()
    if df.empty:
        st.info("No customers available.")
    else:
        cust_id = st.number_input("Enter Customer ID", min_value=1, step=1)
        if cust_id not in df['id'].values:
            st.warning("Customer ID not found.")
        else:
            customer = df[df["id"] == cust_id].iloc[0]
            st.write(f"Customer Name: {customer['name']}")
            st.write(f"Current Due: ₹{customer['due']:.2f}")
            max_payment = float(customer['due'])
            partial_payment = st.number_input("Enter Partial Payment Amount", min_value=0.0, max_value=max_payment, format="%.2f")
            if st.button("Submit Partial Payment"):
                new_due = max_payment - partial_payment
                df.loc[df["id"] == cust_id, "due"] = new_due
                df.loc[df["id"] == cust_id, "last_update"] = pd.Timestamp.now()
                save_customers(df)
                partial_log = {
                    "id": cust_id,
                    "name": customer['name'],
                    "partial_payment_amount": partial_payment,
                    "date": pd.Timestamp.now()
                }
                append_row_to_csv(PARTIAL_CUSTOMERS_CSV, partial_log)

                st.success(f"Partial payment of ₹{partial_payment:.2f} applied. New due: ₹{new_due:.2f}")

elif choice == "delete_customer":
    st.header("Delete Customer")
    df = load_customers()
    if df.empty:
        st.info("No customers available.")
    else:
        cust_id = st.number_input("Enter Customer ID to Delete", min_value=1, step=1)
        if cust_id not in df['id'].values:
            st.warning("Customer ID not found.")
        else:
            customer_row = df[df["id"] == cust_id].iloc[0]
            st.markdown(f"**Customer Name:** {customer_row['name']}")
            st.markdown(f"**Current Due:** ₹{customer_row['due']:.2f}")

        if st.button("Delete Customer"):
            if cust_id not in df['id'].values:
                st.warning("Customer ID not found.")
            else:
                customer_name = df.loc[df["id"] == cust_id, "name"].values[0]
                df = df[df["id"] != cust_id]
                save_customers(df)
                deleted_log = {
                    "id": cust_id,
                    "name": customer_name,
                    "deleted_at": pd.Timestamp.now(),
                    "status": "deleted"
                }
                append_row_to_csv(DELETED_CUSTOMERS_CSV, deleted_log)
                st.success(f"Customer '{customer_name}' with ID {cust_id} deleted successfully!")

    st.markdown("---")
    st.subheader("Delete All Customers")
    if st.button("🗑️ Delete All Customers"):
        if df.empty:
            st.info("No customers to delete.")
        else:
            for _, row in df.iterrows():
                deleted_log = {
                    "id": row['id'],
                    "name": row['name'],
                    "deleted_at": pd.Timestamp.now(),
                    "status": "deleted"
                }
                append_row_to_csv(DELETED_CUSTOMERS_CSV, deleted_log)
            save_customers(df.iloc[0:0])  # Clear all customers
            st.success("All customers deleted successfully!")

elif choice == "view_all":
    st.header("View All Data Tables")

    def style_due_days(row):
        # Calculate days since last update
        try:
            last_update = pd.to_datetime(row['last_update'])
            days_due = (pd.Timestamp.now() - last_update).days
        except Exception:
            days_due = 0

        if days_due >= 45:
            return ['background-color: #ff4d4d'] * len(row)   # red
        elif days_due >= 30:
            return ['background-color: #ffb84d'] * len(row)   # orange
        elif days_due >= 15:
            return ['background-color: #ffff99'] * len(row)   # yellow
        else:
            return [''] * len(row)

    def show_table(file_path, label, filter_func=None, apply_style=False):
        df = load_csv(file_path)
        if df.empty:
            st.markdown(f"*No {label.lower()} found.*")
        else:
            st.markdown(f"### {label}")
            if filter_func:
                df = filter_func(df)

            if apply_style:
                st.dataframe(df.style.apply(style_due_days, axis=1))
            else:
                st.dataframe(df)

    def filter_customers(df):
        search_name = st.text_input("🔍 Search Customers by Name")
        if search_name.strip():
            df = df[df['name'].str.contains(search_name, case=False, na=False)]
        if not df.empty:
            active_count = df[df['status'] == 'active'].shape[0]
        else:
            active_count = 0
        st.write(f"Total Active Customers: {active_count}")
        return df

    # Apply style only for Customers table
    show_table(CUSTOMERS_CSV, "Customers", filter_func=filter_customers, apply_style=True)
    show_table(ADDED_CUSTOMERS_CSV, "Added Customers Log")
    show_table(UPDATED_CUSTOMERS_CSV, "Updated Customers Log")
    show_table(PARTIAL_CUSTOMERS_CSV, "Partial Payments Log")
    show_table(DELETED_CUSTOMERS_CSV, "Deleted Customers Log")

elif choice == "summary":
    st.subheader('📊 Analytics Dashboard')

    API = "http://localhost:5000"  # Define your API endpoint here or import it if you have it elsewhere

    def safe_get_json(response):
        try:
            return response.json()
        except Exception:
            return None

    r = requests.get(f'{API}/customers')
    data = safe_get_json(r)

    if data:
        df = pd.DataFrame(data)
        df = df[df['status'] == 'active']

        st.metric("👥 Total Customers", len(df))
        st.metric("💰 Total Outstanding Due", f"₹{df['due'].sum():,.2f}")

        paid_count = len(df[df['due'] == 0])
        unpaid_count = len(df[df['due'] > 0])
        st.write("### 🧾 Paid vs Unpaid")
        st.plotly_chart({
            "data": [{
                "values": [paid_count, unpaid_count],
                "labels": ["Paid", "Unpaid"],
                "type": "pie"
            }],
            "layout": {"height": 500, "width": 500}  # Increased size here
        })

        st.write("### 📍 Top 5 Debtors")
        top_df = df[df['due'] > 0].nlargest(5, 'due')[['name', 'due']]
        st.table(top_df.set_index('name'))

    else:
        st.info("No customer data available")


elif choice == "recent_activity":
    st.header("🕒 Recent Activity")

    def load_recent(file_path, label, limit=5):
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            if not df.empty:
                st.markdown(f"**{label}:**")
                st.dataframe(df.tail(limit).iloc[::-1])  # Show most recent first
            else:
                st.markdown(f"*No {label.lower()} found.*")
        else:
            st.markdown(f"*No {label.lower()} found.*")

    load_recent(ADDED_CUSTOMERS_CSV, "Recently Added")
    load_recent(UPDATED_CUSTOMERS_CSV, "Recently Updated Dues")
    load_recent(PARTIAL_CUSTOMERS_CSV, "Partial Payments")
    load_recent(DELETED_CUSTOMERS_CSV, "Deleted Customers")
