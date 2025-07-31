


import pandas as pd
from src.clean_literatures import CleanLiterature
from tqdm import tqdm

source_data_path = "data/teroseek_data_pubmed_1000_demo.csv"
df_initial = pd.read_csv(source_data_path)
print(df_initial.columns)
"""
Original Data Storage Format:
T_id: The index of the literature in the Teroseek knowledge base
Includes article metadata: doi, title, abstract, authors, year, journal, etc.
Article section text information: introduction, methods, results, discussion, conclusion
Database source information: wos, scopus, pubmed
All data is obtained from open-access articles in PubMed
df_initial.columns:

Index(['T_id', 'doi', 'title', 'abstract', 'authors', 'year', 'journal',
       'relevant', 'wos', 'scopus', 'pubmed', 'introduction', 'methods',
       'results', 'discussion', 'conclusion'],
      dtype='object')
"""


df = pd.DataFrame()
for _, row in tqdm(df_initial.iterrows()):
    cleanner = CleanLiterature(row)
    df_output = cleanner()
    df = pd.concat([df, df_output])
    df.to_csv("data/all_chunks.csv", index=False)

