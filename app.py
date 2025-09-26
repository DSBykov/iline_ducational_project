from datetime import datetime, UTC

from flask import Flask, render_template, request, flash, redirect, url_for
from utils.database import db, Employee, EmployeeHierarchy, Positions
from config import Config

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = Config.SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PER_PAGE'] = 10  # Количество элементов на странице
app.config['SECRET_KEY'] = Config.SECRET_KEY

db.init_app(app)

@app.route('/employees/')
def employees():
    page = request.args.get('page', 1, type=int)
    sort_by = request.args.get('sort_by', 'full_name')
    sort_order = request.args.get('sort_order', 'asc')  # Направление сортировки
    per_page = app.config['PER_PAGE']
    search = request.args.get('search', '')


    # Базовый запрос
    query = Employee.query

    # Применяем поиск
    if search:
        query = query.filter(Employee.full_name.ilike(f'%{search}%'))

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
        sort_order=sort_order,
        search=search
    )


@app.route('/add_employee/', methods=['GET', 'POST'])
def add_employee():
    if request.method == 'GET':
        # Получаем список должностей и сотрудников для выпадающих списков
        positions = Positions.query.all()
        employees = Employee.query.options(db.joinedload(Employee.position_name)).all()
        today = datetime.now(UTC).date()
        return render_template('add_employee.html',
                             positions=positions,
                             employees=employees,
                             today=today.isoformat())

    elif request.method == 'POST':
        try:
            # Получаем данные из формы
            full_name = request.form['full_name']
            position = request.form['position_id']
            hire_date_str = request.form.get('hire_date')
            salary = request.form['salary']
            boss_id = request.form.get('boss_id') or ''

            # Преобразуем дату
            hire_date = datetime.strptime(hire_date_str, '%Y-%m-%d').date()

            # Валидация данных

            # Создаем нового сотрудника
            new_employee = Employee(
                full_name=full_name,
                position=position,
                hire_date=hire_date,
                salary=salary
            )

            # Записываем в БД
            db.session.add(new_employee)
            db.session.flush()

            # Проверка, что грейд руководителя на один выше чем у подчиненного
            new_employee_position = int(new_employee.position)
            boss = db.session.query(Employee).filter(Employee.id == boss_id).first()
            boss_position = int(boss.position)
            if new_employee_position < 5:
                if boss_position == new_employee_position + 1:
                    # Устанавливаем связь сотрудника с руководителем
                    hierarchy = EmployeeHierarchy(
                        boss_id=boss_id,
                        subordinate_id=new_employee.id
                    )
                    # Записываем в БД
                    db.session.add(hierarchy)
                else:
                    raise ValueError('Грейд руководителя должен быть на 1 больше грейда подчиненного')

            # Сохраняем изменения
            db.session.commit()

            flash('Сотрудник успешно добавлен!', 'success')
            print('Сотрудник успешно добавлен!')
            return redirect(url_for('employees'))

        except Exception as e:
            db.session.rollback()
            print(f'Ошибка при добавлении сотрудника: {str(e)}', 'error')
            flash(f'Ошибка при добавлении сотрудника: {str(e)}', 'error')

    return render_template('add_employee.html')

if __name__ == "__main__":
    app.run()
