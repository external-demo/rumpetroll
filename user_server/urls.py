from handlers.UserHandler import LoginHandler, RegisterHandler, ForgetHandler

handlers = [
    ("/login", LoginHandler),
    ("/register", RegisterHandler),
    ("/register", ForgetHandler),
]
