# Self-Correction Heuristics

Repository for running self-correction and self-diagnosis experiments on BBQ dataset. The entry point is `experiments_final.py`, which orchestrates dozens of `run_experiment.py` calls across models, discourse templates, and bias slices.

## Overview
- `experiments_final.py`: kicks off the full paper sweep (multiple LLMs, seeds, discourse constructions, and capabilities).
- `run_experiment.py`: single-run driver that builds datasets, fine-tunes with LoRA, and evaluates self-correction/self-diagnosis.
- `discourse_construction.py` & `constructionConfig.py`: prompt/discourse templates used to synthesize training/eval text.
- `processor.py`, `evaluator.py`, `sft_finetuning.py`: data processing, evaluation routines, and TRL-based fine-tuning.
- `experiment/dataset/`: BBQ splits already materialized as `bbq.<bias>.{train,test}.json`.

## Setup
1) Python 3.10+ with CUDA-capable GPUs recommended.  
2) Install deps (minimal set):  
   ```bash
   pip install torch transformers datasets trl peft accelerate evaluate google-api-python-client tqdm scipy
   ```  
3) Populate `api_tokens.py` with your Hugging Face and API keys (required for gated models such as Llama/Mistral).  
4) Verify data is present under `experiment/dataset/`; add or swap in new BBQ splits if needed.

## Quick starts
- Baseline evaluation only:  
  ```bash
  python run_experiment.py --llm llama-3.2-3b-instruct --benchmark bbq.gender --baseline_only --eval_only
  ```
- Fine-tune and evaluate self-correction on SES bias:  
  ```bash
  python run_experiment.py --llm llama-3.2-1b-instruct --benchmark bbq.SES \
    --num_train_epochs 10 --batch_size 32 --discourse_construction situation-statement-action1-action2groundTruth \
    --epoch_wise_eval
  ```
- Self-diagnosis variant: add `--capability selfdiagnosis`.  
- Cross-capability eval: append `--cross_capability_evaluation`.  
- Choose different discourse templates via `--discourse_construction ...` (see `discourse_construction.py` for names).

## Full sweep
To launch the exact sweep used in the paper (multiple LLMs, seeds, templates, and cross-capability checks), run:
```bash
python experiments_final.py
```
This script will queue many fine-tuning/eval jobs; ensure you have sufficient GPU time and disk. Intermediate checkpoints are stored under `experiment/finetuning/<llm>/<capability>_<discourse>/` and cleaned up after evaluation.

## Tips
- Use `--eval_only` when you only want zero-shot baselines.  
- Set `--output_dir` explicitly if you prefer to keep checkpoints.  
- Some models require Hugging Face authentication (`huggingface_hub.login` is triggered inside `utils.py`).  
- GPU memory varies by model size; adjust `--batch_size` or pick smaller LLMs if you hit OOM.
