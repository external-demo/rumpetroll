from handlers.UserHandler import LoginHandler, RegisterHandler, ForgetHandler

handlers = [
    ("/login", LoginHandler),
    ("/register", RegisterHandler),
    ("/forget", ForgetHandler),
]
