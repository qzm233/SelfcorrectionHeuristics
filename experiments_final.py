import os

biases_all = ["age", "gender", "nationality", "physical",
              "race", "religion", "SES", "sexualorientation"]

biases_train = ["SES",]

random_seeds = ["42"]

llms = ["llama-3.2-1b-instruct", "llama-3.2-3b-instruct"]
# llms = ["gemma3-4b-instruct","gemma3-1b-instruct","olmo-2-instruct",]
# llms = [ "phi-3.5-instruct"]
# "mistral-v0.3-instruct", "gemma3-1b-instruct",
# llms = ["llama-3-8b-instruct", "mistral-v0.3-instruct"]
# llms = ["mistral-v0.3-instruct"]

epochs = 10
lr = 1e-6
for llm in llms:
    os.system(f"python -u run_experiment.py --baseline_only --llm {llm} --benchmark bbq.{bias_type} --eval_only")

    for bias_type in biases_train:
        # section 3.2 overlap
        for random_seed in random_seeds:
            os.system(f"python -u run_experiment.py --llm {llm} --benchmark bbq.{bias_type} --seed {random_seed} --overlap_analysis --lr {lr}")

        # section 3.3 trivial
        for random_seed in random_seeds:
            # trivial SC
            os.system(f"python -u run_experiment.py --llm {llm} --benchmark bbq.{bias_type} --seed {random_seed} --num_train_epochs {epochs} --epoch_wise_eval  --batch_size 32 --discourse_construction trivial --lr {lr}")
            # trivial SD
            os.system(f"python -u run_experiment.py --llm {llm} --benchmark bbq.{bias_type} --seed {random_seed} --num_train_epochs {epochs} --epoch_wise_eval  --batch_size 32 --discourse_construction trivial --capability selfdiagnosis --lr {lr}")
            # trivial self-diagnosis

        # section 4 self-correction
        # - baseline:
        os.system(f"python -u run_experiment.py --baseline_only --llm {llm} --benchmark bbq.{bias_type} --eval_only ")
        os.system(f"python -u run_experiment.py --baseline_only --llm {llm} --benchmark bbq.{bias_type} --eval_only --capability selfdiagnosis")
        
        for random_seed in random_seeds:
            # - situation-statement-action1-action2groundTruth
            os.system(f"python -u run_experiment.py --llm {llm} --benchmark bbq.{bias_type} --seed {random_seed} --num_train_epochs {epochs} --epoch_wise_eval  --batch_size 24 --discourse_construction situation-statement-action1-action2groundTruth --lr {lr}")

            # - statement-action1-action2groundTruth
            os.system(f"python -u run_experiment.py --llm {llm} --benchmark bbq.{bias_type} --seed {random_seed} --num_train_epochs {epochs} --epoch_wise_eval  --batch_size 24 --discourse_construction statement-action1-action2groundTruth --lr {lr}")
            # - situation-action1-action2groundTruth
            os.system(f"python -u run_experiment.py --llm {llm} --benchmark bbq.{bias_type} --seed {random_seed} --num_train_epochs {epochs} --epoch_wise_eval  --batch_size 24 --discourse_construction situation-action1-action2groundTruth --lr {lr}")
            # situation-statement-action2groundTruth
            os.system(f"python -u run_experiment.py --llm {llm} --benchmark bbq.{bias_type} --seed {random_seed} --num_train_epochs {epochs} --epoch_wise_eval  --batch_size 24 --discourse_construction situation-statement-action2groundTruth --lr {lr}")
            # - situation-statement-action1
            os.system(f"python -u run_experiment.py --llm {llm} --benchmark bbq.{bias_type} --seed {random_seed} --num_train_epochs {epochs} --epoch_wise_eval  --batch_size 24 --discourse_construction situation-statement-action1 --lr {lr}")
            # - situation-statementReasonSituated-action1-action2groundTruth
            os.system(f"python -u run_experiment.py --llm {llm} --benchmark bbq.{bias_type} --seed {random_seed} --num_train_epochs {epochs} --epoch_wise_eval  --batch_size 12 --discourse_construction  situation-statementReasonSituated-action1-action2groundTruth --lr {lr}")



            # - action1-action2groundTruth
            os.system(f"python -u run_experiment.py --llm {llm} --benchmark bbq.{bias_type} --seed {random_seed} --num_train_epochs {epochs} --epoch_wise_eval  --batch_size 24 --discourse_construction action1-action2groundTruth --lr {lr}")
            # -- action2groundTruth
            os.system(f"python -u run_experiment.py --llm {llm} --benchmark bbq.{bias_type} --seed {random_seed} --num_train_epochs {epochs} --epoch_wise_eval  --batch_size 32 --discourse_construction action2groundTruth --lr {lr}")
            # -- situation-action2groundTruth
            os.system(f"python -u run_experiment.py --llm {llm} --benchmark bbq.{bias_type} --seed {random_seed} --num_train_epochs {epochs} --epoch_wise_eval  --batch_size 32 --discourse_construction situation-action2groundTruth --lr {lr}")

            # situationAbs-action1-action2groundTruth
            os.system(f"python -u run_experiment.py --llm {llm} --benchmark bbq.{bias_type} --seed {random_seed} --num_train_epochs {epochs} --epoch_wise_eval  --batch_size 32 --discourse_construction situationAbs-action1-action2groundTruth --lr {lr}")
            # situation-action1-action2absEvent
            os.system(f"python -u run_experiment.py --llm {llm} --benchmark bbq.{bias_type} --seed {random_seed} --num_train_epochs {epochs} --epoch_wise_eval  --batch_size 32 --discourse_construction situation-action1-action2absEvent --lr {lr}")
            # situation-action1-action2general
            os.system(f"python -u run_experiment.py --llm {llm} --benchmark bbq.{bias_type} --seed {random_seed} --num_train_epochs {epochs} --epoch_wise_eval  --batch_size 32 --discourse_construction situation-action1-action2general --lr {lr}")

            # situation
            os.system(f"python -u run_experiment.py --llm {llm} --benchmark bbq.{bias_type} --seed {random_seed} --num_train_epochs {epochs} --epoch_wise_eval  --batch_size 32 --discourse_construction situation --lr {lr}")
            # situation-statement
            os.system(f"python -u run_experiment.py --llm {llm} --benchmark bbq.{bias_type} --seed {random_seed} --num_train_epochs {epochs} --epoch_wise_eval  --batch_size 32 --discourse_construction situation-statement --lr {lr}")
            # situation/statement
            os.system(f"python -u run_experiment.py --llm {llm} --benchmark bbq.{bias_type} --seed {random_seed} --num_train_epochs {epochs} --epoch_wise_eval  --batch_size 32 --discourse_construction situation statement --lr {lr}")

        # - section 4 self-diagnosis
        os.system(f"python -u run_experiment.py --baseline_only --llm {llm} --benchmark bbq.{bias_type} --eval_only --capability selfdiagnosis --lr {lr}")
        # prompting w/o social-group
        os.system(f"python -u run_experiment.py --baseline_only --llm {llm} --benchmark bbq.{bias_type} --eval_only --capability selfdiagnosis --lr {lr} --diagnose_type identify_stereotype ")

        for random_seed in random_seeds:
            # situation-statement
            os.system(f"python -u run_experiment.py --llm {llm} --benchmark bbq.{bias_type} --seed {random_seed} --num_train_epochs {epochs} --epoch_wise_eval  --batch_size 32 --discourse_construction situation-statement --capability selfdiagnosis --lr {lr}")
            # statement
            os.system(f"python -u run_experiment.py --llm {llm} --benchmark bbq.{bias_type} --seed {random_seed} --num_train_epochs {epochs} --epoch_wise_eval  --batch_size 32 --discourse_construction statement --capability selfdiagnosis --lr {lr}")
            # situation
            os.system(f"python -u run_experiment.py --llm {llm} --benchmark bbq.{bias_type} --seed {random_seed} --num_train_epochs {epochs} --epoch_wise_eval  --batch_size 32 --discourse_construction situation --capability selfdiagnosis --lr {lr}")
            


        # section5: cross test for sc and sd
        for random_seed in random_seeds:
            # - situation-action1-action2groundTruth
            os.system(f"python -u run_experiment.py --llm {llm} --benchmark bbq.{bias_type} --seed {random_seed} --num_train_epochs {epochs} --epoch_wise_eval  --batch_size 32 --discourse_construction situation-action1-action2groundTruth --cross_capability_evaluation --lr {lr}")

            # - two diagnosis type (origin and degroup)
            os.system(f"python -u run_experiment.py --llm {llm} --benchmark bbq.{bias_type} --seed {random_seed} --num_train_epochs {epochs} --epoch_wise_eval  --batch_size 32 --discourse_construction situation-action1-action2groundTruth --cross_capability_evaluation --lr {lr} --diagnosis_wo_group_double_evaluation")

            os.system(f"python -u run_experiment.py --llm {llm} --benchmark bbq.{bias_type} --seed {random_seed} --num_train_epochs {epochs} --epoch_wise_eval  --batch_size 32 --discourse_construction situation-action1-action2fair --cross_capability_evaluation --lr {lr} --diagnosis_wo_group_double_evaluation")

            # action2groundTruth
            os.system(f"python -u run_experiment.py --llm {llm} --benchmark bbq.{bias_type} --seed {random_seed} --num_train_epochs {epochs} --epoch_wise_eval  --batch_size 32 --discourse_construction action2groundTruth --cross_capability_evaluation --lr {lr}")
        
