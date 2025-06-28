# SelfcorrectionHeuristics

In this anonymous repository, we show (1) a pdf file of additional experiments to further demonstrate our findings and (2) the dataset we used in our paper.

- Please refer to **EMNLP25_Rebuttal4ShallowSelfCorr.pdf** for the additional experiments we conducted to verify our findings. The additional experiments contains three more models, Phi-3.5-mini-instruct (3.8B), Llama-3-8B-Instruct, and Mistral-7B-Instruct-v0.3.

- Please refer to **dataset** folder for the dataset we used in our paper. Each json file in *dataset* contains the meta data we use either for fine-tuning or evaluation. Each `.train.json` file contains all components we mentioned in our paper for discourse consturctions (e.g. statement, action) as well as original information of BBQ dataset (e.g. context, label). Each `.test.json` file contains the original information of BBQ dataset (e.g. context, label) for evaluation.
    - Attributes:
        - context: the context of the BBQ dataset
        - question: the question of the BBQ dataset
        - (a),(b),(c): the answer options
        - label: the label of the BBQ dataset
        - biased_group: the biased social group of this sample
        - ​​opposite_group​​: another social group
        ​- ​question_polarity​: the ​question_polarity​ of the BBQ dataset
        - ​context_split_identify_str​​: the str to identify the specific situation of this sample within the dataset
        - ​statement: the *statement* component
        - ​​subaction: the *subaction* component
        - action: the *action* component
        - ​statement_situated​​: the *statement_situated* component which shows a situated version of *statement*
