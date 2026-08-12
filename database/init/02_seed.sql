-- ============================================================================
-- Seed data (PostgreSQL)
-- Deterministic: no random functions; results are reproducible.
-- ============================================================================

-- ------------------------- customers -------------------------
INSERT INTO customers (first_name, last_name, email, region, country) VALUES
    ('Aarav',   'Sharma',  'aarav.sharma@example.com',  'North', 'India'),
    ('Ananya',  'Iyer',    'ananya.iyer@example.com',   'South', 'India'),
    ('Rohan',   'Verma',   'rohan.verma@example.com',   'North', 'India'),
    ('Priya',   'Nair',    'priya.nair@example.com',    'South', 'India'),
    ('Vikram',  'Singh',   'vikram.singh@example.com',  'West',  'India'),
    ('Sneha',   'Reddy',   'sneha.reddy@example.com',   'East',  'India'),
    ('Arjun',   'Patel',   'arjun.patel@example.com',   'West',  'India'),
    ('Meera',   'Das',     'meera.das@example.com',     'East',  'India'),
    ('Kabir',   'Khan',    'kabir.khan@example.com',    'North', 'India'),
    ('Ishita',  'Bose',    'ishita.bose@example.com',   'East',  'India'),
    ('Aditya',  'Gupta',   'aditya.gupta@example.com',  'North', 'India'),
    ('Divya',   'Menon',   'divya.menon@example.com',   'South', 'India'),
    ('Rahul',   'Joshi',   'rahul.joshi@example.com',   'West',  'India'),
    ('Tanvi',   'Chopra',  'tanvi.chopra@example.com',  'South', 'India'),
    ('Manish',  'Kumar',   'manish.kumar@example.com',  'East',  'India');

-- ------------------------- products -------------------------
INSERT INTO products (name, category, unit_price, cost) VALUES
    ('Smartphone X',      'Electronics', 45000.00, 30000.00),
    ('Laptop Pro',        'Electronics', 82000.00, 55000.00),
    ('Wireless Earbuds',  'Electronics',  5000.00,  2500.00),
    ('4K Television',     'Electronics', 68000.00, 45000.00),
    ('Office Chair',      'Furniture',   12000.00,  7000.00),
    ('Wooden Desk',       'Furniture',   22000.00, 14000.00),
    ('Bookshelf',         'Furniture',    9500.00,  5500.00),
    ('Cotton T-Shirt',    'Clothing',      900.00,   300.00),
    ('Denim Jeans',       'Clothing',      2500.00,  1000.00),
    ('Running Shoes',     'Clothing',      4200.00,  2000.00),
    ('Espresso Machine',  'Appliances',   18000.00, 10000.00),
    ('Air Conditioner',   'Appliances',   36000.00, 24000.00),
    ('Refrigerator',      'Appliances',   41000.00, 27000.00),
    ('Washing Machine',   'Appliances',   29000.00, 18000.00),
    ('Basmati Rice 5kg',  'Groceries',      750.00,   500.00);

-- ------------------------- orders + order_items -------------------------
-- Deterministic generation across 2025-2026 so analytical questions
-- (monthly/regional/category revenue) return meaningful results.
DO $$
DECLARE
    o_id    INT;
    c_id    INT;
    p_id    INT;
    qty     INT;
    d       DATE;
    seq     INT;
BEGIN
    seq := 0;
    -- Build orders across every month of 2025 and 2026.
    FOR y IN 2025..2026 LOOP
      FOR m IN 1..12 LOOP
        -- 3 orders per month
        FOR k IN 1..3 LOOP
          seq := seq + 1;
          c_id := 1 + (seq % 15);              -- 15 customers
          d := make_date(y, m, 1) + ((seq * 5) % 25);
          INSERT INTO orders (customer_id, order_date, status)
          VALUES (c_id, d, 'completed')
          RETURNING order_id INTO o_id;

          -- 1-3 line items per order
          FOR li IN 1..(1 + (seq % 3)) LOOP
            p_id := 1 + ((seq * 3 + li) % 15);  -- 15 products
            qty := (1 + (seq % 4));
            INSERT INTO order_items (order_id, product_id, quantity, unit_price)
            VALUES (o_id, p_id, qty,
                    (SELECT unit_price FROM products WHERE product_id = p_id));
          END LOOP;
        END LOOP;
      END LOOP;
    END LOOP;
END $$;

