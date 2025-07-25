#!/home/zengt/soft/anaconda3/envs/teroseek/bin/python

from flask import Flask, redirect, render_template, request, Response, jsonify

from teroseek_utils import *
from settings import *
from flask_mail import Mail
from flask_mail import Message

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB
app.config['MAIL_SERVER'] = MAIL_SERVER
app.config['MAIL_PORT'] = MAIL_PORT
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = MAIL_ACCOUNT
app.config['MAIL_PASSWORD'] = MAIL_PASSWORD
app.config['MAIL_DEFAULT_SENDER'] = MAIL_ACCOUNT
mail = Mail(app)
def send_email(subject:str, recipients:list, html:str):
    """
    发送HTML格式的邮件
    """
    with app.app_context():
        msg = Message(subject=subject, 
                      recipients=recipients, 
                      html=html)
        mail.send(msg)
    return

# 注册用户蓝图
from bp_auth.routes import auth_bp
app.register_blueprint(auth_bp, url_prefix='/auth')
# 注册聊天蓝图
from bp_chat.routes  import bp_chat
app.register_blueprint(bp_chat, url_prefix='/chat')
# 注册搜索蓝图
from bp_search.routes import bp_search
app.register_blueprint(bp_search, url_prefix='/search')
# 注册综述蓝图
from bp_review.routes import bp_review
app.register_blueprint(bp_review, url_prefix='/review')


@app.route('/')
def index():
    return render_template('index.html')


@app.route("/paper_info")
def paper_info():
    T_id = request.args.get('T_id')
    return redirect(f'/search/paper_info?T_id={T_id}')



# 配置Debug模式（可通过环境变量或直接设置）
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'qmclab@328'  # 生产环境请使用更安全的密钥
if __name__ == '__main__':
    # 启动开发服务器（带调试和自动重载）
    app.run(host='0.0.0.0', port=9995, debug=True)
