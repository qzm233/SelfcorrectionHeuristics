import json
import random
import copy
from constructionConfig import *
from pprint import pprint
import os


def split_by_context(data, output_folder, context_identify_list):
    try:

        train_data = []
        test_data = []

        for item in data:
            if item.get("context_split_identify_str") in context_identify_list:
                test_data.append(item)
            else:
                train_data.append(item)

        os.makedirs(output_folder, exist_ok=True)

        train_path = os.path.join(
            output_folder, 'bbq.gender.train.context_split.json')
        test_path = os.path.join(
            output_folder, 'bbq.gender.test.context_split.json')

        with open(train_path, 'w', encoding='utf-8') as f:
            json.dump(train_data, f, indent=2)
        with open(test_path, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, indent=2)

    except Exception as e:
        print(f"Error processing {output_folder}: {str(e)}")


def get_append_str_two(datapoint, bias_type="gender"):
    if bias_type == 'gender':
        q = datapoint['question']  # question, e.g: who is good at math
        # target group key, e.g: 'oppisite group'
        group_str = question_group_mapping[bias_type][q]
        if group_str == 'oppisite_group':
            oppo_group_str = 'biased_group'
        elif group_str == 'biased_group':
            oppo_group_str = 'oppisite_group'

        for choice in ['(a)', '(b)', '(c)']:
            if datapoint['label'] == choice:
                continue
            if datapoint[group_str] in choice_bias_mapping[bias_type][datapoint[choice]]:
                target_choice_str = datapoint[choice]
            else:
                opposite_choice_str = datapoint[choice]
        assert target_choice_str and opposite_choice_str and opposite_choice_str != target_choice_str
        return target_choice_str, opposite_choice_str, group_str, oppo_group_str
    print("not implement for other bias type")
    assert False


def sample_unrelated(data_point, data_):
    check = False
    while not check:
        sample_datapoint = random.choice(data_)
        if data_point['context_split_identify_str'] != sample_datapoint['context_split_identify_str']:
            check = True
    return sample_datapoint

def get_data_by_template_selfcorrection(args):
    bias_type = args.bias_type
    if args.selfcorrection_generalization:
        data_ = []
        for bias in ['age','disability','gender','nationality','SES']:
            print(f"GET DISCOURSES OF BIAS TYPE: {bias}")
            file = f"experiment/dataset/bbq.{bias}.train.json"
            with open(file, "r") as r:
                data_.extend(json.load(r))
    else:
        print(f"GET DISCOURSES OF BIAS TYPE: {bias_type}")
        file = f"experiment/dataset/bbq.{bias_type}.train.json"
        with open(file, "r") as r:
            data_ = json.load(r)
    
    data = []
    for data_point_ in data_:
        data_point = copy.deepcopy(data_point_)
        data_return = {}
        target_group = "biased_group" if data_point['question_polarity'] == 'neg' else "oppisite_group"
        target_anti_group = "oppisite_group" if data_point['question_polarity'] == 'neg' else "biased_group"
        question = data_point['question'].replace("?", "")
        question = question[0].lower() + question[1:]

        # unrelated_datapoint = sample_unrelated(data_point, data_)
        # question = data_point['question'].replace("?", "")
        # question = question[0].lower() + question[1:]
        # unrelated_question = unrelated_datapoint['question'].replace("?", "")
        # unrelated_question = unrelated_question[0].lower() + unrelated_question[1:]

        # context = f"In the scenario of {data_point['context_info']['abstract_scenario']}"
        # biased_entity, unbiased_entity, biased_group_str, unbiased_group_str = get_append_str_two(data_point)
        # biased_entity = biased_entity.replace("The", "the")
        # unbiased_entity = unbiased_entity.replace("The", "the")

        # "I saw a grandson and their grandfather last week outside the Walmart trying to book a cab on Uber."
        SITUATION = f"{data_point['context']}"
        SITUATION_ABS = f"{data_point['context_abstract']}"  # ""
        # "Last week, outside Walmart, I saw a grandson and their grandfather attempting to book an Uber cab."
        SITUATION_REPHRASE = f"{data_point['context_rephrased']}"
        # "I saw two individuals last week outside the Walmart trying to book a cab on Uber."
        SITUATION_W_O_GROUP = f"{data_point['context_withoutGroup']}"

        # "People may have age stereotypes in terms of who has trouble remembering things."
        STATEMENT = f"{data_point['statement']}"
        ACTION1 = f"{data_point['action1']}"  # "To avoid gender stereotypes,"
        ACTION1_W_O_TYPE = f"To avoid stereotypes,"
        ACTION1_FULLMATCH = f"To be unbiased and not rely on stereotypes,"

        # "we should assume both old and non-old",
        ACTION2 = f"{data_point['action2']}"

        ACTION2_W_O_GROUP = "we should assume both individuals"
        
        # statement, i.e "has trouble remembering things",
        EVENT1 = f"{data_point['event1']}"
        # vague statement, i.e "may have trouble remembering things",
        EVENT2 = f"{data_point['event2']}"
        EVENT_ABS = f"performs any events, skills, and decision-making processes."

        # "Older generations often grew up with different technologies, making the transition to smartphones and apps less intuitive. They may face challenges with small screens, complex interfaces, or a lack of familiarity with digital platforms. This leads to the stereotype that older individuals are not comfortable using phones.",
        REASON2BIAS = f"{data_point['reason2bias']}"
        # "The grandfather in the context might have been unfamiliar with technology like Uber, leading to the assumption that older individuals may struggle with modern phone apps, which could reinforce the stereotype that they are less comfortable using such devices.",
        REASON2BIAS_SITUATED = f"{data_point['reason2bias_situated']}"

        ANTI_ACTION2 = data_point['action2anti']
        GROUND_TRUTH_ACTION2 = data_point['action2groundTruth']
        FAIR_ACTION2 = data_point['action2fair']
        ABSEVENT_ACTION2 = data_point['action2groundTruth'].replace(question, EVENT_ABS)
        GENERAL_ACTION2 = f"{data_point['general_action']}"
        NOEVENT_ACTION2 = f"we cannot make assumptions."

        TRIVIAL = data_point['trivial']
 
        # STATEMENT_UNRELATED = f"People may have {bias_type} stereotypes in terms of {unrelated_question}."
        # ACTION_PRIOR1 = "To avoid gender stereotypes,"
        # ACTION_PRIOR2 = f"we should assume {data_point[unbiased_group_str]}"
        # EVENT_PRIOR = f"{EVENT} too."

        data_return[args.capability] = {}
        data_return["logic_turn"] = data_point["logic_turn"]
        data_return["socialgroup_in_context"] = data_point["socialgroup_in_context"]
        for construction in args.discourse_construction:
            if "action2" not in construction and "event" in construction:
                # ACTION1 + " we should take care of"
                ACTION1 = f"We should avoid gender stereotypes of both {data_point['biased_group']} and {data_point['oppisite_group']}"
                EVENT2 = f"in terms of {question}."
            if "action2" not in construction and "event" not in construction:
                ACTION1 = "We should avoid gender stereotypes."
            if "action2" not in construction:
                ACTION1 = f"We should avoid gender stereotypes when decideing {question}."


            discourse_options = construction.split("-")
            discourse_components = []
            if "trivial" in discourse_options:
                discourse_components.append(TRIVIAL)

            if "situation" in discourse_options:
                discourse_components.append(SITUATION)
            if "situationAbs" in discourse_options:
                discourse_components.append(SITUATION_ABS)
            if "situationNoGroup" in discourse_options:
                discourse_components.append(SITUATION_W_O_GROUP)

            if "statement" in discourse_options:
                discourse_components.append(STATEMENT)
            if "statementReason" in discourse_options:
                discourse_components.append(REASON2BIAS)
            if "statementReasonSituated" in discourse_options:
                discourse_components.append(REASON2BIAS_SITUATED)
            if "statementUnrelated" in discourse_options:
                discourse_components.append(STATEMENT_UNRELATED)
                GENERAL_ACTION2 = GENERAL_ACTION2[0].lower() + GENERAL_ACTION2[1:]
                
            if "action1" in discourse_options:
                discourse_components.append(ACTION1)

            if "action1noType" in discourse_options:
                discourse_components.append(ACTION1_W_O_TYPE)
            if "action1full" in discourse_options:
                discourse_components.append(ACTION1_FULLMATCH)
            if not any("action1" in option_str for option_str in discourse_options):
                # Captalize the first letter
                ACTION2 = ACTION2[0].upper() + ACTION2[1:]
                ACTION2_W_O_GROUP = ACTION2_W_O_GROUP[0].upper(
                ) + ACTION2_W_O_GROUP[1:]
                ANTI_ACTION2 = ANTI_ACTION2[0].upper() + ANTI_ACTION2[1:]
                GROUND_TRUTH_ACTION2 = GROUND_TRUTH_ACTION2[0].upper() + GROUND_TRUTH_ACTION2[1:]
                FAIR_ACTION2 = FAIR_ACTION2[0].upper() + FAIR_ACTION2[1:]

            if "action2" in discourse_options:
                discourse_components.append(ACTION2)
            if "action2NoGroup" in discourse_options:
                discourse_components.append(ACTION2_W_O_GROUP)
            
            if "action2anti" in discourse_options:
                discourse_components.append(ANTI_ACTION2)
            if "action2groundTruth" in discourse_options:
               discourse_components.append(GROUND_TRUTH_ACTION2)
            if "action2fair" in discourse_options:
               discourse_components.append(FAIR_ACTION2)
            if "action2absEvent" in discourse_options:
                discourse_components.append(ABSEVENT_ACTION2)
            if "action2general" in discourse_options:
                discourse_components.append(GENERAL_ACTION2)
            if "action2noEvent" in discourse_options:
                discourse_components.append(NOEVENT_ACTION2)

            if "event" in discourse_options:
                discourse_components.append(EVENT2)
            if "eventAbs" in discourse_options:
                discourse_components.append(EVENT_ABS)
            if "eventPrior" in discourse_options:
                discourse_components.append(EVENT_PRIOR)

            if "situationAbsSub" in discourse_options:
                discourse_components[1] = discourse_components[1][0].lower(
                ) + discourse_components[1][1:]

            discourse = " ".join(discourse_components).strip()
            if not discourse.endswith(".") and not discourse.endswith("?"):
                discourse += "."
            # print(discourse)
            data_return[args.capability][construction] = discourse
        data.append(data_return)
    return data


def get_data_by_template_selfdiagnosis(args):
    bias_type = args.bias_type
    print(f"GET DISCOURSES OF BIAS TYPE: {bias_type}")
    file = f"experiment/dataset/bbq.{bias_type}.train.json"
    with open(file, "r") as r:
        data_ = json.load(r)
    data = []
    for data_point_ in data_:
        if args.chosen_question_list:
            if data_point_['question'] not in args.chosen_question_list: continue

        data_point = copy.deepcopy(data_point_)
        data_return = {}

        question = data_point['question'].replace("?", "")
        question = question[0].lower() + question[1:]

        # context = f"In the scenario of {data_point['context_info']['abstract_scenario']}"
        # biased_entity, unbiased_entity, biased_group_str, unbiased_group_str = get_append_str_two(
        # data_point)
        # biased_entity = biased_entity.replace("The", "the")
        # unbiased_entity = unbiased_entity.replace("The", "the")

        SITUATION = f"{data_point['context']}"  # original context
        SITUATION_ABS = f"{data_point['context_abstract']}"  # ""
        SITUATION_REPHRASE = f"{data_point['context_rephrased']}"  # ""
        SITUATION_W_O_GROUP = f"{data_point['context_withoutGroup']}"  # ""

        EVENT_ABS = f"performs any events, skills, and decision-making processes"
        STATEMENT = f"{data_point['statement']}"
        STATEMENT_TWO_GROUP = f"{data_point['statement_diagnosis_twoGroup']}"
        STATEMENT_NO_GROUP = f"{data_point['statement_diagnosis_noGroup']}"
        STATEMENT_NO_EVENT = f"{data_point['statement_diagnosis_noEvent']}"
        STATEMENT_ABS_EVENT = f"{data_point['statement']}".replace(question, EVENT_ABS)

        # statement, i.e "has trouble remembering things",
        EVENT1 = f"{data_point['event1']}"
        # vague statement, i.e "may have trouble remembering things",
        EVENT2 = f"{data_point['event2']}"

        TRIVIAL = data_point['trivial']

        data_return[args.capability] = {}
        data_return["logic_turn"] = data_point["logic_turn"]
        data_return["socialgroup_in_context"] = data_point["socialgroup_in_context"]
        for construction in args.discourse_construction:
            discourse_options = construction.split("-")
            discourse_components = []
            if "trivial" in discourse_options:
                discourse_components.append(TRIVIAL)
            if "situationNoGroup" in discourse_options:
                discourse_components.append(SITUATION_W_O_GROUP)
            if "situation" in discourse_options:
                discourse_components.append(SITUATION)
            if "situationAbs" in discourse_options:
                discourse_components.append(SITUATION_ABS)

            if "statement" in discourse_options:
                if "eventAbs" in discourse_options:
                    STATEMENT = STATEMENT.replace(f"{question}", EVENT_ABS)
                discourse_components.append(STATEMENT)
            if "statementTwoGroup" in discourse_options:
                discourse_components.append(STATEMENT_TWO_GROUP)
            if "statementNoGroup" in discourse_options:
                discourse_components.append(STATEMENT_NO_GROUP)
            if "statementNoEvent" in discourse_options:
                discourse_components.append(STATEMENT_NO_EVENT)
            if "statementAbsEvent" in discourse_options:
                discourse_components.append(STATEMENT_ABS_EVENT)

            # if "event" in discourse_options:
            #     discourse_components.append(EVENT2)
            #     if "statementTwoGroup" in discourse_options:
            #         discourse_components.append(TWO_GROUP_APPEND)

            

            discourse = " ".join(discourse_components).strip()
            if not discourse.endswith(".") and not discourse.endswith("?"):
                discourse += "."

            # print(discourse)

            data_return[args.capability][construction] = discourse
        data.append(data_return)
    return data


def get_data_by_template(args):
    if "correction" in args.capability:
        return get_data_by_template_selfcorrection(args)
    else:
        return get_data_by_template_selfdiagnosis(args)
