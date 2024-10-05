# CCTV Analysis Service

Create a `.env` file with your Google Gen-AI API key.

```console
echo 'GOOGLE_GENERATIVE_AI_API_KEY=[Your API Key]
GOOGLE_GENERATIVE_AI_MODEL=gemini-1.5-flash
EMBEDDING_MODEL=sentence-transformers/multi-qa-mpnet-base-cos-v1
CHROMADB_COLLECTION_NAME=cerberus' > .env
```

Upload video files.

```console
python scripts/upload.py 'data/**/*.mp4' 'data/**/*.mov' > data/video-files.jsonl
```

Describe and classify video files.

```console
python scripts/describe-and-classify.py 'Criminal Act' 'Porch Piracy' 'Package Delivery (Non-Theft)' < data/video-files.jsonl > data/video-descriptions-and-classifications.jsonl
```

Calculate confusion matrix values.

```console
python scripts/confusion.py data/video-golden-outputs.jsonl data/video-descriptions-and-classifications.jsonl > data/video-confusion.jsonl
```

Generate text embeddings for the videos.

```console
python scripts/generate-embeddings.py < data/video-descriptions-and-classifications.jsonl > data/video-description-embeddings.jsonl
```

Search for events.

```console
python scripts/dense-retrieval.py 3 ambulance animal delivery < data/video-description-embeddings.jsonl
python scripts/sparse-retrieval.py 3 ambulance animal delivery < data/video-description-embeddings.jsonl
```
