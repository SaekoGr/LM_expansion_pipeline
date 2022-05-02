from os import path, system, remove
import sys
import subprocess
from logger import LoggerBase
import utils

PPL_IDX = 10
PPL1_IDX = 12

# python interface for simple creation of the language model with SRILM toolkit
class LanguageModelApi():
    def __init__(self, source_file, phonexia_model, output_path, ngrams, fingerprint, ppl_path, dictionary):
        self._source_file = source_file
        self._phonexia_model = phonexia_model
        self._output_path = output_path
        self._ngrams = str(ngrams)
        self._ppl_path = ppl_path
        self.dict_path = dictionary
        
        # hard path
        self.lm_stm_corpora_path = path.join(self._output_path, 'stm_corpora')
        self.lm_stm_model_path = path.join(self._output_path, 'lm_stm.kn.gz')
        self.doc_corpora = path.join(self._output_path, 'document_corpora')
        
        
        #self.new_model = path.join(output_path, 'updated_lm.kn.gz')
        
        # soft path
        self.corpora = path.join(output_path, '_'.join(['corpora',str(fingerprint)]))
        self.final_lm_path = path.join(self._output_path, '_'.join(['model',str(fingerprint)]) + '.kn.gz')
        self.mixed_model = path.join(self._output_path, '_'.join(['mixed','model',str(fingerprint)]) + '.kn.gz')
        print(self.corpora)
        print(self.final_lm_path)
        print(self.mixed_model)
        
        # create ppl mapper logger file
        self.ppl_mapper = LoggerBase(output_path, "ppl_mapper_" + fingerprint)
        
        # remove the corpora
        #self._remove_corpora(self.corpora)
        
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
    
    def evaluate_level(self, lm, corpora, ppl_filename, level):
        command = ' '.join(['ngram','-order 1','-lm',lm,'-ppl',corpora,'-debug',str(level),'>', ppl_filename])
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
        print("MIXING TWO MODELS")
        print(' '.join(command))
        system(' '.join(command))
        
    def _get_best_lambdas(self, mix_path):
        print("\nGETTING BEST LAMBDAS")
        command = ["grep 'best lambda'", mix_path,"| sed 's|.*(||; s|).*||;'"]
        lambdas = subprocess.check_output(' '.join(command), shell=True)
        lambdas = lambdas.decode('utf-8')
        lambdas = lambdas.strip('\n').split(' ')
        
        # the length of the lambdas should be 2 (mixing 2 models)
        if len(lambdas) != 2:
            raise Exception("Runtime error when mixing lambdas")
        
        print(lambdas)
        phx_lambda = lambdas[0]
        web_lambda = lambdas[1]
        
        print(phx_lambda, web_lambda)
        
        return phx_lambda, web_lambda
    
    def filter_window(self, clean_document):
        print("WINDOW FILTERING")
        print(clean_document)
        corpora_path = path.join(self._output_path, 'single_line')
        ppl_path = path.join(self._ppl_path, "single_line_ppl")
        print(corpora_path)
        
        for line in clean_document:
            print(line)
            self.write_corpora([line], corpora_path, append=False)
            result = self._parse_perplexity_results(self.evaluate_level(self._phonexia_model, corpora_path, ppl_path, 2))
            print(result)
            break
        
        return clean_document
    
    def _single_mixing_weight(self, model_path, corpus, ppl_lambdas_path):
        command = ['ngram -lm',model_path,'-ppl',corpus,'-debug 2 | tee', ppl_lambdas_path,'| tail -n2']
        print(' '.join(command))
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
                
    def _remove_corpora(self, file_path):
        if path.exists(file_path):
            remove(file_path)
    
    def _create_lm(self, corpora_path, lm_path, smoothing=True):
        if smoothing:
            lm_command = ['ngram-count','-text',corpora_path,'-order', self._ngrams,'-lm', lm_path, '> /dev/null 2>&1'] 
        else:
            lm_command = ['ngram-count','-text',corpora_path,'-order', self._ngrams,'-kndiscount','-interpolate',
                          '-vocab', self.dict_path,'-limit-vocab',
                          '-lm', lm_path, '> /dev/null 2>&1'] 
        
        system(' '.join(lm_command))