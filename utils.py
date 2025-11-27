import os,gc

import argparse
import copy
import glob
import json
import datasets
import numpy as np
import torch
from torch import nn
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    AutoModelForSequenceClassification,
    AutoConfig,
    LlamaTokenizer,
    LlamaForCausalLM,
    GenerationConfig
)
import random
from tqdm import tqdm
from googleapiclient import discovery
from api_tokens import *
import huggingface_hub
import torch.nn.functional as F

# local_rank = os.getenv("LOCAL_RANK")
# device_string = "cuda:" + str(local_rank)

#huggingface_hub.login(token=mistral_v3_token)

llama_7b_dir = "/scratch0/liuguan5/llama/llama-2-7b-chat-hf/"

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

STEREOTYPED_GROUPS = "stereotyped_groups"

def init_model(args, checkpoint_path = None):
    cache_dir = ""
    
    if args.llm in ["mistral","mistral-v0.2-instruct"]:  # 7B
        tokenizer = AutoTokenizer.from_pretrained(
            "mistralai/Mistral-7B-Instruct-v0.2", cache_dir=cache_dir
        )
        tokenizer.padding_side = "left"
        tokenizer.truncation_side = "left"

        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
            tokenizer.pad_token_id = tokenizer.eos_token_id
        model = AutoModelForCausalLM.from_pretrained(
            "mistralai/Mistral-7B-Instruct-v0.2", cache_dir=cache_dir, device_map="auto"
        )
        
    elif args.llm == "mistral-v0.3-base":  # 7B
        tokenizer = AutoTokenizer.from_pretrained(
            "mistralai/Mistral-7B-v0.3", cache_dir=cache_dir
        )
        tokenizer.padding_side = "left"
        tokenizer.truncation_side = "left"

        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
            tokenizer.pad_token_id = tokenizer.eos_token_id
        model = AutoModelForCausalLM.from_pretrained(
            "mistralai/Mistral-7B-v0.3", cache_dir=cache_dir, device_map="auto"
        )
        
    elif args.llm == "mistral-v0.3-instruct":  # 7B
        huggingface_hub.login(token=mistral_v3_token)
        tokenizer = AutoTokenizer.from_pretrained(
            "mistralai/Mistral-7B-Instruct-v0.3", cache_dir=cache_dir
        )
        tokenizer.padding_side = "left"
        tokenizer.truncation_side = "left"

        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
            tokenizer.pad_token_id = tokenizer.eos_token_id
        model = AutoModelForCausalLM.from_pretrained(
            "mistralai/Mistral-7B-Instruct-v0.3", cache_dir=cache_dir, device_map="auto"
        )
    elif args.llm == "qwen2-1.5b-instruct":
        tokenizer = AutoTokenizer.from_pretrained(
            "Qwen/Qwen2.5-1.5B-Instruct", cache_dir=cache_dir
        )
        tokenizer.padding_side = "left"
        tokenizer.truncation_side = "left"

        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
            tokenizer.pad_token_id = tokenizer.eos_token_id
        model = AutoModelForCausalLM.from_pretrained(
            "Qwen/Qwen2.5-1.5B-Instruct", cache_dir=cache_dir, device_map="auto"
        )       
    elif args.llm == "qwen2-3b-instruct":
        tokenizer = AutoTokenizer.from_pretrained(
            "Qwen/Qwen2.5-3B-Instruct", cache_dir=cache_dir
        )
        tokenizer.padding_side = "left"
        tokenizer.truncation_side = "left"

        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
            tokenizer.pad_token_id = tokenizer.eos_token_id
        model = AutoModelForCausalLM.from_pretrained(
            "Qwen/Qwen2.5-3B-Instruct", cache_dir=cache_dir, device_map="auto"
        )     
    elif args.llm == "gemma3-4b-instruct":
        tokenizer = AutoTokenizer.from_pretrained(
            "google/gemma-3-4b-it", cache_dir=cache_dir
        )
        tokenizer.padding_side = "left"
        tokenizer.truncation_side = "left"

        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
            tokenizer.pad_token_id = tokenizer.eos_token_id
        model = AutoModelForCausalLM.from_pretrained(
            "google/gemma-3-4b-it", cache_dir=cache_dir, device_map="auto"
        )
    elif args.llm == "gemma3-1b-instruct":
        tokenizer = AutoTokenizer.from_pretrained(
            "google/gemma-3-1b-it", cache_dir=cache_dir
        )
        tokenizer.padding_side = "left"
        tokenizer.truncation_side = "left"

        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
            tokenizer.pad_token_id = tokenizer.eos_token_id
        model = AutoModelForCausalLM.from_pretrained(
            "google/gemma-3-1b-it", cache_dir=cache_dir, device_map="auto"
        )
    elif args.llm == "olmo-2-base":  # 7B
        tokenizer = AutoTokenizer.from_pretrained(
            "allenai/OLMo-2-1124-7B", cache_dir=cache_dir
        )
        tokenizer.padding_side = "left"
        tokenizer.truncation_side = "left"

        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
            tokenizer.pad_token_id = tokenizer.eos_token_id
        model = AutoModelForCausalLM.from_pretrained(
            "allenai/OLMo-2-1124-7B", cache_dir=cache_dir, device_map="auto"
        )
    elif args.llm == "olmo-2-instruct":  # 1B
        tokenizer = AutoTokenizer.from_pretrained(
            "allenai/OLMo-2-0425-1B-Instruct", cache_dir=cache_dir
        )
        tokenizer.padding_side = "left"
        tokenizer.truncation_side = "left"

        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
            tokenizer.pad_token_id = tokenizer.eos_token_id
        model = AutoModelForCausalLM.from_pretrained(
            "allenai/OLMo-2-0425-1B-Instruct", cache_dir=cache_dir, device_map="auto"
        )
    elif args.llm == "phi-3.5-instruct":
        tokenizer = AutoTokenizer.from_pretrained(
            "microsoft/Phi-3.5-mini-instruct", cache_dir=cache_dir
        )
        tokenizer.padding_side = "left"
        tokenizer.truncation_side = "left"

        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
            tokenizer.pad_token_id = tokenizer.eos_token_id
        model = AutoModelForCausalLM.from_pretrained(
            "microsoft/Phi-3.5-mini-instruct", cache_dir=cache_dir, 
            device_map="auto",
            # device_map={'':device_string}
        )
    elif args.llm == "llama-3-8b-base":
        huggingface_hub.login(token=llama3_token)
        tokenizer = AutoTokenizer.from_pretrained(
            "meta-llama/Meta-Llama-3-8B", cache_dir=cache_dir
        )
        tokenizer.padding_side = "left"
        tokenizer.truncation_side = "left"

        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
            tokenizer.pad_token_id = tokenizer.eos_token_id
        model = AutoModelForCausalLM.from_pretrained(
            "meta-llama/Meta-Llama-3-8B", cache_dir=cache_dir, device_map="auto", offload_folder=None,
        )
        
    elif args.llm == "llama-3.2-3b-base":
        huggingface_hub.login(token=llama3_token)
        tokenizer = AutoTokenizer.from_pretrained(
            "meta-llama/Llama-3.2-3B", cache_dir=cache_dir
        )
        tokenizer.padding_side = "left"
        tokenizer.truncation_side = "left"

        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
            tokenizer.pad_token_id = tokenizer.eos_token_id
        model = AutoModelForCausalLM.from_pretrained(
            "meta-llama/Llama-3.2-3B", cache_dir=cache_dir, device_map="auto"
        )
    elif args.llm == "llama-3.2-3b-instruct":
        print(args.llm,"*"*50)
        #huggingface_hub.login(token=llama3_token)
        tokenizer = AutoTokenizer.from_pretrained(
            "meta-llama/Llama-3.2-3B-Instruct", cache_dir=cache_dir
        )
        tokenizer.padding_side = "left"
        tokenizer.truncation_side = "left"

        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
            tokenizer.pad_token_id = tokenizer.eos_token_id
        model = AutoModelForCausalLM.from_pretrained(
            "meta-llama/Llama-3.2-3B-Instruct", cache_dir=cache_dir, device_map="auto"
        )
        return tokenizer, model

    elif args.llm == "llama-3.2-1b-base":
        huggingface_hub.login(token=llama3_token)
        tokenizer = AutoTokenizer.from_pretrained(
            "meta-llama/Llama-3.2-1B", cache_dir=cache_dir
        )
        tokenizer.padding_side = "left"
        tokenizer.truncation_side = "left"

        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
            tokenizer.pad_token_id = tokenizer.eos_token_id
        model = AutoModelForCausalLM.from_pretrained(
            "meta-llama/Llama-3.2-1B", cache_dir=cache_dir, device_map="auto"
        )
    elif args.llm == "llama-3.2-1b-instruct":
        #huggingface_hub.login(token=llama3_token)
        tokenizer = AutoTokenizer.from_pretrained(
            "meta-llama/Llama-3.2-1B-Instruct", cache_dir=cache_dir
        )
        tokenizer.padding_side = "left"
        tokenizer.truncation_side = "left"

        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
            tokenizer.pad_token_id = tokenizer.eos_token_id
        model = AutoModelForCausalLM.from_pretrained(
            "meta-llama/Llama-3.2-1B-Instruct", cache_dir=cache_dir, device_map="auto"
        )

        return tokenizer, model
        
    elif args.llm == "GPT2XL":
        huggingface_hub.login(token=llama3_token)
        tokenizer = AutoTokenizer.from_pretrained(
            "gpt2-xl", cache_dir=cache_dir
        )
        tokenizer.padding_side = "left"
        tokenizer.truncation_side = "left"
        
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
            tokenizer.pad_token_id = tokenizer.eos_token_id
        model = AutoModelForCausalLM.from_pretrained(
            "gpt2-xl", cache_dir=cache_dir, device_map="auto"
        )
        
    
    elif args.llm == "gemma2-9b":
        tokenizer = AutoTokenizer.from_pretrained(
            "google/gemma-2-9b-it", cache_dir=cache_dir
        )
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer.padding_side = "left"
        model = AutoModelForCausalLM.from_pretrained(
            "google/gemma-2-9b-it", cache_dir=cache_dir, device_map="auto"
        )
        

    elif args.llm == "llama-3-8b-instruct":
        huggingface_hub.login(token=llama3_token)
        tokenizer = AutoTokenizer.from_pretrained(
            "meta-llama/Meta-Llama-3-8B-Instruct", cache_dir=cache_dir
        )
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer.padding_side = "left"
        model = AutoModelForCausalLM.from_pretrained(
            "meta-llama/Meta-Llama-3-8B-Instruct", cache_dir=cache_dir, device_map="auto"
        )
        

    elif args.llm == "llama3-70B":
        huggingface_hub.login(token=llama3_token)
        # meta-llama/Meta-Llama-3-70B-Instruct
        tokenizer = AutoTokenizer.from_pretrained(
            "meta-llama/Meta-Llama-3-70B-Instruct", cache_dir=cache_dir
        )
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer.padding_side = "left"
        model = AutoModelForCausalLM.from_pretrained(
            "meta-llama/Meta-Llama-3-70B-Instruct", cache_dir=cache_dir
        )

        

    elif "gpt2" in args.llm:  # args.llm == "gpt2-xl":
        if args.llm not in ["gpt2", "gpt2-medium", "gpt2-large"]:
            raise RuntimeError
        config = AutoConfig.from_pretrained(
            args.llm, output_hidden_states=True, output_attentions=True
        )
        model = AutoModelForCausalLM.from_pretrained(
            args.llm, config=config, cache_dir=cache_dir
        )
        tokenizer = AutoTokenizer.from_pretrained(args.llm, cache_dir=cache_dir)
        tokenizer.pad_token = tokenizer.eos_token
        
    return tokenizer, model

def init_nli_model(args):
    cache_dir = ""
    cache_dir_slim = "/home/zhangxit/files/llms"
    cache_dir_psu = "/data/bochuan/DPO/cache"
    cache_dir_zhiyu = "/home/zhiyu2/guangliang/zimo/models"
    if args.cluster == "psu":
        cache_dir = cache_dir_psu
    elif args.cluster == "slim":
        cache_dir = cache_dir_slim
    elif args.cluster == "zhiyu":
        cache_dir = cache_dir_zhiyu

    tokenizer = AutoTokenizer.from_pretrained("microsoft/deberta-large-mnli", cache_dir=cache_dir)
    model = AutoModelForSequenceClassification.from_pretrained("microsoft/deberta-large-mnli", cache_dir=cache_dir).to(
        device)
    return tokenizer, model

def remove_last_sentence(text):
    sentences = text.split(". ")
    last_idx = len(sentences) - 1
    min_length = min(len(sentences[last_idx]), len(sentences[last_idx - 1]))
    if sentences[last_idx][:min_length] == sentences[last_idx - 1][:min_length]:
        sentences.remove(sentences[last_idx])

    text = ". ".join(sentences)
    return text

def load_winogender():
    dataset = []
    for line in open("../data/winogender.multianswer.txt"):
        question, label = line.strip().split("\t")
        dataset.append({
            "question": question,
            "label":label
        })
    return dataset

def load_bbq(args,target_data_path = None):
    dataset = []
    bias_type = args.benchmark.split(".")[-1]
    file = f"data/bbq/bbq.{bias_type}.json"
    if target_data_path: file = target_data_path
    if not os.path.exists(file):
        raise FileNotFoundError(f"File not found: {file}")
    with open(file, "r") as r:
        dataset = json.load(r)
    print(f"load bbq {args.benchmark} from {file}")
    return dataset

def load_realtoxicity():
    return [json.loads(line.strip())["prompt"]["text"] for line in open("./data/realtoxicity.txt")]
def load_benchmark(args, target_data_path = None):
    if args.benchmark == "winogender":
        return load_winogender()
    elif "bbq" in args.benchmark:
        return load_bbq(args, target_data_path)
    elif args.benchmark == "realtoxicity":
        return load_realtoxicity()
    elif args.benchmark == "bbq_debug":
        dataset = []
        for file in glob.glob("../data/bbq.sexual_orientation.txt"):
            bias_type = file.split("/")[-1].split(".")[1]

            for line in open(file):
                split_line = line.strip().split("\t")
                context,question,choice = split_line[:3]
                label = split_line[3]
                stereotyped_groups = " ".join(split_line[4:])

                dataset.append(
                {   "context":context,
                    "question": question,
                    "choice":choice,
                    "label": label,
                    "bias": bias_type,
                    STEREOTYPED_GROUPS: stereotyped_groups,
                }
            )
        random.shuffle(dataset)
        return dataset[:]


@torch.no_grad()
def prompting_bbq(args, tokenizer, llm, prompting_list):
    question_list = load_benchmark(args)
    return_list = []
    for question_ in tqdm(question_list,desc="bbq"):
        # print(question_)
        context, question, choice, label = question_["context"],question_["question"],question_["choice"], question_["label"]
        result_json_list = []
        history = ""
        for idx, prompt in enumerate(prompting_list):
            round = idx + 1
            query = copy.deepcopy(prompt)
            query = query.replace("#QUESTION", context+" "+question+" "+choice)
            input_query = copy.deepcopy(query)

            if round > 1:
                input_query = history + input_query

            response = get_response(args, tokenizer, llm, input_query)
            #print(f"output:{response}\tlabel:{label}")
            result_json = {
                "input": copy.deepcopy(input_query),
                "output": response,
                "round": round,
                "label": question_["label"],
                "bias": question_["bias"],
            }

            result_json_list.append(result_json)

            end_session = "</s>"
            history = history +" "+ input_query.strip() + " " + response + end_session

        return_list.append(result_json_list)
    return return_list
@torch.no_grad()
def prompting_winogender(args, tokenizer, llm, prompting_list):
    question_list = load_benchmark(args)
    return_list = []
    for question_ in tqdm(question_list, desc="winogender"):
        #print(question_)
        question, label = question_["question"], question_["label"]
        
        result_json_list = []
        history = ""
        for idx, prompt in enumerate(prompting_list):
            round = idx + 1
            query = copy.deepcopy(prompt)
            query = query.replace("#QUESTION", question)
            input_query = copy.deepcopy(query)

            if round > 1:
                input_query = history + input_query
            
            response = get_response(args, tokenizer, llm, input_query)
            #print(f"output:{response}\tlabel:{label}")
            result_json = {
                "input": copy.deepcopy(input_query),
                "output": response,
                "round": round,
                "label": label,
            }

            result_json_list.append(result_json)

            end_session = "</s>"
            history = history +" "+ input_query.strip() + " " + response + end_session

        return_list.append(result_json_list)
    return return_list
@torch.no_grad()
def prompting_toxicity(args, tokenizer, llm, prompting_list):
    question_list = load_benchmark(args)
    return_list = []
    for question in question_list:
        result_json_list = []
        history = ""
        for idx, prompt in enumerate(prompting_list):
            round = idx + 1
            query = copy.deepcopy(prompt)
            query = query.replace("#QUESTION", question)
            input_query = copy.deepcopy(query)

            if round > 1:
                input_query = history + input_query

            response = get_response(args, tokenizer, llm, input_query)
            #print(f"output:{response}\tlabel:{label}")
            print(idx)
            print(response)
            result_json = {
                "input": copy.deepcopy(input_query),
                "output": response,
                "round": round,
            }

            result_json_list.append(result_json)

            end_session = "</s>"
            history = history +" "+ input_query.strip() + " " + response + end_session

        return_list.append(result_json_list)
    return return_list

@torch.no_grad()
def get_outputs(args, tokenizer, llm, input_query, max_new_tokens):
    # print("input query:", input_query)
    input_ids = tokenizer(input_query, return_tensors="pt")
    attention_mask = input_ids["attention_mask"]
    model_outputs = llm.generate(input_ids.input_ids.to(device), 
                                max_new_tokens=max_new_tokens,
                                attention_mask=attention_mask.to(device),
                                pad_token_id=tokenizer.eos_token_id,
                                do_sample=False,
                                num_beams=1,
                                top_p=1.0,
                                temperature=1.0)
    #print("model outputs:\t",model_outputs)
    # print("query length:", len(input_ids[0]))
    prompt_length = input_ids["input_ids"].shape[1]
    response = tokenizer.decode(
        model_outputs[0][prompt_length:],
        skip_special_tokens=True,
        clean_up_tokenization_spaces=False,
    )
    #print("*****************",response)
    # print(f'first output token: "{tokenizer.decode(model_outputs[0][prompt_length])}"')
    #print("["*15,response,"]"*15)
    response = " ".join(copy.deepcopy(response.strip()).split("\n"))
    #print("response:", response)
    return response

def get_probability_by_choices(tokenizer, llm, output_choices, input_text):
    output_choice_ids = []
    for word in output_choices:
        tokens = tokenizer.tokenize(word)
        assert len(tokens) == 1, f"Word {word} consists of multiple tokens: {tokens}"
        assert tokens[0] not in tokenizer.all_special_tokens, f"Word {word} corresponds to a special token: {tokens[0]}"
        token_id = tokenizer.convert_tokens_to_ids(tokens)[0]
        output_choice_ids.append(token_id)

    inputs = tokenizer(input_text, padding=False, return_tensors='pt').input_ids.to(device)
    # print(f'okokok: "{tokenizer.decode(inputs[:,-2])}","{tokenizer.decode(inputs[:,-1])}"')
    logits = llm(inputs)['logits'] 
    last_token_logits = logits[0, -1, :]

    selected_logits = last_token_logits[output_choice_ids]
    probs = selected_logits.softmax(dim=0) 

    return list(zip(output_choices, probs.tolist()))

class toxicityClf(nn.Module):
    def __init__(self, feature_dim):
        super(toxicityClf, self).__init__()
        self.linearProber = nn.Linear(feature_dim, 2).to(device)
        self.cross_entropy = torch.nn.CrossEntropyLoss(reduction="mean")

    def forward(self, features, labels):
        logits = self.linearProber(features).to(device)
        pred_softmax = torch.nn.functional.softmax(logits, dim=1)
        preds = np.argmax(pred_softmax.detach().cpu().numpy(), axis=1)
        loss = self.cross_entropy(logits, labels)

        return preds, loss.to(device)

def load_reddit_few_shots():
    """
        return the few-shot string
    """
    return "few_shot string"
def load_reddit_prompt():
    """
        return the prompt format with #TEXT
    """
    return "#TEXT"


def load_few_shot(args):
    if "reddit" in args.benchmark:
        return load_reddit_few_shots()
    else: print(f"{args.benchmark} not implemented yet")

def load_prompt(args):
    if "reddit" in args.benchmark:
        return load_reddit_prompt()
    else: print(f"{args.benchmark} not implemented yet")

def get_raw_reddit():
    return True

def eva_toxicity(text):
    client = discovery.build(
    "commentanalyzer",
    "v1alpha1",
    developerKey=PERSPECTIVE_API_KEY,
    discoveryServiceUrl="https://commentanalyzer.googleapis.com/$discovery/rest?version=v1alpha1",
    static_discovery=False,
    )

    analyze_request = {
    'comment': { 'text': text },
    'requestedAttributes': {'TOXICITY': {}}
    }

    response = client.comments().analyze(body=analyze_request).execute()
    return response["attributeScores"]["TOXICITY"]["summaryScore"]["value"]
    # print(json.dumps(response, indent=2))

def biased_determined_single_text(related_entities, candidate_text, bias_type = "gender"):
    if isinstance(related_entities, str): related_entities = [related_entities]
    assert isinstance(related_entities, list)
    for entity in related_entities:
        if entity in candidate_text:
            return True

def biased_determined(dataset, related_entities, candidate_text, bias_type = "gender"):
    results = None
    if dataset == "babylm_train":
        ds = datasets.load_from_disk("data/babylm")['train']
        result = []
        for point in ds:
            if biased_determined_single_text(related_entities, point['text'], bias_type = bias_type):
                result.append(point['text'])
        return results
    elif dataset == "babylm_all":
        result = []
        for split in ['train','test','validation']:
            ds = datasets.load_from_disk("data/babylm")[split]
            for point in ds:
                if biased_determined_single_text(related_entities, point['text'], bias_type = bias_type):
                    result.append(point['text'])
        return results
    elif dataset == "olmo_instruct":
        ds = datasets.load_from_disk("data/olmo_instruct")['train']['messages']
        result = []
        for point in ds:
            for message in point:
                if biased_determined_single_text(related_entities, message['content'], bias_type = bias_type):
                    result.append(point)
                    break
        return results
    elif dataset == "natural-instruction":
        print("not implemented")


def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
