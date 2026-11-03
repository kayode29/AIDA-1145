
-- ============================================================
-- AIDA 1145 - Week 9 Graded Lab 5
-- Cedar Trail Outdoor Co-op Sales Warehouse
--
-- Fact grain:
-- One row per completed source sales order line.
--
-- Money is stored as integer cents.
-- Product key 0 represents an unknown product.
-- ============================================================

PRAGMA foreign_keys = ON;

-- Drop existing tables in dependency order.
-- This makes schema creation repeatable.
DROP TABLE IF EXISTS fact_sales;
DROP TABLE IF EXISTS dim_store;
DROP TABLE IF EXISTS dim_customer;
DROP TABLE IF EXISTS dim_product;
DROP TABLE IF EXISTS dim_date;

-- ============================================================
-- 1. DATE DIMENSION
-- ============================================================

CREATE TABLE dim_date (
    date_key INTEGER PRIMARY KEY,
    full_date TEXT NOT NULL UNIQUE,
    calendar_year INTEGER NOT NULL,
    calendar_month INTEGER NOT NULL,
    month_name TEXT NOT NULL,

    CHECK (calendar_year BETWEEN 2000 AND 2100),
    CHECK (calendar_month BETWEEN 1 AND 12),
    CHECK (length(full_date) = 10)
);

-- ============================================================
-- 2. PRODUCT DIMENSION
-- ============================================================

CREATE TABLE dim_product (
    product_key INTEGER PRIMARY KEY,
    sku TEXT NOT NULL UNIQUE,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL,

    CHECK (length(trim(sku)) > 0),
    CHECK (length(trim(product_name)) > 0),
    CHECK (length(trim(category)) > 0)
);

-- Unknown product member.
-- Do not invent the missing product's name or category.
-- Candidate sales with unmatched SKUs will reference key 0.

INSERT INTO dim_product (
    product_key,
    sku,
    product_name,
    category
)
VALUES (
    0,
    'UNKNOWN',
    'Unknown Product',
    'Unknown'
);

-- ============================================================
-- 3. CUSTOMER DIMENSION
-- ============================================================

CREATE TABLE dim_customer (
    customer_key INTEGER PRIMARY KEY,
    customer_id TEXT NOT NULL UNIQUE,
    customer_name TEXT NOT NULL,
    customer_segment TEXT NOT NULL,

    CHECK (length(trim(customer_id)) > 0),
    CHECK (length(trim(customer_name)) > 0),
    CHECK (length(trim(customer_segment)) > 0)
);

-- ============================================================
-- 4. STORE DIMENSION
-- ============================================================

CREATE TABLE dim_store (
    store_key INTEGER PRIMARY KEY,
    store_code TEXT NOT NULL UNIQUE,
    store_name TEXT NOT NULL,
    region TEXT NOT NULL,

    CHECK (length(trim(store_code)) > 0),
    CHECK (length(trim(store_name)) > 0),
    CHECK (length(trim(region)) > 0)
);

-- ============================================================
-- 5. SALES FACT TABLE
-- Grain: one completed source order line.
-- ============================================================

CREATE TABLE fact_sales (
    fact_key INTEGER PRIMARY KEY,

    -- Original source identifiers
    line_id TEXT NOT NULL UNIQUE,
    order_id TEXT NOT NULL,
    source_sku TEXT NOT NULL,

    -- Dimension foreign keys
    date_key INTEGER NOT NULL,
    product_key INTEGER NOT NULL,
    customer_key INTEGER NOT NULL,
    store_key INTEGER NOT NULL,

    -- Line-level measures
    quantity INTEGER NOT NULL,
    unit_price_cents INTEGER NOT NULL,
    discount_rate TEXT NOT NULL,
    gross_cents INTEGER NOT NULL,
    discount_cents INTEGER NOT NULL,
    net_cents INTEGER NOT NULL,

    -- Foreign-key relationships
    FOREIGN KEY (date_key)
        REFERENCES dim_date(date_key),

    FOREIGN KEY (product_key)
        REFERENCES dim_product(product_key),

    FOREIGN KEY (customer_key)
        REFERENCES dim_customer(customer_key),

    FOREIGN KEY (store_key)
        REFERENCES dim_store(store_key),

    -- Business-rule validation
    CHECK (length(trim(line_id)) > 0),
    CHECK (length(trim(order_id)) > 0),
    CHECK (length(trim(source_sku)) > 0),

    CHECK (quantity > 0),
    CHECK (unit_price_cents >= 0),
    CHECK (gross_cents >= 0),
    CHECK (discount_cents >= 0),
    CHECK (net_cents >= 0),

    CHECK (discount_cents <= gross_cents),
    CHECK (net_cents = gross_cents - discount_cents),

    CHECK (
        CAST(discount_rate AS REAL) >= 0
        AND CAST(discount_rate AS REAL) <= 1
    )
);

-- Helpful indexes for analytical queries.
CREATE INDEX idx_fact_sales_order
    ON fact_sales(order_id);

CREATE INDEX idx_fact_sales_date
    ON fact_sales(date_key);

CREATE INDEX idx_fact_sales_product
    ON fact_sales(product_key);

CREATE INDEX idx_fact_sales_store
    ON fact_sales(store_key);

CREATE INDEX idx_fact_sales_customer
    ON fact_sales(customer_key);
