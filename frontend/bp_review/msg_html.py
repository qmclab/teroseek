

import re
import markdown
import bleach

def welcome_html(topic, sub_topic_list, task_id):
    # function: 生成欢迎页面的HTML内容
    welcome_content = """
    <h1>Welcome to TeroSeek Review System</h1>
    <p>This system is designed to assist you in reviewing terpenoid-related tasks.</p>
    <p>Your task has been successfully submitted.</p>
    """
    welcome_content += f"<h2>Topic: {topic}</h2>"
    welcome_content += "<h3>Sub-topics:</h3><ul>"
    for sub_topic in sub_topic_list:
        welcome_content += f"<li>{sub_topic}</li>"
    welcome_content += "</ul>"
    welcome_content += """
    <p>Thank you for using our system!</p>
    <p>Feel free to reply to this email with your feedback and suggestions.</p>
    <p>Click on the <a href=http://teroseek.qmclab.com/review/task_info?task_id={}>following link</a> to view the progress and results of the task.</p>
    """.format(task_id)
    return welcome_content



def llm_response_html(md_text):
    # 启用Markdown扩展（包括表格扩展）
    extensions = [
        'extra',  # 包含表格、代码块等
        'fenced_code',  # 支持代码块
        'tables',  # 支持表格
        'md_in_html'  # 允许在HTML块中使用Markdown
    ]
    
    # 将Markdown文本转换为HTML
    html_content = markdown.markdown(md_text, extensions=extensions)
    
    # 修复表格格式问题 - 确保表格被正确包裹在<table>标签中
    html_content = html_content.replace('<table>', '<table border="1">')
    
    # 使用bleach清理HTML内容，保留特定标签和属性
    cleaned_html = bleach.clean(
        html_content,
        tags=[
            'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'strong', 'em', 'a',
            'ul', 'ol', 'li', 'pre', 'code', 'blockquote', 'hr', 'br', 'img',
            'table', 'thead', 'tbody', 'tr', 'th', 'td',  # 表格相关标签
            'span', 'div',  # 代码高亮可能需要
            'ce'  # 化学公式标签
        ],
        attributes={
            'a': ['href', 'title', 'rel'],
            'img': ['src', 'alt', 'title', 'width', 'height'],
            'code': ['class'],  # 代码高亮类
            'span': ['class'],  # 代码高亮可能需要
            'div': ['class'],   # 代码块可能需要
            'table': ['border', 'style'],  # 表格属性
            'th': ['align', 'colspan', 'rowspan'],  # 表头属性
            'td': ['align', 'colspan', 'rowspan'],  # 表格单元格属性
            'ce': ['data-formula']  # 化学公式属性
        }
    )
    return cleaned_html



def offline_html_chunk(content:str, ref:dict):
    content_html = llm_response_html(content)
    tmp_html = re.sub(r'\bref_\d+\b', r'__\g<0>__', content_html)
    ref_matches = re.findall(r'__ref_\d+__', tmp_html)
    refs = list(dict.fromkeys(ref_matches))
    ref_list = []
    for ref_id, ref_matche in enumerate(refs, start=1):
        ref_info = ref.get(ref_matche[2:-2], None)
        if ref_info is None:
            continue
        replace_text = '''<a href="{}" target="_blank">ref_{}</a>'''.format(ref_info["url"],ref_id)
        tmp_html = tmp_html.replace(ref_matche, replace_text)
        ref_line = f"ref_{ref_id}: {ref_info['authors']}, {ref_info['title']}, {ref_info['year']}, {ref_info['publisher']}, {ref_info['doi']}"
        ref_list.append(ref_line)
    return tmp_html, ref_list





def mail_status_html(**args):
    return





