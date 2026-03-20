# Mini-Anime-Rec Training Module

This directory contains the end-to-end training pipeline for the sequence-based anime recommendation model.

## Layout

- `configs/`: training and preprocessing configuration.
- `data/`: extracted raw files and generated intermediate datasets.
- `artifacts/`: checkpoints, ONNX exports, metrics, and mappings.
- `docs/`: backend-facing preprocessing and inference contracts.
- `examples/`: sample request payloads for integration.
- `src/`: preprocessing, training, evaluation, export, and inference scripts.
- `tests/`: smoke tests that validate data contracts and preprocessing logic.

## Recommended Environment

Use the provided `environment.yml` or `requirements.txt` in a dedicated Conda environment. Python `3.10` is the default target for compatibility with PyTorch and ONNX tooling.

## Typical Workflow

```bash
conda env create -f training/environment.yml
conda activate mini-anime-rec
python training/src/preprocess.py --config training/configs/default.yaml
python training/src/train.py --config training/configs/default.yaml
python training/src/export_onnx.py --config training/configs/default.yaml
python training/src/infer_onnx.py --config training/configs/default.yaml --input-json training/examples/sample_request.json
pytest training/tests
```
