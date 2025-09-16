# 🍳 Système de Recommandation de Recettes avec Neo4j

## 📋 Description

Ce projet implémente un système de recommandation de recettes utilisant une base de données graphe Neo4j. Le système analyse les interactions entre utilisateurs et recettes pour proposer des recommandations personnalisées basées sur la similarité de Pearson, les catégories de plats, les tags et les ingrédients partagés.

## 🎯 Objectifs

- Développer un système de recommandation intelligent pour une application de restauration en ligne
- Exploiter la puissance des bases de données graphes pour modéliser les relations complexes entre utilisateurs, recettes, ingrédients et tags
- Implémenter un algorithme de recommandation hybride combinant filtrage collaboratif et filtrage basé sur le contenu

## 📊 Dataset

### Source des données

- **Origine** : Food.com (anciennement GeniusKitchen)
- **Contenu** : Plus de 180 000 recettes et 700 000 avis utilisateurs
- **Période** : 18 ans d'interactions utilisateur
- **Disponibilité** : [Kaggle](https://www.kaggle.com/) et [Google Drive](https://drive.google.com/file/d/1MH4_9OQfAekBI8lmVfyg4e_ypqXA9YC2/view?usp=drive_link)

### Structure des données

- `RAW_recipes.csv` : Recettes avec ingrédients, tags, temps de préparation, etc.
- `RAW_interactions.csv` : Interactions utilisateurs (notes, commentaires)

## 🔧 Preprocessing

Le script `script.py` effectue le preprocessing des données :

### Filtres appliqués

- **Recettes populaires** : Conservation des recettes avec au moins 10 interactions
- **Utilisateurs actifs** : Conservation des 10% d'utilisateurs les plus actifs
- **Optimisation** : Suppression des colonnes non pertinentes (`description`, `steps`, `review`, `date`)

### Résultat

- `filtered_recettes.csv` : Recettes filtrées
- `filtered_interactions.csv` : Interactions filtrées

## 🗂️ Modèle de Données Neo4j

### Entités (Nœuds)

- **Recette** : ID, nom, temps de préparation, contributeur, nombre d'ingrédients
- **User** : ID utilisateur
- **Tag** : Étiquettes descriptives des recettes
- **Ingredient** : Ingrédients des recettes
- **CategorieRecette** : Catégories (Entrée, Plat principal, Dessert, Autre)

### Relations

- `RATED` : User → Recette (avec note)
- `HAS_TAG` : Recette → Tag
- `USES` : Recette → Ingredient
- `BELONGS_TO` : Recette → CategorieRecette

## 🚀 Installation et Configuration

### Prérequis

- Neo4j Desktop
- Python 3.x
- pandas

### Étapes d'installation

1. **Cloner le repository**

   ```bash
   git clone [votre-repo]
   cd [nom-du-projet]
   ```

2. **Preprocessing des données**

   ```bash
   python script.py
   ```

3. **Configuration Neo4j**

   - Ouvrir Neo4j Desktop
   - Créer un nouveau projet "MyProject"
   - Créer un DBMS "myproject-DBMS"
   - Créer la base de données "recettes-db"

4. **Copier les fichiers CSV**
   Copier `filtered_recettes.csv` et `filtered_interactions.csv` dans le répertoire import de Neo4j

## 💾 Chargement des Données dans Neo4j

### 1. Création des index

```cypher
CREATE INDEX FOR (r:Recette) ON (r.id);
CREATE INDEX FOR (t:Tag) ON (t.name);
CREATE INDEX FOR (i:Ingredient) ON (i.name);
```

### 2. Chargement des recettes

```cypher
LOAD CSV WITH HEADERS FROM 'file:///filtered_recettes.csv' AS row
CREATE (r:Recette {
    id: toInteger(row.id),
    name: row.name,
    minutes: toInteger(row.minutes),
    contributor_id: toInteger(row.contributor_id),
    submitted: date(row.submitted),
    n_ingredients: toInteger(row.n_ingredients)
});
```

### 3. Chargement des tags

```cypher
LOAD CSV WITH HEADERS FROM 'file:///filtered_recettes.csv' AS row
WITH row, split(replace(row.tags, "'", ""), ", ") AS tags
UNWIND tags AS tag
MERGE (t:Tag {name: trim(tag)})
WITH row, t
MATCH (r:Recette {id: toInteger(row.id)})
MERGE (r)-[:HAS_TAG]->(t);
```

### 4. Chargement des ingrédients

```cypher
LOAD CSV WITH HEADERS FROM 'file:///filtered_recettes.csv' AS row
WITH row, split(replace(row.ingredients, "'", ""), ", ") AS ingredients
UNWIND ingredients AS ingredient
MERGE (i:Ingredient {name: trim(ingredient)})
WITH row, i
MATCH (r:Recette {id: toInteger(row.id)})
MERGE (r)-[:USES]->(i);
```

### 5. Chargement des interactions utilisateurs

```cypher
LOAD CSV WITH HEADERS FROM 'file:///filtered_interactions.csv' AS row
MERGE (u:User {user_id: toInteger(row.user_id)})
WITH u, row
MATCH (r:Recette {id: toInteger(row.recipe_id)})
MERGE (u)-[rel:RATED {rating: toInteger(row.rating)}]->(r);
```

### 6. Création des catégories

```cypher
CREATE (c:CategorieRecette {name: 'Entrée', tags: ['appetizers', 'side-dishes', 'snacks']});
CREATE (c:CategorieRecette {name: 'Plat principal', tags: ['main-dish', 'side-dishes', 'meat', 'lunch']});
CREATE (c:CategorieRecette {name: 'Dessert', tags: ['desserts', 'frozen-desserts', 'snacks', 'kid-friendly']});
CREATE (c:CategorieRecette {name: 'Autre', tags: []});
```

## 🤖 Algorithme de Recommandation

### Composants du système

1. **Similarité de Pearson** : Calcul de la similarité entre utilisateurs basée sur leurs notes
2. **Filtrage par catégorie** : Recommandations dans la même catégorie que la recette source
3. **Similarité de contenu** : Tags et ingrédients partagés
4. **Score pondéré** : Combinaison de la similarité utilisateur et de la note moyenne

### Requête de recommandation complète

```cypher
// Calcul de la similarité de Pearson
MATCH (u1:User {user_id: 56680})-[r:RATED]->(r1:Recette)
WITH u1, avg(r.rating) AS u1_mean
MATCH (u1)-[r1_rating:RATED]->(r1:Recette)<-[r2_rating:RATED]-(u2:User)
WITH u1, u1_mean, u2, COLLECT({r1_rating: r1_rating, r2_rating: r2_rating}) AS ratings
WHERE size(ratings) > 10
MATCH (u2)-[r2:RATED]->(r2_node:Recette)
WITH u1, u1_mean, u2, avg(r2.rating) AS u2_mean, ratings
UNWIND ratings AS r
WITH sum( (r.r1_rating.rating - u1_mean) * (r.r2_rating.rating - u2_mean) ) AS x1,
sqrt( sum( (r.r1_rating.rating - u1_mean)^2) * sum( (r.r2_rating.rating - u2_mean) ^2)) AS x2,
u1, u2 WHERE x2 <> 0
WITH u1, u2, x1/x2 AS pearson

// Filtrage par catégorie
MATCH (r1:Recette {id: 26835})-[:BELONGS_TO]->(cat:CategorieRecette)
WITH cat.name AS category, u2, pearson

// Recommandations basées sur le contenu
MATCH (u2)-[r:RATED]->(r2:Recette)-[:BELONGS_TO]->(cat:CategorieRecette {name: category})
WHERE r.rating > 3
WITH r2, AVG(r.rating) AS average_rating, pearson
MATCH (r2)-[:HAS_TAG]->(tag:Tag)<-[:HAS_TAG]-(r1:Recette {id: 26835})
WITH r2, average_rating, COUNT(tag) AS common_tags, pearson
MATCH (r2)-[:USES]->(ingredient:Ingredient)<-[:USES]-(r1)
WITH r2, average_rating, common_tags, COUNT(ingredient) AS common_ingredients, pearson
ORDER BY average_rating DESC, common_tags DESC, common_ingredients DESC
LIMIT 10

// Score final pondéré
WITH r2, average_rating, common_tags, common_ingredients, pearson
RETURN r2.name AS recommended_recipe, average_rating, common_tags, common_ingredients,
       pearson * average_rating AS weighted_score
ORDER BY weighted_score DESC
LIMIT 10;
```

## 📁 Structure du Projet

```
├── README.md
├── script.py                    # Script de preprocessing
├── filtered_recettes.csv        # Recettes filtrées
├── filtered_interactions.csv    # Interactions filtrées
├── Projet 2 INF8810-RAPPORT.pdf # Rapport complet avec captures
└── Projet 2 INF8810-RAPPORT.txt # Rapport textuel
```

## 🧪 Validation et Tests

### Requêtes de vérification

```cypher
// Lister les recettes
MATCH (r:Recette) RETURN r LIMIT 10;

// Vérifier les relations tags
MATCH (r:Recette)-[:HAS_TAG]->(t:Tag) RETURN r.name, t.name LIMIT 10;

// Vérifier les relations ingrédients
MATCH (r:Recette)-[:USES]->(i:Ingredient) RETURN r.name, i.name LIMIT 10;

// Vérifier les notes utilisateurs
MATCH (u:User)-[rel:RATED]->(r:Recette)
RETURN u.user_id, r.id, rel.rating LIMIT 10;

// Statistiques par catégorie
MATCH (r:Recette)-[:BELONGS_TO]->(c:CategorieRecette)
RETURN c.name AS categorie, COUNT(r) AS nombre_de_recettes;
```

## 🔍 Cas d'Usage

Ce système peut être utilisé dans :

- **Applications de livraison de repas** : Recommandations personnalisées
- **Sites de recettes** : Suggestions basées sur les préférences
- **Planification de menus** : Recommandations équilibrées par catégorie
- **Analyse de tendances culinaires** : Identification de patterns dans les préférences

## 📈 Améliorations Futures

- Intégration de critères nutritionnels
- Prise en compte des allergies et régimes alimentaires
- Recommandations saisonnières
- Interface utilisateur web
- API REST pour intégration externe

## 👥 Contributeurs

Projet réalisé dans le cadre du cours INF8810 - Traitement et Analyse de données massives

## 📄 Documentation

Pour plus de détails, consultez le [rapport complet](Rapport.pdf) qui contient les captures d'écran et analyses détaillées.

---

_Ce projet démontre l'application pratique des bases de données graphes pour résoudre des problèmes complexes de recommandation en exploitant les relations riches entre entités._
