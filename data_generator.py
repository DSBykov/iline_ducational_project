from mimesis import Person, Datetime, Numeric, Finance
from utils.dbconnection import DBConnection
from utils.generation import generate_employee_data
import random

# Создаем экземпляр класса-провайдера с данными для исландского языка.
db = DBConnection()

# генерируем 50 т. сотрудников
for _ in range(50000):
    db.insert_employee(**generate_employee_data())

# Назначаем руководителей
for curent_position in range(1, 5):
    __list_of_subordinates = db.get_users_id_by_position(position=curent_position)
    __list_of_boss = db.get_users_id_by_position(position=curent_position + 1)
    for subordinat in __list_of_subordinates:
        db.insert_employee_hierarchy(subordinate_id=subordinat, 
                                     boss_id= random.choice(__list_of_boss))