import sqlite3
from employee import Employee, EmployeeFactory, SalariedStrategy, HourlyStrategy

class Department:
    def __init__(self, name: str, conn: sqlite3.Connection):
        self.name = name
        self.conn = conn
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                employee_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                base_salary REAL NOT NULL,
                hours_worked INTEGER NOT NULL DEFAULT 0,
                hourly_rate REAL NOT NULL DEFAULT 0.0,
                leave_balance INTEGER NOT NULL DEFAULT 20,
                payroll_strategy TEXT NOT NULL DEFAULT 'SalariedStrategy'
            )
        """)
        self.conn.commit()

    def add_employee(self, employee: Employee):
        if not isinstance(employee, Employee):
            raise TypeError("employee must be an Employee")
        cursor = self.conn.execute(
            """
            INSERT INTO employees (name, role, base_salary, hours_worked, hourly_rate, leave_balance, payroll_strategy)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (employee.name, type(employee).__name__, employee.base_salary,
             employee.hours_worked, employee.hourly_rate, employee.leave_balance,
             type(employee.payroll_strategy).__name__)
        )
        employee.employee_id = cursor.lastrowid

    def get_employee(self, employee_id):
        cursor = self.conn.execute(
            """
            SELECT employee_id, name, role, base_salary, hours_worked, hourly_rate, leave_balance, payroll_strategy
            FROM employees WHERE employee_id = ?
            """, (employee_id,)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        (employee_id, name, role, base_salary, hours_worked, hourly_rate, leave_balance, payroll_strategy) = row
        strategy_map = {"SalariedStrategy": SalariedStrategy, "HourlyStrategy": HourlyStrategy}
        strategy_class = strategy_map.get(payroll_strategy)
        employee = EmployeeFactory.create_employee(
            role, name, base_salary, hours_worked=hours_worked, hourly_rate=hourly_rate,
            payroll_strategy=strategy_class()
        )
        employee.employee_id = employee_id
        employee._leave_balance = leave_balance
        return employee

    def list_employees(self):
        cursor = self.conn.execute(
            """
            SELECT employee_id, name, role, base_salary, hours_worked, hourly_rate, leave_balance, payroll_strategy
            FROM employees
            """
        )
        strategy_map = {"SalariedStrategy": SalariedStrategy, "HourlyStrategy": HourlyStrategy}
        employees = []
        for row in cursor.fetchall():
            (employee_id, name, role, base_salary, hours_worked, hourly_rate, leave_balance, payroll_strategy) = row
            strategy_class = strategy_map.get(payroll_strategy)
            employee = EmployeeFactory.create_employee(
                role, name, base_salary, hours_worked=hours_worked, hourly_rate=hourly_rate,
                payroll_strategy=strategy_class()
            )
            employee.employee_id = employee_id
            employee._leave_balance = leave_balance
            employees.append(employee)
        return employees

    def total_payroll(self):
        return sum(employee.calculate_salary() for employee in self.list_employees())

    def headcount_by_role(self):
        cursor = self.conn.execute("SELECT role, COUNT(*) FROM employees GROUP BY role")
        return dict(cursor.fetchall())

    def update_employee(self, employee: Employee):
        if not isinstance(employee, Employee):
            raise TypeError("employee must be an Employee")
        if employee.employee_id is None:
            raise ValueError("Employee must have an employee_id before it can be updated")
        cursor = self.conn.execute(
            """
            UPDATE employees
            SET name = ?, role = ?, base_salary = ?, hours_worked = ?, hourly_rate = ?, leave_balance = ?, payroll_strategy = ?
            WHERE employee_id = ?
            """,
            (employee.name, type(employee).__name__, employee.base_salary,
             employee.hours_worked, employee.hourly_rate, employee.leave_balance,
             type(employee.payroll_strategy).__name__, employee.employee_id)
        )
        if cursor.rowcount == 0:
            raise ValueError(f"Employee with id {employee.employee_id} does not exist")

    def remove_employee(self, employee_id):
        cursor = self.conn.execute("DELETE FROM employees WHERE employee_id = ?", (employee_id,))
        if cursor.rowcount == 0:
            raise ValueError(f"Employee with id {employee_id} does not exist")