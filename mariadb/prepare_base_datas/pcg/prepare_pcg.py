import pandas as pd

# Lecture du fichier avec encodage correct
df: pd.DataFrame = pd.read_csv("pcg.csv", encoding="ISO-8859-1", sep=",", header=0) # type: ignore

# Compléter la colonne 'Compte' avec des zéros à droite pour avoir 6 chiffres
df['Compte'] = df['Compte'].apply(lambda x: str(x).ljust(6, '0'))   # type: ignore
df['Categorie 2'] = df['Categorie 2'].apply(lambda x: str(x).ljust(3, '0'))   # type: ignore

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
        values = [f"'{str(x).replace('\'', '\'\'')}'" for x in row]
        f.write(f"INSERT INTO 30_pcg VALUES ({', '.join(values)});\n")