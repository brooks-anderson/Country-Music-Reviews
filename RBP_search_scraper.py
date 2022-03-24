# -*- coding: utf-8 -*-
'''
23 March 22

Webscraping script for article metadata
'''

# modules    
import requests
import re
import time
import sys
import pandas as pd
from bs4 import BeautifulSoup

# import cookieFormatter -- requires user to paste cookies into console
sys.path.append("./")
from cookieFormatter import cookieFormatter

# -----------------

# define function to strip metadata from search results
def metaStripper(search_response):
    '''
    Takes rocksbackpage.com (RBP) advanced search results and collects metadata
    for each result. Note: it is not possible to collect article subject
    from the search result pages. This data must be collected from individual
    articles.
    
    Input
    -------
    search_response: requests.models.Response object constructed from RBP 
    advanced search result page.
    
    Returns
    -------
    metadata - dictionary of lists for 
      + raw - unparsed html for each result
      + links - url path to article
      + titles - article titles
      + types - article types (interview, review, profile, ...)
      + authors - names of journalists
      + journals - names of publications
      + subjects - musicians described in article
      + dates - dates of publicatoin
    '''
    from bs4 import BeautifulSoup
    import re
    
    metadata = {}
    
    # create Beautiful Soup obj from Response obj
    soup = BeautifulSoup(search_response.content, \
                         "html.parser", \
                         from_encoding="utf-8")
    
    articles = soup.find(id = "content") \
                   .find_all("div", class_="article-listing")
    
    # list of second paragraphs
    p2 = [x.find_all('p')[1] for x in articles]
    
    # store raw html
    metadata['raw'] = articles
    
    # regex patterns
    journal_pat = r"(?:<i>)(.*)(?:</i>)"
    
    # store features
    metadata['links'] = [x.a['href'] for x in articles]
    
    metadata['titles'] = [(": ").join(x.a.get_text().split(": ")[1:]) \
                          if len(x.a.get_text().split(": ")) > 1 \
                          else x.a.get_text() \
                          for x in articles]
        
    metadata['journals'] = [re.search(journal_pat, str(x))[1] for x in p2]
    
    metadata['authors'] = [x.get_text().split(',')[0].split('by ')[1] \
                           for x in p2]
        
    metadata['types'] = [x.get_text().split(',')[0].split(' by')[0] \
                         for x in p2]
        
    metadata['dates'] = [x.get_text().split(', ')[-1] for x in p2]
        
    return metadata

# -----------------

'''
+ user conducts an advanced search on rocksbackpage.com
+ 20 results are returned per page
+ identify total number of pages of results
'''

s = requests.Session()

# first page of search results
SearchURL = "https://www-rocksbackpages-com.proxy01.its.virginia.edu/Library/" \
            +"SearchResults?SearchText=&YearFrom=1900&YearTo=2022&SubjectId=" \
            +"85&WriterId=0&PublicationId=0&PieceTypeId=0&ArticleType=Text&" \
            +"OrderBy=PublishedDate&PageNumber=1&NewSearch=True&" \
            +"IsAcademicGroupMember=True"

#requires user to paste cookies into console
cookies = cookieFormatter()

SearchPage = s.get(SearchURL, cookies = cookies)

soup = BeautifulSoup(SearchPage.content, "html.parser")

results = soup.find(id="content")

page_els = str(results.find_all("p", class_="paging-details")[0])

page_num_pat = r"[0-9]+(?=\.)"
num_pages = int(re.search(page_num_pat, page_els)[0])

# -----------------

# Collect MetaData for all search results

search_dict = {"id":[],
               "title":[],
               "author":[],
               "journal":[],
               "type":[],
               "date":[],
               "href":[],
               "html":[]}

for i in range(1,num_pages+1):
    SearchURLs = "https://www-rocksbackpages-com.proxy01.its.virginia.edu/" \
                    +"Library/SearchResults?SearchText=&YearFrom=1900&" \
                    +"YearTo=2022&SubjectId=85&WriterId=0&PublicationId=0&" \
                    +"PieceTypeId=0&ArticleType=Text&OrderBy=PublishedDate&" \
                    +"PageNumber=" + str(i)\
                    +"&NewSearch=True&IsAcademicGroupMember=True"

    
    SearchPages = s.get(SearchURLs, cookies = cookies)
    metadata_dict = metaStripper(SearchPages)
   
    search_dict['id'] += [((i*100)+x) for x in \
                          range(len(metadata_dict['links']))]
    search_dict['html'] += metadata_dict['raw']
    search_dict['href'] += metadata_dict['links']
    search_dict['title'] += metadata_dict['titles']
    search_dict['journal'] += metadata_dict['journals']
    search_dict['author'] += metadata_dict['authors']
    search_dict['type'] += metadata_dict['types']
    search_dict['date'] += metadata_dict['dates']
    
    time.sleep(1.5)
    
search_metadata_df = pd.DataFrame(search_dict)

search_metadata_df.to_csv("./data/RBP_search_metadata.csv", \
                          index = False, \
                          encoding = "utf-8")