from math import comb
import os
import sys
import json
import itertools
from lm_pipeline import lm_pipeline
from logger import ExperimentsLogger
from utils import create_fingerprint, hash_fingerprint
from config_parser_values import CONSTRAINT_TYPES

dict_values = list(CONSTRAINT_TYPES.keys())
exp_config = os.path.join(os.getcwd(),"tmp_cs.json")

def load_experiments_config(config_path):
    with open(config_path, 'r') as in_f:
        content = json.load(in_f)
    return content

def create_config_dict(combination, order_values):
    if len(dict_values) != len(combination):
        raise Exception("Invalid input configuration, please make sure all the necessary parameters are present and correctly named")
    
    final_dict = {}
    for real_name, value in zip(order_values, combination):
        final_dict[real_name] = value
    return final_dict

def run_experiments(config_path, exp_name):
    exp_logger = ExperimentsLogger(os.getcwd(),exp_name)
    content = load_experiments_config(config_path)
    order_values = list(content.keys())

    all_permutations = list(itertools.product(*list(content.values())))

    for combination in all_permutations:
        # create characteristic fingerprint
        fingerprint = create_fingerprint(combination)
        
        # create hash
        hash_fp = hash_fingerprint(' '.join(fingerprint))
        hash_hex = hash_fp.hexdigest()
        
        # add hash to the info
        fingerprint.append(hash_hex)
        
        current_exp = create_config_dict(combination, order_values)
        current_exp["fingerprint"] = hash_hex
        
        # always log experiments
        exp_logger.log_experiment(current_exp)

        # pipeline result
        log_result = lm_pipeline(current_exp, hash_hex)

        # log experiment if a new one was carried
        if not log_result:
            sys.stdout.write("Already carried out experiment with these parameters. Skipping...\n\n")
        break

if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.stderr.write("Invalid number of parameters.\nMake sure to call the script as python experiments_runner.py [CONFIG PATH] [EXPERIMENTS FILENAME]\n")
        sys.exit(1)
    
    config = sys.argv[1]
    
    if not os.path.exists(config):
        sys.stderr.write("The given configuration path {} does not exist\n".format(config))
        sys.exit(1)
    
    exp_filename = sys.argv[2]
    run_experiments(config, exp_filename)
    
