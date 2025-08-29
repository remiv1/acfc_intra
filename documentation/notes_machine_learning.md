# Notes sur le projet de Machine Learning : Prédiction de compte comptable

## 🎯 Objectif

Mettre en place un modèle simple et rapide de classification pour prédire le compte comptable (et son numéro) à partir du libellé d’une opération.

## 🏗 Structure du modèle

Classification hiérarchique en 3 niveaux :

1. **Classe principale** (ex. : charges, produits, immobilisations…)
2. **Sous-classe** (ex. : charges externes, charges de personnel…)
3. **Compte précis** (ex. : 6063 – Fournitures de bureau)

Chaînage des modèles :

- Le premier modèle prédit le niveau 1
- Le second affine vers le niveau 2
- Le troisième donne le compte exact

## ⚡ Contraintes

- **Très rapide** : prédiction quasi instantanée lors de la saisie
- **Léger** : pas de modèle lourd type deep learning complexe en production
- **Fiable** : amélioration continue grâce aux validations/corrections des utilisateurs

## 🔁 Pipeline proposé

- **Prétraitement du libellé** : nettoyage, normalisation, tokenisation
- **Vectorisation** : TF-IDF ou embeddings légers pour comprendre le texte
- **Prédiction** :
  - *Modèles simples (Logistic Regression, Naive Bayes, LightGBM)*
  - *Trois étapes successives pour les 3 niveaux*
- **Enregistrement** dans une base NoSQL des prédictions + validations réelles
- **Ré-entraînement mensuel** avec les nouvelles données validées
- **Suivi des performances et des erreurs** via un tableau de bord

## 💡 Workflow utilisateur

```txt
+---------------------------------------+
|   Remplissage du champs "libellé"     |
+---------------------------------------+
                  ↓
+---------------------------------------+
|   Prédiction du compte comptable      |
+---------------------------------------+
                  ↓
+---------------------------------------+
|       Validation / Correction         |
+---------------------------------------+
                  ↓
+---------------------------------------+
|   Stockage pour amélioration future   |
+---------------------------------------+
```

- L’utilisateur saisit le libellé
- passe au champ “compte”
- le modèle prédit automatiquement le compte et son numéro
- l’utilisateur valide ou corrige
- la correction est stockée pour améliorer le modèle.
