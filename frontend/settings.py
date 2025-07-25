
import os

# sysyem setting
# 邮件功能使用了中山大学的教育邮箱，具体配置参考企业邮箱官网
MAIL_SERVER = "smtp.exmail.qq.com"  # 邮件服务器地址
MAIL_PORT = 465  # 邮件服务器端口
MAIL_ACCOUNT = "kangx8@mail2.sysu.edu.cn"  # 邮箱账号
MAIL_PASSWORD = "29f7oiozuddS8KMd"  # 邮箱授权码, 不是登陆密码

# LLM API
# 使用火山引擎api，具体见火山引擎官方网站。
ARK_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
# TeroSeek子项目
AEK_API_KEY = ""
DS_V3_ID = "ep-20250626163448-hrc8p"
DS_R1_ID = "ep-20250626163310-rkbpc"    # 0528
DOUBAO_EMBEDDING_ID = "ep-20250626163553-ff2nq"
# kx 个人账号，暂时已经弃用
# AEK_API_KEY = "44ea595c-61c3-4af1-87fb-50464b5cc95a"
# DS_V3_ID = "ep-20250327150949-k85zh"
# DS_R1_ID = "ep-20250530154229-jjd8s"

# 通用设置，随着模型迭代，可以逐渐放宽
MAX_CONTENT_LEN= 400000



# review_model
REVIEW_PATH = 'bp_review'
REVIEW_OFFLINE_PATH = os.path.join(REVIEW_PATH, 'data')



# 内网路由，dell胖节点运行的服务
RETRIEVE_URL = "http://172.18.241.58:9999/retrieve"
# 用于在review模块生成主题
# {用户输入的话题}
RAG_TOPIC_PROMPT = """
You are an expert in the field of terpene research.
Based on the topic or question provided by the user, generate a list of sub-section titles for a review article in a progressive manner.
Then output all the sub-question titles in list form (do not more than {}), without any other content:
Note: The language used for inheritance issues,
If the user asks in Chinese, the generated sub-questions should also be in Chinese.
If the user asks in English, the generated sub-questions should also be in English.
The user's question is: {}
EXAMPLE JSON OUTPUT:
{{
    "sub_topic": [],
}}
"""
# 用于对每一个子问题进行增强检索
# {检索后的知识} {子问题}
RAG_REVIEW_PROMPT = """
You are an expert in the field of terpenoids.
Please refer to the background knowledge:
[background knowledge]:
{}
[Requirements for answering]
Make full use of the information, charts and data in the background knowledge to answer the questions
Do not omit the information in the reference materials
If the reference materials involve tables,
query：{}
"""
# 结合全部子问题回答生成最后综述
# {全部子问题的回答} {用户输入的话题}
RAG_SUMMARY_PROMPT = """
You are an expert in the field of terpenoids.
Merge the following materials and the article's theme is based on: {}
[content]: 
{}
[Note]: 
 - In your response, retain the quoted information from the original source (ref_x). At the same time, retain the original sequence numbers.
 - If there are multiple ref_, separate them with commas eg. (ref_x, ref_y). do not omit 'ref_'.
 - There is no need to repeat the citation of the literature at the end.
"""






