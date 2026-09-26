import random
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd


# Basic settings for the dataset

NUM_TRANSACTIONS = 50_000
NUM_USERS = 5_000
NUM_MERCHANTS = 1_500

START_DATE = datetime(2026, 1, 1)
DAYS = 180

random.seed(42)
np.random.seed(42)


# Some basic reference data

cities = [
    "Kolkata",
    "Delhi",
    "Mumbai",
    "Bengaluru",
    "Hyderabad",
    "Chennai",
    "Pune",
    "Ahmedabad"
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
    "Other"
]

transaction_types = ["P2P", "P2M"]

statuses = ["SUCCESS", "FAILED", "PENDING"]

status_weights = [0.94, 0.04, 0.02]


# Create our fake users

users = []

for i in range(1, NUM_USERS + 1):
    users.append({
        "user_id": f"U{i:05d}",
        "city": random.choice(cities),
        "device_id": f"D{random.randint(1, 4500):05d}"
    })


# Create fake merchants

merchants = []

for i in range(1, NUM_MERCHANTS + 1):
    merchants.append({
        "merchant_id": f"M{i:05d}",
        "merchant_category": random.choice(merchant_categories),
        "city": random.choice(cities)
    })


# Generate normal UPI transactions first

transactions = []

for i in range(1, NUM_TRANSACTIONS + 1):

    user = random.choice(users)

    user_id = user["user_id"]
    user_city = user["city"]
    device_id = user["device_id"]

    # P2M transactions are more common than P2P here
    transaction_type = random.choices(
        transaction_types,
        weights=[0.35, 0.65],
        k=1
    )[0]

    # Generate a random transaction time
    random_minutes = random.randint(
        0,
        DAYS * 24 * 60 - 1
    )

    timestamp = START_DATE + timedelta(
        minutes=random_minutes
    )

    # Most transactions should be small or medium sized
    amount = np.random.lognormal(
        mean=5.3,
        sigma=0.85
    )

    amount = round(
        min(max(amount, 10), 100000),
        2
    )

    if transaction_type == "P2M":

        merchant = random.choice(merchants)

        merchant_id = merchant["merchant_id"]
        merchant_category = merchant["merchant_category"]

        # Usually the payment happens in the user's city
        if random.random() < 0.90:
            city = user_city
        else:
            city = merchant["city"]

        receiver_id = merchant_id

    else:

        merchant_id = None
        merchant_category = "P2P"

        receiver_id = f"U{random.randint(1, NUM_USERS):05d}"

        city = user_city

    status = random.choices(
        statuses,
        weights=status_weights,
        k=1
    )[0]

    transaction_id = f"TXN{i:08d}"

    transactions.append([
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
        receiver_id
    ])


# Convert everything into a DataFrame

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
    "receiver_id"
]

df = pd.DataFrame(
    transactions,
    columns=columns
)


# We keep the fraud information separately.
# It will never be added to the raw transaction data.

ground_truth = []


def add_ground_truth(transaction_ids, scenario):
    for transaction_id in transaction_ids:
        ground_truth.append({
            "transaction_id": transaction_id,
            "fraud_scenario": scenario
        })


# Scenario 1:
# One user suddenly makes many transactions within minutes.
# This will later help us investigate transaction velocity.

velocity_user = "U04991"

velocity_rows = df[
    df["user_id"] == velocity_user
].sample(
    n=12,
    random_state=42
).index

velocity_ids = []

base_time = datetime(2026, 3, 15, 2, 10)

for position, row_index in enumerate(velocity_rows):

    df.loc[row_index, "timestamp"] = (
        base_time + timedelta(minutes=position)
    )

    df.loc[row_index, "amount"] = round(
        random.uniform(150, 600),
        2
    )

    df.loc[row_index, "status"] = "SUCCESS"

    velocity_ids.append(
        df.loc[row_index, "transaction_id"]
    )

add_ground_truth(
    velocity_ids,
    "HIGH_VELOCITY"
)


# Scenario 2:
# Several different users suddenly use the same device.

shared_device = "D09999"

device_users = [
    "U04980",
    "U04981",
    "U04982",
    "U04983",
    "U04984"
]

device_ids = []

base_time = datetime(2026, 4, 10, 1, 30)

for position, user_id in enumerate(device_users):

    user_rows = df[
        df["user_id"] == user_id
    ]

    row_index = user_rows.sample(
        n=1,
        random_state=100 + position
    ).index[0]

    df.loc[row_index, "device_id"] = shared_device

    df.loc[row_index, "timestamp"] = (
        base_time + timedelta(minutes=position * 2)
    )

    df.loc[row_index, "amount"] = round(
        random.uniform(200, 800),
        2
    )

    df.loc[row_index, "status"] = "SUCCESS"

    device_ids.append(
        df.loc[row_index, "transaction_id"]
    )

add_ground_truth(
    device_ids,
    "SHARED_DEVICE"
)


# Scenario 3:
# Several users send money to the same receiver
# within a short period.

suspicious_receiver = "U04999"

receiver_users = [
    "U04850",
    "U04851",
    "U04852",
    "U04853",
    "U04854",
    "U04855",
    "U04856",
    "U04857"
]

receiver_ids = []

base_time = datetime(2026, 5, 20, 3, 0)

for position, user_id in enumerate(receiver_users):

    user_rows = df[
        df["user_id"] == user_id
    ]

    row_index = user_rows.sample(
        n=1,
        random_state=200 + position
    ).index[0]

    # Turn this transaction into a P2P transfer
    df.loc[row_index, "transaction_type"] = "P2P"
    df.loc[row_index, "merchant_id"] = None
    df.loc[row_index, "merchant_category"] = "P2P"

    df.loc[row_index, "receiver_id"] = suspicious_receiver

    df.loc[row_index, "timestamp"] = (
        base_time + timedelta(minutes=position * 3)
    )

    df.loc[row_index, "amount"] = round(
        random.uniform(500, 1500),
        2
    )

    df.loc[row_index, "status"] = "SUCCESS"

    receiver_ids.append(
        df.loc[row_index, "transaction_id"]
    )

add_ground_truth(
    receiver_ids,
    "RECEIVER_CONCENTRATION"
)


# Scenario 4:
# A user who normally makes smaller transactions
# suddenly makes several unusually large payments.

amount_user = "U04970"

amount_rows = df[
    df["user_id"] == amount_user
].sample(
    n=5,
    random_state=300
).index

amount_ids = []

base_time = datetime(2026, 6, 5, 2, 45)

for position, row_index in enumerate(amount_rows):

    df.loc[row_index, "timestamp"] = (
        base_time + timedelta(minutes=position * 7)
    )

    df.loc[row_index, "amount"] = round(
        random.uniform(7000, 9500),
        2
    )

    df.loc[row_index, "status"] = "SUCCESS"

    amount_ids.append(
        df.loc[row_index, "transaction_id"]
    )

add_ground_truth(
    amount_ids,
    "UNUSUAL_AMOUNT"
)


# Scenario 5:
# Several users use the same device and send money
# to the same receiver within a short time.
#
# This creates a stronger combination of suspicious signals.

coordinated_device = "D08888"
coordinated_receiver = "U04998"

coordinated_users = [
    "U04700",
    "U04701",
    "U04702",
    "U04703",
    "U04704"
]

coordinated_ids = []

base_time = datetime(2026, 7, 12, 2, 20)

for position, user_id in enumerate(coordinated_users):

    user_rows = df[
        df["user_id"] == user_id
    ]

    row_index = user_rows.sample(
        n=1,
        random_state=400 + position
    ).index[0]

    df.loc[row_index, "transaction_type"] = "P2P"
    df.loc[row_index, "merchant_id"] = None
    df.loc[row_index, "merchant_category"] = "P2P"

    df.loc[row_index, "device_id"] = coordinated_device
    df.loc[row_index, "receiver_id"] = coordinated_receiver

    df.loc[row_index, "timestamp"] = (
        base_time + timedelta(minutes=position * 4)
    )

    df.loc[row_index, "amount"] = round(
        1200 + random.uniform(-50, 50),
        2
    )

    df.loc[row_index, "status"] = "SUCCESS"

    coordinated_ids.append(
        df.loc[row_index, "transaction_id"]
    )

add_ground_truth(
    coordinated_ids,
    "COORDINATED_ACTIVITY"
)


# Sort transactions by time

df = df.sort_values(
    "timestamp"
).reset_index(drop=True)


# Remove any duplicate ground-truth records

ground_truth_df = pd.DataFrame(
    ground_truth
).drop_duplicates(
    subset=["transaction_id"]
)


# Create the required folders automatically

project_root = Path(__file__).resolve().parent.parent

raw_folder = project_root / "data" / "raw"
validation_folder = project_root / "data" / "validation"

raw_folder.mkdir(
    parents=True,
    exist_ok=True
)

validation_folder.mkdir(
    parents=True,
    exist_ok=True
)


# Save the raw transaction data

raw_output = raw_folder / "upi_transactions_raw.csv"

df.to_csv(
    raw_output,
    index=False
)


# Save the hidden fraud information separately

validation_output = (
    validation_folder / "fraud_ground_truth.csv"
)

ground_truth_df.to_csv(
    validation_output,
    index=False
)


# Print a quick summary

print("=" * 50)
print("UPI TRANSACTION DATA GENERATED")
print("=" * 50)

print(f"Transactions : {len(df):,}")
print(f"Users        : {df['user_id'].nunique():,}")
print(f"Unique TXNs  : {df['transaction_id'].nunique():,}")

print(
    f"Date range   : "
    f"{df['timestamp'].min()} -> "
    f"{df['timestamp'].max()}"
)

print(
    f"Total value  : "
    f"₹{df['amount'].sum():,.2f}"
)

print()
print("Hidden fraud scenarios:")

print(
    ground_truth_df["fraud_scenario"].value_counts()
)

print()
print(f"Raw data saved to:")
print(raw_output)

print()
print("Ground truth saved to:")
print(validation_output)