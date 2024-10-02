# CCTV Analysis Service

Upload video files.

```console
python scripts/upload.py 'data/**/*.mp4' 'data/**/*.mov' > data/video-files.jsonl
```

Describe and classify video files.

```console
cat data/video-files.jsonl | python scripts/describe-and-classify.py 'Criminal Act' 'Porch Piracy' 'Package Delivery (Non-Theft)' > data/video-descriptions-and-classifications.jsonl
```

Calculate confusion matrix values.

```console
python scripts/confusion.py data/video-golden-outputs.jsonl data/video-descriptions-and-classifications.jsonl > data/video-confusion.jsonl
```

generate text embeddings for the videos
```console
python scripts/gen_text_embedding.py --input_file data/video-descriptions-and-classifications.jsonl --output_file_embedding data/corpus_embedding.json --output_file_text_dir data/documents
```

Search for events
```console
python scripts/ir_system.py --embedding data/corpus_embedding.json --document_dir data/documents --topic_phrase "delivery"
```