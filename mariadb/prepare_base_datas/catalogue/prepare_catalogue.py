import pandas as pd

df = pd.read_csv('catalogue.csv', sep=';', header=0)
df = df.sort_values(by='N°', ascending=True).reset_index(drop=True)
df = df[['Type', 'Sous-Type', 'PU HT', 'Année']]

print(df.head())

with open('21_catalogue.sql', 'w', encoding='utf-8') as f:
    # Création de la table
    f.write("""
CREATE TABLE IF NOT EXISTS 21_catalogue (
    id INT AUTO_INCREMENT PRIMARY KEY,
    type_produit VARCHAR(100) NOT NULL,
    stype_produit VARCHAR(100) NOT NULL,
    millesime INT,
    ref_auto VARCHAR(8) GENERATED ALWAYS AS (CONCAT(SUBSTRING(millesime, -2), UPPER(LEFT(type_produit, 4)), LPAD(id, 2, '0'))) STORED,
    des_auto VARCHAR(100) GENERATED ALWAYS AS (CONCAT(UPPER(stype_produit), ' TARIF ', millesime)) STORED,
    prix_unitaire_ht DECIMAL(10,2) DEFAULT 0.00,
    geographie VARCHAR(10) GENERATED ALWAYS AS (UPPER(SUBSTRING_INDEX(SUBSTRING_INDEX(stype_produit, ' ', 4), ' ', -1))) STORED,
    poids VARCHAR(5) GENERATED ALWAYS AS (SUBSTRING_INDEX(SUBSTRING_INDEX(stype_produit, ' ', 3), ' ', -1)) STORED,
    created_at DATE DEFAULT CURRENT_DATE NOT NULL,
    updated_at DATE DEFAULT CURRENT_DATE ON UPDATE CURRENT_DATE NOT NULL
);
""")
    # Insertion des données
    for _, row in df.iterrows():
        type_produit = row['Type'].replace("'", "''")
        stype_produit = row['Sous-Type'].replace("'", "''")
        millesime = int(row['Année'])
        prix_unitaire_ht = float(row['PU HT'].replace(',', '.'))
        sql = f"INSERT INTO 21_catalogue (type_produit, stype_produit, millesime, prix_unitaire_ht) VALUES ('{type_produit}', '{stype_produit}', {millesime}, {prix_unitaire_ht});\n"
        f.write(sql)

