# -*- coding: utf-8 -*-
"""test_program.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1KgYPX63JOPQE0EyBdsRwu3fw8FMAqmUB
"""


import os
import re
import csv
import numpy as np 
import pandas as pd 
from string import punctuation
from collections import defaultdict
from sklearn.preprocessing import StandardScaler
import pickle 
from keras.models import load_model
from keras.preprocessing.sequence import pad_sequences
# import sys
# sys.path.append('/content/drive/MyDrive/Project')
import feature_engineering

class Test:
  def __init__(self,tokenizer_name = 'tokenizer.pickle',ques_dict_name = 'q_dict.pickle',\
               ss_name = 'ss.pickle',model_name = 'model.h5'):
    
    with open(tokenizer_name, 'rb') as handle:
      self.tokenizer = pickle.load(handle)
    self.word_index = self.tokenizer.word_index
    print('Tokenizer Loaded')

    with open(ques_dict_name, 'rb') as handle:
      self.ques_dict = pickle.load(handle)
    print('Question Dict Loaded')

    with open(ss_name, 'rb') as handle:
      self.ss = pickle.load(handle)
    print('Standard Scalar Loaded')

    self.model = load_model(model_name)
    print('Model Loaded')

    self.test_question1 = []
    self.test_question2 = []
    self.featureEngineering = feature_engineering.FeatureEngineering()

  def text_to_wordlist(self,text):
    
    text = text.lower().split()
    text = " ".join(text)
    text = re.sub(r"coronavirus","corona virus 2019",text)
    text = re.sub(r"covid-19","corona virus 2019",text)
    text = re.sub(r"covid - 19","corona virus 2019",text)
    text = re.sub(r"[^A-Za-z0-9^,!.\/'+-=]", " ", text)
    text = re.sub(r"what's", "what is ", text)
    text = re.sub(r"\'s", " ", text)
    text = re.sub(r"\'ve", " have ", text)
    text = re.sub(r"can't", "cannot ", text)
    text = re.sub(r"n't", " not ", text)
    text = re.sub(r"i'm", "i am ", text)
    text = re.sub(r"\'re", " are ", text)
    text = re.sub(r"\'d", " would ", text)
    text = re.sub(r"\'ll", " will ", text)
    text = re.sub(r",", " ", text)
    text = re.sub(r"\.", " ", text)
    text = re.sub(r"!", " ! ", text)
    text = re.sub(r"\/", " ", text)
    text = re.sub(r"\^", " ^ ", text)
    text = re.sub(r"\+", " + ", text)
    text = re.sub(r"\-", " - ", text)
    text = re.sub(r"\=", " = ", text)
    text = re.sub(r"'", " ", text)
    text = re.sub(r":", " : ", text)
    text = re.sub(r"(\d+)(k)", r"\g<1>000", text)
    text = re.sub(r" e g ", " eg ", text)
    text = re.sub(r" b g ", " bg ", text)
    text = re.sub(r" u s ", " american ", text)
    text = re.sub(r" 9 11 ", "911", text)
    text = re.sub(r"e - mail", "email", text)
    text = re.sub(r"j k", "jk", text)
    text = re.sub(r"\s{2,}", " ", text)
    
    return text
  
  def tokenization(self,df):

    for text in df.question1.values:
      self.test_question1.append(self.text_to_wordlist(text))
      
    for text in df.question2.values:
      self.test_question2.append(self.text_to_wordlist(text))

    self.test_question1 = self.tokenizer.texts_to_sequences(self.test_question1)  
    self.test_question2 = self.tokenizer.texts_to_sequences(self.test_question2)

    #print('Tokenization Done....')

    MAX_SEQUENCE_LENGTH = 60  
    self.test_question1 = pad_sequences(self.test_question1, maxlen=MAX_SEQUENCE_LENGTH)  
    self.test_question2 = pad_sequences(self.test_question2, maxlen=MAX_SEQUENCE_LENGTH)  
    print('Shape of test data vtensor:', self.test_question1.shape)

  def feature_extraction(self,df):
    questions = pd.concat([df[['question1', 'question2']]], axis=0).reset_index(drop='index')
    for i in range(questions.shape[0]):
            self.ques_dict[questions.question1[i]].add(questions.question2[i])
            self.ques_dict[questions.question2[i]].add(questions.question1[i])
    df['q1_q2_intersect'] = df.apply(lambda row: len(set(self.ques_dict.get(row[1])).intersection(set(self.ques_dict.get(row[2])))), axis=1, raw=True)
    df['q1_freq'] = df.apply(lambda row: len(self.ques_dict.get(row[1])), axis=1, raw=True)
    df['q2_freq'] = df.apply(lambda row: len(self.ques_dict.get(row[2])), axis=1, raw=True)

    print('Feature Extraction Completed..')
    return df

  def leak_calculator(self,df,df_nlp):
    df_nlp = df_nlp.fillna(0)
    df['test_id'] = df_nlp['test_id']

    df = df.merge(df_nlp,on='test_id',how='left')
    leak = df.drop(['test_id','question1','question2'], axis=1)
    print(leak)
    leak = self.ss.transform(leak)
    
    print('Leak Data Completed..')
    return leak


  def predict(self,question1,question2):
    self.test_question1 = []
    self.test_question2 = []
    df = pd.DataFrame(data=[[0,question1,question2]] , columns=['test_id','question1','question2'])
    self.tokenization(df)
    df = self.feature_extraction(df)
    df_nlp = self.featureEngineering.two_question(question1,question2)
    leaks = self.leak_calculator(df,df_nlp)
    preds = self.model.predict([self.test_question1, self.test_question2, leaks], batch_size=8192, verbose=1,)
    preds += self.model.predict([self.test_question2, self.test_question1, leaks], batch_size=8192, verbose=1)
    return preds[0][0]/2


