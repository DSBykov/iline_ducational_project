import psycopg2
from psycopg2 import sql
from datetime import datetime

class DBConnection():
    def __init__(self):
        self.db = self.create_connection()    

    # Подключение к базе данных
    def create_connection(self):
        try:
            conn = psycopg2.connect(
                dbname="iline_db",
                user="postgres",
                password="TheItCrowd_86",
                host="localhost",
                port="5432",
                client_encoding="UTF8"
            )
            print("Подключение к PostgreSQL успешно установлено")
            return conn
        except Exception as e:
            print(f"Ошибка подключения к PostgreSQL: {e}")
            return None
        
    # Вставка данных
    def insert_employee(self, full_name, position, hire_date, salary):
        try:
            with self.db.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO employees (full_name, position, hire_date, salary)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                """, (full_name, position, hire_date, salary))
                employee_id = cursor.fetchone()[0]
                self.db.commit()
                print(f"Сотрудник добавлен с ID: {employee_id}")
                return employee_id
        except Exception as e:
            print(f"Ошибка при добавлении сотрудника: {e}")
            self.db.rollback()
            return None
        
    def insert_employee_hierarchy(self, subordinate_id, boss_id):
        with self.db.cursor() as cursor:
            cursor.execute("""
                INSERT INTO employee_hierarchy (subordinate_id, boss_id)
                VALUES (%s, %s)
            """, (subordinate_id, boss_id))
            self.db.commit()
            print(f"Добавлена связь подчиненного {subordinate_id} и начальника {boss_id}")
        

    def get_users_position_by_id(self, user_id):
        try:
            with self.db.cursor() as cursor:
                cursor.execute("""
                    select position
                    from employees
                    where id = %s
                """, (str(user_id)))
                employees_id = cursor.fetchall()
                return employees_id
        except Exception as e:
            print(f"Ошибка при получении списка пользователей по грейду: {e}")
            self.db.rollback()
            return None

    def get_all_employees(self):
        query = """
        SELECT id, full_name, position, boss_id, position_name
        FROM employees
        LEFT JOIN employee_hierarchy ON employees.id = employee_hierarchy.subordinate_id
        LEFT JOIN positions ON employees.position::integer = positions.position_id
        ORDER BY position DESC
        """

        try:
            with self.db.cursor() as cursor:
                cursor.execute(query)
                employees = {row[0]: {"name": row[1], 
                                      "position": row[2], 
                                      "boss": row[3],
                                      "position_name": row[4], 
                                      "node": None} 
                            for row in cursor.fetchall()}
                return employees
        except Exception as e:
            print(f"Ошибка при получении списка всех сотрудников: {e}")
            return None
                
    def get_user_info(self, user_id):
        query = f"""
        SELECT id, full_name, position_name, boss_id
        FROM employees
        LEFT JOIN employee_hierarchy ON employees.id = employee_hierarchy.subordinate_id
        LEFT JOIN positions ON employees.position::integer = positions.position_id
        WHERE id = {user_id}
        """

        try:
            with self.db.cursor() as cursor:
                cursor.execute(query)
                employees = {row[0]: {"name": row[1], 
                                      "position_name": row[2],
                                      "boss": row[3], 
                                      "node": None} 
                            for row in cursor.fetchall()}
                return employees
        except Exception as e:
            print(f"Ошибка при получении списка всех сотрудников: {e}")
            return None

    def get_subordinates(self, user_id):
        query = f"""
        SELECT id, full_name, position_name
        FROM employees
        LEFT JOIN employee_hierarchy ON employees.id = employee_hierarchy.subordinate_id
        LEFT JOIN positions ON employees.position::integer = positions.position_id
        WHERE boss_id = {user_id}
        """

        try:
            with self.db.cursor() as cursor:
                cursor.execute(query)
                employees = {row[0]: {"name": row[1], 
                                      "position_name": row[2], 
                                      "node": None} 
                            for row in cursor.fetchall()}
                return employees
        except Exception as e:
            print(f"Ошибка при получении списка всех сотрудников: {e}")
            return None

    def get_hierarchy(self):
        try:
            with self.db.cursor() as cursor:
                cursor.execute("SELECT boss_id, subordinate_id FROM employee_hierarchy")
                relations = cursor.fetchall()
                return relations
        except Exception as e:
            print(f"Ошибка при получении иерархических связей сотрудников: {e}")
            return None

    def delete_user(self, user_id, max_retries=3):
        for attempt in range(max_retries):
            try:
                with self.db.cursor() as cursor:
                    cursor.execute(f'DELETE FROM employees WHERE id = {str(user_id)}')
                    # employees_id = cursor.fetchone()[0]
                    self.db.commit()
                    print(f"Пользователь с id={user_id} успешно удален.")
                    return True
            except Exception as e:
                self.db.rollback()
                print(f"Попытка {attempt + 1} не удалась: {e}")
                print(f"Ошибка при удалении пользователя {user_id}: {e}")
                
        return False
        
    def get_users_by_name(self, name):
        try:
            with self.db.cursor() as cursor:
                cursor.execute(f"select * from employees where lower(full_name) LIKE '%{name.lower()}%'")
                result = cursor.fetchall()
                # print(f"\nСписок сотрудников с именем {name}: ")
                # print(result)
                return result
        except Exception as e:
            print(f"Ошибка при поиске сотрудника по имени: {e}")
            self.db.rollback()
            return None
        
    def get_users_by_id(self, id):
        try:
            with self.db.cursor() as cursor:
                cursor.execute(f"select * from employees where id = {id}")
                result = cursor.fetchall()
                # print(f"\nВот что нашлось: ")
                # print(result)
                return result
        except Exception as e:
            print(f"Ошибка при поиске сотрудника по ID: {e}")
            self.db.rollback()
            return None
        
    def get_users_by_position(self, position):
        try:
            with self.db.cursor() as cursor:
                cursor.execute(f"select * from employees where position = '{position}'")
                result = cursor.fetchall()
                # print(f"\nВот что нашлось: ")
                # print(result)
                return result
        except Exception as e:
            print(f"Ошибка при поллучении списка сотрудников указанного грейда: {e}")
            self.db.rollback()
            return None
        
    def update_name(self, id, new_name: str):
        try:
            with self.db.cursor() as cursor:
                cursor.execute(f"UPDATE employees SET full_name = '{new_name}' WHERE id = {id};")
                self.db.commit()
        except Exception as e:
            print(f"Ошибка при изменениии имени сотрудника: {e}")
            self.db.rollback()
            return None
        

    def update_hire_date(self, id, new_date):
        try:
            with self.db.cursor() as cursor:
                cursor.execute(f"UPDATE employees SET hire_date = '{new_date}' WHERE id = {id};")
                self.db.commit()
        except Exception as e:
            print(f"Ошибка при изменениии даты приема на работу: {e}")
            self.db.rollback()
            return None

    def update_salary(self, id, new_salary: int):
        try:
            with self.db.cursor() as cursor:
                cursor.execute(f"UPDATE employees SET salary = {new_salary} WHERE id = {id};")
                self.db.commit()
        except Exception as e:
            print(f"Ошибка при изменениии оклада сотрудника: {e}")
            self.db.rollback()
            return None
        
    def __del__(self):
        self.db.close()
        print('Выполнено отключение от БД PostgreSQL')
