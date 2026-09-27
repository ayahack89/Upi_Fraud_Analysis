-- Create a table to store transaction data for fraud investigation analysis
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
How much activity/value is involved?



-- 1. Which users transact unusually frequently?
-- Why first: This establishes the baseline user behavior and immediately highlights users whose activity is unusually high.

SELECT
    user_id,
    COUNT(*) AS transaction_count,
    SUM(amount) AS total_transaction_value,
    ROUND(AVG(amount), 2) AS average_transaction_amount
FROM transactions
GROUP BY user_id
ORDER BY transaction_count DESC;

-- 2. Which receivers receive money from unusually many different users?
-- This is one of the strongest questions from your original list because it looks at the receiver side of the transaction network, not just individual users.

SELECT
    receiver_id,
    COUNT(*) AS transaction_count,
    COUNT(DISTINCT user_id) AS unique_users,
    SUM(amount) AS total_received
FROM transactions
GROUP BY receiver_id
ORDER BY unique_users DESC;


-- 3. Which devices are associated with many different users?
-- This directly addresses your shared-device question.

SELECT
    device_id,
    COUNT(DISTINCT user_id) AS unique_users,
    COUNT(*) AS transaction_count,
    SUM(amount) AS total_transaction_value
FROM transactions
GROUP BY device_id
HAVING COUNT(DISTINCT user_id) > 1
ORDER BY unique_users DESC;


-- 4. Are there suspicious bursts of transactions within a short period?
-- This is the one where I'd keep the SQL simple rather than making it unnecessarily advanced.
SELECT
    user_id,
    DATE_TRUNC('hour', timestamp)
        + INTERVAL '5 minutes' * FLOOR(EXTRACT(MINUTE FROM timestamp) / 5)
        AS transaction_period,
    COUNT(*) AS transaction_count,
    SUM(amount) AS total_transaction_value
FROM transactions
GROUP BY
    user_id,
    transaction_period
HAVING COUNT(*) >= 3
ORDER BY transaction_count DESC;



-- 5. Which transactions are unusually high-value?
-- This gives you a clean monetary-risk analysis.
-- Instead of arbitrarily saying "transactions above ₹50,000 are suspicious," use the dataset's own distribution.
SELECT
    transaction_id,
    user_id,
    receiver_id,
    amount,
    timestamp,
    transaction_type,
    status
FROM transactions
WHERE amount > (
    SELECT AVG(amount) * 3
    FROM transactions
)
ORDER BY amount DESC;


-- 6. Which transactions combine multiple suspicious signals?
-- This is the most important final query because now we're combining the patterns from the previous five analyses.
SELECT
    t.transaction_id,
    t.user_id,
    t.receiver_id,
    t.device_id,
    t.amount,
    t.timestamp,

    CASE
        WHEN t.amount > (
            SELECT AVG(amount) * 3
            FROM transactions
        )
        THEN 1
        ELSE 0
    END AS high_value_flag,

    CASE
        WHEN t.user_id IN (
            SELECT user_id
            FROM transactions
            GROUP BY user_id
            HAVING COUNT(*) >= 20
        )
        THEN 1
        ELSE 0
    END AS frequent_user_flag,

    CASE
        WHEN t.receiver_id IN (
            SELECT receiver_id
            FROM transactions
            GROUP BY receiver_id
            HAVING COUNT(DISTINCT user_id) >= 10
        )
        THEN 1
        ELSE 0
    END AS high_receiver_flag,

    CASE
        WHEN t.device_id IN (
            SELECT device_id
            FROM transactions
            GROUP BY device_id
            HAVING COUNT(DISTINCT user_id) > 1
        )
        THEN 1
        ELSE 0
    END AS shared_device_flag

FROM transactions t

WHERE
    t.amount > (
        SELECT AVG(amount) * 3
        FROM transactions
    )

    OR t.user_id IN (
        SELECT user_id
        FROM transactions
        GROUP BY user_id
        HAVING COUNT(*) >= 20
    )

    OR t.receiver_id IN (
        SELECT receiver_id
        FROM transactions
        GROUP BY receiver_id
        HAVING COUNT(DISTINCT user_id) >= 10
    )

    OR t.device_id IN (
        SELECT device_id
        FROM transactions
        GROUP BY device_id
        HAVING COUNT(DISTINCT user_id) > 1
    )

ORDER BY amount DESC;