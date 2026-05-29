import pandas as pd
import hashlib

COLUMN_MAP={

    "date"               : "sale_date",
    "sale_date"          : "sale_date",
    "sale date"          : "sale_date",
    "order date"         : "sale_date",
    "orderdate"          : "sale_date",
    "transaction date"   : "sale_date",
    "bill date"          : "sale_date",

    "customer"           : "customer_name",
    "customer name"      : "customer_name",
    "customer_name"      : "customer_name",
    "client"             : "customer_name",
    "client name"        : "customer_name",
    "buyer"              : "customer_name",

    "product"            : "product_name",
    "product name"       : "product_name",
    "product_name"       : "product_name",
    "item"               : "product_name",
    "goods"              : "product_name",

    "qty"                : "quantity",
    "units"              : "quantity",
    "pieces"             : "quantity",
    "no of units"        : "quantity",
    "no_of_units"        : "quantity",

    "amount"             : "total_amount",
    "total"              : "total_amount",
    "total amount"       : "total_amount",
    "total_amount"       : "total_amount",
    "sale amount"        : "total_amount",
    "sale_amount"        : "total_amount",
    "bill amount"        : "total_amount",
    "bill_amount"        : "total_amount",
    "revenue"            : "total_amount",

    "price"              : "unit_price",
    "unit price"         : "unit_price",
    "unit_price"         : "unit_price",
    "rate"               : "unit_price",
    "mrp"                : "unit_price",

    "cat"                : "category",
    "category_name"      : "category",   
    "category name"      : "category",
    "product_category"   : "category",
    "product category"   : "category",
    "type"               : "category",

    "city"               : "customer_city",
    "customer city"      : "customer_city",
    "customer_city"      : "customer_city",
    "location"           : "customer_city",

    "state"              : "customer_state",
    "customer state"     : "customer_state",
    "customer_state"     : "customer_state",

    "payment"            : "payment_mode",
    "payment mode"       : "payment_mode",
    "payment_mode"       : "payment_mode",
    "payment method"     : "payment_mode",
    "payment_method"     : "payment_mode",

    "status"             : "order_status",
    "order status"       : "order_status",
    "order_status"       : "order_status",
    "delivery status"    : "order_status",
    "delivery_status"    : "order_status",

    "invoice id"         : "invoice_id",
    "invoice_id"         : "invoice_id",
    "invoice no"         : "invoice_id",
    "invoice_no"         : "invoice_id",
    "invoice number"     : "invoice_id",
    "invoice_number"     : "invoice_id",
    "bill no"            : "invoice_id",
    "bill_no"            : "invoice_id",
    "bill number"        : "invoice_id",
    "bill_number"        : "invoice_id",
    "order id"           : "invoice_id",
    "order_id"           : "invoice_id",
    "transaction id"     : "invoice_id",
    "transaction_id"     : "invoice_id",
    "txn id"             : "invoice_id",
    "txn_id"             : "invoice_id",
    "receipt no"         : "invoice_id",
    "receipt_no"         : "invoice_id",

    "discount"           : "discount",
    "disc"               : "discount",
    "discount amount"    : "discount",
    "discount_amount"    : "discount",

    "salesperson"        : "salesperson",
    "sales person"       : "salesperson",
    "sales_person"       : "salesperson",
    "sales rep"          : "salesperson",
    "sales_rep"          : "salesperson",
    "employee"           : "salesperson",
    "staff"              : "salesperson",
    "sp code"            : "salesperson",
    "sp_code"            : "salesperson",

    "region"             : "region",
    "area"               : "region",
    "zone"               : "region",
    "territory"          : "region",

    "remarks"            : "remarks",
    "notes"              : "remarks",
    "comment"            : "remarks",
    "comments"           : "remarks",
}

REQUIRED_COLUMNS=[
    "sale_date",
    "customer_name",
    "product_name",
    "quantity",
    "total_amount",
    "invoice_id"
]

OPTIONAL_COLUMNS={
    "category":"Unknown",
    "unit_price":0,
    "customer_city":"Unknown",
    "customer_state":"Unknown",
    "payment_mode":"Unknown",
    "order_status":"Delivered",
    "discount"      : 0,
    "salesperson"   : "Unknown",
    "region"        : "Unknown",
    "remarks"       : ""
}

def standardize_columns(df:pd.DataFrame) -> pd.DataFrame:
    df.columns=(df.columns
                .str.strip()
                .str.lower()
                .str.replace(" ","_")
                .str.replace(r"[^a-z0-9_]","",regex=True)
                )
    df=df.rename(columns=COLUMN_MAP)
    return df

def validate_columns(df:pd.DataFrame)->dict:
    missing_required=[
        col for col in REQUIRED_COLUMNS
        if col not in df.columns
    ]

    missing_optional=[
        col for col in OPTIONAL_COLUMNS
        if col not in df.columns
    ]

    return {
        "missing_required":missing_required,
        "missing_optional":missing_optional,
        "can_proceed":len(missing_required)==0
    }
    
def fill_optional_columns(df:pd.DataFrame)->pd.DataFrame:
        for col,default in OPTIONAL_COLUMNS.items():
            if col not in df.columns:
                df[col]=default
        return df


def remove_empty_rows(df:pd.DataFrame):
     before=len(df)
     df=df.dropna(how="all")
     after=len(df)
     return df,before-after

def remove_duplicates(df:pd.DataFrame):
     before=len(df)
     df=df.drop_duplicates()
     after=len(df)
     return df,before-after

def fix_missing_values(df: pd.DataFrame)-> pd.DataFrame:
     df["sale_date"]=pd.to_datetime(
          df["sale_date"],errors="coerce"
     ).fillna(pd.Timestamp.today().normalize())

     df["customer_name"]=df["customer_name"].fillna("Unknown")
     df["product_name"]=df["product_name"].fillna("Unknown")
     df["category"]=df["category"].fillna("Unknown")
     df["customer_city"]=df["customer_city"].fillna("Unknown")
     df["customer_state"]=df["customer_state"].fillna("Unknown")
     df["payment_mode"]=df["payment_mode"].fillna("Unknown")
     df["order_status"]=df["order_status"].fillna("Delivered")

     if "invoice_id" in df.columns:
        df["invoice_id"] = df["invoice_id"].fillna("Unknown")
        df["invoice_id"] = df["invoice_id"].astype(str).str.strip()

     if "discount" in df.columns:
        df["discount"] = pd.to_numeric(
            df["discount"], errors="coerce"
        ).fillna(0).round(2)
     
     if "salesperson" in df.columns:
        df["salesperson"] = df["salesperson"].fillna("Unknown")

     if "region" in df.columns:
        df["region"] = df["region"].fillna("Unknown")

     if "remarks" in df.columns:
        df["remarks"] = df["remarks"].fillna("")

     df["quantity"]=pd.to_numeric(
          df["quantity"],errors="coerce"
     ).fillna(0).round(2)

     df["total_amount"] = pd.to_numeric(
        df["total_amount"], errors="coerce"
    ).fillna(0).round(2)

     df["unit_price"]=pd.to_numeric(
          df["unit_price"],errors="coerce"
     ).fillna(0).round(2)



     return df

def fix_text_columns(df:pd.DataFrame)-> pd.DataFrame:
     text_cols=[
          "customer_name","product_name","category",
          "customer_city","customer_state",
          "payment_mode","order_status"
     ]
     for col in text_cols:
          if col in df.columns:
               df[col]=(
                    df[col]
                    .astype(str)
                    .str.strip()
                    .str.title()
                    .replace("Nan","Unknown")
                    .replace("None","Unknown")
               )
     return df

def recalculate_total(df: pd.DataFrame):
     mismatch_count=0
     if "unit_price" in df.columns:
          calculated=df["unit_price"]*df["quantity"]
          mismatch=(df["total_amount"]-calculated).abs()>1
          mismatch_count=int(mismatch.sum())
          if mismatch_count > 0:
               df.loc[mismatch,"total_amount"]=calculated[mismatch].round(2)
     return df, mismatch_count

def validate_date(df:pd.DataFrame):
     today=pd.Timestamp.today()

     future=df["sale_date"]>today
     if future.sum()>0:
          df.loc[future,"sale_date"]=today

     very_old=df["sale_date"]<pd.Timestamp("2000-01-01")

     return df,int(future.sum()), int(very_old.sum())

def validate_numbers(df: pd.DataFrame):
     negative_qty=int((df["quantity"]<0).sum())
     zero_amount=int((df["total_amount"]<=0).sum())

     df=df[df["quantity"]>0]

     return df,negative_qty,zero_amount

def detect_outliers(df: pd.DataFrame):
     mean=df["total_amount"].mean()
     std=df["total_amount"].std()

     df["is_outlier"]=(
          (df["total_amount"]-mean).abs()>3*std
     )
     return df, int(df["is_outlier"].sum())

def detect_missing_dates(df: pd.DataFrame)->list:
     if df["sale_date"].isna().all():
          return[]
     
     all_dates=pd.date_range(
          start=df["sale_date"].min(),
          end=df["sale_date"].max()
     )
     date_dates=pd.to_datetime(
        df["sale_date"]
     ).dt.date.unique()

     return [
          str(d.date()) for d in all_dates
          if d.date() not in date_dates
     ]

def add_row_hash(df:pd.DataFrame)-> pd.DataFrame:
     core_cols=[
          "sale_date","customer_name",
          "product_name","quantity","total_amount","invoice_id"
     ]
     cols = [c for c in core_cols if c in df.columns]

     df["row_hash"] = df[cols].apply(
        lambda row: hashlib.md5(
            "|".join(str(v) for v in row.values).encode()
        ).hexdigest(),
        axis=1
    )
     return df

def add_metadata(df: pd.DataFrame,file_name:str)->pd.DataFrame:
     df["source_file"]=file_name
     df["uploaded_at"]=pd.Timestamp.now()
     return df

def clean_dataframe(df: pd.DataFrame, file_name: str) -> dict:
    report = {"success": False}

    # 1 — standardize columns
    df = standardize_columns(df)

    # 2 — validate required columns
    validation = validate_columns(df)
    report["validation"] = validation

    if not validation["can_proceed"]:
        report["dataframe"] = df
        return report

    # 3 — fill optional columns
    df = fill_optional_columns(df)
    report["optional_added"] = validation["missing_optional"]

    # 4 — remove empty rows
    df, report["empty_rows_removed"] = remove_empty_rows(df)

    # 5 — remove duplicates
    df, report["duplicates_removed"] = remove_duplicates(df)

    # 6 — fix missing values
    missing_before      = int(df.isnull().sum().sum())
    df                  = fix_missing_values(df)
    report["missing_fixed"] = missing_before - \
                              int(df.isnull().sum().sum())

    # 7 — fix text formatting
    df = fix_text_columns(df)

    # 8 — recalculate total
    df, report["mismatch_total"] = recalculate_total(df)

    # 9 — validate dates
    df, report["future_dates"], \
    report["old_dates"]  = validate_date(df)

    # 10 — validate numbers
    df, report["negative_qty"], \
    report["zero_amount"] = validate_numbers(df)

    # 11 — detect outliers
    df, report["outliers"] = detect_outliers(df)

    # 12 — detect missing date gaps
    report["missing_date_gaps"] = detect_missing_dates(df)

    # 13 — add row hash (includes invoice_id)
    df = add_row_hash(df)

    # 14 — remove hash duplicates within same file
    before = len(df)
    df     = df.drop_duplicates(subset=["row_hash"])
    report["hash_duplicates_removed"] = before - len(df)

    # 15 — add metadata
    df = add_metadata(df, file_name)

    # Final columns
    final_cols = [
        "sale_date", "customer_name", "customer_city",
        "customer_state", "product_name", "category",
        "unit_price", "quantity", "total_amount",
        "discount", "payment_mode", "order_status",
        "invoice_id", "salesperson", "region",
        "remarks", "is_outlier", "row_hash",
        "source_file", "uploaded_at"
    ]
    df = df[[c for c in final_cols if c in df.columns]]

    report["success"]    = True
    report["final_rows"] = len(df)
    report["dataframe"]  = df

    return report