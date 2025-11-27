from statistics import mean
from constructionConfig import *
from scipy import stats
from utils import *
from trl import SFTConfig, SFTTrainer
import argparse
import random
from multiprocessing import cpu_count
from datasets import load_dataset
from peft import LoraConfig
import csv
import sys
import re
from transformers import AutoModelForCausalLM, TrainerCallback
from peft import PeftModelForCausalLM
from evaluate import load

os.environ["WANDB_API_KEY"] = '1845003133e798971e3f1d801db4fb1d2a204b91'


os.system("wandb offline")


def _apply_format_(sys_text, user_text, completion_text):
    text = f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{sys_text}<|eot_id|>\n<|start_header_id|>user<|end_header_id|>\n\n{user_text}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n{completion_text}<|eot_id|>"
    return text

def _idx_misalign_(dm_idx, ds_idx, misalign_rate):
    assert dm_idx == ds_idx
    assert misalign_rate <= 1

    n = len(dm_idx)
    k = int(n * misalign_rate)  # num of elements to suffle
    indices_to_shuffle = random.sample(range(n), k)
    selected_elements = [dm_idx[i] for i in indices_to_shuffle]
    random.shuffle(selected_elements)
    for i, idx in enumerate(indices_to_shuffle):
        dm_idx[idx] = selected_elements[i]
    return dm_idx, ds_idx


def get_context_identify_idx(data, sample_num):
    idx_return = {}
    for idx, da in enumerate(data):
        if da['context_split_identify_str'] not in idx_return:
            idx_return[da['context_split_identify_str']] = []
        idx_return[da['context_split_identify_str']].append(idx)

    for key in idx_return:
        if len(idx_return[key]) > sample_num:
            idx_return[key] = random.sample(idx_return[key], sample_num)

    return idx_return


def parse_by_identifiers(args, data):
    dataset = []
    # indexes = get_context_identify_idx(data, 1)
    print("SAMPLE META DATA:")
    print(data[0])
    for idx, da in enumerate(data[:]):
        # if idx not in indexes[da['context_split_identify_str']]: continue # for each 'context_split_identify_str', leave only several sample
        sample_discourses = []
        for construction in args.discourse_construction:
            sample_discourses.append(da[args.capability][construction])
        dataset.extend(sample_discourses)

    print(f"With dataset length {len(dataset)}")
    print(f"SAMPLE DATA 1: {dataset[0]}")
    print(f"SAMPLE DATA 2: {dataset[1]}")
    print(f"SAMPLE DATA 3: {dataset[2]}")
    print(f"SAMPLE DATA 4: {dataset[3]}")
    print("BLANK STR IN DATASET: ", "" in dataset)
    return dataset


def parse_by_hypo(args, data):
    dataset = []
    temp_dm_list, temp_ds_list = {}, {}
    mis_align_idxes = []
    if args.hypo == "hypo3" and args.misalign_rate == 1:
        mis_align_idxes = [i for i in range(len(data))]
    elif args.hypo == "hypo3" and args.misalign_rate > 0.0 and args.misalign_rate < 1.0:
        k = round(len(data) * args.misalign_rate)
        mis_align_idxes = random.sample(range(len(data)), k)

    for idx, da in enumerate(data):
        if args.hypo == "hypo1":
            if "discourse_suprious_correlation" in da.keys():
                discourses = da["discourse_suprious_correlation"]
                # dataset.extend([item[-1] for item in discourses.items()][:args.top_K])
                dataset.append(discourses["new"])

                # for ds_idx, discourse in discourses.items():
                #    if args.partial_ds and (int(ds_idx) != 0): continue
                #    text = discourse
                #    dataset.append(text)

        elif args.hypo == "hypo2":
            if args.situation in [1, 2, 3, 4]:
                if "discourse_moral_sentiment" in da.keys():
                    discourses = da["discourse_moral_sentiment"]
                    assert f"synthesis_text_specificity{args.situation}" in discourses
                    text = discourses[f"synthesis_text_specificity{args.situation}"]['statement']
                    # text = discourses[f"synthesis_text_specificity{args.situation}"]['dm_expansion'] # test for more situated Dm
                    # text =  discourses[f"synthesis_text_specificity{args.situation}"]['dm_action']
                    if args.situation in [-1]:
                        '''
                             apply format for situation 1,2
                             example text: We should avoid gender-based stereotypes that assume women are less capable of being self-starters at work.
                        '''
                        # text_splits = re.split(r'\bthat\b', sentence, maxsplit=1)
                        user_text = " ".join(text.split("stereotypes")[
                                             :1]) + "stereotypes"
                        completion_text = " ".join(
                            text.split("stereotypes")[1:])

                        sys_text = "You are a helpful, respectfual and honest assistant. Your job is to complete the given sentence."
                        # user_text = text_splits[0]
                        # completion_text = 'that'+  text_splits[1]
                        text = _apply_format_(
                            sys_text, user_text, completion_text)

                    dataset.append(text)
            elif args.situation == 5:
                dataset.append(random.choice(specificity_5_texts))
            elif args.situation == 6:
                dataset.append(random.choice(specificity_6_texts))

        elif args.hypo == "hypo3":
            assert args.misalign_rate <= 1
            if "discourse_moral_sentiment" not in da.keys():
                continue
            if "discourse_suprious_correlation" not in da.keys():
                continue
            dm_list = []
            if args.situation in [1, 2, 3, 4]:
                if "discourse_moral_sentiment" in da.keys():
                    discourses = da["discourse_moral_sentiment"]
                    # dm_discourse = discourses[f"synthesis_text_specificity{args.situation}"]['dm_expansion']
                    dm_discourse = discourses[f"synthesis_text_specificity{args.situation}"]['statement']
                    # dm_discourse = discourses[f"synthesis_text_specificity{args.situation}"]['dm_action']
                    # for situation in [1,2,3,4]: dm_list.append(discourses[f"synthesis_text_specificity{args.situation}"]['statement'])
            elif args.situation == 5:
                dm_discourse = random.choice(specificity_5_texts)
            elif args.situation == 6:
                dm_discourse = random.choice(specificity_6_texts)

            # ds_data = da["discourse_suprious_correlation" ]["new"]
            ds_data = da["discourse_suprious_correlation"]["0"]
            # ds_data_list = [item[-1] for item in da["discourse_suprious_correlation"].items()][:1]
            if idx in mis_align_idxes:
                # print("miss")
                dataset.append(ds_data)
                # for ds_data in ds_data_list:
                #     dataset.append(ds_data)
            else:
                dataset.append(f"{ds_data} {dm_discourse}")
                # dataset.append(f"{dm_discourse}")
                # for ds_data in ds_data_list:
                # dataset.append(f"{ds_data} {dm_list[1]} " )

        elif args.hypo == "hypo4":
            if "discourse_moral_sentiment" not in da.keys():
                continue
            if "discourse_suprious_correlation" not in da.keys():
                continue
            if args.situation in [1, 2, 3, 4]:
                if "discourse_moral_sentiment" in da.keys():
                    discourses = da["discourse_moral_sentiment"]
                    # dm_discourse = discourses[f"synthesis_text_specificity{args.situation}"]['statement']
                    # try dm_expansion
                    dm_discourse = discourses[f"synthesis_text_specificity{args.situation}"]['dm_expansion']
            elif args.situation == 5:
                dm_discourse = random.choice(specificity_5_texts)
            elif args.situation == 6:
                dm_discourse = random.choice(specificity_6_texts)

            # ds_discourses=[item[-1] for item in da["discourse_suprious_correlation"].items()][:args.top_K]
            ds_discourses = [da["discourse_suprious_correlation"]['new']]
            for ds_ in ds_discourses:
                dataset.append(f"{ds_} {dm_discourse}")

        elif args.hypo == "hypo5":
            pass

        elif args.hypo == "hypo6":
            bias_type = args.benchmark.split(".")[-1].lower()
            if "discourse_moral_sentiment" not in da.keys():
                continue
            if args.situation in [1, 2, 3, 4]:
                if "discourse_moral_sentiment" in da.keys():
                    discourses = da["discourse_moral_sentiment"]
                    dm_discourse = discourses[f"synthesis_text_specificity{args.situation}"]['statement']
            elif args.situation == 5:
                dm_discourse = random.choice(specificity_5_texts)
            elif args.situation == 6:
                dm_discourse = random.choice(specificity_6_texts)

            target_group = da['biased_group']
            for choice in ['(a)', '(b)', '(c)']:
                if da['label'] == choice:
                    continue
                if da['biased_group'] in choice_bias_mapping[bias_type][da[choice]]:
                    target_choice_str = da[choice]
            assert target_choice_str

            Q2Statement = da['question'].split(" ")
            Q2Statement[0] = target_choice_str[0].upper() + \
                target_choice_str[1:]
            Q2Statement_str = " ".join(Q2Statement).replace("?", "")
            # ds_ = f"{da['context']} {Q2Statement_str}."
            ds_ = f"{da['context']} {da['question']}"
            dataset.append(
                f"{ds_} Here, in the question and the context, {dm_discourse.lower()}")

    # do misalignment matching, by parsing temp_ds_list and temp_dm_list
    """
    if args.hypo in ["hypo3","hypo5"]:
         dataset = []
         dm_idx = list(temp_dm_list)
         ds_idx = list(temp_ds_list)
        
         if args.hypo == "hypo3":
             dm_idx, ds_idx = _idx_misalign_(dm_idx, ds_idx, args.misalign_rate)
         elif args.hypo == "hypo5":
             dm_idx, ds_idx = _idx_misalign_(dm_idx, ds_idx, 1)

        #assert len(dm_idx) == len(ds_idx)
        for i, dm_i in enumerate(dm_idx):
             ds_discourses = temp_ds_list[i]
             dm_discourse = temp_dm_list[dm_i]
             assert type(ds_discourses) == list and type(dm_discourse) == str
             for ds_discourse in ds_discourses:
                 dataset.append(f"{ds_discourse} {dm_discourse}")
    """

    print(f"With dataset length {len(dataset)}")
    print(f"Sample data: {dataset[0]}")
    return dataset


def prepare_dataset(args, datalist):
    dataset = []
    # with open(file,"r") as reader: datalist = json.load(reader)[:]

    # dataset = parse_by_hypo(args, datalist)
    # get_data_by_template
    dataset = parse_by_identifiers(args, datalist)
    random.shuffle(dataset)
    return dataset

def _train_(args, tokenizer, llm):
    
    # train_dataset = load_dataset('text', data_files={"train":f'{args.train_file}',"test":f'{args.dev_file}'})
    train_dataset = load_dataset(
        'text', data_files={"train": f'{args.train_file}'})
    training_args = SFTConfig(
        fp16=True,  # specify bf16=True instead when training on GPUs that support bf16
        do_eval=False,
        num_train_epochs=args.num_train_epochs,
        max_seq_length=args.max_seq_length,
        # eval_strategy="epoch",
        logging_strategy="steps",
        # max_steps=args.max_training_steps,
        output_dir=args.output_dir,
        overwrite_output_dir=True,
        per_device_eval_batch_size=args.batch_size,  # originally set to 8
        per_device_train_batch_size=args.batch_size,  # originally set to 8
        gradient_accumulation_steps=1,
        save_strategy="epoch",
        save_only_model=True,
        learning_rate=args.lr,
        log_level="info",
        logging_steps=30,

        # gradient_checkpointing=True,
        # gradient_checkpointing_kwargs={"use_reentrant": False},
        # lr_scheduler_type="cosine",
        # seed=args.seed,
    )

    peft_config = LoraConfig(
        r=64,
        lora_alpha=16,
        lora_dropout=0.1,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    )

    if "8b" in args.llm or "mistral" in args.llm:
        print(args.llm)
        print("using peft!!!!!")
        trainer = SFTTrainer(
            model=llm,
            processing_class=tokenizer,
            # tokenizer=tokenizer,
            train_dataset=train_dataset["train"],
            # eval_dataset=train_dataset["test"],
            peft_config=peft_config,
            args=training_args,
        )
    else:
        trainer = SFTTrainer(
            model=llm,
            processing_class=tokenizer,
            # tokenizer=tokenizer,
            train_dataset=train_dataset["train"],
            # eval_dataset=train_dataset["test"],
            args=training_args
        )
    trainer.train()


def run_sft_finetuning(args, tokenizer, llm, datalist):
    set_seed(args.seed)
    # tokenizer, llm = init_model(args)
    # args.data_split = "train"

    # print(f"GET DISCOURSES OF BIAS TYPE: {args.bias_type}")
    # data_file = f"experiment/dataset/{args.benchmark}.train.json"
    # data_file = f"experiment/dataset/{args.benchmark}.{args.data_split}.json"

    parsed_data = prepare_dataset(args, datalist)

    '''
    train_size = int(len(parsed_data) * 0.9)

    train_data, dev_data = parsed_data[:train_size], parsed_data[train_size:]

    args.train_file = f"experiment/{args.llm}/{args.hypo}.{args.situation}.{args.misalign_rate}misalign.train.txt"
    args.dev_file = f"experiment/{args.llm}/{args.hypo}.{args.situation}.{args.misalign_rate}misalign.dev.txt"

    if not os.path.exists(f"experiment/{args.llm}/"): os.makedirs(f"experiment/{args.llm}", exist_ok=True) 

    # with open(args.train_file,"w") as writer: writer.write("\n".join(train_data))
    # with open(args.dev_file,'w') as writer: writer.write("\n".join(dev_data))

    with open(args.train_file, "w") as writer:
        writer.write("\n".join(line for line in train_data if line.strip()))

    with open(args.dev_file, "w") as writer:
        writer.write("\n".join(line for line in dev_data if line.strip()))
    '''
    train_data = parsed_data[:]
    # now the discourse_construction is a list
    args.train_file = f"experiment/{args.llm}/{'+'.join(args.discourse_construction)}.train.txt"

    if not os.path.exists(f"experiment/{args.llm}/"):
        os.makedirs(f"experiment/{args.llm}", exist_ok=True)

    with open(args.train_file, "w") as writer:
        # writer.write("\n".join(line for line in train_data if line.strip()))

        writer.write("\n".join([line.strip() for line in train_data]))

    _train_(args, tokenizer, llm)
