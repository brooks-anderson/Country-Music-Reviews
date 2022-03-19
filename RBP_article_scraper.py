# -*- coding: utf-8 -*-
'''
19 March 22

Webscaping script to collect music review articles. Requires RBP_search_metadata.csv
produced from RBP_search_scraper.py
'''

# modules    
import requests
import re
import time
import random
import sys
import pandas as pd
from bs4 import BeautifulSoup

# exclude certain article types
# + Film/DVD/TV Review
# + Book Review
# + Audio Transcript
# + maybe: memoir

exclude = ['Film/DVD/TV Review',
           'Book Review',
           'Audio transcript of interview',
           'memoir']

links = pd.read_csv("./data/RBP_search_metadata.csv")

links = links[~links.type.isin(exclude)]


# set up request session
s = requests.Session()

# import cookieFormatter -- requires user to paste cookies into console
sys.path.append("./")
from cookieFormatter import cookieFormatter

cookies = cookieFormatter()


URL_prefix = "https://www-rocksbackpages-com.proxy01.its.virginia.edu"

artist_pattern = r'(?:Artist/)(.*)(?:">)'

meta_dict = {'id':[],
             'title':[],
             'author':[],
             'source':[],
             'date':[],
             'subjects':[]}

for i in range(len(links)):

    #time.sleep(2*random.random())   
    
    pageURL = URL_prefix + links.iloc[i].href
    page = s.get(pageURL, cookies = cookies)
    
    article_id = links.iloc[i].id
    
    soup = BeautifulSoup(page.content, "html.parser")
    
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
                
    aside = soup.find(id="content").find('aside').find_all('a')
    subjects = [re.search(artist_pattern, str(x))[1] \
                for x in aside \
                if re.search(artist_pattern, str(x)) is not None]
        
    meta_dict['id'].append(article_id)
    meta_dict['title'].append(title)
    meta_dict['author'].append(author)
    meta_dict['source'].append(source)
    meta_dict['date'].append(date)
    meta_dict['subjects'].append(subjects)
                
    contentHTML = soup.find(id="content").prettify()
    contentTXT = soup.find(id="content").get_text()       
                
    with open(f"./data/articles_html/{article_id}.html", mode='wt', encoding='utf-8') as file:
        file.write(contentHTML)
        
    with open(f"./data/articles_txt/{article_id}.txt", mode='wt', encoding='utf-8') as file:
        file.write(contentTXT)
        
    if i % 50 == 0:
        print(f"\narticles collected: {i}\n")
    
    
metadata = pd.DataFrame(meta_dict)
metadata.to_csv('./data/RBP_article_metadata.csv', encoding = "cp1252", index = False)    
    