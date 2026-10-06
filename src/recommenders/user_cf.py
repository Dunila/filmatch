import pandas as pd
import numpy as np
import sqlite3
import json
from tqdm import tqdm 
from IPython.display import clear_output

import matplotlib.pyplot as plt
import seaborn as sns


def corr_pearson(vector1, vector2):
    """Returns Pearson's coefficient of correlation of two vectors"""
    v1_mean, v2_mean = vector1.mean(), vector2.mean()
    res1, res2 = vector1 - v1_mean, vector2 - v2_mean
    a = sum(res1*res2) 
    b = np.sqrt(sum(res1**2))*np.sqrt(sum(res2**2))
    #print(a, b)
    if b == 0:
        b = 0.0001
    return np.float64(a / b)


def measure_jaccard(vector1, vector2):
    """Returns Jaccard measure or inersection over union measure on two sets.
    Set here are indeces where user left rating or indeces where vector notna. 
    """
    isnan1 = np.isnan(vector1).astype(int)
    isnan2 = np.isnan(vector2).astype(int)
    combined = isnan1 + isnan2
    #print(combined)
    intersection = len(np.where(combined == 0)[0])
    #print(intersection)
    ex_union = len(np.where(combined == 1)[0])
    #print(ex_union+intersection)
    if ex_union == 0:
        return 0
    return np.float64(intersection / (ex_union + intersection))

def common_rated_indices(vec1, vec2):
    """Returns indecies where in vec1 and vec2 at once are ratings."""
    mask = ~np.isnan(vec1) & ~np.isnan(vec2)
    #print(mask)
    return np.where(mask)[0] 

def similarity_user(df, i_user1, i_user2, criterion="combined", theta=0.5):
    """
    params:
        df - pd.DataFrame where rows represents users, columns represents film, value in a cell represents user's rating of film 
        i_user1, i_user2 - int index of users in the df
        criterion - str 
            "pearson" - measure of similarity will be taken from Pearson's correlation coefficient only
            "jaccard" - measure of similarity will be taken from Jaccard's measure only
            "combined" - measure of similarity will be combined from Pearson's correlation coefficient and Jaccard's measure
        theta - float constrainted by [0, 1] - coefficient to wheight influence between types of measures if criterion = combined.
            By default 0.5 so influences are the same. 
            If theta -> 1 so correlation coefficient influences more 
    -----------------------
    returns:
        measure of similarity between two users. Users are recieved from dataframe df by their numeric indecies
    """
    if not criterion in ["combined", "pearson", "jaccard"]:
        criterion = "combined"

    if isinstance(i_user1, str):
        i_user1 = df.index.get_loc(i_user1)
    if isinstance(i_user2, str):
        i_user2 = df.index.get_loc(i_user2)
    
    if i_user1 == i_user2:
        return -0.99
    
    indexes = common_rated_indices(df.iloc[i_user1, :], df.iloc[i_user2, :])
    a = df.iloc[i_user1, indexes]
    b = df.iloc[i_user2, indexes]
    
    if criterion == "pearson":
        similarity = corr_pearson(a, b)
    elif criterion == "jaccard":
        similarity = measure_jaccard(df.iloc[i_user1, :], df.iloc[i_user2, :])
    elif criterion == "combined":
        corr = corr_pearson(a, b)
        measure = measure_jaccard(df.iloc[i_user1, :], df.iloc[i_user2, :])
        similarity = theta*corr + (1-theta)*measure
    else:
        print("No such criterion, picked Pearson")
        similarity = corr_pearson(a, b)
    return similarity

def estimate_rating(df, u, i, similar_users=pd.Series([]), thrashold_corr=0.5, thrashold_cnt=5):
    """
    params:
        df - pd.DataFrame where rows represents users, columns represents film, value in a cell represents user's rating of film
        u -int represents index of user
        i - int represents index of film
        thrashold_corr - float taken as threshold - minimum of similarity measure value to consider users similar.
        thrashold_cnt - int taken as maximum count of users to consider as similar to user u
    returns:
        estimating rating based on collabrative filtration on user2user recomendation. We'll base on hypothesis that similar users will 
        rate same film alike
    """
    if isinstance(u, str):
        u = df.index.get_loc(u)
    if isinstance(i, str):
        i = df.columns.get_loc(i)

    if similar_users.empty:
        similar_users = df.apply(lambda x: similarity_user(df, u, df.index.get_loc(x.name)), axis=1).sort_values(ascending=False)
        similar_users = similar_users[similar_users>thrashold_corr][:thrashold_cnt]
    
    r_of_similars = df.loc[similar_users.index, df.columns[i]]


    mask = ~r_of_similars.isna()
    r_of_similars = r_of_similars[mask]
    similar_users = similar_users[mask]
    
    cnt_rating = r_of_similars.count()

    s = sum(similar_users*r_of_similars)
    t = sum(np.abs(similar_users))
    #print(s, t)
    if t == 0:
        t = 0.001
    return (round(np.float64(s / t), 4), cnt_rating)
