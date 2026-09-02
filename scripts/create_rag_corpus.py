"""Script to create a serverless Vertex AI RAG Engine corpus and import Nutrition Chart data."""

import vertexai
from vertexai.preview import rag
from vertexai.preview.rag.utils import resources as rr

PROJECT_ID = "qwiklabs-gcp-03-97c80a1d932c"
LOCATION = "us-central1"
GCS_PATH = "gs://dietary-coach-media-qwiklabs-03/rag/nutrition_chart.txt"

PARSING_PROMPT = (
    "Extract all daily nutrition requirements, calorie counts, macronutrients, "
    "and dietary guidelines for weight management. Output clean, structured prose."
)


def main():
    vertexai.init(project=PROJECT_ID, location=LOCATION)

    print("Setting RAG Engine config to Serverless mode...")
    cfg = f"projects/{PROJECT_ID}/locations/{LOCATION}/ragEngineConfig"
    rag.update_rag_engine_config(
        rag_engine_config=rag.RagEngineConfig(
            name=cfg,
            rag_managed_db_config=rag.RagManagedDbConfig(mode=rr.Serverless()),
        )
    )

    print("Creating serverless RAG corpus...")
    corpus = rag.create_corpus(
        display_name="dietary-nutrition-corpus",
        embedding_model_config=rag.EmbeddingModelConfig(
            publisher_model="publishers/google/models/text-embedding-005"
        ),
    )
    print("Corpus created successfully:", corpus.name)

    print(f"Importing files from {GCS_PATH}...")
    resp = rag.import_files(
        corpus_name=corpus.name,
        paths=[GCS_PATH],
        transformation_config=rag.TransformationConfig(
            chunking_config=rag.ChunkingConfig(chunk_size=512, chunk_overlap=100)
        ),
        llm_parser=rag.LlmParserConfig(
            model_name="gemini-2.5-flash",
            custom_parsing_prompt=PARSING_PROMPT
        ),
    )
    print("Import response:", resp)
    print(f"Imported {getattr(resp, 'imported_rag_files_count', 1)} files into corpus {corpus.name}")


if __name__ == "__main__":
    main()
