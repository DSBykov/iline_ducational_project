## Структура БД 

### Создание таблицы сотрудников: 

```sql
CREATE TABLE IF NOT EXISTS public.employees
(
    id integer NOT NULL DEFAULT nextval('employees_id_seq'::regclass),
    full_name character varying(100) COLLATE pg_catalog."default" NOT NULL,
    "position" character varying(100) COLLATE pg_catalog."default" NOT NULL,
    hire_date date NOT NULL,
    salary numeric(10,2) NOT NULL,
    CONSTRAINT employees_pkey PRIMARY KEY (id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.employees
    OWNER to postgres;
```

### Создание таблицы связей сотрудников (Начальник - подчиненный)

```sql
CREATE TABLE IF NOT EXISTS public.employee_hierarchy
(
    boss_id integer NOT NULL,
    subordinate_id integer NOT NULL,
    CONSTRAINT employee_hierarchy_pkey PRIMARY KEY (boss_id, subordinate_id),
    CONSTRAINT employee_hierarchy_boss_id_fkey FOREIGN KEY (boss_id)
        REFERENCES public.employees (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE,
    CONSTRAINT employee_hierarchy_subordinate_id_fkey FOREIGN KEY (subordinate_id)
        REFERENCES public.employees (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE CASCADE
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.employee_hierarchy
    OWNER to postgres;
```

### Создание таблицы справочника должности сотрудника

```sql
CREATE TABLE IF NOT EXISTS public.positions
(
    position_id integer NOT NULL,
    position_name character varying(100) COLLATE pg_catalog."default" NOT NULL
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.positions
    OWNER to postgres;
```

#### Заполнение справочника:

```sql
INSERT INTO positions (position_name, position_id) VALUES
('Developer', 1),
('Senior Developer', 2),
('Team Lead', 3),
('Manager', 4),
('CEO', 5);
```

# Запуск проекта

## Настройка виртуального окружения

* Перейти в папку проекта
```bash
cd путь/к/вашему/проекту
```

* Создать виртуальное окружение
```bash
python3 -m venv venv
```

* Активировать виртуальное окружение

Для Windows
```bash
.\venv\Scripts\activate
```

Для MacOS/Linux
```bash
source ./venv/bin/activate
```

После активации в начале командной строки появится (venv).

* Установить зависимости

```bash
pip install -r requirements.txt
```

## Генерация фективных данных 

* Проверьте параметры подключения к БД в файле `./utils/dbconnection.py`, при необходимости отредактируйте их в соотвествии со значениями указанными при создании БД
```python3
                dbname="iline_db",
                user="postgres",
                password="db_password",
                host="localhost",
                port="5432"
```

Откройте кмандную строку и перейдите в корневую деректорию пректа.

Для запуска генерации данных 50000 сотрудников, выполните команду :
 ```bash
# python3 data_generator.py
 ```

 ## Запуск консольного приложения для взаимодействия с БД:
``` bash
# python3 main.py
```
