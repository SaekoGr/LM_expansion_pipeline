#!/usr/bin/python
from base64 import encode
from googlesearch import search
from bs4 import BeautifulSoup
import requests
import re
import urllib
import hashlib
import time
from requests_html import HTML
from requests_html import HTMLSession
from collections import Counter
import utils
import socket
from logger import LoggerBase
from os import path

BING_API = "https://api.bing.microsoft.com/v7.0/search"
BING_KEY = "20ce45f4382045c1a7816d2bdec3d506"
headers = {'Ocp-Apim-Subscription-Key': "20ce45f4382045c1a7816d2bdec3d506"}

# global constant parsing variable
PAGES = "webPages"
CONCRETE_PAGES = "value"
URL = 'url'

class DocumentRetriever:
    def __init__(self, search_preference, download_path, doc_limit, doc_default, web_tags, lang=None):
        self.search_preference = search_preference
        self.download_path = download_path
        self.doc_limit = doc_limit
        self.doc_default = doc_default
        self.web_tags = web_tags
        self.google_pause = 0.5
        self.required_par_len = 10
        self.numbers = "0123456789"
        self.unwanted = ['.pdf','.doc']
        self.lang = utils.to_lower(lang)
        self.url_mapper = LoggerBase(download_path, "url_mapper")
        
    def search_term(self, term, cnt, dct):
        """Search web for the given term, returns links"""
        
        # adjust cnt for the maximum document limit
        if cnt > self.doc_limit:
            cnt = self.doc_limit
        
        if self.search_preference == "google":
            self._google_api(term, cnt, dct)
        else:
            self._bingapi(term, cnt, dct)
        
    def remove_unwanted(self, links):
        links = list(filter(lambda link: (path.splitext(link)[-1]).casefold() not in self.unwanted, links))
        return links
        
    def estimate_term_webprecision(self, term):
        """Estimate how many documents are indexed overall in the search engine"""
        # prepare the query term
        query = urllib.parse.quote_plus(term)
        
        # try to search google
        try:
            session = HTMLSession()
            response = session.get("https://www.google.com/search?q=" + query)
        except requests.exceptions.RequestException as e:
            #print(e)
            return self.doc_default
        
        # parse the html and obtain number of search results
        stats_wrapper = response.html.find('#result-stats', first=True)
    
        # did not find information about the number of search result, degrade to default
        if stats_wrapper is None:
            return self.doc_default
        
        final_num = ""
        stats = stats_wrapper.text
        stats = stats.split('\n')[0]
        stats = stats.replace(" ","")
        stats = stats.replace('\xa0','')
        
        for char in stats:
            if char in self.numbers:
                final_num += char
        #print(stats)
        #print(final_num)
        return min(self.doc_limit, int(final_num))
    
    
    def encode_url(self, url):
        url = str(url)
        return str(hashlib.md5(url.encode()).hexdigest())
    
    def _load_downloaded(self, url):
        full_path = self._download_path(url)
        return utils.remove_newlines(utils.read_file(full_path))
        
    def _already_downloaded(self, url):
        full_path = self._download_path(url)
        return path.exists(full_path)
        
    def _download_path(self, url):
        url = self.encode_url(url)
        return path.join(self.download_path, url)
    
    def _write_downloaded(self, content, url):
        full_path = self._download_path(url)
        
        with open(full_path,'w') as out_f:
            for line in content:
                out_f.write(line + '\n')
        
    # parse given url and return clean document
    def get_document_by_url(self, url):
        if self._already_downloaded(url):
            time.sleep(2.5)
            return self._load_downloaded(url)
        
        try:
            request_result = requests.get(url)
            soup = BeautifulSoup(request_result.content, 'html.parser')
        except (socket.gaierror, urllib.error.URLError) as e:
            return []

        
        # get all paragraphs
        all_paragraphs = soup.find_all(self.web_tags)
        all_paragraphs = [self._strip_tags(w.getText()) for w in all_paragraphs]
        
        # write down the downloaded file
        self._write_downloaded(all_paragraphs, url)
        
        # log to mapper file
        url_hash = self.encode_url(url)
        self.url_mapper.log_list_as_line([url, url_hash])
        
        return all_paragraphs
    
        # removes tags from text
    def _strip_tags(self, content):
        content = re.sub(r'<[^<]+?>', ' ', content)
        content = re.sub(r'\[\d+\]', ' ', content)
        content = re.sub(r'\r', ' ', content)
        content = content.strip('\n')
        return content
        
        
    def _google_api(self, term, cnt, dct):
        """Return obtained links for term"""
        dct["links"] = ["https://cs.wikipedia.org/wiki/Ko%C4%8Dka_dom%C3%A1c%C3%AD"]
        return
        
        links = []
    
        try:
            if self.lang is None:
                for link in search(term, stop=cnt, pause=self.google_pause):
                    links.append(link)
            else:
                for link in search(term, stop=cnt, pause=self.google_pause, lang=self.lang):
                    links.append(link)
        except (socket.gaierror, urllib.error.URLError) as e:
            pass
    
        links = self.remove_unwanted(links)
        dct["links"] = links

    def _bingapi(self, term, cnt, dct):
        """Return obtained links for term"""
        query_params = self._create_bing_query(term)
        response = requests.get(BING_API,params=query_params,headers=headers)
        #extract_webaddresses(response)
        dct["links"] = self.remove_unwanted(self._extract_webaddresses(response))
        
    
    # extract links from the json response
    def _extract_webaddresses(self, full_response):
        """Preprocess obtained response from the web search"""
        individual_pages = full_response[PAGES][CONCRETE_PAGES]
        web_adresses = [page[URL] for page in individual_pages]
        web_adresses = [page.replace('\\','') for page in web_adresses]
        return web_adresses
    
    # create search term for continuous term
    def _clean_bing_query(self, term):
        """Prepare Query Term for google"""
        term = self._tokens_interpunction(term)
        term = self._tokens_spacing(term)
        term = self._tokens_lower(term)
        term = term.replace(' ','+')
        return term

    # create search term for given n-gram / word sequqnce
    def _create_bing_query(self, term):
        """Prepare Query Term for bing api"""
        term = self._clean_query(term)
        term_params = (('q', term),)
        return term_params
