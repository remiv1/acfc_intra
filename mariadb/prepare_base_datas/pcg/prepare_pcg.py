import pandas as pd

# Lecture du fichier avec encodage correct
df: pd.DataFrame = pd.read_csv("pcg.csv", encoding="ISO-8859-1", sep=",", header=1) # type: ignore

df = df.iloc[:, -2:]

df.insert(0, 'Classe', df['Compte'].astype(str).str[:1])    # type: ignore
df.insert(1, 'Categorie 1', df['Compte'].astype(str).str[:2])    # type: ignore
df.insert(2, 'Categorie 2', df['Compte'].astype(str).str[:3])    # type: ignore

# Enregistrement du DataFrame corrigé en CSV
df.to_csv("pcg.csv", index=False, encoding="ISO-8859-1")

# Génération d'un fichier SQL pour insertion dans une base de données
with open("pcg.sql", "w", encoding="ISO-8859-1") as f:
    # Création de la table
    f.write("""
CREATE TABLE IF NOT EXISTS 30_pcg (
    classe INT NOT NULL,
    categorie_1 INT NOT NULL,
    categorie_2 INT NOT NULL,
    compte INT PRIMARY KEY,
    denomination VARCHAR(255) NOT NULL
);
""")
    # Insertion des données
    for _, row in df.iterrows():
        values = "', '".join(str(x).replace("'", "''") for x in row)
        f.write(f"INSERT INTO pcg_corrige VALUES ('{values}');\n")