from handlers.user_handler import ForgetHandler, LoginHandler, RegisterHandler

handlers = [
    ("/login", LoginHandler),
    ("/register", RegisterHandler),
    ("/forget", ForgetHandler),
]
