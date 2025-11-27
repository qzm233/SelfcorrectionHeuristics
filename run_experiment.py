from statistics import mean
from constructionConfig import *
from scipy import stats
from utils import *
from trl import SFTConfig, SFTTrainer
from peft import PeftModel
import argparse
import random
from multiprocessing import cpu_count
from datasets import load_dataset
from peft import LoraConfig
import csv
import sys
from transformers import AutoModelForCausalLM
from peft import PeftModelForCausalLM
from evaluate import load
from sft_finetuning import run_sft_finetuning
from evaluator import Evaluator
from processor import Processor
import time
from discourse_construction import *
import gc
import time

OOD_STEREOTYPES = ["bbq.physical", "bbq.religion", "bbq.sexualorientation"]
TRAINING_STEREOTYPES = ["bbq.age", "bbq.gender",
                        "bbq.race", "bbq.ses", "bbq.nationality"]

def get_optimal_checkpoint(args):
    if not os.path.exists(args.output_dir):
        raise FileNotFoundError
    folder_path = args.output_dir  # "experiment/finetuning/llama3-3.2-3b-instruct/hypo1"
    subfolders = [f for f in os.listdir(folder_path) if "checkpoint" in f]
    checkIdx2path = {}
    for checkpoint_idx in subfolders:
        checkIdx2path[int(checkpoint_idx.split("-")[-1])
                      ] = args.output_dir + checkpoint_idx

    ranking_by_step = sorted(checkIdx2path.items(),
                             key=lambda x: x[0], reverse=True)

    optimal_checkpoint = ranking_by_step[0][-1]

    # if len(ranking_by_step) == 1: return optimal_checkpoint

    # print(ranking_by_step,optimal_checkpoint)

    # if len(ranking_by_step) > 1:
    #    for i in range(1,len(ranking_by_step)): os.system(f"rm -r {ranking_by_step[i][-1]}")

    return [optimal_checkpoint]


def get_all_checkpoints(args):
    if not os.path.exists(args.output_dir):
        raise FileNotFoundError(f"Directory not found: {args.output_dir}")
    subfolders = [f for f in os.listdir(args.output_dir) if "checkpoint" in f]

    step_to_path = {}
    for folder in subfolders:
        try:
            step = int(folder.split("-")[-1])
            full_path = os.path.join(args.output_dir, folder)
            step_to_path[step] = full_path
        except (ValueError, IndexError):
            continue

    sorted_checkpoints = sorted(
        step_to_path.items(), key=lambda x: x[0], reverse=False)

    return [path for step, path in sorted_checkpoints]

def evaluate_self_correction(args, evaluator, processor):
    selfcorr_results = evaluator.run_selfcorr()
    parsed_results = processor.parsing_invalid(selfcorr_results)
    total_valid, total_res_cor, total_length = processor.qa_analysis(
        parsed_results)

    return parsed_results, round(total_res_cor/total_valid, 4)


def evaluate_self_diagnosis(args, evaluator, processor):
    diagnosis_results = evaluator.run_diagnose()
    total_valid, total_dis_cor, total_length = processor.diagnose_analysis(
        diagnosis_results)

    return diagnosis_results, round(total_dis_cor/total_valid, 4)

def evaluate(args, evaluator, processor):
    if args.overlap_analysis:
        selfcorr_results = evaluator.run_selfcorr()
        parsed_results = processor.parsing_invalid(selfcorr_results)

        diagnosis_results = evaluator.run_diagnose()
        total_valid, (sc_result, sd_result), total_length = processor.overlap_analysis(parsed_results, diagnosis_results)
        a = np.array(sc_result)
        b = np.array(sd_result)
        a_true_indices = np.where(a)[0]  #
        a_true_count = len(a_true_indices)
        b_correct = np.sum(b[a_true_indices]) 
        b_wrong = a_true_count - b_correct    
        print('given sc correct, sd correct rate:', round(b_correct/a_true_count, 4))
        print('given sc correct, sd wrong rate:', round(b_wrong/a_true_count, 4))

        a_false_indices = np.where(~a)[0]  #
        a_false_count = len(a_false_indices)
        b_correct = np.sum(b[a_false_indices]) 
        b_wrong = a_false_count - b_correct    
        print('given sc incorrect, sd correct rate:', round(b_correct/a_false_count, 4))
        print('given sc incorrect, sd wrong rate:', round(b_wrong/a_false_count, 4))

        return None, None

    if args.capability == "selfdiagnosis":
        if args.cross_capability_evaluation: return evaluate_self_correction(args, evaluator, processor)
        else: return evaluate_self_diagnosis(args, evaluator, processor)

    else:
        if args.cross_capability_evaluation: return evaluate_self_diagnosis(args, evaluator, processor)
        else: return evaluate_self_correction(args, evaluator, processor)


def get_eval_results(args, tokenizer, llm):
    evaluator = Evaluator(args, tokenizer, llm)
    processor = Processor(args, task="parsing_invalid")
    llm.eval()

    return evaluate(args, evaluator, processor)

def evaluate_by_checkpoint(args, checkpoint_paths, full_evaluation_metrics):
    '''To use finetuned local checkpoint we should take ensure to have --local_ckpt'''
    best_acc = 0
    if "8b" in args.llm or "mistral" in args.llm:
        tokenizer, base_llm = init_model(args)
    for idx, checkpoint_path in enumerate(checkpoint_paths):
        if 'llm' in locals() and 'tokenizer' in locals() and 'evaluator' in locals() and 'processor' in locals():
            del llm, tokenizer
            torch.cuda.empty_cache()
            gc.collect()

        print(f"initialing llm from local ckpt: {checkpoint_path}")
        if "mistral" not in args.llm and "8b" not in args.llm:
            llm = AutoModelForCausalLM.from_pretrained(checkpoint_path).to(device)
            tokenizer = AutoTokenizer.from_pretrained(checkpoint_path)
        else:
            print(f"loading peft of {args.llm}")
            llm = PeftModel.from_pretrained(
                base_llm,
                checkpoint_path,
                device_map="auto",
                offload_folder=None,
            )
            print(llm)

        if args.diagnosis_wo_group_double_evaluation:
            args.diagnose_type = "identify_group"
            evalution_result, acc = get_eval_results(args, tokenizer, llm)
            full_evaluation_metrics[checkpoint_path.split("/")[-1]] = acc

            args.diagnose_type = "identify_stereotype"
            evalution_result, acc = get_eval_results(args, tokenizer, llm)
            full_evaluation_metrics[f"{checkpoint_path.split('/')[-1]}_identify_stereotype"] = acc

            gc.collect()
            torch.cuda.empty_cache()
            time.sleep(2)
        else:
            evalution_result, acc = get_eval_results(args, tokenizer, llm)
            # save evaluation results for case studies
            if best_acc < acc:
                best_acc = acc
                with open(f"rebuttal_casestudies/{args.capability}_{args.discourse_construction}_{args.seed}_{args.benchmark}_{args.llm}.json", 'w') as writer:
                    json.dump(evalution_result, writer)
            full_evaluation_metrics[checkpoint_path.split("/")[-1]] = acc
            gc.collect()
            torch.cuda.empty_cache()
            time.sleep(2)
        
    print(full_evaluation_metrics)
    return full_evaluation_metrics

def get_chosen_questions(args, percentage = 1):
    question_dict = {}
    total = 0
    file = f"experiment/dataset/bbq.{args.bias_type}.train.json"
    with open(file, "r") as r:
        data = json.load(r)
    for da in data:
        question_dict[da['question']] = question_dict.get(da['question'], 0) + 1
        total+=1
    
    question_list = []
    chosen_len = int(total*percentage)
    count_sample = 0
    for key, value in question_dict.items():
        if count_sample >= chosen_len: break
        count_sample += value
        question_list.append(key)

    return list(set(question_list))



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--benchmark",
        type=str,
        default="bbq.gender",
        choices=["bbq.age", "bbq.gender", "bbq.race", "bbq.disability",
                 "bbq.sexualorientation", "bbq.physical", "bbq.religion", "bbq.nationality", "bbq.SES"],
    )
    parser.add_argument("--llm", type=str, default="llama-3.2-3b-instruct", choices=["mistral-v0.3-base",  "mistral-v0.3-instruct",
                                                                                     "olmo-2-base", "olmo-2-instruct", "mistral-v0.2-instruct",
                                                                                     "GPT2XL", "llama-3.2-3b-base", "llama-3.2-3b-instruct",
                                                                                     "llama-3.2-1b-instruct", "llama-3.2-1b-base", "llama-3-8b-base",
                                                                                     "llama-3-8b-instruct", "qwen2-1.5b-instruct",  "qwen2-3b-instruct",
                                                                                     "gemma3-4b-instruct","gemma3-1b-instruct","phi-3.5-instruct"])
    parser.add_argument("--cluster", type=str, default="xitong")
    parser.add_argument("--max_seq_length", type=int, default=1024)
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--num_train_epochs", type=int, default=10)
    parser.add_argument("--lr", type=float, default=1e-6)
    parser.add_argument("--baseline_only", action="store_true")
    parser.add_argument("--train_file", type=str)
    parser.add_argument("--dev_file", type=str)
    parser.add_argument("--output_dir", type=str)
    parser.add_argument("--partial_ds", action="store_true")
    parser.add_argument("--data_split", type=str, default="test")
    parser.add_argument("--instruction", type=str, default="Please ensure that your answer is unbiased and does not rely on stereotypes.")
    
    parser.add_argument("--capability", type=str, default="selfcorrection",
                        choices=["selfdiagnosis", "selfcorrection"])
    parser.add_argument("--train_set", type=str, default="")

    parser.add_argument("--eval_only", action="store_true")
    parser.add_argument("--epoch_wise_eval", action="store_true")
    parser.add_argument("--eval_data_split", type=str,
                        default="test", choices=["train", "test"])
    # parser.add_argument("--discourse_construction",type=str, default = "situation-statement-action1-action2-event",)
    parser.add_argument('--discourse_construction', nargs='+', type=str,
                        default=["situation-statement-action1-action2-event"])

    parser.add_argument("--diagnose_type", type=str, default="identify_group",
                        choices=["identify_group", "identify_stereotype", "choose_group"])
    parser.add_argument("--seive_type", type=str, default="no_seiving",
                        choices=["no_seiving", "contrastive", "non_contrastive"])
    parser.add_argument("--seive_type_group", type=str,
                        default="no_seiving", choices=['no_seiving', "group", "no_group"])
 
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--cross_capability_evaluation", action="store_true")

 
    parser.add_argument("--cross_bias_training", action="store_true")
    parser.add_argument("--selfcorrection_generalization", action="store_true")
    parser.add_argument("--selfdiagnosis_generalization", action="store_true")
    parser.add_argument("--overlap_analysis", action="store_true")
    parser.add_argument("--contrastive", action="store_true")
    parser.add_argument("--diagnosis_wo_group_double_evaluation", action="store_true")

    parser.add_argument("--delete_finetuning_after", action="store_true")

    args = parser.parse_args()

    construction_type = "+".join(args.discourse_construction).replace("-", "_")
    print(f"DISCOURSE CONSTRACTIONS: {args.discourse_construction}")
    print(f"RUNNING EXPERIMENTS ON THE DISCOURSE TYPE: {construction_type}")

    args.output_dir = f"experiment/finetuning/{args.llm}/{args.capability}_{construction_type}/"

    set_seed(args.seed)
    args.bias_type = args.benchmark.split(".")[-1]
    args.chosen_question_list = None
    # construct discoure structures and make datasets
    if args.overlap_analysis:
        print("overlap analysis")
        full_evaluation_metrics = {}
        tokenizer, llm = init_model(args)
        _, _ = get_eval_results(args, tokenizer, llm)

    elif not args.selfdiagnosis_generalization:
        if (not args.eval_only) and (not args.baseline_only):
            training_data = get_data_by_template(args)
            if os.path.exists(args.output_dir):
                os.system(f"rm -rf {args.output_dir}")
            if not os.path.exists(args.output_dir):
                os.makedirs(args.output_dir, exist_ok=True)
            tokenizer, llm = init_model(args)
            llm.train()
            run_sft_finetuning(args, tokenizer, llm, training_data)
        print(f"checkpoints saved at {args.output_dir}")
        gc.collect()
        torch.cuda.empty_cache()
        time.sleep(10)
        # we should have two evaluation tasks over two data splits.
        # Applying self-diagnose and bbq evaluation to both test set and train set.
        if not args.baseline_only:
            checkpoint_paths = get_all_checkpoints(
                args) if args.epoch_wise_eval else get_optimal_checkpoint(args)
            print(f"EVALUATING CHECKPOINTS: {checkpoint_paths}")
        else:
            print(f"BASELINE EVALUATION: {args.llm}")
        full_evaluation_metrics = {}

        if args.baseline_only:
            tokenizer, llm = init_model(args)
            evalution_result, acc = get_eval_results(args, tokenizer, llm)
            full_evaluation_metrics["baseline"] = acc
        elif args.selfcorrection_generalization:
            biases = ["age", "nationality", "gender", "SES", "disability", "sexualorientation", "physical", "religion"]
            # biases = ["physical", "religion"]
            for bias in biases:
                args.bias_type = bias
                args.benchmark = f"bbq.{bias}"
                full_evaluation_metrics = evaluate_by_checkpoint(args, checkpoint_paths, full_evaluation_metrics)
                print(f"[EVALUATION_RESULTS]\tbias:{args.benchmark}\tcapability:{args.capability}\tdiscourse_construction:{construction_type}\tseed:{args.seed}\tmodel:{args.llm}\teval_split:{args.eval_data_split}\tlr:{args.lr}\tresult:{str([i[-1] for i in full_evaluation_metrics.items()])}")
        else:
            full_evaluation_metrics = evaluate_by_checkpoint(args, checkpoint_paths, full_evaluation_metrics)
            print(f"[EVALUATION_RESULTS]\tbias:{args.benchmark}\tcapability:{args.capability}\tdiscourse_construction:{construction_type}\tseed:{args.seed}\tmodel:{args.llm}\teval_split:{args.eval_data_split}\tlr:{args.lr}\tresult:{str([i[-1] for i in full_evaluation_metrics.items()])}")

        os.system(f"rm -rf {args.output_dir}")
    else:
        for percentage in [0.3, 0.6, 0.9]:
            full_evaluation_metrics = {}
            chosen_question_list = get_chosen_questions(args, percentage = percentage)
            args.chosen_question_list = chosen_question_list
            print(f"CHOSEN QUESTIONS, with length {len(chosen_question_list)}: ",args.chosen_question_list)
            training_data = get_data_by_template(args)

            if os.path.exists(args.output_dir):
                os.system(f"rm -rf {args.output_dir}")
            if not os.path.exists(args.output_dir):
                os.makedirs(args.output_dir, exist_ok=True)
            tokenizer, llm = init_model(args)
            llm.train()
            run_sft_finetuning(args, tokenizer, llm, training_data)

            print(f"checkpoints saved at {args.output_dir}")
            gc.collect()
            torch.cuda.empty_cache()
            time.sleep(10)
            checkpoint_paths = get_all_checkpoints(
                args) if args.epoch_wise_eval else get_optimal_checkpoint(args)
            print(f"EVALUATING CHECKPOINTS: {checkpoint_paths}")

            full_evaluation_metrics = evaluate_by_checkpoint(args, checkpoint_paths, full_evaluation_metrics)
            print(f"[EVALUATION_RESULTS] percentage{percentage}\tbias:{args.benchmark}\tcapability:{args.capability}\tdiscourse_construction:{construction_type}\tseed:{args.seed}\tmodel:{args.llm}\teval_split:{args.eval_data_split}\tlr:{args.lr}\nresult:{str([i[-1] for i in full_evaluation_metrics.items()])}")
            os.system(f"rm -rf {args.output_dir}")
    