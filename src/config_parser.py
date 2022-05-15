from config_parser_values import REQUIRED_VALUES, DEFAULT_VALUES, CONSTRAINT_TYPES
from os import path, makedirs

class ConfigParser():
    def __init__(self, config):
        # check for existance of config file first TODO
        self._load_config_values(config)
            
    def _config_checker(self):
        """Check all values for constraint violations"""
        
        for key, val in self.__dict__.items():
            constraint = CONSTRAINT_TYPES[key]
                        
            #print(key, val, constraint)
            if constraint == "path":
                # create folder for output
                if key in ["output_path", "statistics_path", "download_path", "ppl_path"]:
                    if not path.exists(val):
                        makedirs(val)
                    
                # don't check evaluation parameters if evaluation isn't required
                if self.evaluation is False and 'evaluation_' in key:
                    continue
                    
                # check existence of path
                if not path.exists(val):
                    raise Exception("{} does not exist and could not be created".format(val))
            elif constraint == "bool_val":
                if not isinstance(val, bool):
                    raise Exception("{} expected a boolean value, but {} was given".format(key, val))
            elif constraint == "positive_integer" or constraint == "positive_float":
                if not isinstance(val, (int,float)) or int(val) <= 0:
                    if key == "window_len" and val is None:
                        pass
                    else:
                        raise Exception("{} expected a positive integer value, but {} was given".format(key, val))
            elif constraint == "lang":
                if isinstance(val, str):
                    if len(val) != 2:
                        raise Exception("{} expected a 2-character language code string, but {} was given".format(key, val))
                else:
                    raise Exception("{} expected a 2-character language code string, but {} was given".format(key, val))
            elif constraint == "zero_one_range":
                if val is None or isinstance(val, (float, int)):
                    if key == "ngrams_percentage":
                        if val is not None:
                            if not (0 <= val <= 1):
                                raise Exception("{} expected a float value in <0,1> range or None, but {} was given".format(key, val))
                    else:
                        if val is None:
                            raise Exception("{} expected a float value in <0,1> range, but {} was given".format(key, val))

                        if not (0 <= val <= 1):
                            raise Exception("{} expected a float value in <0,1> range, but {} was given".format(key, val))
                else:
                    raise Exception("{} expected a float value in <0,1> range, but {} was given".format(key, val))
            elif constraint == "search_pref":
                if val.casefold() not in ["google", "bing"]:
                    raise Exception("{} expected a value of \"google\" or \"bing\", but {} was given".format(key, val))
            elif constraint == "filter":
                if val.casefold() not in ["median", "avg"]:
                    raise Exception("{} expected a value of \"median\" or \"avg\", but {} was given".format(key, val))
            elif constraint == "negative_float":
                if isinstance(val, (float, int)):
                    if float(val) >= 0:
                        raise Exception("{} expected a negative float value, but {} was given".format(key, val))
                else:
                    raise Exception("{} expected a negative float value, but {} was given".format(key, val))
            elif constraint == "eval_datasets" or constraint == "web_tags":
                if isinstance(val, list):
                    eval_types = [type(item) for item in val]
                    for single_type in eval_types:
                        if single_type != str:
                            raise Exception("{} expected a list of strings, but {} was given".format(key, val))
    
    def _load_single_value(self, config, value_name):
        """Load value from config, otherwise use default value"""
        if value_name in config.keys():
            return config[value_name]
        else:
            return DEFAULT_VALUES[value_name]
    
    def _load_config_values(self, config):
        #sys.stdout.write("Loading config files\n")

        # checks whether required values are present in config file
        config_values = config.keys()
        for req_val in REQUIRED_VALUES:
            if req_val not in config_values:
                raise Exception("Missing required value for {} in the config file".format(req_val))
            
        # load variables from config, explicitly retype to expected type
        # missing values are replaced with the default ones
        self.source_path = self._load_single_value(config, "source_path")
        self.source_model = self._load_single_value(config, "source_model")
        self.create_ngrams = self._load_single_value(config, "create_ngrams")
        self.target_language = self._load_single_value(config, "target_language")
        self.dictionary = self._load_single_value(config, "dictionary")
        self.trim_input = self._load_single_value(config, "trim_input")
        self.evaluation = self._load_single_value(config, "evaluation")
        self.evaluation_path = self._load_single_value(config, "evaluation_path")
        self.evaluation_datasets = self._load_single_value(config, "evaluation_datasets")
        self.lid_threshold = self._load_single_value(config, "lid_threshold")
        self.order_ngram = self._load_single_value(config, "order_ngram")
        self.k_ngrams = self._load_single_value(config, "k_ngrams")
        self.ngrams_percentage = self._load_single_value(config, "ngrams_percentage")
        self.doc_default = self._load_single_value(config, "doc_default")
        self.doc_limit = self._load_single_value(config, "doc_limit")
        self.ppl_threshold = self._load_single_value(config, "ppl_threshold")
        self.len_penalty = self._load_single_value(config, "len_penalty")
        self.web_tags = self._load_single_value(config, "web_tags")
        self.is_standard_lang = self._load_single_value(config, "is_standard_lang")
        self.timeout = self._load_single_value(config, "timeout")
        self.search_preference = self._load_single_value(config, "search_preference")
        self.use_window_par_filter = self._load_single_value(config, "use_window_par_filter")
        self.use_doc_filter = self._load_single_value(config, "use_doc_filter")
        self.filter_type = self._load_single_value(config, "filter_type")
        self.filter_threshold = self._load_single_value(config, "filter_threshold")
        self.window_len = self._load_single_value(config, "window_len")
        self.output_path = self._load_single_value(config, "output_path")
        self.statistics_path = self._load_single_value(config, "statistics_path")
        self.download_path = self._load_single_value(config, "download_path")
        self.ppl_path = self._load_single_value(config, "ppl_path")
   
        self._config_checker()