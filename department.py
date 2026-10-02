from employee import Employee

class Department:
    def __init__(self, name: str):
        self.name = name
        self.__employees = []

    def list_employees(self):
        return list(self.__employees)

    def add_employee(self, employee: Employee):
        # Validate type first
        if not isinstance(employee, Employee):
            raise TypeError("Only instances of Employee or its subclasses can be added.")

        # Then check for duplicate IDs
        if employee.employee_id in [e.employee_id for e in self.__employees]:
            raise ValueError(
                f"Employee with ID {employee.employee_id} already exists in the department."
            )

        self.__employees.append(employee)

    def remove_employee(self, employee_id: int):
        if employee_id not in [e.employee_id for e in self.__employees]:
            raise ValueError(
                f"No employee with ID {employee_id} found in the department."
            )

        self.__employees = [
            e for e in self.__employees
            if e.employee_id != employee_id
        ]

    def get_employee(self, employee_id: int):
        for e in self.__employees:
            if e.employee_id == employee_id:
                return e
        return None

    def total_payroll(self):
        return sum(e.calculate_salary() for e in self.__employees)

    def __repr__(self):
        return f"Department(Name: {self.name}, Employees: {len(self.__employees)})"

    def headcount_by_role(self):
        role_count = {}

        for e in self.__employees:
            role_name = e.__class__.__name__

            if role_name in role_count:
                role_count[role_name] += 1
            else:
                role_count[role_name] = 1

        return role_count
