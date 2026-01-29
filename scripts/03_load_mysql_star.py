import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from urllib.parse import quote_plus

CLEAN_PATH = "data/processed/sales_clean.csv"

def main():
    load_dotenv()

    host = os.getenv("MYSQL_HOST", "localhost")
    port = os.getenv("MYSQL_PORT", "3306")
    user = os.getenv("MYSQL_USER", "root")
    password = os.getenv("MYSQL_PASSWORD", "")
    db = os.getenv("MYSQL_DB", "retail_dw")

    # ✅ Encodage du mot de passe (indispensable si caractères spéciaux comme @, !, :)
    password_enc = quote_plus(password)

    # Connexion serveur (sans DB) pour créer la DB si besoin
    server_engine = create_engine(f"mysql+pymysql://{user}:{password_enc}@{host}:{port}/")
    with server_engine.begin() as conn:
        conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {db}"))

    # Connexion à la DB
    engine = create_engine(
        f"mysql+pymysql://{user}:{password_enc}@{host}:{port}/{db}",
        pool_pre_ping=True
    )

    df = pd.read_csv(CLEAN_PATH)
    df["Date"] = pd.to_datetime(df["Date"])

    # ---------- Dimensions ----------
    dim_customer = (
        df[["Customer ID", "Age", "Gender", "Age_Group"]]
        .drop_duplicates()
        .rename(columns={
            "Customer ID": "customer_id",
            "Age": "age",
            "Gender": "gender",
            "Age_Group": "age_group"
        })
        .reset_index(drop=True)
    )

    dim_product = (
        df[["Product Category"]]
        .drop_duplicates()
        .rename(columns={"Product Category": "product_category"})
        .reset_index(drop=True)
    )

    dim_date = (
        df[["Date", "Year", "Month", "Quarter"]]
        .drop_duplicates()
        .rename(columns={
            "Date": "date",
            "Year": "year",
            "Month": "month",
            "Quarter": "quarter"
        })
        .reset_index(drop=True)
    )
    # date_id stable : YYYYMMDD
    dim_date["date_id"] = dim_date["date"].dt.strftime("%Y%m%d").astype(int)
    dim_date = dim_date[["date_id", "date", "year", "month", "quarter"]]

    # ---------- Fact ----------
    fact_sales = df.rename(columns={
        "Transaction ID": "transaction_id",
        "Customer ID": "customer_id",
        "Product Category": "product_category",
        "Quantity": "quantity",
        "Price per Unit": "unit_price",
        "Total Amount": "total_amount_source",
        "Total_Amount_Calc": "total_amount",
    }).copy()

    fact_sales["date_id"] = pd.to_datetime(fact_sales["Date"]).dt.strftime("%Y%m%d").astype(int)

    fact_sales = fact_sales[[
        "transaction_id",
        "date_id",
        "customer_id",
        "product_category",
        "quantity",
        "unit_price",
        "total_amount",
        "total_amount_source",
        "Amount_Diff"
    ]]

    # Chargement (replace simple pour l'instant)
    dim_customer.to_sql("dim_customer", engine, if_exists="replace", index=False)
    dim_product.to_sql("dim_product", engine, if_exists="replace", index=False)
    dim_date.to_sql("dim_date", engine, if_exists="replace", index=False)
    fact_sales.to_sql("fact_sales", engine, if_exists="replace", index=False)

    print("=== LOAD OK (MySQL) ===")
    print(f"DB : {db} @ {host}:{port}")
    print("dim_customer :", len(dim_customer))
    print("dim_product  :", len(dim_product))
    print("dim_date     :", len(dim_date))
    print("fact_sales   :", len(fact_sales))

if __name__ == "__main__":
    main()
