# TeroSeek
An intelligent dialogue platform exclusively dedicated to terpenoids research


## Create environment
```bash
conda create -n teroseek python=3.11
conda activate teroseek
conda install numpy pandas pyarrow
pip install nltk rank_bm25 uvicorn fastapi
pip install --upgrade "volcengine-python-sdk[ark]"
```




## 1: parse initial data
```bash
python 1_parse_literature.py
```
## 2: embedding all chunks
```bash
python 2_embedding_chunks.py
```
## 3: Start retreival server
```bash
python 3_app.py
```
## 4: Test retreival
```bash
 curl -X POST "http://localhost:9999/retrieve" -H "Content-Type: application/json" -d '{"query":"what is terpene?", "top_k":1}'
```
