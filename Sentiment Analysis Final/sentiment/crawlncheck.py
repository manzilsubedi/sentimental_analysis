# -*- coding: utf-8 -*-
"""Untitled3.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1aKGAU_NKNBG0Kr6zS2oijUuUjhtmZCiv
"""

# from google.colab import drive
# drive.mount('/content/drive')

# !ls /content/drive/MyDrive/MajorProject/text_processor.py

# !cat /content/drive/MyDrive/MajorProject/text_processor.py

# import sys
# sys.path.append('/content/drive/MyDrive/MajorProject')

# Commented out IPython magic to ensure Python compatibility.
# %%capture requirements
import sys
import os
# !{sys.executable} -m pip install bs4
# !{sys.executable} -m pip install lxml
# !{sys.executable} -m pip install pandas
import time
import requests
import lxml
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
import pickle
from multiprocessing import Pool
import nltk

import text_processor as tp

product_link = input('Enter the product link: ')

headers = {'User-Agent': 'Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Chrome/6.0.472.64 Safari/534.3'}
product_page = requests.get(product_link, headers=headers)

product_page_soup = BeautifulSoup(product_page.text, 'lxml')

# product_page_soup

see_all_reviews = product_page_soup.find_all("a", {"data-hook" : "see-all-reviews-link-foot"})[0]
all_reviews_url =  "/".join(product_link.split("/", 3)[:3]) + see_all_reviews['href']
print(all_reviews_url)

all_reviews_page = requests.get(all_reviews_url, headers=headers)
all_reviews_page_soup = BeautifulSoup(all_reviews_page.text, 'lxml')

#do
i=1
# review_id = [i['id'] for i in all_reviews_page_soup.find_all(class_='a-section review aok-relative')[2:]]
names = list([i.text for i in all_reviews_page_soup.find_all(class_='a-profile-name')[2:]])
ratings = list([i.find(class_='a-icon-alt').text[:3] for i in all_reviews_page_soup.find_all(class_='a-section celwidget')])
title = list([i.span.text for i in all_reviews_page_soup.find_all(class_='review-title')[2:]])
date = list([i.text for i in all_reviews_page_soup.find_all(class_='review-date')[2:]])
text = list([i.span.text for i in all_reviews_page_soup.find_all(class_='review-text-content')])
#while
# print(type(all_reviews_page_soup.find(class_='a-pagination').find_all('li')[1].a))
try:
    while all_reviews_page_soup.find(class_='a-pagination'):
        if all_reviews_page_soup.find(class_='a-pagination').find_all('li')[1].a:
            #print(i)
            i+=1
            next_url = 'https://www.amazon.in' + all_reviews_page_soup.find(class_='a-pagination').find_all('li')[1].a['href']
            all_reviews_page = requests.get(next_url)
            all_reviews_page_soup = BeautifulSoup(all_reviews_page.text, 'html.parser')
    #         review_id.append([i['id'] for i in all_reviews_page_soup.find_all(class_='a-section review aok-relative')[2:]])
            temp_names = [i.text for i in all_reviews_page_soup.find_all(class_='a-profile-name')[2:]]
            if temp_names:
                names.append(temp_names)
            else:
                names.append('')
            temp_ratings = [i.find(class_='a-icon-alt').text[:3] for i in all_reviews_page_soup.find_all(class_='a-section celwidget')]
            if temp_ratings:
                ratings.append(temp_ratings)
            else:
                ratings.append('')
            temp_title = [i.span.text for i in all_reviews_page_soup.find_all(class_='review-title')[2:]]
            if temp_title:
                title.append(temp_title)
            else:
                title.append('')
            temp_date = [i.text for i in all_reviews_page_soup.find_all(class_='review-date')[2:]]
            if temp_date:
                date.append(temp_date)
            else:
                date.append('')
            temp_text = [i.span.text for i in all_reviews_page_soup.find_all(class_='review-text-content')]
            if temp_text:
                text.append(temp_text)
            else:
                text.append('')
        else:
            break
except Exception as e:
    print(e, type(all_reviews_page_soup.find(class_='a-pagination')))
#print('Name'+str(len(names))+'Ratings'+str(len(ratings))+'Title'+str(len(title))+'Date'+str(len(date))+'Text'+str(len(text)))
reviews_dict = {'Name':names, 'Ratings':ratings, 'Title':title, 'Date':date, 'Text':text}
#print(reviews_dict)

reviews_df = pd.DataFrame.from_dict(reviews_dict)
#print(reviews_df)

timestr = time.strftime("%Y%m%d-%H%M%S")
csvoutput_file = f'.{os.path.sep}review_{timestr}.csv'
#print(f'saving to {csvoutput_file}')
reviews_df.to_csv(csvoutput_file)

newdata = reviews_df


import re
from nltk.tokenize.toktok import ToktokTokenizer
import spacy

print(newdata.head())
print(newdata.count())

newdata['Text'].replace(r'\s+|\\n', ' ', regex=True, inplace=True)





df = newdata.head(10)


def process_df(df):
    """
    Filters the dataframe and creates dataframe which contains 
    the fields [reviews.text, reviews.rating, sentiment]
    Rating below 3 and above 3 are taken as negative and positive respectively
    """
    df1 = df[['Text','Ratings']]
    df1_filtered = df1[df1['Ratings'] != 3]    
    sentiment_dict = {1:0, 2:0, 4:1, 5:1}    
    df1_filtered['sentiment'] = df1_filtered['Ratings'].map(sentiment_dict)
    return df1_filtered

df1 = process_df(df)


def process_txt(df):
    """
    Apply clean_text method of text_processor in the column 'content'
    """
    df['cleaned_text'] = df['Text'].apply(tp.clean_text)
    return df

def parallelize_df(df, func, n=5):
    """
    Split the dataframe df into 'n' dataframes and parallely apply 'func'
    on each dataframe using multiprocessing
    """
    df_split = np.array_split(df, n)
    pool = Pool(n)
    df = pd.concat(pool.map(func, df_split))
    pool.close()
    pool.join()
    return df

#processing dataset 
processed_df = parallelize_df(df, process_txt)


import nltk
nltk.download('averaged_perceptron_tagger')

from nltk.tokenize.toktok import ToktokTokenizer
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk
nltk.download('vader_lexicon')

sia = SentimentIntensityAnalyzer()

with open('pickles/amazon/mnb_classifier.pickle', 'rb') as data:
    model = pickle.load(data)
    
# import tfidf
with open('pickles/amazon/tfidf.pickle', 'rb') as data:
     tfidf = pickle.load(data)

sentiment_map = {'Negative':0, 'Positive':1, 'Neutral':2}

def get_sentiment(text):
    """
    Predicts the sentiment of text using the Multinomial Naive Bayes Model
    """
    sentiment_id = model.predict(tfidf.transform([text]))
    return get_name(sentiment_id)

def get_name(sentiment_id):
    """
    Gets sentiment name from sentiment_map using sentiment_id
    """
    for sentiment, id_ in sentiment_map.items():
        if id_ == sentiment_id:
            return sentiment

def get_noun(text):
    """
    Finds noun of the text
    """
    tokenizer = ToktokTokenizer()
    tokens = tokenizer.tokenize(text)    
    pos_tags = nltk.pos_tag(tokens)
    nouns = []
    for word, tag in pos_tags:
        if tag == "NN" or tag == "NNP" or tag == "NNS":
            nouns.append(word)
    return nouns

def top_pos_word(text):
    """
    Finds top positive word using nltk vader library
    """
    pos_polarity = dict()
    for word in tp.get_tokens(text):
        pos_score = sia.polarity_scores(word)['pos']
        if word not in pos_polarity:
            pos_polarity[word] = pos_score
        else:
            pos_polarity[word] += pos_score
    top_word = max(pos_polarity, key=pos_polarity.get)
    return top_word

def top_neg_word(text):
    """
    Finds top negative word using nltk vader library
    """
    neg_polarity = dict()
    for word in tp.get_tokens(text):
        neg_score = sia.polarity_scores(word)['neg']
        if word not in neg_polarity:
            neg_polarity[word] = neg_score
        else:
            neg_polarity[word] += neg_score
    top_word = max(neg_polarity, key=neg_polarity.get)
    return top_word

def sentiment_analysis(text):
    """
    Finds the sentiment of text, prints positive or negative word and 
    prints the causing words of positivity or negativity
    """
    text = tp.clean_text(text)
    sentiment = get_sentiment(text)
    print(f'Sentiment: {sentiment}')
    # if sentiment == 'Positive':
    #     nouns = get_noun(text)
    #     # print(f'Positive word: {top_pos_word(text)}')
    #     # print(f'Cause of positivity: {nouns}')
    # elif sentiment == 'Negative':
        # nouns = get_noun(text)
        # print(f'Negative word: {top_neg_word(text)}')
        # print(f'Cause of negativity: {nouns}')


tofind = processed_df['cleaned_text']


processed_df['sentiment'] = processed_df.apply(lambda row: get_sentiment(row['cleaned_text']), axis=1)

test = processed_df


# for x in test.sentiment:
#   if x == 'Neutral':
#     test['score'] = 2;
#   if x == 'Negative':
#     test['score']= 0;
#   if x == 'Positive':
#     test['score'] = 1;




def scoreadd(test):
    df1 = test[['cleaned_text','sentiment']]
    sentiment_dict = {'Negative':0, 'Positive':1, 'Neutral':2}    
    test['score'] = test['sentiment'].map(sentiment_dict)
    return test

newtest = scoreadd(test)


df1 = newtest[['cleaned_text', 'sentiment','score']]

df1.groupby(df1['score']).count()

# Commented out IPython magic to ensure Python compatibility.
# %matplotlib inline
import matplotlib.pyplot as plt
plt.close("all")
import numpy as np

exp_vals = df1['score']
exp_labels = df1['sentiment']

ypos = np.arange(len(exp_vals))

plt.bar(exp_labels,ypos)
plt.axis('equal')
plt.pie(exp_vals)
plt.show
