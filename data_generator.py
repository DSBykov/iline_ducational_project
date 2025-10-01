from utils.dbconnection import DBConnection
from utils.generation import generate_employee_data
import random

db = DBConnection()

# Создаем таблицы в БД, если не созданы
db.create_tables()

# генерируем 50 т. сотрудников
for _ in range(50000):
    db.insert_employee(**generate_employee_data())

# Назначаем руководителей
for curent_position in range(1, 5):
    __list_of_subordinates = db.get_users_by_position(position=curent_position)
    __list_of_boss = db.get_users_by_position(position=curent_position + 1)
    for subordinat in __list_of_subordinates:
        db.insert_employee_hierarchy(subordinate_id=subordinat[0],
                                     boss_id= random.choice(__list_of_boss)[0])