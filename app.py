from datetime import datetime, UTC, timezone

from flask import Flask, render_template, request, flash, redirect, url_for
from utils.database import db, Employee, EmployeeHierarchy, Positions, delete_subordinate, \
    delete_subordinate_with_reassignment, is_validate_positions
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
    if sort_by not in valid_sort_columns:
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

            # Валидация должности сотрудника и связи с руководителем
            if is_validate_positions(employee_position=new_employee.position, boss_id=boss_id):
                if boss_id:
                    hierarchy = EmployeeHierarchy(
                        boss_id=boss_id,
                        subordinate_id=new_employee.id
                    )
                    db.session.add(hierarchy)
                # Сохраняем изменения
                db.session.commit()
                flash('Сотрудник успешно добавлен!', 'success')
                return redirect(url_for('employees'))
            else:
                flash('Сотрудник грейда 5 не может иметь руководителя, '
                      'а остальные сотрудники обязаны иметь руководителя на 1 грейд выше.', 'error')

        except Exception as e:
            db.session.rollback()
            print(f'Ошибка при добавлении сотрудника: {str(e)}', 'error')
            render_template('add_employee.html')
            flash(f'Ошибка при добавлении сотрудника: {str(e)}', 'error')

    return render_template('add_employee.html')


@app.route('/employee/<int:employee_id>/delete', methods=['POST'])
def delete_employee(employee_id):
    """Простое удаление сотрудника (без подчиненных)"""
    success, message = delete_subordinate(employee_id)

    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')

    return redirect(url_for('employees'))


@app.route('/employee/<int:employee_id>/delete_with_reassignment', methods=['POST'])
def delete_employee_with_reassignment(employee_id):
    """Удаление сотрудника с переназначением подчиненных"""
    new_boss_id = request.form.get('new_boss_id')

    if not new_boss_id:
        flash('Необходимо выбрать нового руководителя для подчиненных', 'error')
        return redirect(url_for('edit_employee', employee_id=employee_id))

    success, message = delete_subordinate_with_reassignment(employee_id, int(new_boss_id))

    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')

    return redirect(url_for('employees'))


@app.route('/employee/<int:employee_id>/edit', methods=['GET', 'POST'])
def edit_employee(employee_id):
    employees = Employee.query.options(db.joinedload(Employee.position_name)).all()
    employee = Employee.query.get_or_404(employee_id)

    if request.method == 'POST':
        try:
            # Получаем данные формы
            full_name = request.form.get('full_name', '').strip()
            position_id = request.form.get('position_id')
            boss_id = request.form.get('boss_id') or None
            hire_date_str = request.form.get('hire_date')
            salary = request.form.get('salary')

            # Валидация
            if not full_name:
                flash('Полное имя обязательно для заполнения', 'error')
                return redirect(url_for('edit_employee', employee_id=employee_id))

            if not position_id:
                flash('Выберите должность', 'error')
                return redirect(url_for('edit_employee', employee_id=employee_id))

            if not hire_date_str:
                flash('Укажите дату приема', 'error')
                return redirect(url_for('edit_employee', employee_id=employee_id))

            # Обновляем данные сотрудника
            employee.full_name = full_name
            employee.position = int(position_id)
            employee.salary = float(salary) if salary else 0

            # Обновляем дату приема
            try:
                hire_date = datetime.strptime(hire_date_str, '%Y-%m-%d').date()
                today_utc = datetime.now(timezone.utc).date()
                print('hire_date =', hire_date, '> today =', today_utc)
                if hire_date > today_utc:
                    flash('Дата приема не может быть в будущем', 'error')
                    return redirect(url_for('edit_employee', employee_id=employee_id))
                employee.hire_date = hire_date
            except ValueError:
                flash('Некорректный формат даты', 'error')
                return redirect(url_for('edit_employee', employee_id=employee_id))

            # Получаем текущего руководителя
            current_boss = EmployeeHierarchy.query.filter_by(
                subordinate_id=employee.id
            ).first()
            current_boss_id = current_boss.boss_id if current_boss else None
            print('current_boss_id =', current_boss_id)
            print('boss_id =', boss_id)
            print('position_id =', position_id)

            # Проверяем соответствие указанного грейд сотрудника - грейду руководителя
            if is_validate_positions(employee_position=position_id, boss_id=boss_id):

                # Удаляем связь с руководителем если она есть и если меняется
                if current_boss_id and (boss_id != current_boss_id):
                    print('Удаляем связь с руководителем')
                    db.session.delete(current_boss)

                # Добавляем связь если указан новый руководить
                if boss_id and (boss_id != current_boss_id):
                    print('Добавляем связь')
                    hierarchy = EmployeeHierarchy(
                        boss_id=boss_id,
                        subordinate_id=employee.id
                    )
                    db.session.add(hierarchy)

                db.session.commit()
                flash(f'Данные сотрудника {full_name} успешно обновлены', 'success')
                # return redirect(url_for('employees'))

            else:
                flash('Сотрудник грейда 5 не может иметь руководителя, '
                      'а остальные сотрудники обязаны иметь руководителя на 1 грейд выше.', 'error')

        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при обновлении данных: {str(e)}', 'error')
            return redirect(url_for('edit_employee', employee_id=employee_id))

    # GET запрос - отображение формы
    positions = Positions.query.order_by(Positions.position_name).all()

    # Получаем доступных руководителей (все сотрудники кроме текущего)
    available_bosses = Employee.query.filter(Employee.id != employee.id) \
        .options(db.joinedload(Employee.position_name)) \
        .order_by(Employee.full_name).all()

    # Получаем текущего руководителя через relationship
    current_boss = employee.boss

    # Получаем подчиненных через relationship
    has_subordinates = len(employee.subordinate_relations) > 0
    subordinates = []
    if has_subordinates:
        subordinates = [rel.subordinate for rel in employee.subordinate_relations]

    return render_template('edit_employee.html',
                           employee=employee,
                           employees=employees,
                           positions=positions,
                           available_bosses=available_bosses,
                           current_boss=current_boss,
                           has_subordinates=has_subordinates,
                           subordinates=subordinates,
                           subordinates_count=len(subordinates))

if __name__ == "__main__":
    app.run()
