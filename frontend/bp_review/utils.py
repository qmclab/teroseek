
import os
import multiprocessing
import requests

from teroseek_app import send_email
from bp_chat.utils import *
from settings import *
from .msg_html import *


def run_offline_task(topic, sub_topic_list, email, task_id):
    status_msg = welcome_html(topic, sub_topic_list, task_id)
    send_email(
        subject="TeroSeek Review Task Submission",
        recipients=[email],
        html=status_msg,
    )
    # 创建工作目录
    bin_path = REVIEW_OFFLINE_PATH
    if not os.path.exists(bin_path):
        os.makedirs(bin_path, exist_ok=True)
    task_path = os.path.join(bin_path, task_id)
    os.makedirs(task_path, exist_ok=True)

    topic_info = [] # [(三个元素组成的元组), ]
    for topic_id, sub_topic in enumerate(sub_topic_list, start=1):
        topic_info.append((topic_id, task_path, sub_topic))
    # 由于并行限制，最多使用3个进程来处理子主题
    with multiprocessing.Pool(processes=min(3, len(topic_info))) as pool:
        pool.map(rag_sub_topic, topic_info)

    print(f"Task {task_id} submitted successfully for topic: {topic} with sub-topics: {sub_topic_list}")
    all_ref_dict = {}
    all_content_str = ""
    for (topic_id, _, sub_topic) in topic_info:
        with open(os.path.join(task_path, f"topic_{topic_id}.json"), 'r', encoding='utf-8') as f:
            _data = json.load(f)
            _content = _data["content"]
            all_ref_dict.update(_data["ref_msg_data"])
            all_content_str += f"\n\n# {sub_topic}\n\n{_content}"
    
    summary_reasoning, summary_content = get_r1_response(RAG_SUMMARY_PROMPT.format(all_content_str, topic))
    _summary_data = {
        "topic": topic,
        "sub_topic": sub_topic_list,
        "ref_msg_data": all_ref_dict,
        "reasion_content": summary_reasoning,
        "content": summary_content,
    }
    with open(os.path.join(task_path, "summary.json"), 'w', encoding='utf-8') as f:
        json.dump(_summary_data, f, ensure_ascii=False, indent=4)
    print(f"Task {task_id} completed successfully and saved to {task_path}")

    summary_html, _ = offline_html_chunk(summary_content, all_ref_dict)
    summary_html += """
    <p>Thank you for using our system!</p>
    <p>Feel free to reply to this email with your feedback and suggestions.</p>
    <p><b>Click on the <a href=http://teroseek.qmclab.com/review/task_info?task_id={}>following link</a> to view the progress and results of the task.</b></p>
    """.format(task_id)
    send_email(
        subject=f"TeroSeek Review Task Completion: {topic}",
        recipients=[email],
        html=summary_html,
    )
    return


# 对每一个子主题
def rag_sub_topic(sub_topic_info):
    """
    处理每个子主题，获取相关知识库的引用信息，返回大语言模型的结果。
    默认使用sub_topic_id从0开始，表示第一个子主题。
    """
    sub_topic_id, task_path, sub_topic = sub_topic_info
    start_id = (sub_topic_id - 1) * 30 + 1
    print(f"Processing sub-topic {sub_topic_id} with start_id {start_id}: {sub_topic}")
    ref_msg_data, ref_text = retirval_from_kb_offline(sub_topic, level=1, start_id=start_id)
    reasion_content, content = get_r1_response(RAG_REVIEW_PROMPT.format(ref_text, sub_topic))
    topic_path = os.path.join(task_path, f"topic_{sub_topic_id}.json")
    _data = {
        "topic": sub_topic,
        "ref_msg_data": ref_msg_data,
        "reasion_content": reasion_content,
        "content": content,
    }
    with open(topic_path, 'w', encoding='utf-8') as f:
        json.dump(_data, f, ensure_ascii=False, indent=4)
    print(f"Processed sub-topic {sub_topic_id} successfully: {sub_topic}")
    return


def retirval_from_kb_offline(query, level=0, start_id=1):
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
    print(f"Retrieving information for query: {query}", end=":::::::")
    retirval_sentence = get_v3_response(hr_prompt.format(query))
    print(retirval_sentence, "\n\n")
    headers = {"Content-Type": "application/json"}
    payload = {"query": retirval_sentence, "top_k": level}
    response = requests.post(RETRIEVE_URL, headers=headers, data=json.dumps(payload))
    result_data = response.json()
    # 获取返回信息，直接获取ref_msg和ref_text
    ref_data_list = result_data.get("ref_msg", None)
    ref_text_list = result_data.get("ref_text", "No result found")
    # 进一步处理ref信息
    ref_msg_data = {}
    ref_text_str = ""
    for ref_id, _ref_data in enumerate(ref_data_list, start=start_id):
        ref_msg_data[f"ref_{ref_id}"] = generate_ref_data(_ref_data)
    for ref_id, _ref_text in enumerate(ref_text_list, start=start_id):
        ref_text_str += f"ref_{ref_id}: {_ref_text}\n"
    return ref_msg_data, ref_text_str[:MAX_CONTENT_LEN]  # 限制返回内容长度












