#!/home/kangx/.conda/envs/teroseek/bin/python

import os
import nltk
nltk.data.path.append("teroseek_data/nltk_data")
import numpy as np
import pandas as pd
from rank_bm25 import BM25Okapi
from nltk.tokenize import word_tokenize
from volcenginesdkarkruntime import Ark


# LLM API
# 使用火山引擎api，具体见火山引擎官方网站。
ARK_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
# TeroSeek子项目
AEK_API_KEY = "104510e0-cf1d-447d-a2d1-a9d47407f1"
DS_V3_ID = "ep-20250626163448-hrc8p"
DS_R1_ID = "ep-20250626163310-rkbpc"    # 0528-cb
DOUBAO_EMBEDDING_ID = "ep-20250626163553-ff2nq"

client = Ark(
    base_url=ARK_BASE_URL,
    api_key=AEK_API_KEY,
)
def get_v3_response(query):
    # deepseek-v3-0324
    completion = client.chat.completions.create(
        model=DS_V3_ID,
        messages=[
            {"role": "user", "content": query},
        ],
    )
    return completion.choices[0].message.content

def get_embedding(question, dim=512):
    resp = client.embeddings.create(
        model=DOUBAO_EMBEDDING_ID,
        input=question
    )
    return resp.data[0].embedding

def sliced_norm_l2(vec, dim=2560):
    import numpy as np
    vec = np.array(vec[:dim], dtype=np.float32)
    norm = np.linalg.norm(vec).astype(np.float32)
    return vec / norm

def retrival_top_k(__df__, query_vector, k=30):
    import numpy as np
    import pandas as pd
    """
    input: datafram with "chunk_id", "embedding"
    output: DataFrame with "chunk_id", "dot_product(score)"
    """
    embeddings_matrix = np.vstack(__df__['embedding'].values)
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
        """
        初始化BM25检索系统
        
        :param paragraphs: 字符串列表，包含所有候选段落
        :param tokenizer: 分词函数，默认为NLTK的word_tokenize
        """
        self.T_ids = list(paragraphs_data.keys())
        self.paragraphs = list(paragraphs_data.values())
        self.tokenizer = tokenizer
        self.tokenized_corpus = self._tokenize_corpus(self.paragraphs)
        self.bm25 = BM25Okapi(self.tokenized_corpus)
    
    def _tokenize_corpus(self, corpus):
        """分词处理所有段落"""
        return [self.tokenizer(doc.lower()) for doc in corpus]
    
    def _tokenize_query(self, query):
        """分词处理查询"""
        return self.tokenizer(query.lower())
    
    def search(self, keywords):
        """
        执行关键词检索
        """
        # 将关键词列表合并为查询字符串
        query = " ".join(keywords)
        tokenized_query = self._tokenize_query(query)
        # 获取BM25分数
        doc_scores = self.bm25.get_scores(tokenized_query)
        # 将结果与原始段落配对
        results = list(zip(self.T_ids, self.paragraphs, doc_scores))
        results.sort(key=lambda x: x[-1], reverse=True)
        return results

def retrival_sorted_data(query, threshold=200):
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


df_introduction = pd.read_parquet("teroseek_data/article/chunks_introduction.parquet")
df_introduction["embedding"] = df_introduction["embedding"].apply(sliced_norm_l2)
print("df_introduction loaded, shape:", df_introduction.shape)
df_method = pd.read_parquet("teroseek_data/article/chunks_method.parquet")
df_method["embedding"] = df_method["embedding"].apply(sliced_norm_l2)
print("df_method loaded, shape:", df_method.shape)
df_result = pd.read_parquet("teroseek_data/article/chunks_result.parquet")
df_result["embedding"] = df_result["embedding"].apply(sliced_norm_l2)
print("df_result loaded, shape:", df_result.shape)
df_discuession = pd.read_parquet("teroseek_data/article/chunks_discuession.parquet")
df_discuession["embedding"] = df_discuession["embedding"].apply(sliced_norm_l2)
print("df_discuession loaded, shape:", df_discuession.shape)
df_conclusion = pd.read_parquet("teroseek_data/article/chunks_conclusion.parquet")
df_conclusion["embedding"] = df_conclusion["embedding"].apply(sliced_norm_l2)
print("df_conclusion loaded, shape:", df_conclusion.shape)
paper_info_df = pd.read_csv("teroseek_data/.data/TA_info.csv")



import uvicorn
from typing import List, Dict, Any
from fastapi import FastAPI, Body
from fastapi import Query

app = FastAPI(title="LlamaIndex RAG API for article")
@app.post("/retrieve", response_model=Dict[str, Any])
async def retrieve_documents(
    query: str = Body(..., description="检索查询内容"),
    top_k: int = Body(1, description="返回结果数量")):
    if top_k == 0:
        vector_top_k = 100
        keyword_top_k = 10
    elif top_k == 1:
        vector_top_k = 300
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
        # _ref_data["ref_id"] = f"ref_{ref_id}"
        # ref_text += f"ref_{ref_id}: {doc}\n"
    return {"ref_msg":ref_msg_list, "ref_text": ref_text_list}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9999)

