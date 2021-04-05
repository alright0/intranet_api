from Statistics import *

user = User(username="test_user_for_pytest", password="test_password")


# проверка записей в базу
def test_add_user():

    session.add(user)
    session.commit()

    test_add_result = User.query.filter(User.username == user.username).first()

    assert test_add_result.__repr__() == f"<User {user.username}>"


# проверка удаления из базы
def test_delete_user():

    session.delete(user)
    session.commit()

    test_delete_result = User.query.filter(User.username == user.username).first()

    print(test_delete_result)

    assert test_delete_result == None
