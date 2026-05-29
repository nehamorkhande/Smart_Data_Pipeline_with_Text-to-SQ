CREATE DATABASE IF NOT EXISTS pipeline_db;
USE pipeline_db;

CREATE TABLE IF NOT EXISTS admins(
    admin_id        INT PRIMARY KEY AUTO_INCREMENT,
    username        VARCHAR(50) UNIQUE NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    business_name   VARCHAR(100),
    email           VARCHAR(100),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active       BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS categories(
    category_id     INT PRIMARY KEY AUTO_INCREMENT,
    admin_id        INT NOT NULL,
    category_name   VARCHAR(50) NOT NULL,
    UNIQUE(admin_id, category_name),
    FOREIGN KEY (admin_id) REFERENCES admins(admin_id)
);

CREATE TABLE IF NOT EXISTS customers(
    customer_id     INT PRIMARY KEY AUTO_INCREMENT,
    admin_id        INT NOT NULL,
    customer_name   VARCHAR(100) NOT NULL,
    customer_city   VARCHAR(100),
    customer_state  VARCHAR(100),
    UNIQUE(admin_id, customer_name),
    FOREIGN KEY (admin_id) REFERENCES admins(admin_id)
);

CREATE TABLE IF NOT EXISTS products(
    product_id      INT PRIMARY KEY AUTO_INCREMENT,
    admin_id        INT NOT NULL,
    product_name    VARCHAR(100) NOT NULL,
    category_id     INT,
    current_price   DECIMAL(10,2) DEFAULT 0,
    UNIQUE(admin_id, product_name),
    FOREIGN KEY (admin_id) REFERENCES admins(admin_id),
    FOREIGN KEY (category_id) REFERENCES categories(category_id)
);

CREATE TABLE IF NOT EXISTS sales(
    sale_id         INT PRIMARY KEY AUTO_INCREMENT,
    admin_id        INT NOT NULL,
    customer_id     INT,
    product_id      INT,
    sale_date       DATE,
    quantity        INT DEFAULT 0,
    unit_price      DECIMAL(10,2) DEFAULT 0,
    total_amount    DECIMAL(10,2) DEFAULT 0,
    payment_mode    VARCHAR(50),
    order_status    VARCHAR(50),
    invoice_id      VARCHAR(50),
    discount        DECIMAL(10,2) DEFAULT 0,
    salesperson     VARCHAR(100),
    region          VARCHAR(100),
    remarks         VARCHAR(255),
    row_hash        VARCHAR(32) UNIQUE,
    source_file     VARCHAR(255),
    uploaded_at     DATETIME,
    FOREIGN KEY (admin_id)    REFERENCES admins(admin_id),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (product_id)  REFERENCES products(product_id)
);

CREATE TABLE IF NOT EXISTS upload_log(
    log_id          INT PRIMARY KEY AUTO_INCREMENT,
    admin_id        INT NOT NULL,
    file_name       VARCHAR(255),
    total_rows      INT DEFAULT 0,
    new_rows        INT DEFAULT 0,
    duplicate_rows  INT DEFAULT 0,
    missing_fixed   INT DEFAULT 0,
    empty_removed   INT DEFAULT 0,
    status          VARCHAR(50) DEFAULT 'success',
    uploaded_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (admin_id) REFERENCES admins(admin_id)
);

CREATE TABLE IF NOT EXISTS audit_log(
    log_id          INT PRIMARY KEY AUTO_INCREMENT,
    admin_id        INT,
    table_name      VARCHAR(50),
    action          VARCHAR(10),
    row_id          INT,
    done_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sales_history(
    history_id      INT PRIMARY KEY AUTO_INCREMENT,
    sale_id         INT,
    admin_id        INT,
    old_data        JSON,
    changed_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


DELIMITER $$
CREATE PROCEDURE IF NOT EXISTS insert_sale(
    IN p_admin_id     INT,
    IN p_customer_id  INT,
    IN p_product_id   INT,
    IN p_date         DATE,
    IN p_quantity     INT,
    IN p_unit_price   DECIMAL(10,2),
    IN p_amount       DECIMAL(10,2),
    IN p_payment      VARCHAR(50),
    IN p_status       VARCHAR(50),
    IN p_invoice_id   VARCHAR(50),
    IN p_discount     DECIMAL(10,2),
    IN p_salesperson  VARCHAR(100),
    IN p_region       VARCHAR(100),
    IN p_remarks      VARCHAR(255),
    IN p_hash         VARCHAR(32),
    IN p_file         VARCHAR(255)
)
BEGIN
    IF NOT EXISTS(
        SELECT 1 FROM sales WHERE row_hash = p_hash
    ) THEN
        INSERT INTO sales(
            admin_id, customer_id, product_id,
            sale_date, quantity, unit_price,
            total_amount, payment_mode, order_status,
            invoice_id, discount, salesperson,
            region, remarks, row_hash,
            source_file, uploaded_at
        ) VALUES (
            p_admin_id, p_customer_id, p_product_id,
            p_date, p_quantity, p_unit_price,
            p_amount, p_payment, p_status,
            p_invoice_id, p_discount, p_salesperson,
            p_region, p_remarks, p_hash,
            p_file, NOW()
        );
    END IF;
END $$
DELIMITER ;


DELIMITER $$
CREATE TRIGGER IF NOT EXISTS after_sale_insert
AFTER INSERT ON sales
FOR EACH ROW
BEGIN
    INSERT INTO audit_log(admin_id, table_name, action, row_id)
    VALUES(NEW.admin_id, 'sales', 'INSERT', NEW.sale_id);
END$$
DELIMITER ;


DELIMITER $$
CREATE TRIGGER IF NOT EXISTS before_sale_update
BEFORE UPDATE ON sales
FOR EACH ROW
BEGIN
    INSERT INTO sales_history(sale_id, admin_id, old_data)
    VALUES(OLD.sale_id, OLD.admin_id, JSON_OBJECT(
        'quantity',     OLD.quantity,
        'unit_price',   OLD.unit_price,
        'total_amount', OLD.total_amount,
        'sale_date',    OLD.sale_date,
        'discount',     OLD.discount,
        'salesperson',  OLD.salesperson,
        'region',       OLD.region,
        'remarks',      OLD.remarks
    ));
END$$
DELIMITER ;


CREATE OR REPLACE VIEW sales_full_view AS
SELECT
    s.sale_id,
    s.admin_id,
    s.sale_date,
    c.customer_name,
    c.customer_city,
    c.customer_state,
    p.product_name,
    cat.category_name   AS category,
    s.unit_price,
    s.quantity,
    s.total_amount,
    s.discount,
    s.payment_mode,
    s.order_status,
    s.invoice_id,
    s.salesperson,
    s.region,
    s.remarks,
    s.source_file,
    s.uploaded_at
FROM      sales      s
JOIN      customers  c   ON s.customer_id = c.customer_id
JOIN      products   p   ON s.product_id  = p.product_id
LEFT JOIN categories cat ON p.category_id = cat.category_id;


INSERT IGNORE INTO admins
    (username, password_hash, business_name, email)
VALUES
    ('admin',  SHA2('admin123', 256), 'Super Admin',         'admin@gmail.com'),
    ('store1', SHA2('store123', 256), 'Rahul Medical Store', 'rahul@gmail.com'),
    ('store2', SHA2('store456', 256), 'Priya Grocery Shop',  'priya@gmail.com');


SELECT table_name AS 'Tables Created'
FROM information_schema.tables
WHERE table_schema = 'pipeline_db';