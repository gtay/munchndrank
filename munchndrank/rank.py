import numpy as np
from scipy.sparse import lil_matrix, coo_matrix
from scipy.spatial.distance import sqeuclidean
from munchndrank.models import *
from operator import itemgetter
import math

# entry point
# takes in a list of dictd, each object with a col number and a float value
# returns an ordered list of relevant recipes by ID
def getRankList(dictlist, searchkey, dictsize):
  dictsize = dictsize + 1; # to be 1-index
  searchvec = lil_matrix((1,dictsize));
  for k in searchkey:
    if not k == 'id':
      searchvec[0,int(k)] = 1;
  searchvec = searchvec.tocsc();

  veclist = [];
  for d in dictlist:
    vec = lil_matrix((1,dictsize));
    for k in d:
      if not k == 'id':
        vec[0,int(k)] = 1;
    veclist.append(vec.tocsc());
  
  for v in range(len(veclist)):
  # perform scoring function
    score = score_func(searchvec, veclist[v]);
    dictlist[v]['score'] = score;

  new_list = sorted(dictlist,key=itemgetter('score'))
  return new_list;

def score_func(searchvec, currvec):
  # this performs the cosine similarity
  # -1 is the most similar
  # 1 is the most different
  numerator = searchvec.dot(currvec.transpose());
  s2 = searchvec.multiply(searchvec);
  s3 = math.sqrt(s2.sum());
  c2 = currvec.multiply(currvec);
  c3 = math.sqrt(c2.sum());
  score = numerator[0,0] / (s3 * c3);
  return -1 * score;
