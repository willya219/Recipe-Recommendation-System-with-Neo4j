import pandas as pd

# Chemins des fichiers d'entrée
recettes_file = "RAW_recipes.csv"
interactions_file = "RAW_interactions.csv"

# Chargement des fichiers
recettes = pd.read_csv(recettes_file)
interactions = pd.read_csv(interactions_file)

# Définir les seuils pour filtrage
min_interactions_recette = 10  # Garder les recettes avec au moins 10 interactions
top_percentage_users = 0.1   # Garder les interactions des 10% des utilisateurs les plus actifs

# Filtrer les recettes populaires
recette_counts = interactions['recipe_id'].value_counts()

popular_recettes = recette_counts[recette_counts >= min_interactions_recette].index
filtered_recettes = recettes[recettes['id'].isin(popular_recettes)]

# Filtrer les utilisateurs actifs
user_counts = interactions['user_id'].value_counts()
top_users = user_counts.nlargest(int(len(user_counts) * top_percentage_users)).index
filtered_interactions = interactions[
    (interactions['recipe_id'].isin(popular_recettes)) &
    (interactions['user_id'].isin(top_users))
]

# Supprimer la colonne 'description' après le filtrage des recettes
if 'description' in filtered_recettes.columns:
    filtered_recettes = filtered_recettes.drop(columns=['description'])

# Supprimer la colonne 'steps' après le filtrage des recettes
if 'steps' in filtered_recettes.columns:
    filtered_recettes = filtered_recettes.drop(columns=['steps'])
    filtered_recettes = filtered_recettes.drop(columns=['n_steps'])

# Supprimer la colonne 'review' après le filtrage des interaction 
if 'review' in filtered_interactions.columns:
    filtered_interactions = filtered_interactions.drop(columns=['review'])

# Supprimer la colonne 'date' après le filtrage des interaction 
if 'date' in filtered_interactions.columns:
    filtered_interactions = filtered_interactions.drop(columns=['date'])

# Sauvegarder les fichiers réduits
filtered_recettes.to_csv("filtered_recettes.csv", index=False)
filtered_interactions.to_csv("filtered_interactions.csv", index=False)

print("Fichiers réduits sauvegardés.")
