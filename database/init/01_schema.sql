-- ============================================================================
-- Natural Language -> SQL Analytics Assistant
-- Schema definition (PostgreSQL)
-- Tables: customers, products, orders, order_items
-- ============================================================================

CREATE TABLE IF NOT EXISTS customers (
    customer_id  SERIAL PRIMARY KEY,
    first_name   TEXT        NOT NULL,
    last_name    TEXT        NOT NULL,
    email        TEXT        NOT NULL UNIQUE,
    region       TEXT        NOT NULL,
    country      TEXT        NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS products (
    product_id  SERIAL PRIMARY KEY,
    name        TEXT          NOT NULL,
    category    TEXT          NOT NULL,
    unit_price  NUMERIC(12,2) NOT NULL,
    cost        NUMERIC(12,2) NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
    order_id    SERIAL PRIMARY KEY,
    customer_id INT           NOT NULL REFERENCES customers(customer_id),
    order_date  DATE          NOT NULL,
    status      TEXT          NOT NULL DEFAULT 'completed'
);

CREATE TABLE IF NOT EXISTS order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id      INT           NOT NULL REFERENCES orders(order_id),
    product_id    INT           NOT NULL REFERENCES products(product_id),
    quantity      INT           NOT NULL,
    unit_price    NUMERIC(12,2) NOT NULL
);

-- Indexes for analytical queries
CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_order_date ON orders(order_date);
CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_product ON order_items(product_id);
