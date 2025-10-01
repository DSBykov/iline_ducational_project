from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import mapped_column, relationship
from datetime import datetime, timezone
from sqlalchemy import Integer, String, Date, Numeric, ForeignKey, PrimaryKeyConstraint

db = SQLAlchemy()


class Employee(db.Model):
  __tablename__ = 'employees'

  id = mapped_column(Integer, primary_key=True, nullable=False)
  full_name = mapped_column(String(100), nullable=False)
  position = mapped_column(Integer, ForeignKey("positions.position_id"), nullable=False)
  hire_date = mapped_column(Date, default=lambda: datetime.now(timezone.utc))
  salary = mapped_column(Numeric(10, 2), nullable=False)

  position_name = relationship("Positions", back_populates="employees")

  def to_dict(self):
    return {
      'id': self.id,
      'full_name': self.full_name,
      'position': self.position_name,
      'hire_date': self.hire_date.isoformat(),
      'salary': float(self.salary)
    }

  boss = relationship(
    'Employee',
    secondary='employee_hierarchy',
    primaryjoin='Employee.id == EmployeeHierarchy.subordinate_id',
    secondaryjoin='EmployeeHierarchy.boss_id == Employee.id',
    uselist=False,
    viewonly=True
  )

  def __repr__(self):
    return f'<Employee {self.id}, full name: {self.full_name} >'


# Альтернативный вариант: через класс-модель
class EmployeeHierarchy(db.Model):
  __tablename__ = 'employee_hierarchy'

  boss_id = mapped_column(
    Integer,
    ForeignKey('employees.id', ondelete='CASCADE'),
    primary_key = True,
    nullable = False
  )

  subordinate_id = mapped_column(
    Integer,
    ForeignKey('employees.id', ondelete='CASCADE'),
    primary_key = True,
    nullable = False
  )

  # Связи
  boss = relationship('Employee', foreign_keys=[boss_id], backref='subordinate_relations')
  subordinate = relationship('Employee', foreign_keys=[subordinate_id], backref='boss_relations')

  __table_args__ = (
    # Явное указание первичного ключа
    PrimaryKeyConstraint('boss_id', 'subordinate_id', name='employee_hierarchy_pkey'),
  )

  def __repr__(self):
    return f'<Hierarchy {self.boss_id} -> {self.subordinate_id}>'


class Positions(db.Model):
  __tablename__ = 'positions'

  position_id = mapped_column(Integer, primary_key=True, nullable = False)
  position_name = mapped_column(String(100), nullable=False)

  employees = relationship("Employee", back_populates="position_name")

def has_subordinates(employee_id):
  """Проверяет, есть ли у сотрудника подчиненные"""
  employee = Employee.query.get(employee_id)
  if not employee:
    return False

  # Проверяем через relationship (если backref настроен правильно)
  return employee.subordinate_relations


def delete_subordinate(employee_id):
  """Удаляет сотрудника (без подчиненных)"""
  try:
    employee = Employee.query.get(employee_id)
    if not employee:
      return False, "Сотрудник не найден"

    # Проверяем, что нет подчиненных
    if employee.subordinate_relations:
      return False, "Нельзя удалить сотрудника с подчиненными"

    employee_name = employee.full_name

    # Удаляем связи где сотрудник является подчиненным
    EmployeeHierarchy.query.filter_by(subordinate_id=employee_id).delete()

    # Удаляем самого сотрудника
    db.session.delete(employee)
    db.session.commit()

    return True, f"Сотрудник {employee_name} успешно удален"

  except Exception as e:
    db.session.rollback()
    return False, f"Ошибка при удалении сотрудника: {str(e)}"


def delete_subordinate_with_reassignment(employee_id, new_boss_id):
  """Удаление сотрудника с переназначением подчиненных"""
  try:
    employee = Employee.query.get(employee_id)
    if not employee:
      return False, "Сотрудник не найден"

    new_boss = Employee.query.get(new_boss_id)
    if not new_boss:
      return False, "Новый руководитель не найден"

    employee_name = employee.full_name
    new_boss_name = new_boss.full_name

    # Переназначаем подчиненных новому руководителю
    for hierarchy in employee.subordinate_relations:
      hierarchy.boss_id = new_boss_id

    # Удаляем связи, где сотрудник является подчиненным
    EmployeeHierarchy.query.filter_by(subordinate_id=employee_id).delete()

    # Удаляем сотрудника
    db.session.delete(employee)
    db.session.commit()

    return True, f"Сотрудник {employee_name} удален. Подчиненные переназначены {new_boss_name}"

  except Exception as e:
    db.session.rollback()
    return False, f"Ошибка при удалении: {str(e)}"

def is_validate_positions(employee_position, boss_id=None) -> bool:
  print('START is_validate_positions')
  print('type of employee_position =', type(employee_position), 'value =', employee_position)
  print('type of boss_id =', type(boss_id), 'value =', boss_id)
  # Проверка, что грейд руководителя на один выше чем у подчиненного
  new_employee_position = int(employee_position)
  if boss_id:
    boss_position = get_position_by_employee_id(boss_id)
    print('END is_validate_positions')
    return boss_position == new_employee_position + 1
  else:
    print('END is_validate_positions')
    return new_employee_position == 5

def get_position_by_employee_id(employee_id) -> int:
  print('START get_position_by_employee_id')
  emp = db.session.query(Employee).filter(Employee.id == employee_id).first()
  print('END get_position_by_employee_id')
  return int(emp.position)