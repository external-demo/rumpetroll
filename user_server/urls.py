from handlers.UserHandler import ForgetHandler, LoginHandler, RegisterHandler

handlers = [
    ("/login", LoginHandler),
    ("/register", RegisterHandler),
    ("/forget", ForgetHandler),
]
