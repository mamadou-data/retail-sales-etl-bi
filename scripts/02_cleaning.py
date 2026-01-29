import pandas as pd
import numpy as np

RAW_PATH = "data/raw/sales.csv"
CLEAN_PATH = "data/processed/sales_clean.csv"
REJECT_PATH = "data/processed/sales_rejected.csv"

# Règles qualité (tu peux ajuster)
AGE_MIN = 10
AGE_MAX = 100
AMOUNT_TOLERANCE = 0  # tolérance d'écart entre Total Amount et recalcul (0 = strict)

def age_group(age: int) -> str:
    if age < 18:
        return "<18"
    elif age <= 25:
        return "18-25"
    elif age <= 35:
        return "26-35"
    elif age <= 45:
        return "36-45"
    elif age <= 60:
        return "46-60"
    else:
        return "60+"

def main():
    df = pd.read_csv(RAW_PATH)

    # 1) Parse date
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    # 2) Standardisation texte
    df["Customer ID"] = df["Customer ID"].astype(str).str.strip()
    df["Gender"] = df["Gender"].astype(str).str.strip().str.title()
    df["Product Category"] = df["Product Category"].astype(str).str.strip().str.title()

    # 3) Champs dérivés
    df["Total_Amount_Calc"] = df["Quantity"] * df["Price per Unit"]
    df["Amount_Diff"] = df["Total Amount"] - df["Total_Amount_Calc"]

    df["Year"] = df["Date"].dt.year
    df["Month"] = df["Date"].dt.month
    df["Quarter"] = df["Date"].dt.quarter

    df["Age_Group"] = df["Age"].apply(age_group)

    # 4) Qualité / règles de rejet
    reject_reasons = []

    # Règle : date valide
    mask_date_invalid = df["Date"].isna()
    reject_reasons.append(("INVALID_DATE", mask_date_invalid))

    # Règle : Quantity > 0
    mask_qty_invalid = df["Quantity"] <= 0
    reject_reasons.append(("INVALID_QUANTITY", mask_qty_invalid))

    # Règle : Price per Unit > 0
    mask_price_invalid = df["Price per Unit"] <= 0
    reject_reasons.append(("INVALID_PRICE", mask_price_invalid))

    # Règle : Age dans bornes
    mask_age_invalid = (df["Age"] < AGE_MIN) | (df["Age"] > AGE_MAX)
    reject_reasons.append(("INVALID_AGE", mask_age_invalid))

    # Règle : Customer ID non vide
    mask_customer_invalid = df["Customer ID"].str.len() == 0
    reject_reasons.append(("INVALID_CUSTOMER_ID", mask_customer_invalid))

    # Règle : Total Amount cohérent avec recalcul
    mask_amount_invalid = df["Amount_Diff"].abs() > AMOUNT_TOLERANCE
    reject_reasons.append(("AMOUNT_MISMATCH", mask_amount_invalid))

    # Construction de la raison de rejet (si plusieurs raisons, on concatène)
    df["reject_reason"] = ""
    for reason, mask in reject_reasons:
        df.loc[mask, "reject_reason"] = np.where(
            df.loc[mask, "reject_reason"].eq(""),
            reason,
            df.loc[mask, "reject_reason"] + "|" + reason
        )

    rejected = df[df["reject_reason"] != ""].copy()
    clean = df[df["reject_reason"] == ""].copy()

    # 5) Sauvegarde
    clean.to_csv(CLEAN_PATH, index=False)
    rejected.to_csv(REJECT_PATH, index=False)

    # 6) Résumé
    print("=== RESULTATS QUALITE ===")
    print(f"Lignes total : {len(df)}")
    print(f"Lignes clean : {len(clean)}")
    print(f"Lignes rejetées : {len(rejected)}")

    if len(rejected) > 0:
        print("\nTop raisons de rejet :")
        print(rejected["reject_reason"].value_counts().head(10))

    # Contrôle de cohérence clé (CA)
    print("\n=== CONTROLE MONTANT ===")
    print("Somme Total Amount (source) :", df["Total Amount"].sum())
    print("Somme Total_Amount_Calc     :", df["Total_Amount_Calc"].sum())
    print("Ecart global                :", (df["Total Amount"].sum() - df["Total_Amount_Calc"].sum()))

if __name__ == "__main__":
    main()
