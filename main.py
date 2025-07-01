from utils.cli_interface import CliInterface
interface = CliInterface()

print('Добро пожаловать в консольную утилиту управления базой данных сотрудников iLine.')

choise_action = '''
Выберите действие: 
1 - Добавить нового сотрудника
2 - Просмотр информации
3 - Изменить данные о сотруднике
4 - Удалить информацию о сотруднике
5 - Выход
'''


while True:
    user_input = input(choise_action)
    match user_input:
        case '1':
            interface.add_user()
        case '2':
            interface.view_info()
        case '3': 
            interface.update_user_data()
        case '4':
            interface.delete_user()
        case '5':
            answer = input("Хотите покинуть программу? Да/Нет: ")
            if answer.lower() == 'да':
                break
        case _:
            print('Такого варианта нет, попробуйте снова')
