from os import getcwd, path

# values that must be provided in the config file
REQUIRED_VALUES = [
    "source_path",          # path to the source file
    "source_model",         # path to the original model
    "target_language",      # ISO code of target language
    "dictionary",           # Phonexia language dictionary 
    "evaluation_path",      # path to where evaluation datasets are stored
    "evaluation_datasets"   # list of datasets, uses stm transcripts by default
]

# values that do not have to be provided
DEFAULT_VALUES = {
    "evaluation" : False,           # True / False (not evaluating at all)  
    "create_ngrams" : True,        # True (stt.phxstm) / False (kws.phxstm)
    "trim_input" : True,            # remove spelling and bracketed (foreign) words
    "lid_threshold" : 0.9,          # threshold for language identification
    "order_ngram" : 3,              # order of ngram
    "k_ngrams" : 200,               # k top ngrams
    "ngrams_percentage" : None,     # percentage of top k ngrams
    "doc_default" : 20,
    "doc_limit" : 50,
    "ppl_threshold" : 1200,
    "len_penalty" : 20,             # penalise shorter ngrams
    "web_tags" : ['p','span'],
    "is_standard_lang" : True,      # uses the standard charset of the source file
    "search_preference" : "google",
    "output_path" : path.join(getcwd(),"results"),
    "statistics_path" : path.join(getcwd(),"statistics"),
    "download_path" : path.join(getcwd(), "download"),
    "ppl_path" : path.join(getcwd(), "ppl"),
    "evaluation_path" : "/home/sabi/Desktop/datasets-lfs",
    "use_window_par_filter" : False,
    "use_doc_filter" : False,
    "filter_type" : "avg",
    "window_len" : None,
    "filter_threshold" : -4,
    "timeout" : 90,
    "evaluation_datasets" : []
}

# used for simpler constraint checking
CONSTRAINT_TYPES = {"source_path" : "path",
                    "source_model" : "path",
                    "create_ngrams" : "bool_val",
                    "target_language" : "lang",
                    "dictionary" : "path",
                    "trim_input" : "bool_val",
                    "evaluation" : "bool_val",
                    "evaluation_path" : "path",
                    "evaluation_datasets" : "eval_datasets",
                    "lid_threshold" : "zero_one_range",
                    "order_ngram" : "positive_integer",
                    "k_ngrams" : "positive_integer",
                    "ngrams_percentage" : "zero_one_range",
                    "doc_default" : "positive_integer",
                    "doc_limit" : "positive_integer",
                    "ppl_threshold" : "positive_float",
                    "len_penalty" : "positive_integer",
                    "web_tags" : "web_tags",
                    "is_standard_lang" : "bool_val",
                    "search_preference" : "search_pref",
                    "use_window_par_filter" : "bool_val",
                    "use_doc_filter" : "bool_val",
                    "filter_type" : "filter",
                    "window_len" : "positive_integer",
                    "filter_threshold" : "negative_float",
                    "output_path" : "path",
                    "statistics_path" : "path",
                    "download_path" : "path",
                    "ppl_path" : "path",
                    "timeout" : "positive_integer"
}

all_hyperparameters = list(CONSTRAINT_TYPES.keys())
all_hyperparameters.sort()