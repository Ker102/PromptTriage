# Colab Upload Folder

Quick access to all files needed for Colab Enterprise fine-tuning.

## Files

| File | Size | Description |
|------|------|-------------|
| `train.jsonl` | ~1 MB | 139 training pairs (90%) |
| `val.jsonl` | ~104 KB | 16 validation pairs (10%) |
| `qwen3_finetune.py` | ~18 KB | Colab notebook (`.py` percent format) |

## Quick Start

1. Open **Colab Enterprise** in your GCP project (Vertex AI → Colab Enterprise)
2. Upload `qwen3_finetune.py` as a notebook
3. When prompted, upload `train.jsonl` and `val.jsonl`
4. Select **A100 GPU** runtime
5. Run all cells

## Notes

- These files are **copies** from `backend/research/training_data/` and `notebooks/`
- Training data is for **fine-tuning ONLY** — NOT for RAG pipeline
- Run `python -m research.combine_training_data` from `backend/` to regenerate
