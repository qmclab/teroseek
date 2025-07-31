
import nltk
nltk.data.path.append("data/nltk_data")
from rank_bm25 import BM25Okapi
from nltk.tokenize import word_tokenize
import numpy as np
import pandas as pd
from src.llms import *




def retrival_top_k(__df__, query_vector, k=30):
    """
    input: datafram with "chunk_id", "embedding"
    output: DataFrame with "chunk_id", "dot_product(score)"
    """
    embeddings_matrix = np.vstack(__df__['embedding_norm'].values)
    dot_products = np.dot(embeddings_matrix, query_vector)
    top_k_indices = np.argpartition(dot_products, -k)[-k:]
    top_k_indices = top_k_indices[np.argsort(-dot_products[top_k_indices])]
    result_df = __df__.iloc[top_k_indices].copy()[["chunk_id", "summary", "original_text"]]
    result_df['dot_product'] = dot_products[top_k_indices]
    return result_df

def search_doc_by_id(chunk_id):
    # chunk_id: TAXXXXXX_X_XXXX
    if "I" in chunk_id:
        return df_introduction[df_introduction["chunk_id"]==chunk_id]["original_text"].values[0]
    if "M" in chunk_id:
        return df_method[df_method["chunk_id"]==chunk_id]["original_text"].values[0]
    if "R" in chunk_id:
        return df_result[df_result["chunk_id"]==chunk_id]["original_text"].values[0]
    if "D" in chunk_id:
        return df_discuession[df_discuession["chunk_id"]==chunk_id]["original_text"].values[0]
    if "C" in chunk_id:
        return df_conclusion[df_conclusion["chunk_id"]==chunk_id]["original_text"].values[0]

class BM25Retrieval:
    def __init__(self, paragraphs_data, tokenizer=word_tokenize):
        self.T_ids = list(paragraphs_data.keys())
        self.paragraphs = list(paragraphs_data.values())
        self.tokenizer = tokenizer
        self.tokenized_corpus = self._tokenize_corpus(self.paragraphs)
        self.bm25 = BM25Okapi(self.tokenized_corpus)
    
    def _tokenize_corpus(self, corpus):
        return [self.tokenizer(doc.lower()) for doc in corpus]
    
    def _tokenize_query(self, query):
        return self.tokenizer(query.lower())
    
    def search(self, keywords):
        query = " ".join(keywords)
        tokenized_query = self._tokenize_query(query)
        doc_scores = self.bm25.get_scores(tokenized_query)
        results = list(zip(self.T_ids, self.paragraphs, doc_scores))
        results.sort(key=lambda x: x[-1], reverse=True)
        return results

def retrival_sorted_data(query, threshold=20):
    query_vector = sliced_norm_l2(get_embedding(query))
    retrival_df = pd.concat([
        retrival_top_k(df_introduction, query_vector, k=threshold),
        retrival_top_k(df_method, query_vector, k=threshold),
        retrival_top_k(df_result, query_vector, k=threshold),
        retrival_top_k(df_discuession, query_vector, k=threshold),
        retrival_top_k(df_conclusion, query_vector, k=int(threshold/2)),
    ])
    retrival_data = {}
    for _id in retrival_df["chunk_id"].tolist():
        T_id, chunk_type, chunk_id = _id.split("_")
        if T_id not in retrival_data.keys():
            retrival_data[T_id] = {
                "I": [],
                "M": [],
                "R": [],
                "D": [],
                "C": [],
            }
        retrival_data[T_id][chunk_type].append(chunk_id)
    for k,v in retrival_data.items():
        _data = []
        for _k, _v in v.items():
            if len(_v) == 0:
                continue
            _v = sorted(_v)
            for __v in _v:
                _data.append(f"{k}_{_k}_{__v}")
        retrival_data[k] = _data
    sorted_dict = dict(sorted(retrival_data.items(), key=lambda item: len(item[1]), reverse=True))
    return sorted_dict

def generate_keywords(query):
    keywords = None
    keywords_prompt = """
    {}
    Based on this question, generate up to five most important key englist words
    the kewords must be in english
    EXAMPLE JSON OUTPUT:
    {{
        "keywords": []
    }}
    """
    while not keywords:
        try:
            response_kw = get_v3_response(keywords_prompt.format(query))
            response_kw = response_kw.replace("`", '').replace("\n", '').replace("json", '')
            keywords = eval(response_kw)["keywords"]
        except:
            print("Error parsing keywords, retrying...")
            keywords = None
    return keywords

def keyword_filter(filter_data, keywords, top_k=30):
    msgs = {}
    for k, v in list(filter_data.items())[:200]:
        if k not in msgs:
            msgs[k] = ""
        for _id in v:
            msgs[k] += search_doc_by_id(_id)
    retriever = BM25Retrieval(msgs)
    all_results = retriever.search(keywords)
    return all_results[:top_k]

def get_paper_info(_df, T_id):
    _row = _df[_df["T_id"]==T_id]
    doi = _row.doi.values[0]
    title = _row.title.values[0]
    year = _row.year.values[0]
    authors = _row.authors.values[0]
    publisher = _row.publisher.values[0]
    return {
        "T_id": str(T_id),
        "doi": str(doi) if not pd.isna(doi) else "",
        "title": str(title) if not pd.isna(title) else "",
        "year": str(year) if not pd.isna(year) else "",
        "authors": str(authors) if not pd.isna(authors) else "",
        "publisher": str(publisher) if not pd.isna(publisher) else ""
    }



df_introduction = pd.read_parquet("data/chunks_I.parquet")
print("df_introduction loaded, shape:", df_introduction.shape)

df_method = pd.read_parquet("data/chunks_M.parquet")
print("df_method loaded, shape:", df_method.shape)

df_result = pd.read_parquet("data/chunks_R.parquet")
print("df_result loaded, shape:", df_result.shape)

df_discuession = pd.read_parquet("data/chunks_D.parquet")
print("df_discuession loaded, shape:", df_discuession.shape)

df_conclusion = pd.read_parquet("data/chunks_C.parquet")
print("df_conclusion loaded, shape:", df_conclusion.shape)

paper_info_df = pd.read_csv("data/TA_info.csv")


# start fastapi

import uvicorn
from typing import List, Dict, Any
from fastapi import FastAPI, Body
from fastapi import Query

app = FastAPI(title="LlamaIndex RAG API for article")
@app.post("/retrieve", response_model=Dict[str, Any])
async def retrieve_documents(
    query: str = Body(..., description="query"),
    top_k: int = Body(1, description="top_k")):
    if top_k == 0:
        vector_top_k = 10
        keyword_top_k = 10
    elif top_k == 1:
        vector_top_k = 20
        keyword_top_k = 30

    keywords = generate_keywords(query)
    result_data = retrival_sorted_data(query, threshold=vector_top_k)
    result = keyword_filter(result_data, keywords, keyword_top_k)
    ref_msg_list = []
    ref_text_list = []
    for T_id, doc, score in result:
        _ref_data = get_paper_info(paper_info_df, T_id)
        ref_msg_list.append(_ref_data)
        ref_text_list.append(doc)
    return {"ref_msg":ref_msg_list, "ref_text": ref_text_list}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9999)

