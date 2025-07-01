from mimesis import Person, Datetime, Numeric, Finance 
import random

personal = Person('ru')
dt = Datetime('ru')
num = Numeric()
finance = Finance()

position_weights = {
    1: 40,  # Много разработчиков
    2: 30,
    3: 20,
    4: 8,
    5: 2    # Очень мало топ-менеджеров
}

def generate_employee_data():
    __position = random.choices(
        population=list(position_weights.keys()),
        weights=list(position_weights.values()),
        k=1
    )[0]

    # __position = num.integer_number(start=1, end=5)
    __ks = __position * 1.2
    return {
        'full_name': personal.full_name(),
        'position': __position,
        'hire_date': str(dt.date(start=2010, end=2024)),
        'salary': finance.price(minimum=100000 * __ks, maximum= 200000 * __ks)
    }

# def set_relations():
