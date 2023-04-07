# 导入 os 模块
import os

# 从 settings 导入 DEBUG 和 PORT
from settings import DEBUG, PORT

# 获取当前文件的绝对路径作为 BASE_DIR
BASE_DIR = os.path.dirname(__file__)

# 定义 settings 字典
settings = dict(
    # 设置 template_path 为 BASE_DIR/templates 目录
    template_path=os.path.join(BASE_DIR, "templates"),
    # 设置 static_path 为 BASE_DIR/static 目录
    static_path=os.path.join(BASE_DIR, "static"),
    # 禁用跨站请求伪造保护
    xsrf_cookies=False,
    # 设置 cookie_secret
    cookie_secret="bb904fe1b095cab9499a85f864e6c612",
    # 设置监听的端口号
    port=PORT,
    # 设置是否开启调试模式
    debug=DEBUG,
)
