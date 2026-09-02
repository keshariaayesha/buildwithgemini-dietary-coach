"""Firestore tools for food catalog reading and writing."""

from google.cloud import firestore

# Hardcoded GCP Project ID as required by Agent Platform
FIRESTORE_PROJECT_ID = "qwiklabs-gcp-03-97c80a1d932c"


def get_firestore_client() -> firestore.Client:
    """Returns a Firestore client initialized with hardcoded GCP project ID."""
    return firestore.Client(project=FIRESTORE_PROJECT_ID)


def search_food_catalog(query: str = "", category: str = "", tag: str = "") -> str:
    """Search or list items from the Firestore food catalog.

    Args:
        query: Optional search keyword to filter by item name (e.g. 'chicken', 'salad', 'salmon').
        category: Optional category filter (e.g. 'Protein', 'Snack', 'Breakfast', 'Salad & Grain').
        tag: Optional dietary tag filter (e.g. 'high_protein', 'vegan', 'gluten_free', 'peanut_free').

    Returns:
        Formatted string list of matching catalog items with calories, portion size, and macros.
    """
    db = get_firestore_client()
    collection_ref = db.collection("food_catalog")
    docs = collection_ref.stream()

    results = []
    for doc in docs:
        data = doc.to_dict()
        data_id = doc.id
        name = data.get("name", "")
        item_category = data.get("category", "")
        tags = data.get("tags", [])

        if query and query.lower() not in name.lower() and query.lower() not in data_id.lower():
            continue
        if category and category.lower() not in item_category.lower():
            continue
        if tag and tag.lower() not in [t.lower() for t in tags]:
            continue

        results.append(
            f"• {name} [{item_category}]: {data.get('calories')} kcal per {data.get('portion')} "
            f"(Protein: {data.get('protein_g')}g, Carbs: {data.get('carbs_g')}g, Fat: {data.get('fat_g')}g, Fiber: {data.get('fiber_g', 0)}g). "
            f"Tags: {', '.join(tags)}"
        )

    if not results:
        return f"No items found in food catalog matching query='{query}', category='{category}', tag='{tag}'."

    return "Food Catalog Results:\n" + "\n".join(results)


def add_food_to_catalog(
    name: str,
    category: str,
    portion: str,
    calories: int,
    protein_g: float,
    carbs_g: float,
    fat_g: float,
    fiber_g: float = 0.0,
    tags: str = "",
) -> str:
    """Add a new healthy food or dish entry to the Firestore food catalog.

    Args:
        name: Name of the food item or dish (e.g. 'Turkey Avocado Wrap').
        category: Food category (e.g. 'Protein', 'Snack', 'Breakfast', 'Salad & Grain').
        portion: Standard serving size (e.g. '1 wrap', '150g').
        calories: Total calorie count per serving.
        protein_g: Grams of protein.
        carbs_g: Grams of carbohydrates.
        fat_g: Grams of fat.
        fiber_g: Grams of dietary fiber.
        tags: Comma-separated list of dietary tags (e.g. 'high_protein, gluten_free, peanut_free').

    Returns:
        Confirmation message with the created document ID in Firestore.
    """
    db = get_firestore_client()
    doc_id = name.lower().replace(" ", "-").replace("&", "and")
    parsed_tags = [t.strip().lower().replace(" ", "_") for t in tags.split(",") if t.strip()]

    item_data = {
        "id": doc_id,
        "name": name,
        "category": category,
        "portion": portion,
        "calories": calories,
        "protein_g": protein_g,
        "carbs_g": carbs_g,
        "fat_g": fat_g,
        "fiber_g": fiber_g,
        "tags": parsed_tags,
    }

    doc_ref = db.collection("food_catalog").document(doc_id)
    doc_ref.set(item_data)

    return f"Successfully added '{name}' to Firestore food_catalog with ID '{doc_id}'."
