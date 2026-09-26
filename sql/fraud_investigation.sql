CREATE TABLE transactions (
    transaction_id VARCHAR(20),
    user_id VARCHAR(20),
    timestamp TIMESTAMP,
    amount DECIMAL(12, 2),
    transaction_type VARCHAR(10),
    merchant_category VARCHAR(50),
    merchant_id VARCHAR(20),
    city VARCHAR(50),
    device_id VARCHAR(20),
    status VARCHAR(20),
    receiver_id VARCHAR(20)
);