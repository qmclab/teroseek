



import pandas as pd
from src.llms import *

"""
in the finst step, we clean and summary all paragraph in linteratures
then vectoize all chunks by summary with an embedding model
finally, split all part with introduction(I), method(M), result(R), discussion(D) and conclusion(C)
save into a parquet file to accelerate storage and reading
"""

df_chunks = pd.read_csv("data/all_chunks.csv")
df_chunks["embedding"] = df_chunks["summary"].apply(get_embedding)
df_chunks["embedding_norm"] = df_chunks["embedding"].apply(sliced_norm_l2)
df_chunks["type"] = df_chunks["chunk_id"].str[9]
df_chunks_I = df_chunks[df_chunks["type"]=="I"]
df_chunks_M = df_chunks[df_chunks["type"]=="M"]
df_chunks_R = df_chunks[df_chunks["type"]=="R"]
df_chunks_D = df_chunks[df_chunks["type"]=="D"]
df_chunks_C = df_chunks[df_chunks["type"]=="C"]
df_chunks_I.to_parquet("data/chunks_I.parquet")
df_chunks_M.to_parquet("data/chunks_M.parquet")
df_chunks_R.to_parquet("data/chunks_R.parquet")
df_chunks_D.to_parquet("data/chunks_D.parquet")
df_chunks_C.to_parquet("data/chunks_C.parquet")


