from abc import abstractmethod
from os import path
import pycountry
import fasttext
import os
import numpy as np

# ignore warnings regarding compatibility
fasttext.FastText.eprint = lambda x: None

LANG_STRUCT = {"LANGS":0,"PROBS":1}

class LanguageIdentification:
    def __init__(self, target_language, threshold):
        self._default_model = "lid.176.bin"
        self._model_link = "https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin"
        self._lid_threshold = threshold
        self._valid_language(target_language)
        
        # download the model if not available
        if not LanguageIdentification._model_available(self._default_model):
            self._download_default_model()
            
        self.model = self._load_model(self._default_model)  
        
    def _valid_language(self, target_language):
        # check valid iso code
        self.lang_iso = pycountry.languages.get(alpha_2=target_language)
        
        if(self.lang_iso is None):
            raise ValueError("The provdied iso language code "  + target_language+ " is invalid")
        
        # store the target iso code
        self.lang_iso = self.lang_iso.alpha_2
        
    @abstractmethod
    def _model_available(model):
        return path.exists(model)
        
    def _download_default_model(self):
        command = "curl " + self._model_link + " -o " + self._default_model
        os.system(command)

    def _load_model(self, model_name):
        if not LanguageIdentification._model_available(model_name):
            raise Exception("Model {} is not available and could not be downloaded\n".format(model_name))
        return fasttext.load_model(model_name)
    
    def _clean_lang_label(self, label):
        return label.replace('__label__','')
    
    def _identify_lang(self, text):
        predictions = self.model.predict(text)
        
        # get idx of the most probable language
        probable_lang_idx = np.argmax(predictions[LANG_STRUCT["PROBS"]])
        
        # get probability of the most probable language
        probability = float(predictions[LANG_STRUCT["PROBS"]][probable_lang_idx])
        
        # get iso code 
        chosen_lang = predictions[LANG_STRUCT["LANGS"]][probable_lang_idx]
        chosen_lang = self._clean_lang_label(chosen_lang)
        
        return chosen_lang, probability
    
    
    def is_target_lang(self, text):
        # firstly, identify what languages are present
        probable_lang, lang_probability = self._identify_lang(text)
        
        # is it the target language
        if(self.lang_iso.casefold() != probable_lang.casefold()):
            return False
    
        # is it confident enough that the languages match
        if(lang_probability < self._lid_threshold):
            return False
    
        return True