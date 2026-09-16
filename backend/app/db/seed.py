import asyncio
import json
import random
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from app.core.database import engine, demo_engine, AsyncSessionLocal, DemoAsyncSessionLocal, Base
from app.core.security import get_password_hash
from app.db.models import (
    User,
    SchemaMetadata,
    Customer,
    Category,
    Product,
    Order,
    OrderItem,
    ProductReview,
    DemoBase,
)

# Realistic E-Commerce DDL definition for the default schema
ECOMMERCE_DDL = """
CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    country VARCHAR(100) NOT NULL,
    city VARCHAR(100) NOT NULL,
    signup_date TIMESTAMP NOT NULL,
    account_status VARCHAR(50) NOT NULL DEFAULT 'ACTIVE'
);

CREATE TABLE categories (
    category_id SERIAL PRIMARY KEY,
    category_name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT
);

CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    category_id INTEGER REFERENCES categories(category_id),
    price NUMERIC(10, 2) NOT NULL,
    stock_quantity INTEGER NOT NULL DEFAULT 0,
    rating NUMERIC(3, 2) NOT NULL DEFAULT 5.0
);

CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(customer_id),
    order_date TIMESTAMP NOT NULL,
    total_amount NUMERIC(10, 2) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'COMPLETED',
    payment_method VARCHAR(50) NOT NULL DEFAULT 'CREDIT_CARD'
);

CREATE TABLE order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(order_id),
    product_id INTEGER REFERENCES products(product_id),
    quantity INTEGER NOT NULL DEFAULT 1,
    unit_price NUMERIC(10, 2) NOT NULL
);

CREATE TABLE product_reviews (
    review_id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(product_id),
    customer_id INTEGER REFERENCES customers(customer_id),
    rating INTEGER NOT NULL,
    review_text TEXT,
    review_date TIMESTAMP NOT NULL
);
"""

ECOMMERCE_SCHEMA_JSON = {
    "tables": [
        {
            "name": "customers",
            "description": "Registered customers and demographic info",
            "columns": [
                {"name": "customer_id", "type": "INTEGER", "primary_key": True},
                {"name": "first_name", "type": "VARCHAR(100)", "primary_key": False},
                {"name": "last_name", "type": "VARCHAR(100)", "primary_key": False},
                {"name": "email", "type": "VARCHAR(255)", "primary_key": False},
                {"name": "country", "type": "VARCHAR(100)", "primary_key": False},
                {"name": "city", "type": "VARCHAR(100)", "primary_key": False},
                {"name": "signup_date", "type": "TIMESTAMP", "primary_key": False},
                {"name": "account_status", "type": "VARCHAR(50)", "primary_key": False},
            ],
        },
        {
            "name": "categories",
            "description": "Product hierarchy categories",
            "columns": [
                {"name": "category_id", "type": "INTEGER", "primary_key": True},
                {"name": "category_name", "type": "VARCHAR(100)", "primary_key": False},
                {"name": "description", "type": "TEXT", "primary_key": False},
            ],
        },
        {
            "name": "products",
            "description": "Catalog of available items and stock levels",
            "columns": [
                {"name": "product_id", "type": "INTEGER", "primary_key": True},
                {"name": "product_name", "type": "VARCHAR(255)", "primary_key": False},
                {"name": "category_id", "type": "INTEGER", "foreign_key": "categories.category_id"},
                {"name": "price", "type": "NUMERIC(10,2)", "primary_key": False},
                {"name": "stock_quantity", "type": "INTEGER", "primary_key": False},
                {"name": "rating", "type": "NUMERIC(3,2)", "primary_key": False},
            ],
        },
        {
            "name": "orders",
            "description": "Customer purchase transaction records",
            "columns": [
                {"name": "order_id", "type": "INTEGER", "primary_key": True},
                {"name": "customer_id", "type": "INTEGER", "foreign_key": "customers.customer_id"},
                {"name": "order_date", "type": "TIMESTAMP", "primary_key": False},
                {"name": "total_amount", "type": "NUMERIC(10,2)", "primary_key": False},
                {"name": "status", "type": "VARCHAR(50)", "primary_key": False},
                {"name": "payment_method", "type": "VARCHAR(50)", "primary_key": False},
            ],
        },
        {
            "name": "order_items",
            "description": "Line items breakdown per order",
            "columns": [
                {"name": "order_item_id", "type": "INTEGER", "primary_key": True},
                {"name": "order_id", "type": "INTEGER", "foreign_key": "orders.order_id"},
                {"name": "product_id", "type": "INTEGER", "foreign_key": "products.product_id"},
                {"name": "quantity", "type": "INTEGER", "primary_key": False},
                {"name": "unit_price", "type": "NUMERIC(10,2)", "primary_key": False},
            ],
        },
        {
            "name": "product_reviews",
            "description": "User ratings and feedback per product",
            "columns": [
                {"name": "review_id", "type": "INTEGER", "primary_key": True},
                {"name": "product_id", "type": "INTEGER", "foreign_key": "products.product_id"},
                {"name": "customer_id", "type": "INTEGER", "foreign_key": "customers.customer_id"},
                {"name": "rating", "type": "INTEGER", "primary_key": False},
                {"name": "review_text", "type": "TEXT", "primary_key": False},
                {"name": "review_date", "type": "TIMESTAMP", "primary_key": False},
            ],
        },
    ]
}


async def seed_database():
    """Create all tables and seed default users, schemas, and demo dataset."""
    # 1. Create tables in primary DB
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Ensure avatar_url column exists in users table (if table was created prior)
        try:
            from sqlalchemy import text
            await conn.execute(text("ALTER TABLE users ADD COLUMN avatar_url VARCHAR(500)"))
        except Exception:
            pass

    # 2. Create tables in demo sandbox DB
    async with demo_engine.begin() as conn:
        await conn.run_sync(DemoBase.metadata.create_all)

    # 3. Seed Users & Schema Metadata
    async with AsyncSessionLocal() as session:
        # Check if users already seeded
        res = await session.execute(select(User).limit(1))
        if not res.scalars().first():
            admin_user = User(
                email="admin@company.com",
                hashed_password=get_password_hash("Admin@123456"),
                full_name="Enterprise Administrator",
                role="admin",
                is_active=True,
            )
            analyst_user = User(
                email="analyst@company.com",
                hashed_password=get_password_hash("Analyst@123456"),
                full_name="Lead Data Analyst",
                role="analyst",
                is_active=True,
            )
            viewer_user = User(
                email="viewer@company.com",
                hashed_password=get_password_hash("Viewer@123456"),
                full_name="Executive Viewer",
                role="viewer",
                is_active=True,
            )
            session.add_all([admin_user, analyst_user, viewer_user])
            await session.flush()

            # Seed default schema
            default_schema = SchemaMetadata(
                user_id=admin_user.id,
                name="E-Commerce & Retail Analytics",
                description="Global e-commerce retail database including customers, orders, categories, line items, and product reviews.",
                dialect="postgres",
                ddl_content=ECOMMERCE_DDL.strip(),
                schema_json=json.dumps(ECOMMERCE_SCHEMA_JSON),
                is_default=True,
            )
            session.add(default_schema)
            await session.commit()

    # 4. Seed Demo E-Commerce Data
    async with DemoAsyncSessionLocal() as session:
        res = await session.execute(select(Customer).limit(1))
        if not res.scalars().first():
            # Categories
            categories_data = [
                Category(category_name="Electronics", description="Smartphones, Laptops, Audio & Gadgets"),
                Category(category_name="Home & Kitchen", description="Appliances, Furniture, Decor & Cookware"),
                Category(category_name="Apparel & Fashion", description="Men, Women, Footwear & Accessories"),
                Category(category_name="Books & Media", description="Paperbacks, Hardcovers, Audiobooks & E-books"),
                Category(category_name="Sports & Fitness", description="Gym equipment, Outdoor gear & Apparel"),
            ]
            session.add_all(categories_data)
            await session.flush()

            # Products
            products_data = [
                Product(product_name="ProBook 16-inch M3 Max", category_id=1, price=2499.99, stock_quantity=45, rating=4.9),
                Product(product_name="UltraSound Noise Cancelling Headphones", category_id=1, price=349.50, stock_quantity=120, rating=4.7),
                Product(product_name="Smart OLED 4K 65-inch TV", category_id=1, price=1299.00, stock_quantity=30, rating=4.8),
                Product(product_name="Wireless Ergonomic Mouse", category_id=1, price=79.99, stock_quantity=200, rating=4.5),
                Product(product_name="Espresso Deluxe Machine", category_id=2, price=599.00, stock_quantity=60, rating=4.6),
                Product(product_name="Robot Vacuum Cleaner AI", category_id=2, price=449.99, stock_quantity=85, rating=4.4),
                Product(product_name="Cast Iron Dutch Oven 6-Qt", category_id=2, price=89.95, stock_quantity=110, rating=4.9),
                Product(product_name="Italian Leather Jacket", category_id=3, price=299.00, stock_quantity=40, rating=4.8),
                Product(product_name="Running Performance Shoes", category_id=3, price=139.99, stock_quantity=150, rating=4.6),
                Product(product_name="Classic Aviator Sunglasses", category_id=3, price=160.00, stock_quantity=90, rating=4.3),
                Product(product_name="Designing Data-Intensive Applications", category_id=4, price=45.00, stock_quantity=300, rating=5.0),
                Product(product_name="Clean Architecture in Python", category_id=4, price=39.50, stock_quantity=220, rating=4.7),
                Product(product_name="Adjustable Dumbbell Set 50lbs", category_id=5, price=320.00, stock_quantity=50, rating=4.8),
                Product(product_name="Pro Yoga Mat 6mm Non-Slip", category_id=5, price=55.00, stock_quantity=140, rating=4.5),
            ]
            session.add_all(products_data)
            await session.flush()

            # Customers
            first_names = ["Emma", "Liam", "Olivia", "Noah", "Sophia", "Jackson", "Ava", "Lucas", "Isabella", "Aiden", "Mia", "Ethan", "Harper", "Oliver", "Evelyn", "Elijah"]
            last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson"]
            cities_countries = [
                ("New York", "USA"), ("San Francisco", "USA"), ("London", "UK"), ("Toronto", "Canada"),
                ("Berlin", "Germany"), ("Paris", "France"), ("Sydney", "Australia"), ("Tokyo", "Japan"),
                ("Singapore", "Singapore"), ("Amsterdam", "Netherlands"), ("Austin", "USA"), ("Seattle", "USA")
            ]

            customers = []
            for i in range(40):
                fn = first_names[i % len(first_names)]
                ln = last_names[(i * 3) % len(last_names)]
                city, country = cities_countries[i % len(cities_countries)]
                days_ago = random.randint(30, 700)
                signup = datetime.now(timezone.utc) - timedelta(days=days_ago)
                status_choice = "ACTIVE" if random.random() > 0.1 else "INACTIVE"
                c = Customer(
                    first_name=fn,
                    last_name=ln,
                    email=f"{fn.lower()}.{ln.lower()}{i+1}@example.com",
                    country=country,
                    city=city,
                    signup_date=signup,
                    account_status=status_choice
                )
                customers.append(c)
            session.add_all(customers)
            await session.flush()

            # Orders & OrderItems
            orders = []
            order_items = []
            reviews = []

            for i in range(120):
                cust = random.choice(customers)
                days_ago = random.randint(1, 365)
                order_date = datetime.now(timezone.utc) - timedelta(days=days_ago)
                order_status = random.choices(["COMPLETED", "COMPLETED", "COMPLETED", "PENDING", "REFUNDED"], weights=[70, 15, 5, 7, 3])[0]
                payment_method = random.choice(["CREDIT_CARD", "PAYPAL", "APPLE_PAY", "BANK_TRANSFER"])

                # Pick 1 to 4 items
                num_items = random.randint(1, 4)
                chosen_products = random.sample(products_data, num_items)
                total_amount = 0.0

                order = Order(
                    customer_id=cust.customer_id,
                    order_date=order_date,
                    total_amount=0.0,
                    status=order_status,
                    payment_method=payment_method,
                )
                session.add(order)
                await session.flush()

                for prod in chosen_products:
                    qty = random.randint(1, 3)
                    item_total = float(prod.price) * qty
                    total_amount += item_total
                    oi = OrderItem(
                        order_id=order.order_id,
                        product_id=prod.product_id,
                        quantity=qty,
                        unit_price=float(prod.price),
                    )
                    order_items.append(oi)

                    # Occasional review
                    if random.random() > 0.6:
                        rev = ProductReview(
                            product_id=prod.product_id,
                            customer_id=cust.customer_id,
                            rating=random.choice([4, 5, 5, 3, 4, 5]),
                            review_text=f"Great experience with {prod.product_name}. High quality and fast shipping!",
                            review_date=order_date + timedelta(days=random.randint(2, 10)),
                        )
                        reviews.append(rev)

                order.total_amount = round(total_amount, 2)

            session.add_all(order_items)
            session.add_all(reviews)
            await session.commit()
            print("[Database Seed] Seeded default users, schema metadata, and 120+ e-commerce records successfully.")


if __name__ == "__main__":
    asyncio.run(seed_database())
