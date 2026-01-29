import pandas as pd

PATH = "data/raw/sales.csv"

df = pd.read_csv(PATH)

print("Aperçu :")
print(df.head(5))

print("\nColonnes :")
print(df.columns.tolist())

print("\nTypes :")
print(df.dtypes)

print("\nValeurs manquantes :")
print(df.isna().sum())

print("\nDoublons (toutes colonnes) :", df.duplicated().sum())
print("Doublons Transaction ID :", df["Transaction ID"].duplicated().sum() if "Transaction ID" in df.columns else "col manquante")
