from settings import PORT, DEBUG
import os

BASE_DIR = os.path.dirname(__file__)

settings = dict(
    template_path=os.path.join(BASE_DIR, "templates"),
    static_path=os.path.join(BASE_DIR, "static"),
    xsrf_cookies=False,
    cookie_secret="bb904fe1b095cab9499a85f864e6c612",
    port=PORT,
    debug=DEBUG,
)
