# 导入 ForgetHandler, LoginHandler, RegisterHandler 类
from handlers.user_handler import ForgetHandler, LoginHandler, RegisterHandler

# 处理程序列表，每个元素都是一个元组，
# 元组的第一个元素是路径，第二个元素是处理程序类的引用
handlers = [
    ("/login", LoginHandler),        # 登录路由
    ("/register", RegisterHandler),  # 注册路由
    ("/forget", ForgetHandler),      # 忘记密码路由
]
