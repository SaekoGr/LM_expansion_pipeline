import string
import re
import utils
import num2words

class TextCleaner:
    def __init__(self, is_standard_lang=True):
        self.numbers = "0123456789"
        self.required_par_len = 10
        self._space_start = re.compile(r'^ +')
        self._space_end = re.compile(r' +$')
        self._space = re.compile(r' +')
        self._manual_fixes = {'\xa0':'','\n':''}
        self._is_standard_lang = is_standard_lang
        
    def set_charset(self, charset):
        self.charset = charset
        
    def set_lang(self, lang):
        self.lang = lang
    
    def clean_document(self, content):
        full_doc = [self._clean_paragraph(paragraph) for paragraph in content]
        full_doc = [sentence for sentence in full_doc if sentence]
        return full_doc
    
    def trim_input(self, content):
        for i in range(0,len(content)):
            single_line = content[i]
            single_line = self._tokens_adjust_tags(single_line)
            single_line = self._remove_spelling(single_line)
            single_line = self._tokens_lower(single_line)
            single_line = self._tokens_spacing(single_line)
            content[i] = single_line
        return content
    
    def _tokens_adjust_tags(self, transcript):
        transcript = re.sub(r'<.*?>', '', transcript)
        transcript = re.sub(r'\[(.*?)\]', r' \1 ', transcript)
        return transcript
    
        # remove segments that are too short
    def _tokens_remove_short(self, term):
        if len(term) <= self.required_par_len:
            return ''
        else:
            return term
        
    def _tokens_remove_charset_violations(self, term):
        """If the chosen paragraph contains charasters outside of scope, remove it"""
        if self.charset is None:
            return term
        
        for char in term:
            if char not in self.charset:
                return ''
        return term

    # replace interpunction characters with space
    def _tokens_interpunction(self, term):
        additional_interpunction = set(['“','：','„','–','·','…','©','•','。','”','（','）',':','」','「','、','、','《','》'
                                        '，','，','『','』','；','？','℃','》','．','！','】','【'])
        general_interpunction = set(string.punctuation)
        #general_interpunction.remove('.')

        for char in general_interpunction:
            term = term.replace(char, ' ')

        for char in additional_interpunction:
            term = term.replace(char, ' ')

        return term

    def _tokens_lower(self, term):
        return term.lower()
    
    def _remove_spelling(self, line):
        line = re.sub(r'_','',line)
        return line
    
    # removes redundant spacing
    def _tokens_spacing(self, term):
        # remove multiple white spaces
        term = re.sub(self._space_end, '', term)
        term = re.sub(self._space_start, '', term)
        term = re.sub(self._space, ' ', term)
        return term
    
    # removes tags from text
    def _strip_tags(self, content):
        content = re.sub(r'<[^<]+?>', ' ', content)
        content = re.sub(r'\[\d+\]', ' ', content)
        content = re.sub(r'\r', ' ', content)
        content = content.strip('\n')
        return content
    
    def _tokens_remove_numerical(self, term):        
        # save the full length of paragraph
        full_len = len(term.replace(' ',''))
        numeric = 0
        graphemes_cnt = utils.words_occurance_cnt(term)
    
        # count occurance of numbers
        for char in self.numbers:
            if char in graphemes_cnt.keys():
                numeric += graphemes_cnt[char]

        # if more than half of that paragraph is numeric, then the result is empty        
        if numeric >= full_len/2:
            return ''
        else:
            return term
        
    def _tokens_expand_numbers(self, line):
        matches = re.findall(r'\b[0-9]+\b',line)
            
        for match in matches:
            try:
                expanded = num2words(int(match), lang=self.lang)
            except:
                expanded = ''
                
            if expanded != '' :
                line = re.sub(rf'\b{match}\b', expanded. line)
            
        return line
    
    def _tokens_manual_fixes(self, line):
        for case in self._manual_fixes:
            line = line.replace(case, self._manual_fixes[case])
        
        return line
    
    def _tokens_chinese(self, line):
        line = re.sub(r'([\u4e00-\u9fff])',r' \1 ',line)
        
        return line
    
    def _tokens_remove_nonchinese(self, line):
        tmp = line.replace(' ','')
        full_len = len(line)
        
        if full_len == 0:
            return line
        
        matches = re.findall(r'[\u4e00-\u9fff]', line)
        
        chinese_rate = len(matches) / full_len * 100
        if chinese_rate > 70:
            return line
        else:
            return ''
    
    # cleaning functions for single paragraph
    def _clean_paragraph(self, line):
        line = self._tokens_manual_fixes(line)
        line = self._tokens_lower(line)
        line = self._tokens_interpunction(line)
        line = self._tokens_remove_short(line)
        line = self._tokens_remove_numerical(line)
        
        if self._is_standard_lang:
            line = self._tokens_expand_numbers(line)
            
        line = self._tokens_remove_nonchinese(line)
        line = self._tokens_chinese(line)
        line = self._tokens_spacing(line)
        line = self._tokens_remove_charset_violations(line)
        return line