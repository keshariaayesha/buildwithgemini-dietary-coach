"""Video generation and Cloud Storage upload tool using Google Omni model for Dietary Coach."""

import base64
import time
from google import genai
from google.genai import types
from google.cloud import storage
from google.adk.tools import ToolContext

# Hardcoded GCP Project and GCS Bucket as required by Agent Platform
PROJECT_ID = "qwiklabs-gcp-03-97c80a1d932c"
BUCKET_NAME = "dietary-coach-media-qwiklabs-03"


def generate_food_video(
    food_description: str,
    tool_context: ToolContext,
) -> str:
    """Generate a short culinary video for a food or healthy meal dish using Google Omni model (gemini-omni-flash-preview) in global region, save as artifact, and upload to public Cloud Storage.

    Args:
        food_description: Description or name of the food item or dish (e.g. 'A fresh vibrant Greek salad with olives, feta cheese, and olive oil').
        tool_context: ToolContext automatically injected by ADK to save artifacts.

    Returns:
        Public HTTPS URL of the uploaded video hosted on Cloud Storage.
    """
    client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")
    prompt = f"A short video showing {food_description}, fresh healthy ingredients, beautiful food presentation, natural lighting."

    interaction = None
    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        try:
            interaction = client.interactions.create(
                model="gemini-omni-flash-preview",
                input=prompt,
            )
            break
        except Exception as e:
            if ("429" in str(e) or "exhausted" in str(e).lower()) and attempt < max_attempts:
                time.sleep(attempt * 5)
                continue
            raise e

    video_bytes = None
    mime_type = "video/mp4"

    if hasattr(interaction, "output_video") and interaction.output_video:
        data = getattr(interaction.output_video, "data", None)
        if data:
            if isinstance(data, str):
                video_bytes = base64.b64decode(data)
            else:
                video_bytes = data
        if getattr(interaction.output_video, "mime_type", None):
            mime_type = interaction.output_video.mime_type
    elif hasattr(interaction, "outputs") and interaction.outputs:
        for out in interaction.outputs:
            if hasattr(out, "video") and out.video:
                data = getattr(out.video, "data", None)
                if data:
                    video_bytes = base64.b64decode(data) if isinstance(data, str) else data
                    if getattr(out.video, "mime_type", None):
                        mime_type = out.video.mime_type
                    break

    if not video_bytes:
        return "Failed to generate video bytes from omni model."

    # 1. Save artifact with tool_context for Playground Artifacts panel
    artifact_part = types.Part.from_bytes(data=video_bytes, mime_type=mime_type)
    filename = f"food_video_{int(time.time())}.mp4"
    tool_context.save_artifact(filename=filename, artifact=artifact_part)

    # 2. Upload same video bytes directly to public GCS bucket
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(BUCKET_NAME)

    object_name = f"food_videos/{filename}"
    blob = bucket.blob(object_name)
    blob.upload_from_string(video_bytes, content_type=mime_type)

    public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{object_name}"
    return public_url
