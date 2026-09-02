"""Seed script for Firestore food_catalog collection."""

from google.cloud import firestore

# Hardcoded GCP Project ID (Agent Platform project number fallback breaks Firestore if dynamic)
PROJECT_ID = "qwiklabs-gcp-03-97c80a1d932c"

SEED_FOODS = [
    {
        "id": "grilled-chicken-breast",
        "name": "Grilled Chicken Breast",
        "category": "Protein",
        "portion": "100g",
        "calories": 165,
        "protein_g": 31.0,
        "carbs_g": 0.0,
        "fat_g": 3.6,
        "fiber_g": 0.0,
        "tags": ["high_protein", "low_fat", "peanut_free", "dairy_free", "gluten_free"],
    },
    {
        "id": "salmon-fillet",
        "name": "Baked Salmon Fillet",
        "category": "Protein",
        "portion": "120g",
        "calories": 240,
        "protein_g": 25.0,
        "carbs_g": 0.0,
        "fat_g": 15.0,
        "fiber_g": 0.0,
        "tags": ["high_protein", "omega3", "peanut_free", "dairy_free", "gluten_free"],
    },
    {
        "id": "quinoa-avocado-salad",
        "name": "Quinoa & Avocado Salad",
        "category": "Salad & Grain",
        "portion": "1 cup",
        "calories": 220,
        "protein_g": 6.0,
        "carbs_g": 28.0,
        "fat_g": 10.0,
        "fiber_g": 5.0,
        "tags": ["vegan", "high_fiber", "peanut_free", "dairy_free", "gluten_free"],
    },
    {
        "id": "greek-yogurt-berries",
        "name": "Greek Yogurt with Berries",
        "category": "Snack",
        "portion": "200g",
        "calories": 150,
        "protein_g": 15.0,
        "carbs_g": 18.0,
        "fat_g": 2.0,
        "fiber_g": 3.0,
        "tags": ["high_protein", "peanut_free", "gluten_free"],
    },
    {
        "id": "oatmeal-chia-seeds",
        "name": "Oatmeal with Chia Seeds",
        "category": "Breakfast",
        "portion": "1 bowl (150g)",
        "calories": 180,
        "protein_g": 7.0,
        "carbs_g": 32.0,
        "fat_g": 3.5,
        "fiber_g": 6.0,
        "tags": ["high_fiber", "vegan", "peanut_free", "dairy_free"],
    },
]


def seed_database() -> None:
    """Seed the Firestore food_catalog collection with initial items."""
    db = firestore.Client(project=PROJECT_ID)
    collection_ref = db.collection("food_catalog")
    for food in SEED_FOODS:
        doc_id = food["id"]
        doc_ref = collection_ref.document(doc_id)
        doc_ref.set(food)
        print(f"Seeded document: {doc_id}")
    print("Firestore seeding complete!")


if __name__ == "__main__":
    seed_database()
