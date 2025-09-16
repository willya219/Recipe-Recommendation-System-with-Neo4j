# 🍳 Recipe Recommendation System with Neo4j

## 📋 Description

This project implements a recipe recommendation system using a Neo4j graph database. The system analyzes interactions between users and recipes to provide personalized recommendations based on Pearson similarity, dish categories, tags, and shared ingredients.

## 🎯 Objectives

- Develop an intelligent recommendation system for an online restaurant application
- Leverage the power of graph databases to model complex relationships between users, recipes, ingredients, and tags
- Implement a hybrid recommendation algorithm combining collaborative filtering and content-based filtering

## 📊 Dataset

### Data Source

- **Origin**: Food.com (formerly GeniusKitchen)
- **Content**: Over 180,000 recipes and 700,000 user reviews
- **Period**: 18 years of user interactions
- **Availability**: [Kaggle](https://www.kaggle.com/) and [Google Drive](https://drive.google.com/file/d/1MH4_9OQfAekBI8lmVfyg4e_ypqXA9YC2/view?usp=drive_link)

### Data Structure

- `RAW_recipes.csv`: Recipes with ingredients, tags, preparation time, etc.
- `RAW_interactions.csv`: User interactions (ratings, comments)

## 🔧 Preprocessing

The `script.py` script performs data preprocessing:

### Applied Filters

- **Popular recipes**: Keep recipes with at least 10 interactions
- **Active users**: Keep the top 10% most active users
- **Optimization**: Remove irrelevant columns (`description`, `steps`, `review`, `date`)

### Output

- `filtered_recettes.csv`: Filtered recipes
- `filtered_interactions.csv`: Filtered interactions

## 🗂️ Neo4j Data Model

### Entities (Nodes)

- **Recette**: ID, name, preparation time, contributor, number of ingredients
- **User**: User ID
- **Tag**: Descriptive labels for recipes
- **Ingredient**: Recipe ingredients
- **CategorieRecette**: Categories (Appetizer, Main Course, Dessert, Other)

### Relationships

- `RATED`: User → Recipe (with rating)
- `HAS_TAG`: Recipe → Tag
- `USES`: Recipe → Ingredient
- `BELONGS_TO`: Recipe → CategorieRecette

## 🚀 Installation and Setup

### Prerequisites

- Neo4j Desktop
- Python 3.x
- pandas

### Installation Steps

1. **Clone the repository**

   ```bash
   git clone [your-repo]
   cd [project-name]
   ```

2. **Data preprocessing**

   ```bash
   python script.py
   ```

3. **Neo4j Setup**

   - Open Neo4j Desktop
   - Create a new project "MyProject"
   - Create a DBMS "myproject-DBMS"
   - Create the database "recettes-db"

4. **Copy CSV files**
   Copy `filtered_recettes.csv` and `filtered_interactions.csv` to the Neo4j import directory

## 💾 Loading Data into Neo4j

### 1. Create indexes

```cypher
CREATE INDEX FOR (r:Recette) ON (r.id);
CREATE INDEX FOR (t:Tag) ON (t.name);
CREATE INDEX FOR (i:Ingredient) ON (i.name);
```

### 2. Load recipes

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

### 3. Load tags

```cypher
LOAD CSV WITH HEADERS FROM 'file:///filtered_recettes.csv' AS row
WITH row, split(replace(row.tags, "'", ""), ", ") AS tags
UNWIND tags AS tag
MERGE (t:Tag {name: trim(tag)})
WITH row, t
MATCH (r:Recette {id: toInteger(row.id)})
MERGE (r)-[:HAS_TAG]->(t);
```

### 4. Load ingredients

```cypher
LOAD CSV WITH HEADERS FROM 'file:///filtered_recettes.csv' AS row
WITH row, split(replace(row.ingredients, "'", ""), ", ") AS ingredients
UNWIND ingredients AS ingredient
MERGE (i:Ingredient {name: trim(ingredient)})
WITH row, i
MATCH (r:Recette {id: toInteger(row.id)})
MERGE (r)-[:USES]->(i);
```

### 5. Load user interactions

```cypher
LOAD CSV WITH HEADERS FROM 'file:///filtered_interactions.csv' AS row
MERGE (u:User {user_id: toInteger(row.user_id)})
WITH u, row
MATCH (r:Recette {id: toInteger(row.recipe_id)})
MERGE (u)-[rel:RATED {rating: toInteger(row.rating)}]->(r);
```

### 6. Create categories

```cypher
CREATE (c:CategorieRecette {name: 'Entrée', tags: ['appetizers', 'side-dishes', 'snacks']});
CREATE (c:CategorieRecette {name: 'Plat principal', tags: ['main-dish', 'side-dishes', 'meat', 'lunch']});
CREATE (c:CategorieRecette {name: 'Dessert', tags: ['desserts', 'frozen-desserts', 'snacks', 'kid-friendly']});
CREATE (c:CategorieRecette {name: 'Autre', tags: []});
```

## 🤖 Recommendation Algorithm

### System Components

1. **Pearson Similarity**: Calculate similarity between users based on their ratings
2. **Category Filtering**: Recommendations within the same category as the source recipe
3. **Content Similarity**: Shared tags and ingredients
4. **Weighted Score**: Combination of user similarity and average rating

### Complete Recommendation Query

```cypher
// Calculate Pearson similarity
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

// Category filtering
MATCH (r1:Recette {id: 26835})-[:BELONGS_TO]->(cat:CategorieRecette)
WITH cat.name AS category, u2, pearson

// Content-based recommendations
MATCH (u2)-[r:RATED]->(r2:Recette)-[:BELONGS_TO]->(cat:CategorieRecette {name: category})
WHERE r.rating > 3
WITH r2, AVG(r.rating) AS average_rating, pearson
MATCH (r2)-[:HAS_TAG]->(tag:Tag)<-[:HAS_TAG]-(r1:Recette {id: 26835})
WITH r2, average_rating, COUNT(tag) AS common_tags, pearson
MATCH (r2)-[:USES]->(ingredient:Ingredient)<-[:USES]-(r1)
WITH r2, average_rating, common_tags, COUNT(ingredient) AS common_ingredients, pearson
ORDER BY average_rating DESC, common_tags DESC, common_ingredients DESC
LIMIT 10

// Weighted final score
WITH r2, average_rating, common_tags, common_ingredients, pearson
RETURN r2.name AS recommended_recipe, average_rating, common_tags, common_ingredients,
       pearson * average_rating AS weighted_score
ORDER BY weighted_score DESC
LIMIT 10;
```

## 📁 Project Structure

```
├── README.md
├── README_EN.md                 # English version
├── script.py                    # Preprocessing script
├── filtered_recettes.csv        # Filtered recipes
├── filtered_interactions.csv    # Filtered interactions
├── Rapport.pdf                  # Complete report with screenshots
└── Projet 2 INF8810-RAPPORT.txt # Text report
```

## 🧪 Validation and Testing

### Verification Queries

```cypher
// List recipes
MATCH (r:Recette) RETURN r LIMIT 10;

// Check tag relationships
MATCH (r:Recette)-[:HAS_TAG]->(t:Tag) RETURN r.name, t.name LIMIT 10;

// Check ingredient relationships
MATCH (r:Recette)-[:USES]->(i:Ingredient) RETURN r.name, i.name LIMIT 10;

// Check user ratings
MATCH (u:User)-[rel:RATED]->(r:Recette)
RETURN u.user_id, r.id, rel.rating LIMIT 10;

// Statistics by category
MATCH (r:Recette)-[:BELONGS_TO]->(c:CategorieRecette)
RETURN c.name AS category, COUNT(r) AS recipe_count;
```

## 🔍 Use Cases

This system can be used in:

- **Food delivery applications**: Personalized recommendations
- **Recipe websites**: Preference-based suggestions
- **Menu planning**: Balanced recommendations by category
- **Culinary trend analysis**: Pattern identification in preferences

## 📈 Future Improvements

- Integration of nutritional criteria
- Consideration of allergies and dietary restrictions
- Seasonal recommendations
- Web user interface
- REST API for external integration

## 📄 Documentation

For more details, see the [complete report](Rapport.pdf) which contains screenshots and detailed analyses.

---

_This project demonstrates the practical application of graph databases to solve complex recommendation problems by exploiting rich relationships between entities._
