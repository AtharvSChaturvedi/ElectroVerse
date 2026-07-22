BEGIN TRANSACTION;
CREATE TABLE admins (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    );
INSERT INTO "admins" VALUES(1,'admin','240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9');
CREATE TABLE billbook (
        id INTEGER PRIMARY KEY,
        seller_id INTEGER NOT NULL,
        order_id INTEGER,
        amount REAL NOT NULL,
        type TEXT NOT NULL,
        description TEXT,
        payment_date TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY(seller_id) REFERENCES sellers(id),
        FOREIGN KEY(order_id) REFERENCES seller_orders(id)
    );
CREATE TABLE notifications (
        id INTEGER PRIMARY KEY,
        from_seller_id INTEGER,
        order_id INTEGER,
        message TEXT NOT NULL,
        is_read INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY(from_seller_id) REFERENCES sellers(id)
    );
CREATE TABLE products (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        category TEXT,
        price REAL NOT NULL,
        bulk_price REAL,
        quantity INTEGER DEFAULT 0,
        image_url TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        is_active INTEGER DEFAULT 1
    );
INSERT INTO "products" VALUES(1,'Samsung 65" 4K OLED TV','Stunning 4K OLED display with smart features','Television',89999.0,75000.0,15,NULL,'2026-06-20 04:48:50',0);
INSERT INTO "products" VALUES(2,'Sony WH-1000XM5 Headphones','Industry-leading noise cancelling wireless headphones','Audio',29999.0,24000.0,30,NULL,'2026-06-20 04:48:50',0);
INSERT INTO "products" VALUES(3,'iPhone 15 Pro Max','Latest Apple flagship with titanium design','Smartphones',159900.0,145000.0,20,NULL,'2026-06-20 04:48:50',0);
INSERT INTO "products" VALUES(4,'LG 1.5T Split AC','5-star rated inverter air conditioner','Air Conditioners',45000.0,38000.0,10,NULL,'2026-06-20 04:48:50',0);
INSERT INTO "products" VALUES(5,'Bosch Washing Machine 8kg','Fully automatic front-loading with i-Dos','Appliances',55000.0,46000.0,8,NULL,'2026-06-20 04:48:50',0);
INSERT INTO "products" VALUES(6,'Dell XPS 15 Laptop','OLED display, Intel i9, 32GB RAM','Laptops',189000.0,172000.0,12,NULL,'2026-06-20 04:48:50',0);
INSERT INTO "products" VALUES(7,'Canon EOS R6 Mark II','Full-frame mirrorless camera 40fps','Cameras',229000.0,210000.0,5,NULL,'2026-06-20 04:48:50',0);
INSERT INTO "products" VALUES(8,'PS5 Console','PlayStation 5 with DualSense controller','Gaming',54990.0,49000.0,25,NULL,'2026-06-20 04:48:50',0);
INSERT INTO "products" VALUES(9,'ESP-32 WROOM','','Microcontrollers',429.0,379.0,50,'','2026-06-20 05:33:47',1);
INSERT INTO "products" VALUES(10,'Arduino UNO R3 SMD Atmega328P','','Microcontrollers',249.0,219.0,100,'','2026-06-20 05:36:17',1);
INSERT INTO "products" VALUES(11,'Arduino Nano Board R3 with CH340 (Soldered,Compatible)','','Microcontrollers',225.0,199.0,100,'','2026-06-20 05:37:12',1);
INSERT INTO "products" VALUES(12,'Arduino MEGA 2560 R3 ATmega2560','','Microcontrollers',1499.0,1299.0,50,'','2026-06-20 05:37:59',1);
INSERT INTO "products" VALUES(13,'HC-SR04 Ultrasonic Sensor HCSR04','','Sensors',79.0,67.0,150,'','2026-06-20 05:39:23',1);
INSERT INTO "products" VALUES(14,'Digital IR Sensor Module IR Proximity LM393','','Sensors',35.0,29.0,150,'','2026-06-20 05:40:33',1);
INSERT INTO "products" VALUES(15,'PIR Motion Detector Sensor Module HC-SR501','','Sensors',99.0,85.0,100,'','2026-06-20 05:41:27',1);
INSERT INTO "products" VALUES(16,'MPU6050 - 6 Axis -Accelerometer and Gyroscope Sensor','','Sensors',199.0,175.0,100,'','2026-06-20 05:50:43',1);
INSERT INTO "products" VALUES(17,'SG90 Mini Servo - 180 degree Rotation','','Acuators',99.0,85.0,100,'','2026-06-20 05:55:07',1);
INSERT INTO "products" VALUES(18,'5mm Blue Diffused LED','','Acuators',1.0,0.8,200,'','2026-06-20 05:56:33',1);
INSERT INTO "products" VALUES(19,'12V Goli Buzzer Active Electromagnetic','','Acuators',15.0,12.0,200,'','2026-06-20 05:58:18',1);
INSERT INTO "products" VALUES(20,'18mm 8R 0.5 Watt 8 OHM Speaker','','Acuators',39.0,33.0,100,'https://www.indianhobbycenter.com/products/18mm-8r-0-5-watt-8-ohm-speaker?_pos=1&_sid=972f98d83&_ss=r','2026-06-20 05:59:58',1);
CREATE TABLE seller_order_items (
        id INTEGER PRIMARY KEY,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price REAL NOT NULL,
        FOREIGN KEY(order_id) REFERENCES seller_orders(id),
        FOREIGN KEY(product_id) REFERENCES products(id)
    );
CREATE TABLE seller_orders (
        id INTEGER PRIMARY KEY,
        seller_id INTEGER NOT NULL,
        status TEXT DEFAULT 'pending',
        total_amount REAL DEFAULT 0,
        notes TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        delivered_at TEXT,
        FOREIGN KEY(seller_id) REFERENCES sellers(id)
    );
CREATE TABLE sellers (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        store_name TEXT NOT NULL,
        phone TEXT,
        email TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        is_active INTEGER DEFAULT 1
    );
INSERT INTO "sellers" VALUES(1,'waveonics_stores','2c962e0dbf9f5797498b0d87fdb55122344af6733e77e82ad44394737862280d','Waveonics Stores','1234567890','waveonics@store.in','2026-06-20 05:47:12',1);
INSERT INTO "sellers" VALUES(2,'bliss_electronics','8ef1fd36a7961707fd09cc9fa1c1fe52aa84f0515f3f2a8f64a07cc7083eb897','Bliss Electronics','2345678901','bliss@electronics.in','2026-06-20 06:18:50',1);
INSERT INTO "sellers" VALUES(3,'sams_tech_store','e3e9fc033c2647b79bac54f75d0965c0715c6856e662fd02da8742100e5cda22','Sam''s Tech Store','3456789012','sams@store.in','2026-06-20 06:20:23',1);
INSERT INTO "sellers" VALUES(4,'crease_tech_centre','89bb47525a52986bad461ab29024ff44c0ea3dcd357b71d4b60ac58a90f5cfdf','Crease Tech Centre','4567890123','crease_tech@centre.in','2026-06-20 06:21:58',1);
INSERT INTO "sellers" VALUES(5,'apex_compos','aa7079615177d0432fedbfdeb5af227ebfc181b6165768b7fefca5c8058658d3','Apex Compos','5678901234','apex@store.in','2026-06-20 06:24:47',1);
CREATE TABLE user_order_items (
        id INTEGER PRIMARY KEY,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price REAL NOT NULL,
        FOREIGN KEY(order_id) REFERENCES user_orders(id),
        FOREIGN KEY(product_id) REFERENCES products(id)
    );
CREATE TABLE user_orders (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        status TEXT DEFAULT 'pending',
        total_amount REAL DEFAULT 0,
        shipping_address TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY(user_id) REFERENCES users(id)
    );
CREATE TABLE users (
        id INTEGER PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        name TEXT NOT NULL,
        phone TEXT,
        address TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    );
COMMIT;
