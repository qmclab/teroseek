
import re
import os
import time
import json
from flask import Blueprint, render_template
from flask import request, Response, jsonify
import requests
import uuid
import threading

from bp_chat.utils import *
from settings import *
from .msg_html import *



bp_review = Blueprint('bp_review', 
                    __name__,
                    static_folder='static',
                    template_folder='templates'
                    )


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
    return ref_msg_list, ref_text_str[:MAX_CONTENT_LEN]  # 限制返回内容长度





@bp_review.route('/api/review', methods=['POST'])
def review():
    data = request.json
    user_message = data.get('messages', '')[1:]
    tmp_query = user_message[-1]["content"]
    sub_topic_list = get_v3_response_json(RAG_TOPIC_PROMPT.format(4, tmp_query))["sub_topic"]
    def generate_topic():
        all_ref_list = []
        all_resp_str = ""
        topic_head_content = "the following are the sub questions for the user query: {}\n\n".format(tmp_query)
        topic_head_data = {
            'delta': topic_head_content, 
            'reasoning_content': False,
            'finished': False
        }
        yield f"data: {json.dumps(topic_head_data)}\n\n"
        for topic_id, sub_topic in enumerate(sub_topic_list, start=1):
            _send_topic = f"{topic_id}. {sub_topic}\n\n"
            chunk_data = {
                    'delta': _send_topic, 
                    'reasoning_content': False,
                    'finished': False
            }
            time.sleep(0.05)
            yield f"data: {json.dumps(chunk_data)}\n\n"
        yield f"data: {json.dumps({'finished': True})}\n\n"
        # 逐个回答
        for sub_topic in sub_topic_list:
            title_content_chunk = {
                'delta': f"\n\n# {sub_topic}\n\n", 
                'reasoning_content': False,
                'finished': False
            }
            yield f"data: {json.dumps(title_content_chunk)}\n\n\n\n"
            ref_msg_list, ref_text = retirval_from_kb(sub_topic, level=1, start_id=len(all_ref_list) if all_ref_list else 1)
            all_ref_list += ref_msg_list
            for _ref_msg in ref_msg_list:
                time.sleep(0.05)
                yield f"data: {json.dumps({'ref_msg': _ref_msg, 'finished': False})}\n\n"
            stream = client.chat.completions.create(
                model = DS_R1_ID,
                messages=[{"role": "user", "content": RAG_REVIEW_PROMPT.format(ref_text, sub_topic)}],
                stream=True
            )
            for chunk in stream:
                if not chunk.choices:
                    continue
                if chunk.choices[0].delta.reasoning_content:
                    chunk_data = {
                        'delta': chunk.choices[0].delta.reasoning_content,
                        'reasoning_content': True,
                        'finished': False
                    }
                    yield f"data: {json.dumps(chunk_data)}\n\n"
                else:
                    all_resp_str += chunk.choices[0].delta.content.strip()
                    chunk_data = {
                        'delta': chunk.choices[0].delta.content, 
                        'reasoning_content': False,
                        'finished': False
                    }
                    yield f"data: {json.dumps(chunk_data)}\n\n"
        # 最后一次输出
        stream = client.chat.completions.create(
            model = DS_R1_ID,
            messages=[{"role": "user", "content": RAG_SUMMARY_PROMPT.format(all_resp_str, tmp_query)}],
            stream=True
        )
        for chunk in stream:
            if not chunk.choices:
                continue
            if chunk.choices[0].delta.reasoning_content:
                chunk_data = {
                    'delta': chunk.choices[0].delta.reasoning_content,
                    'reasoning_content': True,
                    'finished': False
                }
                yield f"data: {json.dumps(chunk_data)}\n\n"
            else:
                all_resp_str += chunk.choices[0].delta.content.strip()
                chunk_data = {
                    'delta': chunk.choices[0].delta.content, 
                    'reasoning_content': False,
                    'finished': False
                }
                yield f"data: {json.dumps(chunk_data)}\n\n"

    return Response(generate_topic(), mimetype='text/plain')


@bp_review.route('/api/topic', methods=['POST'])
def get_topic_tiems():
    topic = request.json.get('topic')
    print(f"Received topic: {topic}")
    sub_topic_list = get_v3_response_json(RAG_TOPIC_PROMPT.format(8, topic))["sub_topic"]
    return jsonify(sub_topic_list)


@bp_review.route('/api/task', methods=['POST'])
def submit_task():
    task_id = str(uuid.uuid4())
    topic = request.json.get('topic')
    sub_topic_list = request.json.get('data')
    email = request.json.get('email')
    # 保存用户查询记录
    with open("static/user_review.txt", "a") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {email:<40} - {topic} - {str(sub_topic_list)}\n")
    # 启动一个线程来处理离线任务
    # 不能在主函数导入模块，会造成循环导入
    from .utils import run_offline_task
    thread = threading.Thread(
                              target=run_offline_task, 
                              args=(topic, sub_topic_list, email, task_id),
                              daemon=True # 
                              )
    thread.start()
    return jsonify({
        'status': 'success',
        'message': 'Task submitted successfully!',
        'taskId': task_id,
    })



@bp_review.route('/')
def index():
    return render_template('review.html')


@bp_review.route('/offline_task')
def offline_task():
    return render_template('review_offline.html')


@bp_review.route('/task_info')
def task_info():
    task_id = request.args.get('task_id', '')
    task_path = os.path.join("./bp_review/data", task_id)
    summary_json_path = os.path.join(task_path, "summary.json")
    if not os.path.exists(summary_json_path):
        return "the task is not finished yet, please wait for a while."
    with open(summary_json_path, "r") as f:
        summary_data = json.load(f)
    # 获取summary内容和引用信息
    summary_content = summary_data.get("content", "")
    summary_ref = summary_data.get("ref_msg_data", {})
    tmp_html, ref_list = offline_html_chunk(summary_content, summary_ref)
    summary_ = {
        "topic": summary_data["topic"],
        # "content": summary_content,
        "content": tmp_html,
        "ref_list": ref_list,
    }
    # 获取全部字主题信息
    topic_list = []
    for i in range(len(summary_data["sub_topic"])):
        topic_json_path = os.path.join(task_path, f"topic_{i+1}.json")
        with open(topic_json_path, "r") as f:
            sub_data = json.load(f)
        sub_content = sub_data.get("content", "")
        sub_ref = sub_data.get("ref_msg_data", {})
        sub_html, sub_ref_list = offline_html_chunk(sub_content, sub_ref)
        topic_list.append({
            "topic": sub_data["topic"],
            # "content_html": sub_html,
            "content_html": sub_html,
            "ref_list": sub_ref_list,
        })
    return render_template('task2.html', 
                           summary = summary_,
                           topic = topic_list,
                           )






# @bp_review.route('/mail_test')
# def mail_test():
#     from teroseek_app import send_email
#     send_email(
#         subject="测试邮件",
#         recipients=["854825090@qq.com"],
#         html_content="这是一封来自蓝图的测试邮件2",
#     )
#     return "邮件已发送，请检查您的邮箱。<br>如果没有收到，请检查垃圾邮件或稍后再试。"
