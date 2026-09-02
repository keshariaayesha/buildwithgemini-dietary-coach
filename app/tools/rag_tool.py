"""Vertex AI RAG Engine Retrieval Tool for Nutrition Chart corpus."""

import vertexai
from vertexai.preview import rag

PROJECT_ID = "qwiklabs-gcp-03-97c80a1d932c"
LOCATION = "us-central1"
CORPUS_NAME = "projects/468881849645/locations/us-central1/ragCorpora/1496347364472913920"


def consult_nutrition_chart(query: str) -> str:
    """Search the Nutrition Chart RAG corpus for daily nutrient guidelines, calorie charts, and dietary recommendations.

    Args:
        query: Specific food item, nutrient requirement, or calorie guideline to query.

    Returns:
        Matched passages from the nutrition chart grounding document.
    """
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    try:
        resp = rag.retrieval_query(
            text=query,
            rag_resources=[rag.RagResource(rag_corpus=CORPUS_NAME)],
            rag_retrieval_config=rag.RagRetrievalConfig(top_k=5),
        )
    except Exception as e:
        return f"Retrieval failed: {e}"

    contexts = getattr(resp.contexts, "contexts", [])
    passages = [c.text.strip() for c in contexts if getattr(c, "text", "").strip()]
    return "\n\n---\n\n".join(passages) or "No relevant passage found in nutrition chart."
