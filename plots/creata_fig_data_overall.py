import tqdm
import pickle
import pymongo
import numpy as np
import pandas as pd
from itertools import permutations 
from itertools import combinations
from collections import defaultdict


Client = pymongo.MongoClient("mongodb://localhost:27017")
db = Client["openAlex"]
collection_work = db["works"]    
collection_authors = db["author_profile"]    

#%% Fig1_b Share solo authors and companies

def idk():
    list_of_insertion = []
    for year in tqdm.tqdm(range(2016,2021)):
        docs = collection_work.find({"publication_year":year})
        n_solo_authors = 0
        n_companies = 0
        n = 0
        for doc in tqdm.tqdm(docs):
            n += 1
            comp_part = False
            if doc["authorships"]:
                if len(doc["authorships"]) == 1:
                    n_solo_authors += 1
                for author in doc["authorships"]:
                    for inst in author["institutions"]:
                        try:
                            if inst["type"] == "company":
                                comp_part = True
                        except:
                            continue
            if comp_part == True:
                n_companies += 1
        list_of_insertion.append([year,n,n_solo_authors,n_companies])
        
    
    df = pd.DataFrame(list_of_insertion, columns = ["year","publications","n_solo_authors","n_companies"])        
    df["share_solo_authors"] = df["n_solo_authors"]/df["publications"]
    df["share_companies"] = df["n_companies"]/df["ai_publications"]
    df.to_csv("Data/Fig1_b_notai.csv",index=False)



#%% Fig1_c Flow of researchers

unique_tags = []
docs = collection_authors.find({})

i = 0
for doc in tqdm.tqdm(docs):
    for year in range(2000,2021):
        try:
            unique_tags.append(doc[str(year)]["aff_type"])
        except:
            continue
    i += 1
    if i % 10000 ==0:
        unique_tags = list((set(unique_tags)))
unique_tags = list((set(unique_tags)))
unique_tags = [i for i in unique_tags if i not in [None]]

transition_tags = []
for comb in combinations(unique_tags, 2):
    transition_tags += ["_".join(i) for i in permutations(comb)]

transition = {year:defaultdict(int) for year in range(2000,2021)}
for year in range(2000,2021):
    context = list(range(year-1, year+2))
    query = {str(i):{"$exists":1,"$ne":None} for i in context }
    docs = collection_authors.find(query)
    for doc in tqdm.tqdm(docs):
        if "true_ai" not in doc:
            if doc[str(year-1)]["aff_type"] != doc[str(year)]["aff_type"] and doc[str(year)]["aff_type"] == doc[str(year+1)]["aff_type"]:
                transition_name = doc[str(year-1)]["aff_type"]  + "_" + doc[str(year)]["aff_type"]
                transition[year][transition_name] += 1
            else:
                continue

df_transition_all = pd.DataFrame(np.zeros(shape = (len( list(range(2001,2021))),len(transition_tags)+1)), index = list(range(2001,2021)),columns = transition_tags+["Total"])
df_transition_all = df_transition_all.fillna(0)

for year in range(2000,2021):
    n = 0
    for tag in transition[year]:
        df_transition_all.at[year,tag] = transition[year][tag]
        n += transition[year][tag]
    df_transition_all.at[year,"Total"] = n

    
# edu-comp comp-edu

df_transition_comp_edu = pd.DataFrame()
for year in range(2000,2021):
    df_transition_comp_edu[year] = [transition[year]["education_company"],-transition[year]["company_education"]]
df_transition_comp_edu = df_transition_comp_edu.T
df_transition_comp_edu.columns = ["education_company","company_education"]
df_transition_comp_edu["year"] = list(range(2000,2021,1))

df_transition_comp_edu.to_csv("Data/Fig1_c_notai.csv", index=False)

#%% Fig1_d Institutions transition

unique_types = []
unique_names = []
docs = collection_authors.find({})

i = 0
for doc in tqdm.tqdm(docs):
    for year in range(2000,2021,1):
        try:
            unique_types.append(doc[str(year)]["aff_type"])
            unique_names.append(doc[str(year)]["aff_type"])
        except:
            continue
    i += 1
    if i % 10000 ==0:
        unique_types = list((set(unique_types)))
        unique_names = list((set(unique_names)))
        
unique_types = list((set(unique_types)))
unique_types = [i for i in unique_types if i not in [None]]

unique_names = list((set(unique_names)))
unique_names = [i for i in unique_names if i not in [None]]


transition_tags = []
for comb in combinations(unique_tags, 2):
    transition_tags += ["_".join(i) for i in permutations(comb)]

transition = {year:defaultdict(int) for year in range(2001,2021)}
for year in range(2001,2021):
    context = list(range(year-1, year+2))
    query = {str(i)+".aff_type":{"$exists":1,"$ne":None} for i in context }
    docs = collection_authors.find(query)
    for doc in tqdm.tqdm(docs):
        if "true_ai" not in doc:
            if doc[str(year-1)]["aff_type"] != doc[str(year)]["aff_type"] and doc[str(year)]["aff_type"] == doc[str(year+1)]["aff_type"]:
                transition_name = doc[str(year-1)]["aff_type"]  + "_" + doc[str(year)]["aff_type"]
                if transition_name == "education_company":
                    transition_inst = doc[str(year-1)]["aff_display_name"]  + "_" + doc[str(year)]["aff_display_name"]
                    transition[year][transition_inst] += 1
            else:
                continue
        
inst_tags = []
for year in tqdm.tqdm(range(2001,2021)):
    inst_tags += list(set(transition[year]))
    inst_tags = list(set(inst_tags))


df_transition_all = pd.DataFrame(np.zeros(shape = (len( list(range(2001,2021))),len(inst_tags)+1)), index = list(range(2001,2021)),columns = inst_tags+["Total"])
df_transition_all = df_transition_all.fillna(0)

for year in tqdm.tqdm(range(2001,2021)):
    n = 0
    for tag in tqdm.tqdm(transition[year]):
        df_transition_all.at[year,tag] = transition[year][tag]
        n += transition[year][tag]
    df_transition_all.at[year,"Total"] = n

pd.DataFrame(df_transition_all,columns= ["value"])
df_transition_all.sum()
df = pd.DataFrame()
df["education_company"] = df_transition_all.index
df.index = df_transition_all.index
df["value"] = df_transition_all

df[['education', 'company']] =  df.education_company.str.split("_", expand = True)
df = df.drop("Total")

universities =  list(df.groupby("education").sum("value").sort_values(by="value").tail(10).index)
companies = list(df.groupby("company").sum("value").sort_values(by="value").tail(10).index)

df = df[df['education'].isin(universities)][df['company'].isin(companies)].reset_index(drop=True)
df.to_csv("Data/Fig1_d_notai.csv")


#%% Fig4_a

with open("Data/authors_profile_cleaned.pickle", 'rb') as file:
    ai_researcher = list(pickle.load(file))

seniority_dropout = pd.read_csv("Data/seniority_dropout.csv")

seniority_dropout_notai = seniority_dropout[~seniority_dropout['AID'].isin(ai_researcher)]
seniority_dropout_notai.to_csv("Data/Fig4_a_notai.csv")
