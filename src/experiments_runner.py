from math import comb
import os
import sys
import json
import itertools
from lm_pipeline import lm_pipeline
from logger import ExperimentsLogger
from utils import create_fingerprint, hash_fingerprint, read_input, remove_chosen
import hashlib
from config_parser_values import CONSTRAINT_TYPES

dict_values = list(CONSTRAINT_TYPES.keys())
exp_config = os.path.join(os.getcwd(),"experiments_config_zh.json")

def load_experiments_config(config_path):
    with open(config_path, 'r') as in_f:
        content = json.load(in_f)
    return content

### TODO TODO MAKE THIS DYNAMIC
def create_config_dict(combination):
    if len(dict_values) != len(combination):
        raise Exception("Invalid input configuration, please make sure all necessary parameters are present in the correct order")
    
    final_dict = {}
    for real_name, value in zip(dict_values, combination):
        print(real_name, value)
        final_dict[real_name] = value
        
    print(final_dict)
    return final_dict

def run_experiments():
    exp_logger = ExperimentsLogger(os.getcwd(),'experiments_mandarin.tsv')
    content = load_experiments_config(exp_config)

    all_permutations = list(itertools.product(*list(content.values())))

    for combination in all_permutations:
        print("\n\n" + "="*20)
        # create characteristic fingerprint
        fingerprint = create_fingerprint(combination)
        
        # create hash
        hash_fp = hash_fingerprint(' '.join(fingerprint))
        hash_hex = hash_fp.hexdigest()
        
        # add hash to the info
        fingerprint.append(hash_hex)
        
        current_exp = create_config_dict(combination)
        current_exp["fingerprint"] = hash_hex
        
        # always log experiments
        exp_logger.log_experiment(current_exp)

        # pipeline result
        log_result = lm_pipeline(current_exp, hash_hex)

        # log experiment if a new one was carried
        if not log_result:
            sys.stdout.write("Already carried out experiment with these parameters. Skipping...\n\n")


if __name__ == "__main__":
    run_experiments()
    
