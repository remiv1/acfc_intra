# TODO: Refactorisation gestion des lignes de commande

## Schéma de traitement (proposition)

1. **Côté client (front)**
    - Le formulaire JS construit un JSON structuré :

    ```json
    {
    "lignes": [
        {"id": 12, "produit_id": 3, "qte": 2, "prix": 10.5, "remise": 0.1},
        {"id": null, "produit_id": 7, "qte": 1, "prix": 5.0, "remise": 0.0}
    ]
    }
    ```

    - Chaque ligne a un identifiant unique (id de la ligne si existante, sinon null pour une nouvelle).
    - Le JSON est envoyé en POST (Content-Type: application/json).

2. **Côté serveur (Python)**

    - Récupérer le JSON : `lignes = request.json['lignes']`
    - Récupérer les lignes existantes en base pour la commande :

    ```python
    lignes_db = session_db.query(DevisesFactures).filter_by(id_commande=commande.id).all()
    lignes_db_dict = {ligne.id: ligne for ligne in lignes_db}
    ```

    - Pour chaque ligne du JSON :
        - Si `id` existe dans `lignes_db_dict` : mettre à jour la ligne.
        - Si `id` est null ou absent de la base : créer une nouvelle ligne.
    - Pour chaque ligne en base non présente dans le JSON : soft delete (ex: `ligne.is_deleted = True`).
    - Commit.

3. **Avantages**
   - Plus simple, plus lisible, moins d’erreurs de parsing.
   - Facile à maintenir et à tester.
   - Adapté à une interface moderne (tableau dynamique, drag&drop, etc.).

---

À implémenter lors de la prochaine session.
