import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd


# CONFIGURATION
NUM_TRANSACTIONS = 50_000

START_DATE = datetime(2026, 1, 1)
DAYS = 180

random.seed(42)
np.random.seed(42)


# REFERENCE DATA
cities = [
    "Kolkata",
    "Delhi",
    "Mumbai",
    "Bengaluru",
    "Hyderabad",
    "Chennai",
    "Pune",
    "Ahmedabad",
]

merchant_categories = [
    "Grocery",
    "Food",
    "Shopping",
    "Travel",
    "Utilities",
    "Healthcare",
    "Entertainment",
    "Education",
    "Fuel",
    "Other",
]

transaction_types = [
    "P2P",
    "P2M",
]

statuses = [
    "SUCCESS",
    "FAILED",
    "PENDING",
]

status_weights = [
    0.94,
    0.04,
    0.02,
]


# USERS
NUM_USERS = 5_000

users = []

for i in range(1, NUM_USERS + 1):

    users.append(
        {
            "user_id": f"U{str(i).zfill(5)}",
            "city": random.choice(cities),
            "device_id": f"D{random.randint(1, 4500):05d}",
        }
    )


# MERCHANTS
NUM_MERCHANTS = 1_500

merchants = []

for i in range(1, NUM_MERCHANTS + 1):

    merchants.append(
        {
            "merchant_id": f"M{str(i).zfill(5)}",
            "merchant_category": random.choice(merchant_categories),
            "city": random.choice(cities),
        }
    )


# GENERATE TRANSACTIONS
transactions = []
for i in range(1, NUM_TRANSACTIONS + 1):

    user = random.choice(users)

    user_id = user["user_id"]
    user_city = user["city"]
    device_id = user["device_id"]

    transaction_type = random.choices(
        transaction_types,
        weights=[0.35, 0.65],
        k=1
    )[0]

    random_minutes = random.randint(
        0,
        DAYS * 24 * 60 - 1
    )

    timestamp = START_DATE + timedelta(
        minutes=random_minutes
    )


    # Transaction amount
    # Log-normal distribution gives, many small/medium transactions, and fewer large transactions.

    amount = np.random.lognormal(
        mean=5.3,
        sigma=0.85
    )

    amount = round(amount, 2)

    # Keep the synthetic UPI amount, within a reasonable range.
    amount = min(max(amount, 10), 100000)

    # P2M transaction
    if transaction_type == "P2M":

        merchant = random.choice(merchants)

        merchant_id = merchant["merchant_id"]
        merchant_category = merchant["merchant_category"]

        # Most merchant transactions
        # happen in the user's city.

        if random.random() < 0.90:
            city = user_city
        else:
            city = merchant["city"]

        receiver_id = merchant_id

    # P2P transaction

    else:

        merchant_id = None
        merchant_category = "P2P"

        receiver_id = (
            f"U{random.randint(1, NUM_USERS):05d}"
        )

        city = user_city


    # -----------------------------
    # Transaction status
    # -----------------------------

    status = random.choices(
        statuses,
        weights=status_weights,
        k=1
    )[0]


    # -----------------------------
    # Transaction ID
    # -----------------------------

    transaction_id = f"TXN{str(i).zfill(8)}"


    # -----------------------------
    # Store transaction
    # -----------------------------

    transactions.append(
        [
            transaction_id,
            user_id,
            timestamp,
            amount,
            transaction_type,
            merchant_category,
            merchant_id,
            city,
            device_id,
            status,
            receiver_id,
        ]
    )


# ============================================================
# CREATE DATAFRAME
# ============================================================

columns = [
    "transaction_id",
    "user_id",
    "timestamp",
    "amount",
    "transaction_type",
    "merchant_category",
    "merchant_id",
    "city",
    "device_id",
    "status",
    "receiver_id",
]

df = pd.DataFrame(
    transactions,
    columns=columns
)


# ============================================================
# SORT BY TIME
# ============================================================

df = df.sort_values(
    "timestamp"
).reset_index(drop=True)


# ============================================================
# SAVE RAW DATA
# ============================================================

output_path = "data/raw/upi_transactions_raw.csv"

df.to_csv(
    output_path,
    index=False
)


# ============================================================
# BASIC OUTPUT
# ============================================================

print("=" * 60)
print("UPI TRANSACTION DATA GENERATED")
print("=" * 60)

print(f"Transactions : {len(df):,}")
print(f"Users        : {df['user_id'].nunique():,}")
print(f"Transactions : {df['transaction_id'].nunique():,}")
print(f"Date range   : {df['timestamp'].min()} → {df['timestamp'].max()}")
print(f"Total value  : ₹{df['amount'].sum():,.2f}")

print()
print(f"Saved to: {output_path}")