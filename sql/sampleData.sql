-- Sample data for schema.sql. 
BEGIN;

INSERT INTO users (user_id, username, email, password_hash, shipping_addr, billing_addr) VALUES
    (1, 'maya_chen', 'maya.chen@example.com', 'pass_maya_001', '101 Cedar Lane, Portland, OR 97201', '101 Cedar Lane, Portland, OR 97201'),
    (2, 'leo_martin', 'leo.martin@example.com', 'pass_leo_002', '22 Harbor Street, Seattle, WA 98101', '22 Harbor Street, Seattle, WA 98101'),
    (3, 'amira_khan', 'amira.khan@example.com', 'pass_amira_003', '8 Maple Avenue, Austin, TX 78701', '8 Maple Avenue, Austin, TX 78701'),
    (4, 'noah_brooks', 'noah.brooks@example.com', 'pass_noah_004', '75 Birch Road, Denver, CO 80202', '75 Birch Road, Denver, CO 80202'),
    (5, 'sofia_rossi', 'sofia.rossi@example.com', 'pass_sofia_005', '16 Lakeview Drive, Chicago, IL 60601', '400 Market Street, Chicago, IL 60605');

INSERT INTO cards (card_number, card_cvv, card_exp_date) VALUES
    ('9999000011110001', '123', DATE '2030-12-31'),
    ('9999000011110002', '456', DATE '2031-06-30'),
    ('9999000011110003', '789', DATE '2030-09-30'),
    ('9999000011110004', '321', DATE '2031-03-31');

INSERT INTO user_cards (user_id, card_number) VALUES
    (1, '9999000011110001'),
    (1, '9999000011110002'),
    (3, '9999000011110003'),
    (5, '9999000011110004');

INSERT INTO sellers (seller_id, user_id, store_name, bank_acc_number) VALUES
    (1, 2, 'Northstar Goods',  'SAMPLE-ACCT-1001'),
    (2, 4, 'Juniper Workshop', 'SAMPLE-ACCT-1002');

INSERT INTO items (item_id, seller_id, name, description, price, is_listed) VALUES
    (1, 1, 'Insulated Travel Mug',      'Reusable stainless-steel mug with a leak-resistant lid.',  24.50, TRUE),
    (2, 1, 'Canvas Market Tote',        'Durable cotton tote for groceries and everyday errands.',  18.00, TRUE),
    (3, 1, 'Desk Organizer',            'Compact organizer with compartments for stationery.',      32.75, TRUE),
    (4, 2, 'Handmade Ceramic plate',    'Small glazed ceramic plate, made in a home studio.',     29.00, TRUE),
    (5, 2, 'Wooden Serving Board',      'Solid wood serving board with a food-safe finish.',        45.00, TRUE),
    (6, 2, 'Linen Table Runner',        'Natural linen runner suitable for everyday dining.',       38.25, FALSE);

INSERT INTO cart (user_id, item_id, quantity) VALUES
    (1, 4, 1),
    (1, 2, 2),
    (3, 3, 1),
    (5, 5, 1);

-- total = price * quantity at purchase time
INSERT INTO orders (order_id, user_id, item_id, quantity, order_date, total, order_status) VALUES
    (1, 1, 1, 2, TIMESTAMPTZ '2026-10-12 14:30:00-07', 49.00, 'delivered'),
    (2, 3, 4, 1, TIMESTAMPTZ '2026-11-02 09:15:00-06', 29.00, 'delivered'),
    (3, 5, 2, 1, TIMESTAMPTZ '2026-11-10 16:45:00-06', 18.00, 'delivered'),
    (4, 1, 5, 1, TIMESTAMPTZ '2026-11-21 11:10:00-08', 45.00, 'cancelled'),
    (5, 5, 3, 1, TIMESTAMPTZ '2026-11-05 11:20:00-06', 32.75, 'delivered'),
    (6, 3, 1, 1, TIMESTAMPTZ '2026-11-24 10:05:00-06', 24.50, 'shipped'),
    (7, 3, 2, 2, TIMESTAMPTZ '2026-11-25 18:40:00-06', 36.00, 'pending');

-- Every review matches a delivered order by the same user for the same item,
-- and no seller reviews their own item.
INSERT INTO reviews (review_id, user_id, item_id, stars, title, description) VALUES
    (1, 1, 1, 5, 'Great for commuting',   'Keeps drinks warm and fits neatly in my bag.'),
    (2, 3, 4, 4, 'Beautiful plate',       'The color and glaze are beautiful. It feels sturdy.'),
    (3, 5, 2, 5, 'Useful everyday tote',  'It is well made and stores my essentials.'),
    (4, 5, 3, 4, 'Practical item',        'It is helps keeps my desk neat and tidy.');

-- Keep identity sequences ahead of the explicit sample IDs.
SELECT setval(pg_get_serial_sequence('users',   'user_id'),   (SELECT MAX(user_id)   FROM users),   TRUE);
SELECT setval(pg_get_serial_sequence('sellers', 'seller_id'), (SELECT MAX(seller_id) FROM sellers), TRUE);
SELECT setval(pg_get_serial_sequence('items',   'item_id'),   (SELECT MAX(item_id)   FROM items),   TRUE);
SELECT setval(pg_get_serial_sequence('orders',  'order_id'),  (SELECT MAX(order_id)  FROM orders),  TRUE);
SELECT setval(pg_get_serial_sequence('reviews', 'review_id'), (SELECT MAX(review_id) FROM reviews), TRUE);

COMMIT;
