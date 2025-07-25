
import time
import json
from flask import Blueprint, render_template
from flask import request, Response, jsonify
import requests
from .utils import *

bp_chat = Blueprint('bp_chat', 
                    __name__,
                    static_folder='static',
                    template_folder='templates'
                    )
# 内网路由，dell胖节点运行的服务
RETRIEVE_URL = "http://172.18.241.58:9999/retrieve"
# 加载数据
df_id_name = pd.read_csv("TKCid_name_small.csv")
print("TKCid_name_small.csv loaded in bp_chat/routes.py")
df_id_smi = pd.read_csv("TKCid_smi.csv")
print("TKCid_smi.csv loaded in bp_chat/routes.py")


def retirval_from_kb(query, level=0, start_id=1):
    """
    level = 0 简单检索，返回更短的结果
    level = 1 高级检索，返回更长的结果
    返回html的ref代码，和整段ref_text文本
    """
    # 假设性回答
    hr_prompt = """
    You are an expert in the field of terpenoids.
    Based on your knowledge, provide a brief answer to the current question, using no more than two sentences.
    the question is: {}
    """
    retirval_sentence = get_v3_response(hr_prompt.format(query))
    print(retirval_sentence)
    headers = {"Content-Type": "application/json"}
    payload = {"query": retirval_sentence, "top_k": level}
    response = requests.post(RETRIEVE_URL, headers=headers, data=json.dumps(payload))
    result_data = response.json()
    # 获取返回信息，直接获取ref_msg和ref_text
    ref_data_list = result_data.get("ref_msg", None)
    ref_text_list = result_data.get("ref_text", "No result found")
    # 进一步处理ref信息
    ref_msg_list = []
    ref_text_str = ""
    for ref_id, _ref_data in enumerate(ref_data_list, start=start_id):
        _ref_msg_html = generate_ref_html(_ref_data, ref_id)
        ref_msg_list.append(_ref_msg_html)
    for ref_id, _ref_text in enumerate(ref_text_list, start=start_id):
        ref_text_str += f"ref_{ref_id}: {_ref_text}\n"
    return ref_msg_list, ref_text_str


@bp_chat.route('/api/chat', methods=['POST'])
def chat():
    rag_prompt = """
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
    data = request.json
    # 跳过第一条欢迎信息
    user_message = data.get('messages', '')[1:]
    print(user_message)
    ref_msg_list = None
    if len(user_message) == 1:
        tmp_query = user_message[-1]["content"]
        # 保存用户查询记录
        with open("static/user_query.txt", "a") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {tmp_query}\n")
        # 保存用户查询记录
        ref_msg_list, ref_text = retirval_from_kb(tmp_query, level=1)
        ref_text = ref_text[:350000]
        print("当前参考信息的长度为：：：：", len(ref_text))
        user_message[-1]["content"] = rag_prompt.format(ref_text, tmp_query)
    return Response(generate(ref_msg_list, user_message, df_id_name, df_id_smi),
                     mimetype='text/plain')


@bp_chat.route('/api/get_teromol', methods=['POST'])
def get_teromol():
    data = request.json
    user_message = data.get('question', '')
    print("get_teromol", user_message)
    tero_prompt = """
    问题：{}
    判断问题中是否包含萜类分子的名称，
    如果有，则返回这个分子的英文名称，
    如果没有则返回"None"
    EXAMPLE JSON OUTPUT:
    {{
        "tero_name": "",
    }}
    """.format(user_message)
    tero_name = get_v3_response_json(tero_prompt)["tero_name"]
    if str(tero_name.strip()) == "None":
        return jsonify({'teromol': []})
    data = teromol_data(tero_name, df_id_name, df_id_smi)
    if not data:
        return jsonify({'teromol': []})
    return jsonify({'teromol': data})


@bp_chat.route('/')
def index():
    return render_template('qa.html')



