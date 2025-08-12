import pandas as pd
import os
from datetime import datetime

DATA_PATH = os.path.join(os.path.dirname(__file__), 'data')

CUSTOMERS_CSV = os.path.join(DATA_PATH, 'customers.csv')
ADDED_CUSTOMERS_CSV = os.path.join(DATA_PATH, 'added_customers.csv')
UPDATED_CUSTOMERS_CSV = os.path.join(DATA_PATH, 'updated_customers.csv')
PARTIAL_CUSTOMERS_CSV = os.path.join(DATA_PATH, 'partial_customers.csv')
DELETED_CUSTOMERS_CSV = os.path.join(DATA_PATH, 'deleted_customers.csv')
DUES_CSV = os.path.join(DATA_PATH, 'dues.csv')

def append_row_to_csv(file_path, new_row_dict):
    """
    Append a new row (dict) to a CSV file.
    Creates the file if it doesn't exist.
    """
    new_row_df = pd.DataFrame([new_row_dict])
    if os.path.exists(file_path):
        existing_df = pd.read_csv(file_path)
        updated_df = pd.concat([existing_df, new_row_df], ignore_index=True)
    else:
        updated_df = new_row_df
    updated_df.to_csv(file_path, index=False)

def load_customers():
    if os.path.exists(CUSTOMERS_CSV):
        df = pd.read_csv(CUSTOMERS_CSV)
        if 'last_update' in df.columns:
            df['last_update'] = pd.to_datetime(df['last_update'], errors='coerce')
        return df
    else:
        columns = ["id", "name", "phone", "address", "due", "category", "last_update", "status"]
        return pd.DataFrame(columns=columns)

def save_customers(df):
    os.makedirs(DATA_PATH, exist_ok=True)
    # Convert any datetime columns to string before saving to CSV
    if 'last_update' in df.columns:
        df['last_update'] = df['last_update'].apply(lambda x: x.isoformat() if pd.notnull(x) else "")
    df.to_csv(CUSTOMERS_CSV, index=False)

def get_all_customers():
    df = load_customers()
    return df.to_dict(orient='records')

def add_customer(name, phone, address, due=0.0, category='Regular'):
    df = load_customers()
    new_id = int(df['id'].max()) + 1 if not df.empty else 1

    now = datetime.now()
    new_customer = {
        'id': new_id,
        'name': name,
        'phone': phone,
        'address': address,
        'due': float(due),
        'category': category,
        'last_update': now,
        'status': 'active'
    }
    new_customer_save = new_customer.copy()
    new_customer_save['last_update'] = now.isoformat()

    df = pd.concat([df, pd.DataFrame([new_customer_save])], ignore_index=True)
    save_customers(df)

    # Append to added_customers.csv log
    append_row_to_csv(ADDED_CUSTOMERS_CSV, new_customer_save)

    return new_customer

def update_due(customer_id, new_due):
    df = load_customers()
    if customer_id not in df['id'].values:
        return None

    now = datetime.now()
    df.loc[df['id'] == customer_id, 'due'] = float(new_due)
    df.loc[df['id'] == customer_id, 'last_update'] = now

    # Save customers with datetime conversion
    save_customers(df)

    updated = df[df['id'] == customer_id].iloc[0].to_dict()
    updated['last_update'] = now.isoformat()

    # Append to updated_customers.csv log
    append_row_to_csv(UPDATED_CUSTOMERS_CSV, updated)

    return updated

def delete_customer(customer_id):
    df = load_customers()
    if customer_id not in df['id'].values:
        return False

    deleted_customer = df[df['id'] == customer_id].iloc[0].to_dict()
    # Convert datetime fields to string before logging
    if 'last_update' in deleted_customer and pd.notnull(deleted_customer['last_update']):
        deleted_customer['last_update'] = pd.to_datetime(deleted_customer['last_update']).isoformat()

    # Append to deleted_customers.csv log
    append_row_to_csv(DELETED_CUSTOMERS_CSV, deleted_customer)

    df = df[df['id'] != customer_id]
    save_customers(df)
    return True

def record_partial_payment(customer_id, payment_amount):
    """
    Record a partial payment: decrease due, update last_update,
    append partial payment info to partial_customers.csv.
    """
    df = load_customers()
    if customer_id not in df['id'].values:
        return None

    customer = df[df['id'] == customer_id].iloc[0]
    current_due = customer['due']
    new_due = max(current_due - float(payment_amount), 0.0)

    now = datetime.now()
    df.loc[df['id'] == customer_id, 'due'] = new_due
    df.loc[df['id'] == customer_id, 'last_update'] = now

    save_customers(df)

    partial_payment_record = {
        'id': customer_id,
        'name': customer['name'],
        'phone': customer['phone'],
        'payment_amount': float(payment_amount),
        'new_due': new_due,
        'payment_date': now.isoformat()
    }
    append_row_to_csv(PARTIAL_CUSTOMERS_CSV, partial_payment_record)

    return partial_payment_record

def load_dues():
    if os.path.exists(DUES_CSV):
        df = pd.read_csv(DUES_CSV)
        if 'due_date' in df.columns:
            df['due_date'] = pd.to_datetime(df['due_date'], errors='coerce')
        if 'last_message_date' in df.columns:
            df['last_message_date'] = pd.to_datetime(df['last_message_date'], errors='coerce')
        return df
    else:
        columns = ["name", "phone", "address", "customer_category", "due_amount", "due_date", "last_message_date"]
        return pd.DataFrame(columns=columns)

def save_dues(df):
    os.makedirs(DATA_PATH, exist_ok=True)
    # Convert datetime to string before save
    if 'due_date' in df.columns:
        df['due_date'] = df['due_date'].apply(lambda x: x.isoformat() if pd.notnull(x) else "")
    if 'last_message_date' in df.columns:
        df['last_message_date'] = df['last_message_date'].apply(lambda x: x.isoformat() if pd.notnull(x) else "")
    df.to_csv(DUES_CSV, index=False)

def add_due_record(customer_id, due_amount, due_date=None):
    df_customers = load_customers()
    customer = df_customers[df_customers['id'] == customer_id]
    if customer.empty:
        return False

    due_date = due_date or datetime.now()

    new_due = {
        "name": customer.iloc[0]['name'],
        "phone": customer.iloc[0]['phone'],
        "address": customer.iloc[0]['address'],
        "customer_category": customer.iloc[0]['category'],
        "due_amount": float(due_amount),
        "due_date": due_date,
        "last_message_date": pd.NaT
    }
    df_dues = load_dues()
    df_dues = pd.concat([df_dues, pd.DataFrame([new_due])], ignore_index=True)
    save_dues(df_dues)
    return True

def delete_all_customers():
    df = load_customers()
    if df.empty:
        return False

    for _, row in df.iterrows():
        deleted_log = {
            "id": row['id'],
            "name": row['name'],
            "deleted_at": pd.Timestamp.now(),
            "status": "deleted"
        }
        append_row_to_csv(DELETED_CUSTOMERS_CSV, deleted_log)

    save_customers(df.iloc[0:0])  # clear all
    return True
