import pandas as pd

df = pd.read_csv('cp_villes.csv', sep=';', header=0)    # type: ignore
df = df.sort_values(by='Nom_commune', ascending=True).reset_index(drop=True)

print(df.head())

with open('91_villes.sql', 'w', encoding='ISO-8859-1') as f:
    # Création de la table
    f.write("""
CREATE TABLE IF NOT EXISTS 91_villes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(255) NOT NULL,
    code_postal INT NOT NULL
);
""")
    # Insertion des données
    for _, row in df.iterrows():
        nom = row['Nom_commune'].replace("'", "''")
        code_postal = int(row['Code_postal'])
        sql = f"INSERT INTO 91_villes (nom, code_postal) VALUES ('{nom}', {code_postal});\n"
        f.write(sql)

