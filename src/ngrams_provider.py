import utils
import collections

class NgramsProvider:
    def __init__(self, content, parameters, already_processed=[]):
        self.order_ngram = parameters.order_ngram
        self.precision_length = parameters.len_penalty
        self.document_limit = parameters.doc_limit
        self.create_ngrams = parameters.create_ngrams
        if self.create_ngrams:
            self.ngrams = self._create_ngrams(content, self.order_ngram)
        else:
            self.ngrams = content
    
        self.expected_count = {}
        self.already_processed = already_processed
        
        self.get_top_ngrams(500)
        
    # go through all the sentences and extract all tuples
    def _create_ngrams(self, sentences, n=3):
        ngram_results = []

        for sentence in sentences:
            sentence = sentence.split(' ')

            for i in range(0, len(sentence) - n + 1):
                ngram_results.append(tuple(sentence[i:i+n]))
        return ngram_results
    
    # sort dictionary, highest values first
    def _sort_ngrams_dict(self, ngrams, reverse = False):
        return {k: v for k, v in sorted(ngrams.items(), key=lambda item: item[1], reverse = reverse)}
    
    # calculate precision of a single ngram
    def _single_ngram_precision(self, ngram):
        """Calculates the initial precision of the searched term"""
        ngram = ' '.join(ngram)
        ngramLen = len(' '.join(ngram))
        precision = min((ngramLen/self.precision_length)**2, 1.0)
        return precision
     
    # calculate the document frequency
    def _estimate_ngram_frequency(self, ngrams):
        cnt = utils.words_occurance_cnt(ngrams)
        return cnt
        
    # estimate initial precision
    def _estimate_initial_precision(self, ngrams):
        precision = {}
        for ngram in ngrams:
            precision[ngram] = self._single_ngram_precision(ngram)
        return precision
    
    def _choose_chinese(self, k, ngrams):
        new_ngrams = {}
        for key, val in ngrams.items():
            # choose less common trigram
            if float(val) < 2: # and float(val) > 1:
                if len(list(set(key))) == self.order_ngram:
                    new_ngrams[key] = val
        
        return new_ngrams
        
    def get_top_ngrams(self, k = 50, percentage = None):
        if self.create_ngrams:
            # firstly, estimate the document count
            self._estimate_document_count()
            
            # sort the ngrams according to the score (highest score first)
            all_ngrams = self._sort_ngrams_dict(self.expected_count, reverse = True)
            
            # use percentage if given
            if percentage is not None:
                k = round(len(all_ngrams.keys()) * percentage)
            
            # choose all ngrams
            if k >= len(all_ngrams.keys()):
                chosen_ngrams = list(all_ngrams.keys())
                tmp = list(all_ngrams.items())
            else: # actually choose top k ones
                chosen_ngrams = list(all_ngrams.keys())[:k]
                tmp = list(all_ngrams.items())[:k]
                
                
            # filter out those that were already processed
            chosen_ngrams = list(filter(lambda ngram: ' '.join(ngram) not in self.already_processed, chosen_ngrams))

            return chosen_ngrams
        else:
            return self.ngrams
        
    def _estimate_document_count(self):
        self.precision = self._estimate_initial_precision(self.ngrams)
        self.frequency = self._estimate_ngram_frequency(self.ngrams)

        for ngram in self.ngrams:
            self.expected_count[ngram] = self.precision[ngram] * self.frequency[ngram]
        
    def get_expected_count(self, term):
        term = tuple(term.split(' '))
        
        if term in self.expected_count.keys():
            expected_cnt = self.expected_count[term]
        else:
            expected_cnt = 0
        return int(round(expected_cnt, 0))