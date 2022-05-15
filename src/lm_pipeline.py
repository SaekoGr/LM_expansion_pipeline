from config_parser import ConfigParser
from document_retriever import DocumentRetriever
from logger import EvaluationLogger, StatisticsLogger
from language_identification import LanguageIdentification
from language_model_interface import LanguageModelApi
from text_cleaner import TextCleaner
from ngrams_provider import NgramsProvider
import utils
from os import path, environ
from sys import exit
import time
from datetime import datetime
import multiprocessing


# sample configuration for ease of testing
SAMPLE_CONFIG = {
    "source_path" : "/home/sabi/Desktop/datasets-lfs/CS_CZ_SKODAv1/stt.phxstm",     # path to the source file
    "source_model" : "/home/sabi/Desktop/DP_code/LM_sample/LM.arpa.gz",             # path to the original model
    "create_ngrams" : True,                                                         # True (stt.phxstm) / False (kws.phxstm)
    "target_language" : "CS",                                                       # ISO code of target language
    "evaluation" : True,
    "evaluation_path" : "/home/sabi/Desktop/datasets-lfs",
    "evaluation_datasets" : ["CS_CZ_DEVRIESv1/stt.phxstm","CS_CZ_GENERALIv1/stt.phxstm","CS_CZ_INNOGYv1/stt.phxstm","CS_CZ_KOOPERATIVAv1/stt.phxstm","CS_CZ_SKODAv1/stt.phxstm","CS_CZ_TMOBILEDEMOv1/stt.phxstm"]
}

    
class WebCrawler:
    def __init__(self, parameters, fingerprint=None, preferred_type=None):
        self.parameters = parameters
        self.default_cnt = 20
        self.preferred_type = preferred_type
        
        # prepare fingerprint, either used the one provided or calculate a fresh one
        self._prepare_fingerprint(fingerprint)
        #print(self.fingerprint)
        
        # initialize the text cleaner
        self.text_cleaner = TextCleaner(is_standard_lang=parameters.is_standard_lang)
        
        # create charset constraint
        self._estimate_charset()
        self.text_cleaner.set_charset(self.charset_constraint)
        
        # try to find existing logger file
        stats_logger_path = path.join(parameters.statistics_path, '_'.join(['statistics',str(fingerprint)]) + '.tsv')
        self.already_processed = self._search_logger_file(stats_logger_path)
        
        # create instance for every class
        self.lid = LanguageIdentification(parameters.target_language, parameters.lid_threshold)
        self.lm_api = LanguageModelApi(parameters.source_path, parameters.source_model, parameters.output_path, parameters.order_ngram, 
                                       fingerprint, parameters.ppl_path, parameters.dictionary, (parameters.use_window_par_filter or parameters.use_doc_filter), 
                                       parameters.window_len, parameters.filter_type, parameters.filter_threshold)
        self.document_retriever = DocumentRetriever(parameters.search_preference, parameters.download_path, parameters.doc_limit, parameters.doc_default, 
                                                    parameters.web_tags, parameters.target_language)
        self.eval_logger = EvaluationLogger(parameters.statistics_path, '_'.join(['evaluation',str(fingerprint)]) + '.tsv')
        self.stats_logger = StatisticsLogger(parameters.statistics_path, '_'.join(['statistics',str(fingerprint)]) + '.tsv')

        # set language for text cleaner after LID checked it
        self.text_cleaner.set_lang(parameters.target_language.lower())

        # create LM from the source file
        content = self._read_source_file()
        self.lm_api.create_source_lm(content)
        
        self.ngrams_provider = NgramsProvider(content, self.parameters, self.already_processed)
        
        if self.parameters.evaluation is True:
            # make sure "srilm" is in the path variable
            if "srilm" not in environ["PATH"]:
                print("Please make sure to install SRILM and include it in the PATH environment variable")
                exit(1)
        
    def _search_logger_file(self, logger_path):
        if path.exists(logger_path):
            with open(logger_path) as in_f:
                _ = in_f.readline()
                content = [line.strip().split('\t')[0] for line in in_f.readlines()]
                
                if len(content) > 0:
                    lastly_processed = content[-1]
                else:
                    lastly_processed = None
                    
                content = list(set(content))
                
                # remove the last one so it can be re-searched
                if lastly_processed in content:
                    content.remove(lastly_processed)
                return content
        else:
            return []

    def _prepare_fingerprint(self, initial_fingerprint):
        if initial_fingerprint is None:
            fingerprint = utils.create_fingerprint(self.parameters.values())
            # create hash
            hash_fp = utils.hash_fingerprint(' '.join(fingerprint))
            self.fingerprint = hash_fp.hexdigest()
        else:
            self.fingerprint = initial_fingerprint
        
    def _estimate_charset(self):
        """Estimate expected charset for the web documents"""
        if self.parameters.is_standard_lang:
            # obtain the source file
            content = self._read_source_file()
            charset_dictionary = utils.graphemes_occurance_cnt(content)
            self.charset_constraint = self._charset_add_numbers(list(charset_dictionary.keys()))
        else:
            self.charset_constraint = None
            
    def _charset_add_numbers(self, charset):
        """Include numerals for the charset constraint"""
        numbers = "0123456789"
        
        for num in numbers:
            charset.append(num)
        
        return list(set(charset))
        
    def _read_source_file(self):
        """Read the source file, obtain text and trim if necessary"""
        content = utils.read_input(self.parameters.source_path, self.preferred_type)
        content = utils.remove_chosen(content)
        
        # trimming involves the removal of bracketed words and spelling underscore
        if(self.parameters.trim_input):
            content = self.text_cleaner.trim_input(content)
            
        return content
                
    def _single_search(self, link, term):
        link_fingerprint = self.document_retriever.encode_url(link)

        # obtain the raw document
        raw_document = self.document_retriever.get_document_by_url(link)
        
        # clean the document
        clean_document = self.text_cleaner.clean_document(raw_document)
        print(clean_document)
        
        # language identification
        lid_result = self.lid.is_target_lang(' '.join(clean_document))
        
        current_time = datetime.now()
        print(term, link, str(len(''.join(raw_document))), str(len(''.join(clean_document))), current_time.strftime("%H:%M:%S"))
        
        # ppl results
        ppl_result = self.lm_api.evaluate_ppl_doc(clean_document, self.fingerprint, link_fingerprint, link, term)
        
        if self.parameters.use_doc_filter:
            clean_document = self.lm_api.filter_document(clean_document)
        
        if self.parameters.use_window_par_filter:
            print("PARAM FIL")
            clean_document = self.lm_api.filter_window(clean_document)

        # access and log results
        resulting_corpora = self._assess_results(term, link, raw_document, clean_document, lid_result, ppl_result)
        
        # write down the corpora
        self.lm_api.write_corpora(resulting_corpora, self.lm_api.corpora, append=True)
        
    # assesses results from single link exploration, writes the results to stats file
    def _assess_results(self, term, link, raw_document, clean_document, lid, ppl):
        raw_len = len(''.join(raw_document))
        lid_res = "YES" if lid else "NO"
        ppl_binary_res = True if ppl > self.parameters.ppl_threshold else False
        clean_len = len(''.join(clean_document)) if lid and ppl_binary_res else 0
        
        if raw_len == 0:
            percentage = 0
        else:
            percentage = round(clean_len / raw_len * 100, 2)
        
        self.stats_logger.log_search_result(term, link, raw_len, lid_res, ppl, clean_len, percentage)
        
        if ppl_binary_res and lid:
            return clean_document
        else:
            return []

    # evaluate with every evaluation dataset
    def _evaluate_model(self, model):
        """Evaluates model with all evaluation datasets"""
        self._preprocess_eval_datasets()
        
        for dataset in self.parameters.evaluation_datasets:
            out_dataset_path = path.join(self.parameters.output_path, dataset.split('/')[0] + '.eval')
            
            result = self.lm_api.evaluate(model, out_dataset_path, 'experiment_' + str(self.fingerprint))
            
            self.eval_logger.log_eval_result(model, out_dataset_path, result)
        
    def _preprocess_eval_datasets(self):
        # iterate over all available evaluation datasets and extract them
        for dataset in self.parameters.evaluation_datasets:
            # create input dataset
            dataset_path = path.join(self.parameters.evaluation_path, dataset)
            # path for transcriptions only
            out_dataset_path = path.join(self.parameters.output_path, dataset.split('/')[0] + '.eval')
            
            if path.exists(out_dataset_path):
                continue
            
            # read file and save the transcriptions
            content = utils.read_input(dataset_path, self.preferred_type)
            self.lm_api.write_corpora(content, out_dataset_path, append=False)


    def search_web(self):
        # get the chosen ngrams
        terms = self.ngrams_provider.get_top_ngrams(self.parameters.k_ngrams, self.parameters.ngrams_percentage)

        # iterate over all the terms
        for term in terms:
            # convert to string
            if not isinstance(term,str):
                term = ' '.join(term)
            
            # expected count of documents for given term
            if self.parameters.create_ngrams:
                expected_cnt = self.ngrams_provider.get_expected_count(term)
            else:
                expected_cnt = self.default_cnt
            
            
            # obtain all links
            manager = multiprocessing.Manager()
            found_links = manager.dict()
            
            link_process = multiprocessing.Process(target=self.document_retriever.search_term, args=(term, expected_cnt, found_links))
            link_process.start()
            link_process.join(timeout=self.parameters.timeout*2)
            link_process.terminate()

            if link_process.exitcode is None:
                #print("Did not get links for " + str(term))
                continue

            links = found_links["links"]
            
            print("GOT LINKS")
            print(links)
            print(term)
            
            
            # iterate over all the links
            for link in links:
                single_search = multiprocessing.Process(target=self._single_search, args=(link, term, ))
                single_search.start()
                single_search.join(timeout=self.parameters.timeout) #500
                single_search.terminate()
                
                if single_search.exitcode is None:
                    #print("TIMEOUTED:\t" +  link)
                    pass
                
            exit(1)

    def mix_models(self):
        # create LM from the source file
        content = self._read_source_file()
        self.lm_api.create_source_lm(content)
        
        # create lm model from the downloaded corpora
        self.lm_api._create_webcorpora_lm()
        
        # estimate mixing weights for both models
        self.lm_api.mix_models()


    def already_done(self):
        return self.lm_api.already_done()
    
    def evaluate(self):
        if self.parameters.evaluation:
            self._evaluate_model(self.parameters.source_model)
            self._evaluate_model(self.lm_api.mixed_model)
            
        #self.lm_api.remove_models()
            
def lm_pipeline(config, fingerprint=None, preferred_type=None):
    # create parameters variable
    parameters = ConfigParser(config)
    pipeline = WebCrawler(parameters, fingerprint, preferred_type)


    if pipeline.already_done():
        return False
    pipeline.search_web()
    #pipeline.mix_models()
    #pipeline.evaluate()
    return True

