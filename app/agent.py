# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types

from app.tools.firestore import add_food_to_catalog, search_food_catalog
from app.tools.image_tool import generate_food_image, generate_meal_plate_image
from app.tools.rag_tool import consult_nutrition_chart
from app.tools.video_tool import generate_food_video

MODEL = "gemini-2.5-flash"


async def generate_memories_callback(callback_context: CallbackContext):
    """Callback to extract and send durable user memories to Vertex AI Memory Bank."""
    await callback_context.add_session_to_memory()
    return None


def lookup_food_nutrition(food_item: str, portion: str = "1 serving") -> str:
    """Lookup calorie count and nutritional details for a food or drink item.

    Args:
        food_item: Name of the food or beverage item.
        portion: Portion size or quantity (e.g. '100g', '1 cup', '1 slice').

    Returns:
        String with calories, protein, carbohydrates, fat, and dietary fiber information.
    """
    item = food_item.lower()
    if "chicken" in item:
        return f"Nutrition for {food_item} ({portion}): 165 calories, 31g protein, 0g carbs, 3.6g fat."
    elif "egg" in item:
        return f"Nutrition for {food_item} ({portion}): 72 calories, 6.3g protein, 0.4g carbs, 4.8g fat."
    elif "apple" in item:
        return f"Nutrition for {food_item} ({portion}): 95 calories, 0.5g protein, 25g carbs (4.4g fiber), 0.3g fat."
    elif "salad" in item:
        return f"Nutrition for {food_item} ({portion}): 120 calories, 3g protein, 10g carbs (3g fiber), 7g fat."
    elif "rice" in item or "oat" in item or "bread" in item:
        return f"Nutrition for {food_item} ({portion}): 130 calories, 2.7g protein, 28g carbs (1g fiber), 0.3g fat."
    return f"Nutrition estimate for {food_item} ({portion}): ~200 calories, 10g protein, 20g carbs, 5g fat."


def calculate_bmi_and_tdee(weight_kg: float, height_cm: float, age: int, gender: str = "unspecified") -> str:
    """Calculate Body Mass Index (BMI) and estimated Total Daily Energy Expenditure (TDEE).

    Args:
        weight_kg: Body weight in kilograms.
        height_cm: Height in centimeters.
        age: Age in years.
        gender: Gender ('male', 'female', or 'unspecified') for metabolic calculations.

    Returns:
        Formatted BMI score, health classification, and recommended daily weight loss calorie target.
    """
    bmi = weight_kg / ((height_cm / 100) ** 2)
    category = "Normal weight"
    if bmi < 18.5:
        category = "Underweight"
    elif 25 <= bmi < 30:
        category = "Overweight"
    elif bmi >= 30:
        category = "Obesity"

    # Mifflin-St Jeor BMR calculation
    if gender.lower() == "male":
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
    elif gender.lower() == "female":
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161
    else:
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 78

    tdee = bmr * 1.375  # Moderate light activity multiplier
    weight_loss_target = max(1200, int(tdee - 500))

    return (
        f"BMI: {bmi:.1f} ({category}). "
        f"Estimated TDEE: {int(tdee)} kcal/day. "
        f"Recommended weight-loss budget: ~{weight_loss_target} kcal/day."
    )


def log_meal(food_item: str, calories: int, protein_g: float = 0.0) -> str:
    """Log a meal to keep track of total daily caloric intake.

    Args:
        food_item: Name of the meal or food item consumed.
        calories: Total calories in the meal.
        protein_g: Grams of protein in the meal.

    Returns:
        Confirmation message of logged meal entry.
    """
    return f"Logged meal: '{food_item}' ({calories} kcal, {protein_g}g protein)."


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=(
        "You are an empathetic, expert Dietary & Weight Management Coach designed to help users lose weight, "
        "reach a healthy BMI, and prevent obesity. "
        "You provide accurate calorie and nutrient breakdowns for food items, calculate BMI and daily calorie budgets, and log meals. "
        "CRITICAL MEMORY DIRECTIVE: Pay special attention to and remember ALL user food allergies, medical conditions, and dietary intolerances "
        "(e.g., peanuts, lactose/dairy, gluten, shellfish, tree nuts, eggs, soy). "
        "Always check remembered user allergies before recommending any meal or food item, and strictly avoid or issue clear warnings for any food containing an allergen."
    ),
    tools=[
        PreloadMemoryTool(),
        lookup_food_nutrition,
        calculate_bmi_and_tdee,
        log_meal,
        search_food_catalog,
        add_food_to_catalog,
        generate_meal_plate_image,
        generate_food_image,
        generate_food_video,
        consult_nutrition_chart,
    ],
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
