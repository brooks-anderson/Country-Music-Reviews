# -*- coding: utf-8 -*-
"""
March 25, 2022

Class Definition for rbpScraper
"""
import requests
import re
import os
import pandas as pd

from bs4 import BeautifulSoup


class RBPScraper():
    '''
    Retrieves metadata and articles from rocksbackpages.com
    '''

    def __init__(self, desc = "", write_path="./", search_URL=None, cookies=None):
        
        self.url = search_URL
        self.cookies = cookies
        self.path = write_path  
        self.desc = desc
        self.__searchMeta = None
        self.LIB = None
        
        if self.url is None:
            self.getSearchURL()
        
        if self.cookies is None:
            self.cookieFormatter()
            
    
    def searchScraper(self):
        '''
        searchScraper visits each page of search results and collects 

        Parameters
        ----------
        descriptor : str, optional
            Word that characterizes the search. This might be a genre, artist, 
            or publication. 

        Returns
        -------
        self
        '''
        # used in creation of article_ids
        desc_abbrv= [x[0] for x in self.desc.lower().split()]
        self.label  = ''.join([x for x in desc_abbrv])
        
        s = requests.Session()
        SearchPage = s.get(self.url, cookies = self.cookies)
        
        num_pages = self.__pageNumStripper(SearchPage)
        print(f"Number of pages: {num_pages}")
        print("Retrieving metadata...")
        
        search_dict = {"id":[],
                       "type":[],
                       "href":[]}
        
        prefix_pat = r"^(.*PageNumber=)(?:[0-9])"
        suffix_pat = r"(?:PageNumber=[0-9])(.*)$"
        prefix_url = re.search(prefix_pat, self.url)[1]
        suffix_url = re.search(suffix_pat, self.url)[1]
        
        for i in range(1,num_pages+1):
            SearchURLs = prefix_url + str(i) + suffix_url
            
            
            SearchPages = s.get(SearchURLs, cookies = self.cookies)
            metadata_dict = self.__metaStripper(SearchPages)
           
            search_dict['id'] += [self.label+str(((i*100)+x)) for x in \
                                  range(len(metadata_dict['links']))]
            search_dict['href'] += metadata_dict['links']
            search_dict['type'] += metadata_dict['types']

        
        search_df = pd.DataFrame(search_dict)
        search_df = search_df.set_index('id')
        self.__searchMeta = search_df
        print("Complete.")
        return self

    def articleScraper(self):
        '''
        article Scraper collects each article listed in __searchMeta.
        Articles are saved as html and txt to respective subdirectories. 
        MetaData from articles is saved as pandas dataframe to LIB attribute.
        
        Returns
        -----
        self
        '''
        try:
            self.__searchMeta.count()
        except AttributeError:
            raise ValueError("searchScraper must be called before articleScraper")
            
        # check if path directory exists, if not create it
        if not os.path.isdir(self.path):
            os.makedirs(os.path.dirname(self.path))
                
        # check if sub directories exist, if not create
        if not os.path.isdir(self.path+"html/"):
            os.makedirs(os.path.join(self.path, 'html/'))
        # if not os.path.isdir(self.path+"txt/"):
        #     os.makedirs(os.path.join(self.path, 'txt/'))
         
        prefix_pat = r"^(.*)(?:/Library)"
        prefix_url = re.search(prefix_pat, self.url)[1]
        
        s = requests.Session()

        print("Retrieving articles...")
        count = 0
        numIter = len(self.__searchMeta)
        LIB_dict = {'id':[],
                    'title':[],
                    'author':[],
                    'source':[],
                    'date':[],
                    'subjects':[]}
            
        for i in self.__searchMeta.index:
            try:
                meta_dict = self.__collectArticleMeta(i, prefix_url, s)
            except AttributeError:
                print(f"article {i} not found.\n")
                continue
            
            LIB_dict['id'].append(meta_dict['id'])
            LIB_dict['title'].append(meta_dict['title'])
            LIB_dict['author'].append(meta_dict['author'])
            LIB_dict['source'].append(meta_dict['source'])
            LIB_dict['date'].append(meta_dict['date'])
            LIB_dict['subjects'].append(meta_dict['subjects'])
        
            self.__saveArticle(i, prefix_url, s)
            
            # print progress
            count += 1
            if count % round(numIter/100) == 0:
                print(f"{round(count*100/numIter)}% Complete")
            
        
        LIB_pd = pd.DataFrame(LIB_dict)
        LIB_pd = LIB_pd.set_index('id')
        LIB_pd['topic'] = self.desc
        LIB_pd = LIB_pd.join(self.__searchMeta)
        self.LIB = LIB_pd
        
        return self
        
    def cookieFormatter(self, cookies = None):
        '''
        cookieFormatter prompts the user to paste web-browsing cookies into the
        console. It assigns a dictionary of cookies to the class's cookies
        attribute
        
        The input should be copied from the developer tools window in a web 
        browser. Cookies can be found by navigating to the network tab. 
        Cookies can also be passed as an argument to the method but this is not
        recommended due to rigid formatting requirements.
        
        Returns
        -----
        None. Assigns cookies attribute of class
        '''
        
        if cookies is None:
            cookies = input("Please paste cookies:\n\n")
            print("\nThank you.\n")
            
        try:
            split_cookies = cookies.split("; ")
            
            key_value_pairs = [x.split("=") for x in split_cookies]
            
            cookies_dict = dict(key_value_pairs)
            
            self.cookies = cookies_dict
        except:
            ValueError("Cookie input is unparsable.")
            
    def getSearchURL(self, search_URL=None):
        '''
        getSearchURL assigns the search url to the class's url attribute. User
        can pass the search URL as a string to the method. If no argument is
        passed, the method will prompt the user to paste the search URL into 
        the console.
        
        Returns
        -------
        None. Assigns search URL to url attribute of class.
        '''
        
        if search_URL is None:
            search_URL = input("Please paste URL:\n\n")
            print("\nThank you.\n")
        
        self.url = search_URL
        
    def __metaStripper(self, search_response):
        '''
        Takes rocksbackpages.com (RBP) advanced search results and collects 
        metadata for each result.
        
        Input
        -------
        search_response: requests.models.Response object constructed from RBP 
        advanced search result page.
        
        Returns
        -------
        metadata - dictionary
          + links - url path to article
          + types - article types (interview, review, profile, ...)
        '''
        
        metadata = {}
        
        # create Beautiful Soup obj from Response obj
        soup = BeautifulSoup(search_response.content, \
                             "html.parser", \
                             from_encoding="utf-8")
        
        articles = soup.find(id = "content") \
                       .find_all("div", class_="article-listing")
        
        # list of second paragraphs
        p2 = [x.find_all('p')[1] for x in articles]
        
        # store features
        metadata['links'] = [x.a['href'] for x in articles]
        metadata['types'] = [x.get_text().split(',')[0].split(' by')[0] \
                             for x in p2]
        return metadata
    
    def __pageNumStripper(self, search_response):
        '''
        Takes rocksbackpages.com (RBP) advanced search results and collects 
        total number of pages of results.

        Parameters
        ----------
        search_response: requests.models.Response object constructed from RBP 
        advanced search result page.
        
        Returns
        -------
        num_pages - int, number of pages of search results

        '''
        soup = BeautifulSoup(search_response.content, "html.parser")
        results = soup.find(id="content")

        page_els = str(results.find_all("p", class_="paging-details")[0])

        page_num_pat = r"[0-9]+(?=\.)"
        num_pages = int(re.search(page_num_pat, page_els)[0])

        return num_pages
        
    def __collectArticleMeta(self, article_id, prefix_url, session):

        page_url = prefix_url+self.__searchMeta.loc[article_id].href
        page = session.get(page_url, cookies = self.cookies)
        soup = BeautifulSoup(page.content, \
                             "html.parser", \
                             from_encoding='utf-8')
        try:
            soup.find(id="content") \
                .find("span", class_="citations") \
                .get_text()
        except AttributeError:
            print("Cookies expired")
            self.cookies = self.cookieFormatter()
            
            page = session.get(page_url, cookies = self.cookies)
            soup = BeautifulSoup(page.content, \
                                 "html.parser", \
                                 from_encoding='utf-8')
  
        title = soup.find(id="content") \
                    .find("h1", class_="article") \
                    .get_text() \
                    .strip()
                    
        author = soup.find(id="content") \
                     .find("p", class_="article-details")\
                     .find("span", class_="writer") \
                     .get_text()
        
        source = soup.find(id="content") \
                     .find("p", class_="article-details") \
                     .find("span", class_="publication") \
                     .get_text()
                     
        date = soup.find(id="content") \
                   .find("p", class_="article-details") \
                   .get_text() \
                   .split("\r\n")[-2] \
                   .strip()
        
        artist_pattern = r'(?:Artist/)(.*)(?:">)'
        aside = soup.find(id="content").find('aside').find_all('a')
        subjects = [re.search(artist_pattern, str(x))[1] \
                    for x in aside \
                    if re.search(artist_pattern, str(x)) is not None]

        meta_dict = {'id' : article_id,
                     'title': title,
                     'author': author,
                     'source': source,
                     'date': date,
                     'subjects': subjects}
        return meta_dict
    
    def __saveArticle(self, article_id, prefix_url, session):

        page_url = prefix_url+self.__searchMeta.loc[article_id].href
        
        page = session.get(page_url, cookies = self.cookies)
        soup = BeautifulSoup(page.content, \
                             "html.parser", \
                             from_encoding='utf-8')
        try:
            soup.find(id="content") \
                .find("span", class_="citations") \
                .get_text()
        except AttributeError:
            print("Cookies expired")
            self.cookies = self.cookieFormatter()
            
            page = session.get(page_url, cookies = self.cookies)
            soup = BeautifulSoup(page.content, \
                                 "html.parser", \
                                 from_encoding='utf-8')
        
        contentHTML = soup.find(id="content").prettify()
        # contentTXT = soup.find(id="content").get_text() 
            
        with open(f"{self.path}html/{article_id}.html", \
                  mode='wt', \
                  encoding='utf-8') as file:
            file.write(contentHTML)
                
        # with open(f"{self.path}txt/{article_id}.txt", \
        #           mode='wt', \
        #           encoding='utf-8') as file:
        #     file.write(contentTXT)
        
        return None
    
    def writeLIB(self):
        '''
        writeLIB writes the LIB attribute to a .csv file in the directory
        specified by path attribute.
        
        Returns
        -------
        None.
        '''
        if not os.path.isdir(self.path):
            os.makedirs(os.path.dirname(self.path))
        try:
            self.LIB.to_csv(self.path + self.label + "LIB.csv")
        except AttributeError:
            raise ValueError("LIB not found. Try calling articleScraper.")
        
        
    # if directory does not exist:    
    # os.makedirs(os.path.dirname("./test/"), exist_ok=True)            

if __name__ == '__main__':
    pass