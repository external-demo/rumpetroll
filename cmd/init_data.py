# 导入用户模型
from models.usermodels import UserGolds, Users

# 初始化数据
def init_data():
    Users.metadata.create_all()
    UserGolds.metadata.create_all()


if __name__ == '__main__':
    init_data()
