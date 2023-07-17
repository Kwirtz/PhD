import tqdm
import pymongo
import pandas as pd
from collections import defaultdict

client = pymongo.MongoClient("mongodb://localhost:27017")
mydb = client["openAlex"]
collection = mydb["works"]


docs = collection.find()
pub_info = defaultdict(lambda: defaultdict(int))

for doc in tqdm.tqdm(docs):
    if len(doc["authorships"]) == 0:
        continue
    year = doc["publication_year"]
    pub_info[year]["n"] += 1
    if len(doc["authorships"]) == 1:
        pub_info[year]["n_solo"] += 1
    if len(doc["authorships"]) > 1:
        countries = []
        for author in doc["authorships"]:
            for inst in author["institutions"]:
                try:
                    countries.append(inst["country_code"])
                except:
                    pass
        if len(list(set(countries))) > 1:
            pub_info[year]["n_inter"] += 1
        else:
            pub_info[year]["n_not_inter"] += 1

pub_info.pop(None)
list_of_insertion = []
for year in tqdm.tqdm(pub_info):
    if year > 2020:
        continue
    list_of_insertion.append([year, pub_info[year]["n"], pub_info[year]["n_inter"], pub_info[year]["not_inter"], pub_info[year]["n_solo"]])

df = pd.DataFrame(list_of_insertion, columns = ["year", "n", "n_inter", "not_inter", "n_solo"])
df = df.sort_values(by=['year'], ascending=True)

df.to_csv("plots/Fig1.csv")
