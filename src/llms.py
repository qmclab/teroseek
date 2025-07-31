


from setting import *
from volcenginesdkarkruntime import Ark


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

def get_embedding(question):
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










