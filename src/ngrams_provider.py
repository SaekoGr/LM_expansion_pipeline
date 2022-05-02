import utils

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
        
    def _create_ngrams(self, sentences, n=3):
        ngram_results = []

        for sentence in sentences:
            sentence = sentence.split(' ')

            for i in range(0, len(sentence) - n + 1):
                ngram_results.append(tuple(sentence[i:i+n]))
        return ngram_results
    
    def _sort_ngrams_dict(self, ngrams, reverse = False):
        return {k: v for k, v in sorted(ngrams.items(), key=lambda item: item[1], reverse = reverse)}
    
    def _single_ngram_precision(self, ngram):
        """Calculates the initial precision of the searched term"""
        ngram = ' '.join(ngram)
        ngramLen = len(' '.join(ngram))
        precision = min((ngramLen/self.precision_length)**2, 1.0)
        return precision
     
    def _estimate_ngram_frequency(self, ngrams):
        cnt = utils.words_occurance_cnt(ngrams)
        return cnt
        
    def _estimate_initial_precision(self, ngrams):
        precision = {}
        for ngram in ngrams:
            precision[ngram] = self._single_ngram_precision(ngram)
        return precision
        
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
            else: # actually choose top k ones
                chosen_ngrams = list(all_ngrams.keys())[:k]
                
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