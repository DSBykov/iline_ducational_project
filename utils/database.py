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
    return f'<Employee {self.id}, full name: {self.full_name}, >'


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

