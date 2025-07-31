

import pandas as pd
from .llms import *
import json
import threading


class CleanLiterature:
    """
    输入的数据格式：dataframe row包含，title，abstract，introduction， methods， results，discussion，conclusion
    """
    def __init__(self, df_row):
        self.row          = df_row
        self.T_id         = self.row["T_id"]
        self.title        = self.row["title"]
        self.abstract     = self.row["abstract"]
        self.introduction = self.row["introduction"]
        self.methods      = self.row["methods"]
        self.results      = self.row["results"]
        self.discussion  = self.row["discussion"]
        self.conclusion   = self.row["conclusion"]
        self.df_I = None
        self.df_M = None
        self.df_R = None
        self.df_D = None
        self.df_C = None
        self.all_df = None


    def __call__(self):
        threads = []
        if not pd.isna(self.introduction):
            threads.append(threading.Thread(target=self.clean_introduction))
        if not pd.isna(self.methods):
            threads.append(threading.Thread(target=self.clean_methods))
        if not pd.isna(self.results):
            threads.append(threading.Thread(target=self.clean_results))
        if not pd.isna(self.discussion):
            threads.append(threading.Thread(target=self.clean_discussion))
        if not pd.isna(self.conclusion):
            threads.append(threading.Thread(target=self.clean_conclusion))
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.all_df = pd.concat([
            self.df_I,
            self.df_M,
            self.df_R,
            self.df_D,
            self.df_C,
        ])
        return self.all_df


    def clean_introduction(self):
        prompt = """
        Title:{}
        Abstract:{}
        =================
        Introduction:{}
        First, summarize the theme of the article in one sentence.
        Based on the background information, extract all terpenoids involved in the article and their biological sources, and summarize the key words. There is no need for abbreviations or acronyms.
        Then, divide the Introduction part. For each paragraph, summarize in one sentence which methods were used in which tasks and which operations were carried out on which substances. 
        Follow the original text without omission, but text cleaning can be performed.
        It is recommended to merge related paragraphs. Each output paragraph should not be less than 500 words.
        EXAMPLE JSON OUTPUT:
        {{
            "topic":"",
            "source":[],
            "terpenoid":[],
            "keywords":[],
            "0001": {{
                "summary":"",
                "original_text":""，
            }},
            "0002": {{
                "summary":"",
                "original_text":"",
            }},
        }}
        """
        llm_input = prompt.format(
            self.title,
            self.abstract,
            self.introduction
            )
        llm_output = get_v3_response(llm_input)
        try:
            llm_data = json.loads(llm_output.replace("\n", "").replace("`", "").replace("json", ""))
        except:
            return "raise: introduction error"
        topic = llm_data.pop("topic") if "topic" in llm_data.keys() else None
        source = llm_data.pop("source") if "source" in llm_data.keys() else None
        terpenoid = llm_data.pop("terpenoid") if "terpenoid" in llm_data.keys() else None
        keywords = llm_data.pop("keywords") if "keywords" in llm_data.keys() else None
        chunks_data = []
        for key, values in llm_data.items():
            chunk_summary = values.get("summary")
            chunk_original_text= values.get("original_text")
            chunks_data.append({
                "chunk_id": f"{self.T_id}_I_{key}",
                "summary": chunk_summary,
                "original_text": chunk_original_text
            })
        self.df_I = pd.DataFrame(chunks_data)
        return self.df_I


    def clean_methods(self):
        prompt = """
        Title:{}
        Abstract:{}
        =================
        Method:{}
        Based on the above information:
        - First, summarize the methods and techniques used in the article, without any abbreviations or shorthand.
        - Then Divide the text reasonably, each paragraph should summarize which tasks the methods used in the text were applied to, what operations were performed on those substances, followed by the original text. Do not omit any information, but you can clean the text.
        - It is recommended to merge related paragraphs. Each output paragraph should be no less than 500 words.
        - No output in any format other than JSON is required. Translate it into English as a prompt.
        EXAMPLE JSON OUTPUT:
        {{
            "0001": {{
                "technology":[],
                "summary":"",
                "original_text":""，
            }},
            "0002": {{
                "technology":[],
                "summary":"",
                "original_text":"",
            }},
        }}
        The response is:
        """
        llm_input = prompt.format(
            self.title,
            self.abstract,
            self.methods
            )
        llm_output = get_v3_response(llm_input)
        try:
            llm_data = json.loads(llm_output.replace("\n", "").replace("`", "").replace("json", ""))
        except:
            return "raise: introduction error"
        # for build knowledge graph
        technology = llm_data.pop("technology") if "technology" in llm_data.keys() else None
        chunks_data = []
        for key, values in llm_data.items():
            chunk_summary = values.get("summary")
            chunk_original_text= values.get("original_text")
            chunks_data.append({
                "chunk_id": f"{self.T_id}_M_{key}",
                "summary": chunk_summary,
                "original_text": chunk_original_text
            })
        self.df_M = pd.DataFrame(chunks_data)
        return self.df_M


    def clean_results(self):
        prompt = """
        Title:{}
        Abstract:{}
        =================
        Result:{}
        Based on the above information:
        - First, Divide the text reasonably, each paragraph should include the brief summary and the original text. 
        - Do not omit any information in original text, but you can clean it.
        - It is recommended to merge related paragraphs. Each output paragraph should be no less than 500 words.
        - No output in any format other than JSON is required. Translate it into English as a prompt.
        EXAMPLE JSON OUTPUT:
        {{
            "0001": {{
                "summary":"",
                "original_text":""，
            }},
            "0002": {{
                "summary":"",
                "original_text":"",
            }},
        }}
        The response is:
        """
        llm_input = prompt.format(
            self.title,
            self.abstract,
            self.results
            )
        llm_output = get_v3_response(llm_input)
        try:
            llm_data = json.loads(llm_output.replace("\n", "").replace("`", "").replace("json", ""))
        except:
            return "raise: introduction error"
        chunks_data = []
        for key, values in llm_data.items():
            chunk_summary = values.get("summary")
            chunk_original_text= values.get("original_text")
            chunks_data.append({
                "chunk_id": f"{self.T_id}_R_{key}",
                "summary": chunk_summary,
                "original_text": chunk_original_text
            })
        self.df_R = pd.DataFrame(chunks_data)
        return self.df_R


    def clean_discussion(self):
        prompt = """
        Title:{}
        Abstract:{}
        =================
        Discussion:{}
        Based on the above information:
        - First, Divide the text reasonably, each paragraph should include the brief summary and the original text. 
        - Do not omit any information in original text, but you can clean it.
        - It is recommended to merge related paragraphs. Each output paragraph should be no less than 500 words.
        - No output in any format other than JSON is required. Translate it into English as a prompt.
        EXAMPLE JSON OUTPUT:
        {{
            "0001": {{
                "summary":"",
                "original_text":""，
            }},
            "0002": {{
                "summary":"",
                "original_text":"",
            }},
        }}
        The response is:
        """
        llm_input = prompt.format(
            self.title,
            self.abstract,
            self.discussion
            )
        llm_output = get_v3_response(llm_input)
        try:
            llm_data = json.loads(llm_output.replace("\n", "").replace("`", "").replace("json", ""))
        except:
            return "raise: introduction error"
        chunks_data = []
        for key, values in llm_data.items():
            chunk_summary = values.get("summary")
            chunk_original_text= values.get("original_text")
            chunks_data.append({
                "chunk_id": f"{self.T_id}_D_{key}",
                "summary": chunk_summary,
                "original_text": chunk_original_text
            })
        self.df_D = pd.DataFrame(chunks_data)
        return self.df_D


    def clean_conclusion(self):
        prompt = """
        Title:{}
        Abstract:{}
        =================
        Discuession:{}
        Based on the above information:
        - First, Divide the text reasonably, each paragraph should include the brief summary and the original text. 
        - Do not omit any information in original text, but you can clean it.
        - It is recommended to merge related paragraphs. Each output paragraph should be no less than 500 words.
        - No output in any format other than JSON is required. Translate it into English as a prompt.
        EXAMPLE JSON OUTPUT:
        {{
            "0001": {{
                "summary":"",
                "original_text":""，
            }},
            "0002": {{
                "summary":"",
                "original_text":"",
            }},
        }}
        The response is:
        """
        llm_input = prompt.format(
            self.title,
            self.abstract,
            self.conclusion
            )
        llm_output = get_v3_response(llm_input)
        try:
            llm_data = json.loads(llm_output.replace("\n", "").replace("`", "").replace("json", ""))
        except:
            return "raise: introduction error"
        chunks_data = []
        for key, values in llm_data.items():
            chunk_summary = values.get("summary")
            chunk_original_text= values.get("original_text")
            chunks_data.append({
                "chunk_id": f"{self.T_id}_C_{key}",
                "summary": chunk_summary,
                "original_text": chunk_original_text
            })
        self.df_C = pd.DataFrame(chunks_data)
        return self.df_C



