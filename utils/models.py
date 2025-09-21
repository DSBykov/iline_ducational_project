from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from sqlalchemy.orm import Mapped, mapped_column


db = SQLAlchemy()


class Employee(db.Model):
    __tablename__ = 'employees'

    id: Mapped[int] = mapped_column(primary_key=True, nullable=False) # = db.Column(db.Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(nullable=False)  #  db.Column(db.String(100), nullable=False)
    position: Mapped[str] = mapped_column(nullable=False)# db.Column(db.String(100), nullable=False)
    hire_date: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc)) # db.Column(db.Date, nullable=False)
    salary = db.Column(db.Numeric(10, 2), nullable=False)

    def __repr__(self):
        return f'<Employee {self.full_name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'full_name': self.full_name,
            'position': self.position,
            'hire_date': self.hire_date.isoformat(),
            'salary': float(self.salary)
        }


