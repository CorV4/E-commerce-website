-- Sample data for schema.sql. 
BEGIN;

-- password_hash = SHA-256 of the password, the same as app/security.py hash_password().
-- test user's password is the text inside encode(sha256(...), 'hex')

INSERT INTO users (user_id, username, email, password_hash, shipping_addr, billing_addr) VALUES
    (1, 'maya_chen', 'maya.chen@example.com', encode(sha256('pass_maya_001'), 'hex'), '101 Cedar Lane, Portland, OR 97201', '101 Cedar Lane, Portland, OR 97201'),
    (2, 'leo_martin', 'leo.martin@example.com', encode(sha256('pass_leo_002'), 'hex'), '22 Harbor Street, Seattle, WA 98101', '22 Harbor Street, Seattle, WA 98101'),
    (3, 'amira_khan', 'amira.khan@example.com', encode(sha256('pass_amira_003'), 'hex'), '8 Maple Avenue, Austin, TX 78701', '8 Maple Avenue, Austin, TX 78701'),
    (4, 'noah_brooks', 'noah.brooks@example.com', encode(sha256('pass_noah_004'), 'hex'), '75 Birch Road, Denver, CO 80202', '75 Birch Road, Denver, CO 80202'),
    (5, 'sofia_rossi', 'sofia.rossi@example.com', encode(sha256('pass_sofia_005'), 'hex'), '16 Lakeview Drive, Chicago, IL 60601', '400 Market Street, Chicago, IL 60605'),
    -- Users 6 and 7 share a card.
    (6,  'ethan_wright',  'ethan.wright@example.com',  encode(sha256('pass_ethan_006'), 'hex'),  '9 Willow Court, San Jose, CA 95112',     '9 Willow Court, San Jose, CA 95112'),
    (7,  'olivia_wright', 'olivia.wright@example.com', encode(sha256('pass_olivia_007'), 'hex'), '9 Willow Court, San Jose, CA 95112',     '9 Willow Court, San Jose, CA 95112'),
    -- Users 8-20 each own a store (sellers 3-15).
    (8,  'lucas_nguyen',  'lucas.nguyen@example.com',  encode(sha256('pass_lucas_008'), 'hex'),  '310 Pine Street, San Francisco, CA 94104', '310 Pine Street, San Francisco, CA 94104'),
    (9,  'hana_sato',     'hana.sato@example.com',     encode(sha256('pass_hana_009'), 'hex'),   '47 Orchard Road, Sacramento, CA 95814',  '47 Orchard Road, Sacramento, CA 95814'),
    (10, 'daniel_ortiz',  'daniel.ortiz@example.com',  encode(sha256('pass_daniel_010'), 'hex'), '1200 Canyon Drive, Boulder, CO 80302',   '1200 Canyon Drive, Boulder, CO 80302'),
    (11, 'grace_kim',     'grace.kim@example.com',     encode(sha256('pass_grace_011'), 'hex'),  '58 Elm Street, Boston, MA 02108',        '58 Elm Street, Boston, MA 02108'),
    (12, 'mateo_silva',   'mateo.silva@example.com',   encode(sha256('pass_mateo_012'), 'hex'),  '230 Bay Avenue, Miami, FL 33131',        'PO Box 412, Miami, FL 33131'),
    (13, 'priya_patel',   'priya.patel@example.com',   encode(sha256('pass_priya_013'), 'hex'),  '77 Lotus Lane, Edison, NJ 08817',        '77 Lotus Lane, Edison, NJ 08817'),
    (14, 'omar_haddad',   'omar.haddad@example.com',   encode(sha256('pass_omar_014'), 'hex'),   '19 Cypress Way, Dearborn, MI 48126',     '19 Cypress Way, Dearborn, MI 48126'),
    (15, 'chloe_dubois',  'chloe.dubois@example.com',  encode(sha256('pass_chloe_015'), 'hex'),  '5 Rue Lane, New Orleans, LA 70112',      '5 Rue Lane, New Orleans, LA 70112'),
    (16, 'ryan_oconnor',  'ryan.oconnor@example.com',  encode(sha256('pass_ryan_016'), 'hex'),   '88 Shamrock Street, Philadelphia, PA 19103', '88 Shamrock Street, Philadelphia, PA 19103'),
    (17, 'zara_ali',      'zara.ali@example.com',      encode(sha256('pass_zara_017'), 'hex'),   '402 Garden Row, Phoenix, AZ 85004',      '402 Garden Row, Phoenix, AZ 85004'),
    (18, 'ben_carter',    'ben.carter@example.com',    encode(sha256('pass_ben_018'), 'hex'),    '61 Spoke Avenue, Minneapolis, MN 55401', '61 Spoke Avenue, Minneapolis, MN 55401'),
    (19, 'isla_morgan',   'isla.morgan@example.com',   encode(sha256('pass_isla_019'), 'hex'),   '14 Highland Road, Burlington, VT 05401', '14 Highland Road, Burlington, VT 05401'),
    (20, 'kai_tanaka',    'kai.tanaka@example.com',    encode(sha256('pass_kai_020'), 'hex'),    '930 Kiln Street, Honolulu, HI 96813',    '930 Kiln Street, Honolulu, HI 96813');

-- User 21 closed their account (soft delete), personal data was overwritten, but their past order (order 22) is kept.
INSERT INTO users (user_id, username, email, password_hash, shipping_addr, billing_addr, is_active) VALUES
    (21, 'deleted_user_21', 'deleted_21@deleted.invalid', '!', 'deleted', 'deleted', FALSE);

INSERT INTO cards (card_number, card_cvv, card_exp_date) VALUES
    ('9999000011110001', '123', DATE '2030-12-31'),
    ('9999000011110002', '456', DATE '2031-06-30'),
    ('9999000011110003', '789', DATE '2030-09-30'),
    ('9999000011110004', '321', DATE '2031-03-31'),
    ('9999000011110005', '654', DATE '2029-11-30'),
    ('9999000011110006', '987', DATE '2030-04-30'),
    ('9999000011110007', '147', DATE '2031-08-31'),
    ('9999000011110008', '258', DATE '2029-07-31'),
    ('9999000011110009', '369', DATE '2030-01-31'),
    ('9999000011110010', '741', DATE '2031-10-31'),
    ('9999000011110011', '852', DATE '2030-06-30'),
    ('9999000011110012', '963', DATE '2029-12-31'),
    ('9999000011110013', '159', DATE '2031-02-28'),
    ('9999000011110014', '1234', DATE '2030-08-31'),
    ('9999000011110015', '357', DATE '2031-05-31');

INSERT INTO user_cards (user_id, card_number) VALUES
    (1, '9999000011110001'),
    (1, '9999000011110002'),
    (3, '9999000011110003'),
    (5, '9999000011110004'),
    (6, '9999000011110005'),   -- card 5 is shared by users 6 and 7
    (7, '9999000011110005'),
    (2, '9999000011110006'),
    (4, '9999000011110007'),
    (8, '9999000011110008'),
    (9, '9999000011110009'),
    (10, '9999000011110010'),
    (11, '9999000011110011'),
    (12, '9999000011110012'),
    (13, '9999000011110013'),
    (6, '9999000011110014'),   -- user 6 has two cards
    (14, '9999000011110015');

INSERT INTO sellers (seller_id, user_id, store_name, bank_acc_number) VALUES
    (1,  2,  'Northstar Goods',      '100100100'),
    (2,  4,  'Juniper Workshop',     '100200200'),
    (3,  8,  'Nguyen Tech Supply',   '100300300'),
    (4,  9,  'Sato Stationery',      '100400400'),
    (5,  10, 'Ortiz Outdoor Co.',    '100500500'),
    (6,  11, 'Kim Kitchenworks',     '100600600'),
    (7,  12, 'Silva Coffee Roasters','100700700'),
    (8,  13, 'Patel Spice House',    '100800800'),
    (9,  14, 'Haddad Leather',       '100900900'),
    (10, 15, 'Dubois Candle Studio', '101000100'),
    (11, 16, 'Emerald Isle Books',   '101100110'),
    (12, 17, 'Zara''s Plant Shop',   '101200120'),
    (13, 18, 'Carter Cycle Parts',   '101300130'),
    (14, 19, 'Morgan Knitwear',      '101400140'),
    (15, 20, 'Tanaka Pottery',       '101500150');

INSERT INTO items (item_id, seller_id, name, description, price, is_listed) VALUES
    (1, 1, 'Insulated Travel Mug',      'Reusable stainless-steel mug with a leak-resistant lid.',  24.50, TRUE),
    (2, 1, 'Canvas Market Tote',        'Durable cotton tote for groceries and everyday errands.',  18.00, TRUE),
    (3, 1, 'Desk Organizer',            'Compact organizer with compartments for stationery.',      32.75, TRUE),
    (4, 2, 'Handmade Ceramic plate',    'Small glazed ceramic plate, made in a home studio.',     29.00, TRUE),
    (5, 2, 'Wooden Serving Board',      'Solid wood serving board with a food-safe finish.',        45.00, TRUE),
    (6, 2, 'Linen Table Runner',        'Natural linen runner suitable for everyday dining.',       38.25, FALSE),
    (7,  3,  'Wireless Mouse',          'Quiet-click mouse with a USB-C receiver.',                 21.99, TRUE),
    (8,  4,  'Dot Grid Notebook',       'A5 notebook with 160 pages of dot grid paper.',            12.00, TRUE),
    (9,  5,  'Camping Lantern',         'Rechargeable LED lantern with three brightness levels.',   34.95, TRUE),
    (10, 6,  'Chef Knife',              'Eight-inch stainless-steel chef knife.',                   59.00, TRUE),
    (11, 7,  'Whole Bean Coffee',       'A 12 oz bag of medium roast coffee beans.',                16.50, TRUE),
    (12, 8,  'Spice Sampler',           'Six jars of popular cooking spices.',                      27.00, TRUE),
    (13, 9,  'Leather Wallet',          'Slim bifold wallet made of full-grain leather.',           42.00, TRUE),
    (14, 10, 'Soy Candle',              'Lavender soy candle with a 40-hour burn time.',            19.75, TRUE),
    (15, 11, 'Used Paperback Set',      'Five classic novels in good condition.',                   25.00, TRUE),
    (16, 12, 'Potted Succulent',        'Small succulent in a 4-inch clay pot.',                     9.50, TRUE),
    (17, 13, 'Bike Light Set',          'Front and rear USB-rechargeable bike lights.',             28.40, TRUE),
    (18, 14, 'Wool Beanie',             'Hand-knit beanie made of merino wool.',                    22.00, TRUE),
    (19, 15, 'Ceramic Bowl',            'Hand-thrown bowl with a speckled glaze.',                  31.00, TRUE);

-- Only listed items, and no one has their own item in their cart.
INSERT INTO cart (user_id, item_id, quantity) VALUES
    (1, 4, 1),
    (1, 2, 2),
    (3, 3, 1),
    (5, 5, 1),
    (6, 10, 1),
    (7, 11, 2),
    (8, 1, 1),
    (9, 7, 1),
    (10, 12, 1),
    (11, 13, 1),
    (12, 14, 3),
    (13, 16, 2),
    (14, 17, 1),
    (15, 18, 1),
    (2, 19, 1);

-- total = price * quantity at purchase time
INSERT INTO orders (order_id, user_id, item_id, quantity, order_date, total, order_status) VALUES
    (1, 1, 1, 2, TIMESTAMPTZ '2026-10-12 14:30:00-07', 49.00, 'delivered'),
    (2, 3, 4, 1, TIMESTAMPTZ '2026-11-02 09:15:00-06', 29.00, 'delivered'),
    (3, 5, 2, 1, TIMESTAMPTZ '2026-11-10 16:45:00-06', 18.00, 'delivered'),
    (4, 1, 5, 1, TIMESTAMPTZ '2026-11-21 11:10:00-08', 45.00, 'cancelled'),
    (5, 5, 3, 1, TIMESTAMPTZ '2026-11-05 11:20:00-06', 32.75, 'delivered'),
    (6, 3, 1, 1, TIMESTAMPTZ '2026-11-24 10:05:00-06', 24.50, 'shipped'),
    (7, 3, 2, 2, TIMESTAMPTZ '2026-11-25 18:40:00-06', 36.00, 'pending'),
    (8,  6,  7,  1, TIMESTAMPTZ '2026-10-03 10:00:00-07', 21.99, 'delivered'),
    (9,  7,  8,  3, TIMESTAMPTZ '2026-10-08 13:25:00-07', 36.00, 'delivered'),
    (10, 8,  9,  1, TIMESTAMPTZ '2026-10-15 08:40:00-07', 34.95, 'delivered'),
    (11, 9,  10, 1, TIMESTAMPTZ '2026-10-19 19:05:00-07', 59.00, 'delivered'),
    (12, 10, 11, 2, TIMESTAMPTZ '2026-10-22 07:30:00-06', 33.00, 'delivered'),
    (13, 11, 12, 1, TIMESTAMPTZ '2026-10-27 12:15:00-04', 27.00, 'delivered'),
    (14, 12, 13, 1, TIMESTAMPTZ '2026-10-30 17:50:00-04', 42.00, 'delivered'),
    (15, 13, 14, 2, TIMESTAMPTZ '2026-11-01 09:45:00-05', 39.50, 'delivered'),
    (16, 14, 15, 1, TIMESTAMPTZ '2026-11-04 15:20:00-05', 25.00, 'delivered'),
    (17, 15, 16, 4, TIMESTAMPTZ '2026-11-07 11:35:00-06', 38.00, 'delivered'),
    (18, 16, 19, 1, TIMESTAMPTZ '2026-11-09 14:10:00-05', 31.00, 'delivered'),
    (19, 17, 18, 1, TIMESTAMPTZ '2026-11-23 16:00:00-07', 22.00, 'shipped'),
    (20, 19, 17, 1, TIMESTAMPTZ '2026-11-26 09:30:00-05', 28.40, 'pending'),
    -- Item 6 is unlisted now, but this older order for it is kept.
    (21, 7,  6,  1, TIMESTAMPTZ '2026-09-20 18:00:00-07', 38.25, 'delivered'),
    -- Order by the closed account (user 21).
    (22, 21, 1,  1, TIMESTAMPTZ '2026-09-14 12:00:00-07', 24.50, 'delivered');

INSERT INTO reviews (review_id, user_id, item_id, stars, title, description) VALUES
    (1, 1, 1, 5, 'Great for commuting',   'Keeps drinks warm and fits neatly in my bag.'),
    (2, 3, 4, 4, 'Beautiful plate',       'The color and glaze are beautiful. It feels sturdy.'),
    (3, 5, 2, 5, 'Useful everyday tote',  'It is well made and stores my essentials.'),
    (4, 5, 3, 4, 'Practical item',        'It helps keep my desk neat and tidy.'),
    (5,  6,  7,  4, 'Solid mouse',          'Clicks are quiet and the battery lasts weeks.'),
    (6,  7,  8,  5, 'Love the paper',       'Thick pages with no bleed-through from my pens.'),
    (7,  8,  9,  3, 'Bright but heavy',     'Very bright, but heavier than I expected for hiking.'),
    (8,  9,  10, 5, 'Very sharp',           'Cuts cleanly and holds its edge well.'),
    (9,  10, 11, 4, 'Smooth roast',         'Nice flavor, not bitter. I would buy it again.'),
    (10, 11, 12, 5, 'Great variety',        'Good mix of spices for everyday cooking.'),
    (11, 12, 13, 4, 'Nice wallet',          'Slim and well stitched. The leather feels soft.'),
    (12, 13, 14, 2, 'Weak scent',           'The candle burns evenly, but the scent is faint.'),
    (13, 14, 15, 5, 'Good condition',       'All five books arrived in great shape.'),
    (14, 15, 16, 3, 'Small plant',          'Healthy plant, but smaller than in the photo.'),
    (15, 16, 19, 5, 'Beautiful bowl',       'The glaze is lovely and it is the perfect size.');

-- Keep identity sequences ahead of explicit sample IDs.
SELECT setval(pg_get_serial_sequence('users',   'user_id'),   (SELECT MAX(user_id)   FROM users),   TRUE);
SELECT setval(pg_get_serial_sequence('sellers', 'seller_id'), (SELECT MAX(seller_id) FROM sellers), TRUE);
SELECT setval(pg_get_serial_sequence('items',   'item_id'),   (SELECT MAX(item_id)   FROM items),   TRUE);
SELECT setval(pg_get_serial_sequence('orders',  'order_id'),  (SELECT MAX(order_id)  FROM orders),  TRUE);
SELECT setval(pg_get_serial_sequence('reviews', 'review_id'), (SELECT MAX(review_id) FROM reviews), TRUE);

COMMIT;
