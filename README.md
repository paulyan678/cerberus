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
