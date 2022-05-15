from os import path, system, remove
from copy import deepcopy
import sys
import re
import subprocess
import numpy as np
import time
from logger import LoggerBase
import utils

PPL_IDX = 10
PPL1_IDX = 12

# python interface for simple creation of the language model with SRILM toolkit
class LanguageModelApi():
    def __init__(self, source_file, phonexia_model, output_path, ngrams, fingerprint, ppl_path, dictionary, advanced_filtering = False, window_len = None, filter_type = "avg", filter_threshold = -4.0):
        self._source_file = source_file
        self._phonexia_model = phonexia_model
        self._output_path = output_path
        self._ngrams = str(ngrams)
        self._ppl_path = ppl_path
        self.dict_path = dictionary
        self.window_len = window_len
        self.filter_type = filter_type
        self.filter_threshold = filter_threshold
        self.unigram_dct = None
        
        if advanced_filtering:
            self._init_unigram_dct()
        
        # hard path
        self.lm_stm_corpora_path = path.join(self._output_path, 'stm_corpora')
        self.lm_stm_model_path = path.join(self._output_path, 'lm_stm.kn.gz')
        self.doc_corpora = path.join(self._output_path, 'document_corpora')
        
        # soft path
        self.corpora = path.join(output_path, '_'.join(['corpora',str(fingerprint)]))
        self.final_lm_path = path.join(self._output_path, '_'.join(['model',str(fingerprint)]) + '.kn.gz')
        self.mixed_model = path.join(self._output_path, '_'.join(['mixed','model',str(fingerprint)]) + '.kn.gz')
        
        # create ppl mapper logger file
        self.ppl_mapper = LoggerBase(output_path, "ppl_mapper_" + fingerprint)
        
    def __del__(self):
        pass
        #self._remove_corpora(self.doc_corpora)
        
    def evaluate_ppl_doc(self, corpora, exp_fingerprint, link_fingerprint, link, term):
        # write down the corpora
        self.write_corpora(corpora, self.doc_corpora, append=False)
        # create ppl filename
        ppl_filename = path.join(self._ppl_path, '_'.join([exp_fingerprint, link_fingerprint]))
        # evaluate
        eval_result = self.evaluate(self.lm_stm_model_path, self.doc_corpora, ppl_filename)
        result = self._parse_perplexity_results(eval_result)
        
        if len(result) > 10:
            result = float(result[PPL_IDX])
        else:
            result = float('inf')
            
        self.ppl_mapper.log_list_as_line([link_fingerprint, link, term, str(result)]) 
        return result
    
    def evaluate(self, lm, corpora, ppl_filename):
        command = ' '.join(['ngram','-lm',lm,'-ppl',corpora,'>',ppl_filename])
        system(command)
        
        with open(ppl_filename,'r') as in_f:
            result = in_f.readlines()
        result = ''.join(result)
        return result
    
    def _parse_perplexity_results(self, results):
        """Parse results from measuring perplexity with ngram ppl"""
        results = results.strip('\n')
        results = results.strip('\n0')
        results = results.split(' ')
        results = results[2:]
        return results
    
    def _create_webcorpora_lm(self):
        self._create_lm(self.corpora, self.final_lm_path)
        
    def already_done(self):
        # the corpora lm was created
        if path.exists(self.final_lm_path):
            if path.exists(self.mixed_model):
                return True
            else:
                sys.stdout.write("\nWARNING! Mixed model {} does not exist".format(self.mixed_model))
        else:
            return False
        
    # all weights will be estimated and stored in the output folder
    def mix_models(self):
        # estimate weights for phonexia model
        phx_model_name = self._phonexia_model.split('/')[-1]
        phx_ppl_path = path.join(self._output_path, phx_model_name + '.ppl_for_lambdas')
        
        web_model_name = self.final_lm_path.split('/')[-1]
        web_ppl_path = path.join(self._output_path, web_model_name + '.ppl_for_lambdas')
        
        best_mix_path = path.join(self._output_path, 'best_mix.log')
        
        # estimate mixing weight lambdas for both models
        self._single_mixing_weight(self._phonexia_model, self.lm_stm_corpora_path, phx_ppl_path)
        self._single_mixing_weight(self.final_lm_path, self.lm_stm_corpora_path, web_ppl_path)

        # compute the best mixing weights
        command = ['compute-best-mix', phx_ppl_path, web_ppl_path, '| tee', best_mix_path]
        system(' '.join(command))
        
        # estimate the lambdas
        phx_lambda, web_lambda = self._get_best_lambdas(best_mix_path)
        
        # mix with chosen lambdas
        self._mix_two_models(self._phonexia_model, self.final_lm_path, phx_lambda, self.mixed_model)
        
    def _mix_two_models(self, primary_path, secondary_path, primary_lambda, output_lm):
        command = ['ngram -order',self._ngrams,'-lm',primary_path,'-lambda',primary_lambda,'-mix-lm',
                   secondary_path,'-unk -map-unk "<UNK>"','-write-lm',output_lm,'| tee interpolation_command']
        system(' '.join(command))
        
    def _get_best_lambdas(self, mix_path):
        command = ["grep 'best lambda'", mix_path,"| sed 's|.*(||; s|).*||;'"]
        lambdas = subprocess.check_output(' '.join(command), shell=True)
        lambdas = lambdas.decode('utf-8')
        lambdas = lambdas.strip('\n').split(' ')
        
        # the length of the lambdas should be 2 (mixing 2 models)
        if len(lambdas) != 2:
            raise Exception("Runtime error when mixing lambdas")

        phx_lambda = lambdas[0]
        web_lambda = lambdas[1]
        
        return phx_lambda, web_lambda
    
    def _parse_unigram_probabilities(self, file):
        with open(file, 'r') as in_f:
            content = in_f.readlines()
            content = [line.strip('\n') for line in content]
            content = [line for line in content if line and "= [1gram]" in line]
            
        final_dict = {}
        for line in content:
            key = re.findall(r'\tp\( (.+?) \|',line)[0]
            value = re.findall(r'\[ (.+?) \]$',line)[0]
            final_dict[key] = float(value)

        return final_dict
    
    def _chop_to_windows(self, line):
        line = line.split(' ')
        len_line = len(line)
        final_windows = []
        
        for i in range(0, len_line, self.window_len):
            if i + self.window_len >= len_line:
                final_windows += [line[i:]]
            else:
                final_windows += [line[i:i+self.window_len]]
        return final_windows
    
    def _create_windows(self, all_windows):
        scored_windows = [None]*len(all_windows)
        j = 0
        
        for window in all_windows:
            current_score = [None]*len(window)
            
            for i in range(len(window)):
                if window[i] in self.unigram_keys:
                    current_score[i] = self.unigram_dct[window[i]]
                else:
                    current_score[i] = self.unigram_dct["<unk>"]
                    
            scored_windows[j] = np.array(current_score)
            j += 1
        
        return all_windows, scored_windows
    
    def _evaluate_windows(self, segments, scored_segments):
        passed_segments = []

        # iterate over all segments
        for segment, segment_score in zip(segments, scored_segments):
            
            # use chosen filter type
            if self.filter_type == "avg":
                calculated_score = np.mean(segment_score)
            elif self.filter_type == "median":
                calculated_score = np.median(segment_score)
            
            # passed through the threshold
            if calculated_score > self.filter_threshold:
                passed_segments.append(' '.join(segment))

        return passed_segments
    
    # load unigram dictionary
    def _init_unigram_dct(self):
        unzipped = self._phonexia_model.replace('.gz','')
        self.unigram_dct = {}
        
        if not path.exists(unzipped):
            statement = ' '.join(["gunzip -c", self._phonexia_model,">",unzipped])
            system(statement)
            
        with open(unzipped,'r') as in_f:
            # move until the \1-ngrams:
            while True:
                line = in_f.readline()
                if "-grams:" in line:
                    break
                
            while True: 
                line = in_f.readline()
                line = line.strip('\n')
                # end of \1-ngrams
                if len(line) == 0:
                    break
                
                line = line.split('\t')
                self.unigram_dct[line[1]] = float(line[0])
                
        self.unigram_dct["<unk>"] = float('-inf')
        self.unigram_keys = list(self.unigram_dct.keys())
        
    def filter_document(self, clean_document):
        original_document = deepcopy(clean_document)

        clean_document = ' '.join(clean_document)
        _, scored_windows = self._create_windows([clean_document.split(' ')])
        
        if self.filter_type == "avg":
            score = np.mean(scored_windows[0])
        elif self.filter_type == "median" or self.filter_type is None:
            score = np.median(scored_windows[0])

        # passed through the threshold
        if score > self.filter_threshold:
            return original_document
        else:
            return []
    
    def filter_window(self, clean_document):
        final_segments = []
        
        for line in clean_document:            
            if self.window_len is None:
                preprocessed_windows = [line.split(' ')]
            else:
                preprocessed_windows = self._chop_to_windows(line)
            all_windows, scored_windows = self._create_windows(preprocessed_windows)
            approved_segments = self._evaluate_windows(all_windows, scored_windows)
            
            final_segments += approved_segments

        return final_segments
    
    def _single_mixing_weight(self, model_path, corpus, ppl_lambdas_path):
        command = ['ngram -lm',model_path,'-ppl',corpus,'-debug 2 | tee', ppl_lambdas_path,'| tail -n2']
        system(' '.join(command))
    
    def create_source_lm(self, content):
        # write down the corpora
        self.write_corpora(content, self.lm_stm_corpora_path, append=False)
        
        # create the language model
        self._create_lm(self.lm_stm_corpora_path, self.lm_stm_model_path)
    
    def write_corpora(self, corpora, path, append=False):
        """Write down the corpora"""
        mode = 'a' if append else 'w'
        
        corpora = list(set(corpora))
            
        with open(path, mode) as out_f:
            for line in corpora:
                line = ' '.join(line.split())
                out_f.write(line + '\n')
                
    def remove_models(self):
        self._remove_corpora(self.final_lm_path)
        self._remove_corpora(self.mixed_model)
                
    def _remove_corpora(self, file_path):
        if path.exists(file_path):
            remove(file_path)
    
    def _create_lm(self, corpora_path, lm_path, smoothing=True):
        if smoothing:
            lm_command = ['ngram-count','-text',corpora_path,'-order', self._ngrams,'-kndiscount','-interpolate',
                          '-vocab', self.dict_path,'-limit-vocab',
                          '-lm', lm_path, '> /dev/null 2>&1'] 
        else:
            lm_command = ['ngram-count','-text',corpora_path,'-order', self._ngrams,'-lm', lm_path, '> /dev/null 2>&1']
            
            
        
        system(' '.join(lm_command))