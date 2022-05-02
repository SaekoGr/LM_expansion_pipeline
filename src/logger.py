from os import path, stat
import varname

class LoggerBase:
    def __init__(self, output_path, output_file):
        self.output_path = output_path
        self.output_file = output_file
        self.absolute_path = path.join(output_path, output_file)
        self._delim = '\t'
        
        # choose correct mode    
        if not path.exists(self.absolute_path):
            newly_created = open(self.absolute_path, 'w')
            newly_created.close()
        
        self.mode = 'a'
            
        
    def log_line(self, line):
        with open(self.absolute_path, self.mode) as out_f:
            out_f.write(line + '\n')
            
    def log_list_as_line(self, line):
        with open(self.absolute_path, self.mode) as out_f:
            out_f.write((self._delim).join(line) + '\n')
    
    # does not include haeder
    def __del__(self):
        with open(self.absolute_path, 'r') as in_f:
            content = in_f.readlines()
            
        uniq_content = list(set(content))
        
        with open(self.absolute_path, 'w') as out_f:
            for exp in uniq_content:
                out_f.write(exp)
        
class ExperimentsLogger(LoggerBase):
    def __init__(self, output_path, output_file):
        super().__init__(output_path, output_file)
        self._header = ["source_path","source_model","create_ngrams","target_language","dictionary","trim_input","evaluation",
            "evaluation_path","evaluation_datasets","lid_threshold","order_ngram","k_ngrams","ngrams_percentage",
            "doc_default","doc_limit","ppl_threshold","len_penalty","web_tags","is_standard_lang","search_preference",
            "use_window","window_len","output_path","statistics_path","download_path","ppl_path","timeout","fingerprint"]
        
        if stat(self.absolute_path).st_size == 0:
            self.prepare_header()
        
    def prepare_header(self):
        self.log_line('\t'.join(self._header))
        
    def log_experiment(self, content):
        result = []
        
        all_keys = content.keys()
        for column in self._header:
            if column in all_keys:
                found_val = content[column]
                
                if found_val is None:
                    found_val = "None"
                elif isinstance(found_val, bool):
                    found_val = str(found_val)
                elif isinstance(found_val, list):
                    found_val = ','.join(found_val)
                elif isinstance(found_val, float) or isinstance(found_val, int):
                    found_val = str(found_val)
                    
                
                result.append(found_val)
        self.log_line('\t'.join(result))
        
    def __del__(self):
        with open(self.absolute_path, 'r') as in_f:
            header = in_f.readline()
            content = in_f.readlines()
            
        uniq_content = list(set(content))
        
        with open(self.absolute_path, 'w') as out_f:
            out_f.write(header)
            for exp in uniq_content:
                out_f.write(exp)
        
class EvaluationLogger(LoggerBase):
    def __init__(self, output_path, output_file):     
        super().__init__(output_path, output_file)
        if stat(self.absolute_path).st_size == 0:
            self.prepare_header()
        
    def prepare_header(self):
        header = ["model","evaluation file","num of sentences","num of words","oov","logprob","ppl1","ppl2"]
        self.log_line('\t'.join(header))
        
    def log_eval_result(self, model, eval_path, results):
        results = results.strip('\n').split(' ')
        final_result = [model, eval_path, results[2], results[4], results[6], results[10], results[12], results[14]]
        self.log_line('\t'.join(final_result))
        pass
    
    def __del__(self):
        with open(self.absolute_path, 'r') as in_f:
            header = in_f.readline()
            content = in_f.readlines()
            
        uniq_content = list(set(content))
        
        with open(self.absolute_path, 'w') as out_f:
            out_f.write(header)
            for exp in uniq_content:
                out_f.write(exp)
    

class StatisticsLogger(LoggerBase):
    def __init__(self, output_path, output_file):
        super().__init__(output_path, output_file)
        if stat(self.absolute_path).st_size == 0:
            self.prepare_header()
        self.accepted = 0
        self.rejected = 0
        
    def prepare_header(self):
        header = ["trigram","link","raw document length","passed language identification","ppl score","clean document length","gain (%)"]
        self.log_line('\t'.join(header))
        
    def log_search_result(self, term, link, raw_len, lid_res, ppl, clean_len, percentage):
        line = [term, link, str(raw_len), lid_res, str(ppl), str(clean_len), str(percentage)]
        self.log_line('\t'.join(line))
        
        if clean_len == 0:
            self.rejected += 1
        else:
            self.accepted += 1
            
    def __del__(self):
        pass

    def output_overall_stats(self):
        self.log_line('')
        self.log_line('='*30)
        total = self.rejected + self.accepted
        line = ["TOTAL", str(total), "ACCEPTED", str(self.accepted), "REJECTED", str(self.rejected)]
        self.log_line('\t'.join(line))
        
        
