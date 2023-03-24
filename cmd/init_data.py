from models.UserModels import UserGolds, Users


def init_data():
    Users.metadata.create_all()
    UserGolds.metadata.create_all()


if __name__ == '__main__':
    init_data()
