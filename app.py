from flask import Flask, render_template, request
from utils.database import db, Employee, EmployeeHierarchy, Positions
from config import Config

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = Config.SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PER_PAGE'] = 10  # Количество элементов на странице

db.init_app(app)

@app.route('/employees/')
def employees():
    page = request.args.get('page', 1, type=int)
    sort_by = request.args.get('sort_by', 'full_name')
    sort_order = request.args.get('sort_order', 'asc')  # Направление сортировки
    per_page = app.config['PER_PAGE']


    # Базовый запрос
    query = Employee.query

    # Валидация и применение сортировки
    valid_sort_columns = [column.name for column in Employee.__table__.columns] # Допустимые поля для сортировки
    print('Check', sort_by, 'in', valid_sort_columns)
    if sort_by not in valid_sort_columns:
        print(sort_by, 'not in', valid_sort_columns)
        sort_by = 'full_name'  # Значение по умолчанию при невалидном поле

        # Сортировка по полям Employee
    column = getattr(Employee, sort_by)
    if sort_order.lower() == 'desc':
        query = query.order_by(column.desc())
    else:
        query = query.order_by(column.asc())

    # Применяем пагинацию
    employees_pagination = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )

    # Получаем ID всех сотрудников на странице
    employee_ids = [emp.id for emp in employees_pagination.items]

    # Загружаем должности для отображения
    positions_map = {}
    if employee_ids:
        positions_data = db.session.query(
            Employee.id,
            Positions.position_name
        ).join(Positions, Employee.position == Positions.position_id
               ).filter(Employee.id.in_(employee_ids)).all()

        positions_map = {emp_id: title for emp_id, title in positions_data}

    # Запрашиваем руководителей для этих сотрудников
    boss_dict = {}
    if employee_ids:
        bosses = db.session.query(
            EmployeeHierarchy.subordinate_id,
            Employee.full_name.label('boss_name')
        ).join(Employee, EmployeeHierarchy.boss_id == Employee.id
               ).filter(EmployeeHierarchy.subordinate_id.in_(employee_ids)).all()

        # Создаем словарь для быстрого доступа
        boss_dict = {sub_id: boss_name for sub_id, boss_name in bosses}

        # Добавляем имена руководителей к сотрудникам
        for emp in employees_pagination.items:
            emp.boss_name = boss_dict.get(emp.id)

    # Добавляем дополнительные данные к сотрудникам
    for emp in employees_pagination.items:
        emp.boss_name = boss_dict.get(emp.id)
        emp.position_title = positions_map.get(emp.id, 'Не указана')

    return render_template(
        'all_employees.html',
        employees=employees_pagination,
        sort_by=sort_by,
        sort_order=sort_order
    )

if __name__ == "__main__":
    app.run()
