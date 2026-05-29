# import pandas as pd
# from db.connection import engine

# def get_or_create_categories(df: pd.DataFrame, admin_id:int):
#     try:
#         existing=pd.read_sql(
#             "SELECT category_id,category_name "
#             "FROM categories WHERE admin_id=%s",
#             engine, params=(admin_id,)
#         )
#     except:
#         existing=pd.DataFrame(
#             columns=["category_id","category_name"]
#         )
    
#     if "category" not in df.columns:
#         return existing
    
#     new_cats=df[["category"]]\
#                 .rename(columns={"category":"category_name"})\
#                 .drop_duplicates()
    
#     new_cats=new_cats.merge(
#         existing[["category_name"]],
#         on="category_name",
#         how="left", 
#         indicator=True
#     ).query('_merge=="left_only"')\
#     .drop(columns=["_merge"])

#     if len(new_cats)>0:
#         new_cats["admin_id"]=admin_id
#         new_cats.to_sql(
#             "categories",engine,
#             if_exists="append",
#             index=False
#         )
    
#     return pd.read_sql(
#         "SELECT category_id,category_name "
#         "FROM categories WHERE admin_id=%s",
#         engine, params=(admin_id,)
#     )

# def get_or_create_customers(df: pd.DataFrame,admin_id:int):
#     try:
#         existing=pd.read_sql(
#             "SELECT customer_id,customer_name "
#             "FROM customers WHERE admin_id=%s",
#             engine,params=(admin_id,)
#         )
#     except:
#         existing=pd.DataFrame(
#             columns=["customer_id","customer_name"]
#         )

    
#     cols=[
#         c for c in [
#             "customer_name",
#             "customer_city",
#             "customer_state"
#         ] if c in df.columns
#     ]
#     new_custs=df[cols]\
#                 .drop_duplicates(subset=["customer_name"])
    
#     new_custs=new_custs.merge(
#         existing[["customer_name"]],
#         on="customer_name",
#         how="left",
#         indicator=True
#     ).query('_merge=="left_only"')\
#      .drop(columns=["_merge"])
    
#     if len(new_custs)>0:
#         new_custs["admin_id"]=admin_id
#         new_custs.to_sql(
#             "customers",engine,
#             if_exists="append",
#             index=False
#         )
    
#     return pd.read_sql(
#         "SELECT customer_id,customer_name "
#         "FROM customers WHERE admin_id=%s",
#         engine,params=(admin_id,)
#     )

# def get_or_create_products(df:pd.DataFrame, categories: pd.DataFrame,admin_id: int):
#     try: 
#         existing=pd.read_sql(
#             "SELECT product_id, product_name "
#             "FROM products WHERE admin_id=%s",
#             engine,params=(admin_id,)
#         )
#     except:
#         existing=pd.DataFrame(
#             columns=["product_id","product_name"]
#         )
    
#     cols=[
#         c for c in [
#             "product_name",
#             "category",
#             "unit_price"
#         ] if c in df.columns
#     ]
#     new_prods=df[cols]\
#                 .drop_duplicates(subset=["product_name"])
    
#     new_prods=new_prods.merge(
#         existing[["product_name"]],
#         on="product_name",
#         how="left",
#         indicator=True
#     ).query('_merge=="left_only"')\
#     .drop(columns=["_merge"])

#     if len(new_prods)>0 and "category" in new_prods.columns:
#         new_prods=new_prods.merge(
#             categories.rename(
#                 columns={"category_name":"category"}
#             ),
#             on="category",
#             how="left"
#         )
#         if "unit_price" in new_prods.columns:
#             new_prods=new_prods.rename(
#                 columns={"unit_price":"current_price"}
#             )

#         new_prods["admin_id"]=admin_id

#         keep=[
#             c for c in [
#                 "product_name",
#                 "category_id",
#                 "current_price",
#                 "admin_id"
#             ] if c in new_prods.columns
#         ]

#         new_prods[keep].to_sql(
#             "products", engine,
#             if_exists="append",
#             index=False
#         )

#     return pd.read_sql(
#         "SELECT product_id, product_name "
#         "FROM products WHERE admin_id=%s",
#         engine, params=(admin_id,)
#     )

# def load_sales(df, customers, products, admin_id):

#     df = df.merge(customers, on="customer_name", how="left")
#     df = df.merge(products,  on="product_name",  how="left")
#     df["admin_id"] = admin_id

#     # Updated keep list with new columns
#     keep = [c for c in [
#         "admin_id", "customer_id", "product_id",
#         "sale_date", "quantity", "unit_price",
#         "total_amount", "discount",
#         "payment_mode", "order_status",
#         "invoice_id", "salesperson",
#         "region", "remarks",
#         "row_hash", "source_file", "uploaded_at"
#     ] if c in df.columns]

#     df_insert = df[keep].dropna(
#         subset=["customer_id", "product_id", "row_hash"]
#     )

#     if df_insert.empty:
#         return 0, len(df)

#     inserted = 0
#     skipped  = 0

#     with engine.connect() as conn:
#         for _, row in df_insert.iterrows():
#             try:
#                 row_dict = {
#                     k: v for k, v in row.to_dict().items()
#                     if k in keep
#                 }
#                 cols_str = ", ".join(row_dict.keys())
#                 vals_str = ", ".join(
#                     ["%s"] * len(row_dict)
#                 )
#                 conn.execute(
#                     f"INSERT IGNORE INTO sales "
#                     f"({cols_str}) VALUES ({vals_str})",
#                     tuple(row_dict.values())
#                 )
#                 inserted += 1
#             except:
#                 skipped += 1
#         conn.commit()

#     return inserted, skipped

# def log_upload( admin_id, file_name, total, new, dupes, missing, empty):
#     with engine.connect() as conn:
#         conn.execute(
#             "INSERT INTO upload_log "
#             "(admin_id,file_name, total_rows, new_rows, "
#             "duplicate_rows, missing_fixed, empty_removed,status) "
#             "VALUES (%s, %s, %s, %s, %s, %s, %s,'success')",
#             (admin_id, file_name, total, new, dupes, missing, empty)
#         )
#         conn.commit()

# def normalize_and_load( df: pd.DataFrame, admin_id: int)-> dict:
#     result={}
#     categories=get_or_create_categories(df, admin_id)

#     customers=get_or_create_customers(df, admin_id)

#     products=get_or_create_products(df, categories, admin_id)

#     new_rows, skipped=load_sales(
#         df, customers, products, admin_id
#     )

#     result["new_rows"]=new_rows
#     result["skipped"]=skipped
#     result["customers"]=len(customers)
#     result["products"]=len(products)
#     result["categories"]=len(categories)

#     return result


import pandas as pd
from sqlalchemy import text
from db.connection import engine


def get_or_create_categories(df: pd.DataFrame, admin_id: int):
    try:
        existing = pd.read_sql(
            "SELECT category_id, category_name FROM categories WHERE admin_id=%s",
            engine, params=(admin_id,)
        )
    except:
        existing = pd.DataFrame(columns=["category_id", "category_name"])

    if "category" not in df.columns:
        return existing

    # Normalize category names to Title Case before insert
    new_cats = df[["category"]].copy()
    new_cats["category"] = new_cats["category"].astype(str).str.strip().str.title()
    new_cats = new_cats.rename(columns={"category": "category_name"}).drop_duplicates()

    # Filter out Unknown
    new_cats = new_cats[new_cats["category_name"] != "Unknown"]

    new_cats = new_cats.merge(
        existing[["category_name"]],
        on="category_name", how="left", indicator=True
    ).query('_merge=="left_only"').drop(columns=["_merge"])

    if len(new_cats) > 0:
        new_cats["admin_id"] = admin_id
        new_cats.to_sql("categories", engine, if_exists="append", index=False)

    return pd.read_sql(
        "SELECT category_id, category_name FROM categories WHERE admin_id=%s",
        engine, params=(admin_id,)
    )


def get_or_create_customers(df: pd.DataFrame, admin_id: int):
    try:
        existing = pd.read_sql(
            "SELECT customer_id, customer_name FROM customers WHERE admin_id=%s",
            engine, params=(admin_id,)
        )
    except:
        existing = pd.DataFrame(columns=["customer_id", "customer_name"])

    cols = [c for c in ["customer_name", "customer_city", "customer_state"] if c in df.columns]
    new_custs = df[cols].copy()

    # Normalize to Title Case to match DB
    new_custs["customer_name"] = new_custs["customer_name"].astype(str).str.strip().str.title()
    new_custs = new_custs.drop_duplicates(subset=["customer_name"])

    new_custs = new_custs.merge(
        existing[["customer_name"]],
        on="customer_name", how="left", indicator=True
    ).query('_merge=="left_only"').drop(columns=["_merge"])

    if len(new_custs) > 0:
        new_custs["admin_id"] = admin_id
        new_custs.to_sql("customers", engine, if_exists="append", index=False)

    return pd.read_sql(
        "SELECT customer_id, customer_name FROM customers WHERE admin_id=%s",
        engine, params=(admin_id,)
    )


def get_or_create_products(df: pd.DataFrame, categories: pd.DataFrame, admin_id: int):
    try:
        existing = pd.read_sql(
            "SELECT product_id, product_name FROM products WHERE admin_id=%s",
            engine, params=(admin_id,)
        )
    except:
        existing = pd.DataFrame(columns=["product_id", "product_name"])

    cols = [c for c in ["product_name", "category", "unit_price"] if c in df.columns]
    new_prods = df[cols].copy()

    # Normalize product and category names to Title Case
    new_prods["product_name"] = new_prods["product_name"].astype(str).str.strip().str.title()
    if "category" in new_prods.columns:
        new_prods["category"] = new_prods["category"].astype(str).str.strip().str.title()

    new_prods = new_prods.drop_duplicates(subset=["product_name"])

    new_prods = new_prods.merge(
        existing[["product_name"]],
        on="product_name", how="left", indicator=True
    ).query('_merge=="left_only"').drop(columns=["_merge"])

    if len(new_prods) > 0 and "category" in new_prods.columns:
        # categories df has category_name — rename to match df's "category" column
        cat_lookup = categories.copy()
        cat_lookup["category_name"] = cat_lookup["category_name"].astype(str).str.strip().str.title()

        new_prods = new_prods.merge(
            cat_lookup.rename(columns={"category_name": "category"}),
            on="category",
            how="left"
        )

        if "unit_price" in new_prods.columns:
            new_prods = new_prods.rename(columns={"unit_price": "current_price"})

        new_prods["admin_id"] = admin_id

        keep = [c for c in ["product_name", "category_id", "current_price", "admin_id"]
                if c in new_prods.columns]
        new_prods[keep].to_sql("products", engine, if_exists="append", index=False)

    return pd.read_sql(
        "SELECT product_id, product_name FROM products WHERE admin_id=%s",
        engine, params=(admin_id,)
    )


def load_sales(df, customers, products, admin_id):
    # Normalize names before merge so they match DB values
    df = df.copy()
    df["customer_name"] = df["customer_name"].astype(str).str.strip().str.title()
    df["product_name"]  = df["product_name"].astype(str).str.strip().str.title()

    customers = customers.copy()
    customers["customer_name"] = customers["customer_name"].astype(str).str.strip().str.title()

    products = products.copy()
    products["product_name"] = products["product_name"].astype(str).str.strip().str.title()

    df = df.merge(customers, on="customer_name", how="left")
    df = df.merge(products,  on="product_name",  how="left")
    df["admin_id"] = admin_id

    keep = [c for c in [
        "admin_id", "customer_id", "product_id",
        "sale_date", "quantity", "unit_price",
        "total_amount", "discount",
        "payment_mode", "order_status",
        "invoice_id", "salesperson",
        "region", "remarks",
        "row_hash", "source_file", "uploaded_at"
    ] if c in df.columns]

    # Log how many rows dropped due to missing customer/product
    total_before = len(df)
    df_insert = df[keep].dropna(subset=["customer_id", "product_id", "row_hash"])
    dropped = total_before - len(df_insert)
    if dropped > 0:
        print(f"WARNING: {dropped} rows dropped — customer_id or product_id not found")

    if df_insert.empty:
        return 0, len(df)

    df_insert = df_insert.copy()
    if "sale_date" in df_insert.columns:
        df_insert["sale_date"] = pd.to_datetime(
            df_insert["sale_date"], errors="coerce"
        ).dt.strftime("%Y-%m-%d")

    inserted = 0
    skipped  = 0

    with engine.begin() as conn:
        for _, row in df_insert.iterrows():
            try:
                row_dict = {
                    k: (None if pd.isna(v) else v)
                    for k, v in row.to_dict().items()
                }
                cols_str = ", ".join(row_dict.keys())
                vals_str = ", ".join([f":{k}" for k in row_dict.keys()])
                sql = text(f"INSERT IGNORE INTO sales ({cols_str}) VALUES ({vals_str})")
                conn.execute(sql, row_dict)
                inserted += 1
            except Exception as e:
                skipped += 1
                print(f"Insert error: {e}")

    return inserted, skipped


def log_upload(admin_id, file_name, total, new, dupes, missing, empty):
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO upload_log "
                "(admin_id, file_name, total_rows, new_rows, "
                "duplicate_rows, missing_fixed, empty_removed, status) "
                "VALUES (:admin_id, :file_name, :total, :new, "
                ":dupes, :missing, :empty, 'success')"
            ),
            {
                "admin_id": admin_id, "file_name": file_name,
                "total": total,       "new": new,
                "dupes": dupes,       "missing": missing,
                "empty": empty
            }
        )


def normalize_and_load(df: pd.DataFrame, admin_id: int) -> dict:
    result     = {}
    categories = get_or_create_categories(df, admin_id)
    customers  = get_or_create_customers(df, admin_id)
    products   = get_or_create_products(df, categories, admin_id)
    new_rows, skipped = load_sales(df, customers, products, admin_id)

    result["new_rows"]   = new_rows
    result["skipped"]    = skipped
    result["customers"]  = len(customers)
    result["products"]   = len(products)
    result["categories"] = len(categories)
    return result



