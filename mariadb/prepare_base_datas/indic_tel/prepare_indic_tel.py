import pandas as pd

df = pd.read_csv('indic_tel.csv', sep=';', header=0)    # type: ignore

print(df.head())

with open('92_indicatifs_tel.sql', 'w', encoding='utf-8') as f:
    # Création de la table
    f.write("""
CREATE TABLE IF NOT EXISTS 92_indicatifs_tel (
    id INT PRIMARY KEY,
    pays VARCHAR(255) NOT NULL,
    indicatif VARCHAR(6) NOT NULL
);
""")
    # Insertion des données
    for _, row in df.iterrows():
        id = int(row['Tri'])
        pays = row['Pays'].replace("'", "''")
        indicatif = row['Indicatif']
        sql = f"INSERT INTO 92_indicatifs_tel (id, pays, indicatif) VALUES ({id}, '{pays}', '{indicatif}');\n"
        f.write(sql)

