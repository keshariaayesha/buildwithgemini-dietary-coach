"""Image generation and Cloud Storage upload tool for Dietary Coach."""

import io
import time
from PIL import Image, ImageDraw, ImageFont
from google import genai
from google.genai import types
from google.cloud import storage
from google.adk.tools import ToolContext

# Hardcoded GCP Project and GCS Bucket as required by Agent Platform
PROJECT_ID = "qwiklabs-gcp-03-97c80a1d932c"
BUCKET_NAME = "dietary-coach-media-qwiklabs-03"


def generate_food_image(
    food_description: str,
    tool_context: ToolContext,
) -> str:
    """Generate an AI image for a food item or healthy meal dish using gemini-3.1-flash-lite-image in the global region, save it as an artifact, and upload to public Cloud Storage.

    Args:
        food_description: Description or name of the food item or dish (e.g. 'Grilled chicken bowl with quinoa, avocado, and broccoli').
        tool_context: ToolContext automatically injected by ADK to save artifacts.

    Returns:
        Public HTTPS URL of the uploaded image hosted on Cloud Storage.
    """
    client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")
    prompt = f"A high-quality, professional food photograph of {food_description}, delicious plating, soft natural lighting."

    response = client.models.generate_content(
        model="gemini-3.1-flash-lite-image",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
        ),
    )

    img_bytes = None
    mime_type = "image/jpeg"

    if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
        for part in response.candidates[0].content.parts:
            if part.inline_data and part.inline_data.data:
                img_bytes = part.inline_data.data
                if part.inline_data.mime_type:
                    mime_type = part.inline_data.mime_type
                break

    if not img_bytes:
        return "Failed to generate image bytes from model."

    # 1. Save artifact with tool_context for Playground Artifacts panel
    artifact_part = types.Part.from_bytes(data=img_bytes, mime_type=mime_type)
    ext = "jpg" if "jpeg" in mime_type.lower() or "jpg" in mime_type.lower() else "png"
    filename = f"food_{int(time.time())}.{ext}"
    tool_context.save_artifact(filename=filename, artifact=artifact_part)

    # 2. Upload same image bytes directly to public GCS bucket
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(BUCKET_NAME)

    object_name = f"food_images/{filename}"
    blob = bucket.blob(object_name)
    blob.upload_from_string(img_bytes, content_type=mime_type)

    public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{object_name}"
    return public_url


def generate_meal_plate_image(
    meal_name: str,
    calories: int = 350,
    protein_g: float = 25.0,
    carbs_g: float = 30.0,
    fat_g: float = 10.0,
    dietary_tags: str = "healthy, high_protein",
) -> str:
    """Generate a visual meal card image for a suggested healthy dish and upload it to public Cloud Storage.

    Args:
        meal_name: Name of the meal or dish (e.g., 'Grilled Chicken Breast with Quinoa').
        calories: Total calorie count (e.g., 350).
        protein_g: Grams of protein (e.g., 25.0).
        carbs_g: Grams of carbohydrates (e.g., 30.0).
        fat_g: Grams of fat (e.g., 10.0).
        dietary_tags: Comma-separated dietary tags (e.g., 'high_protein, gluten_free, peanut_free').

    Returns:
        Public HTTP URL of the generated meal image hosted on Cloud Storage.
    """
    width, height = 800, 500
    image = Image.new("RGB", (width, height), color="#121826")
    draw = ImageDraw.Draw(image)

    # Decorative header banner gradient
    draw.rectangle([0, 0, width, 120], fill="#1E293B")
    draw.rectangle([0, 116, width, 120], fill="#10B981")  # Emerald accent line

    # Header text
    try:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
        font_sub = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
        font_bold = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    except Exception:
        font_title = font_sub = font_bold = font_small = ImageFont.load_default()

    draw.text((40, 30), "🥗 DIETARY & WEIGHT COACH", fill="#10B981", font=font_sub)
    draw.text((40, 60), meal_name[:38], fill="#FFFFFF", font=font_title)

    # Calorie Pill
    cal_box = [580, 35, 760, 85]
    draw.rounded_rectangle(cal_box, radius=12, fill="#0F766E", outline="#34D399", width=2)
    draw.text((600, 48), f"🔥 {calories} kcal", fill="#FFFFFF", font=font_bold)

    # Macro Section
    draw.text((40, 150), "NUTRITIONAL BREAKDOWN (PER SERVING)", fill="#94A3B8", font=font_sub)

    macros = [
        ("Protein", f"{protein_g}g", "#3B82F6", 190),
        ("Carbohydrates", f"{carbs_g}g", "#F59E0B", 260),
        ("Healthy Fats", f"{fat_g}g", "#EC4899", 330),
    ]

    for label, val, color, y in macros:
        draw.text((40, y), label, fill="#E2E8F0", font=font_bold)
        draw.text((220, y), val, fill=color, font=font_bold)
        # Background bar
        draw.rounded_rectangle([320, y + 5, 760, y + 20], radius=6, fill="#334155")
        # Value bar width (scaled)
        bar_val = min(440, int((float(val.replace('g', '')) / 50.0) * 440))
        if bar_val > 0:
            draw.rounded_rectangle([320, y + 5, 320 + max(15, bar_val), y + 20], radius=6, fill=color)

    # Dietary Tags Section
    draw.text((40, 400), "DIETARY TAGS & ALLERGEN SAFETY:", fill="#94A3B8", font=font_sub)
    tag_list = [t.strip().replace('_', ' ').title() for t in dietary_tags.split(",") if t.strip()]

    x_offset = 40
    for tag in tag_list:
        tag_width = len(tag) * 10 + 20
        if x_offset + tag_width > 760:
            break
        draw.rounded_rectangle([x_offset, 430, x_offset + tag_width, 465], radius=8, fill="#1E293B", outline="#475569")
        draw.text((x_offset + 10, 438), f"✓ {tag}", fill="#38BDF8", font=font_small)
        x_offset += tag_width + 12

    # Save to memory buffer
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format="PNG")
    img_bytes = img_byte_arr.getvalue()

    # Upload to Cloud Storage
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(BUCKET_NAME)

    filename = f"meal_plates/{meal_name.lower().replace(' ', '_')}_{int(time.time())}.png"
    blob = bucket.blob(filename)
    blob.upload_from_string(img_bytes, content_type="image/png")

    public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"
    return f"Generated meal plate card uploaded successfully: {public_url}"
