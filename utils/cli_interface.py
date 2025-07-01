from utils.dbconnection import DBConnection
from datetime import datetime
from anytree import Node, RenderTree
from tabulate import tabulate

def is_valid_date_extended(date_str):
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d')
        return date_str == date.strftime('%Y-%m-%d')
    except ValueError:
        return False


class CliInterface():
    def __init__(self):
        self.db = DBConnection()

    def __input_full_name(self):
        while True:
            full_name = input('Введите фамилию, имя и отчество\n')
            parts = full_name.split()
            if len(parts) >= 2 and all(part.isalpha() for part in parts):
                return full_name
            else:
                print('Введены некорректные данные: ' \
                'ФИО должно состоять минимум из 2-х слов и содержать только буквы')
    
    def __input_gtade(self):
        while True:
            position = input('Укажите грейд сотрудника, где: \n' \
            '1 - Developer \n2 - Senior Developer \n3 - Team Lead \n4 - Manager \n5 - CEO\n')
            if 1 <= int(position) <= 5:
                return position
            else:
                print(f'Введены некорректные данные: Вариант {position} не предусмотрен.')



    def __input_hire_date(self):
        while True:
            hire_date = input('Дата приема на работу в формате: ГГГГ-ММ-ДД\n')
            if is_valid_date_extended(hire_date):
                return hire_date
            else:
                print('Введены некорректные данные: Дата должна быть реальной, ' \
                'и соответствовать формату ГГГГ-ММ-ДД')

    def __input_salary(self):
        while True:
            salary = input('Укажите размер оклада:')
            try:
                return float(salary)
            except ValueError:
                print('Введены некорректные данные: данное поле может содержать только цифры')    
        

    def add_user(self):
        full_name = self.__input_full_name()
        position = int(self.__input_gtade())
        hire_date = self.__input_hire_date()
        salary = self.__input_salary()

        user_id = self.db.insert_employee(full_name, position, hire_date, salary)
        if position < 5: 
            result = self.db.get_users_by_position(position= position + 1)
            print(tabulate(result, 
                           headers=["ID", "Имя", "Позиция", "Дата приема на рабоу", "Оклад"], 
                           tablefmt="psql",
                           floatfmt=".2f"))
            boss_id = input('Выберите руководителя для нового сотрудника, и укажите его ID:')
            try:    
                self.db.insert_employee_hierarchy(subordinate_id=user_id, boss_id=boss_id)
            except BaseException as e:
                self.db.delete_user(user_id)
                print('Запись о новом сотруднике удалена, т.к. не удалось назначить руководителя.')

    def set_boss(self, user_id, position=0):
        if position == 0:
            position = self.db.get_users_position_by_id(user_id)
        if position < 5: 
            result = self.db.get_users_by_position(position= position + 1)
            print(tabulate(result, 
                           headers=["ID", "Имя", "Позиция", "Дата приема на рабоу", "Оклад"], 
                           tablefmt="psql",
                           floatfmt=".2f"))
            boss_id = input('Выберите руководителя и укажите его ID:')
            try:    
                self.db.insert_employee_hierarchy(subordinate_id=user_id, boss_id=boss_id)
            except BaseException as e:
                self.db.delete_user(user_id)
                print('Запись о новом сотруднике удалена, т.к. не удалось назначить руководителя.')

    def view_info(self):
        while True:
            menu = """
Меню просмотра информации:
1 - Показать всех сотрудников
2 - Найти и показать данные о сотруднике
3 - Возврат к главному меню
"""
            choice = input(menu)
            match choice:
                case '1':
                    self.view_all_users()
                case '2':
                    self.search_user_by_name()
                case '3':
                    return None

    def view_all_users(self):
        employees = self.db.get_all_employees()

        # Строим дерево
        root_nodes = []
            
        try:
            for emp_id in employees:
                if int(employees[emp_id]["position"]) == 5:
                    employees[emp_id]["node"] = Node(
                        f"{employees[emp_id]['name']} ({employees[emp_id]['position_name']})"
                    )
                    root_nodes.append(employees[emp_id]["node"])
                elif employees[emp_id]["boss"] is None:
                    print(f'ВНИМАНИЕ! Сотруднику {employees[emp_id]["name"]}, ID: {emp_id} на должности {employees[emp_id]["position_name"]} не назначен руководитель')
                else:
                    if employees[emp_id]["node"] is None:
                        employees[emp_id]["node"] = Node(
                            f"{employees[emp_id]['name']} ({employees[emp_id]['position_name']})",
                            parent=employees[employees[emp_id]["boss"]]["node"]
                        )

            # 4. Отображаем дерево
            print("\nДерево всех сотрудников компании:")
            print("========================")
            print_rows = 0
            answer = ''
            for root in root_nodes:
                for pre, _, node in RenderTree(root):
                    print(f"{pre}{node.name}")
                    print_rows += 1
                    if print_rows >= 10:
                        print('   Нажмите "О" чтобы Остановить печать, или любую кнопку чтобы продолжить.', end='\r')
                        answer = input().lower()
                        if 'о' in answer:
                            break
                        else:
                            print_rows = 0
                if 'о' in answer:
                    break

    
        except Exception as e:
            print(f"Ошибка при построении иерархии: {e}")

    def search_user_by_position(self, position):
        result = self.db.get_users_by_position(position= position)
        if len(result) == 0:
            print(f'Не найдено ни одного сотрудника с грейдом "{position}"!')
        else:
            print(tabulate(result, 
                           headers=["ID", "Имя", "Позиция", "Дата приема на рабоу", "Оклад"], 
                           tablefmt="psql",
                           floatfmt=".2f"))
            return result

    def search_user_by_name(self):
        user_name = input('Укажите имя пользователя которого необходимо найти: ')
        result = self.db.get_users_by_name(name= user_name)
        if len(result) == 0:
            print(f'Не найдено ни одного совпадения по запросу "{user_name}"!')
        else:
            print(tabulate(result, 
                           headers=["ID", "Имя", "Позиция", "Дата приема на рабоу", "Оклад"], 
                           tablefmt="psql",
                           floatfmt=".2f"))
            if len(result) == 1:
                answer = input('Показать положение в иерархии компании?')
                if answer.lower() == 'да':
                    curent_user_id = result[0][0]
                    curent_user = self.db.get_user_info(user_id=curent_user_id)
                    boss_id = curent_user[curent_user_id]['boss']
                    if boss_id is None:
                        curent_user[curent_user_id]['node'] = Node(
                            f"{curent_user[curent_user_id]['name']} ({curent_user[curent_user_id]['position_name']})")
                        root_node = curent_user[curent_user_id]['node']
                    else:
                        boss = self.db.get_user_info(user_id=boss_id)
                        boss[boss_id]['node'] = Node(f"{boss[boss_id]['name']} ({boss[boss_id]['position_name']})")
                        root_node = boss[boss_id]['node']
                        curent_user[curent_user_id]['node'] = Node(
                            f"{curent_user[curent_user_id]['name']} ({curent_user[curent_user_id]['position_name']})", 
                            parent=boss[boss_id]["node"])
                    subordinates = self.db.get_subordinates(user_id=curent_user_id)
                    for subordinate_id in subordinates:
                        subordinates[subordinate_id]['node'] = Node(
                            f"{subordinates[subordinate_id]['name']} ({subordinates[subordinate_id]['position_name']})",
                            parent=curent_user[curent_user_id]["node"])
                    for pre, _, node in RenderTree(root_node):
                        print(f"{pre}{node.name}")
        return result
        


    def update_user_data(self):
        print('Для начала найдем в базе сотрудника, данные которого хотите изменить.')
        search_result = self.search_user_by_name()
        if len(search_result) > 1:
            print('Найдено несколько совпадений.')
            user_id = input('Укажите ID сотрудника: ')
        elif len(search_result) == 1:
            print('Найден пользователь:', search_result)
            if input('Хотите изменить данные этого сотрудника?').lower() == 'да':
                user_id = int(search_result[0][0])
            else:
                print('Выход из режима редактирования.')
                return None

        choice = input('Какие данные вы хотели бы изменить?\n' \
        '1 - Имя\n' \
        '2 - Дата приема на работу\n' \
        '3 - Позиция\n' \
        '4 - Оклад\n')
        match choice:
            case '1':
                new_name = self.__input_full_name()
                self.db.update_name(user_id, new_name)
            case '2':
                new_date = self.__input_hire_date()
                self.db.update_hire_date(user_id, new_date)
            case '3':
                new_position = int(self.__input_gtade())
                user_data = self.db.get_users_by_id(user_id)
                self.db.delete_user(user_id)
                user_id = self.db.insert_employee(full_name=user_data[0][1], 
                                                  position=new_position, 
                                                  hire_date=user_data[0][3], 
                                                  salary=user_data[0][4])
                self.set_boss(user_id, position=new_position)
            case '4':
                new_salary = self.__input_salary()
                self.db.update_salary(user_id, new_salary)

    def delete_user(self):
        print('Для начала найдем в базе сотрудника, данные которого хотите удалить.')
        search_result = self.search_user_by_name()
        if len(search_result) > 1:
            print('Найдено несколько совпадений.')
            user_id = input('Укажите ID сотрудника: ')
            self.db.delete_user(user_id)
        elif len(search_result) == 1:
            print('Найден пользователь:', search_result)
            if input('Хотите удалить данные этого сотрудника?').lower() == 'да':
                user_id = search_result[0][0]
                self.db.delete_user(user_id)
        