from abc import ABC, abstractmethod
import itertools

class EmployeeFactory:
    @staticmethod
    def create_employee(employee_type:str, name:str, base_salary:float,**kwargs):
        role_map = {
            "manager": Manager,
            "developer": Developer,
            "intern": Intern
        }
        if employee_type.lower() in role_map:
            return role_map[employee_type.lower()](name, base_salary, **kwargs)
        else:
            raise ValueError(f"Unknown employee type: {employee_type}")
           
class Employee(ABC):
    _id_counter = itertools.count(1)
    def __init__(self, name:str, base_salary:float,hours_worked:int=0, hourly_rate:float=0.0,payroll_strategy=None):
        self.employee_id = next(self._id_counter)  # Unique ID for each employee
        self.name = name
        self.base_salary = base_salary
        self.hours_worked = hours_worked
        self.hourly_rate = hourly_rate
        self._leave_balance = 20
        self.payroll_strategy = payroll_strategy if payroll_strategy is not None else SalariedStrategy()  # Default strategy

    
    @property
    def leave_balance(self):
        return self._leave_balance

    def deduct_leave(self, days:int):
        if days <= self._leave_balance:
            self._leave_balance -= days
        else:
            raise ValueError("Insufficient leave balance")

    def restore_leave(self, days:int):
        self._leave_balance += days

    def calculate_salary(self):
        return self.payroll_strategy.calculate(self)
    @property
    @abstractmethod
    def bonus_multiplier(self):
        pass

    def __repr__(self):
        return f"{self.__class__.__name__}(ID: {self.employee_id}, Name: {self.name}, Base Salary: {self.base_salary}, Leave Balance: {self._leave_balance})"


class Manager(Employee):
    @property
    def bonus_multiplier(self):
        return 1.2  # Managers get a 20% bonus

class Developer(Employee):
    @property
    def bonus_multiplier(self):
        return 1.1  # Developers get a 10% bonus

class Intern(Employee):
    @property
    def bonus_multiplier(self):
        return 1.0  # Interns do not get a bonus


class PayrollStrategy(ABC):
    @abstractmethod
    def calculate(self, employee):
        pass

class SalariedStrategy(PayrollStrategy):
    def calculate(self, employee):
        return employee.base_salary * employee.bonus_multiplier


class HourlyStrategy(PayrollStrategy):
    def calculate(self, employee):
        return employee.hours_worked * employee.hourly_rate


class LeaveState(ABC):
    @abstractmethod
    def approve(self, leave_request):
        pass

    @abstractmethod
    def reject(self, leave_request):
        pass


class PendingState(LeaveState):
    def approve(self, leave_request):
        leave_request.employee.deduct_leave(leave_request.days)
        leave_request.state = ApprovedState()

    def reject(self, leave_request):
        # No leave was deducted while the request was pending,
        # so there is nothing to restore.
        leave_request.state = RejectedState()


class ApprovedState(LeaveState):
    def approve(self, leave_request):
        raise ValueError("Leave already approved.")

    def reject(self, leave_request):
        raise ValueError("Cannot reject an already approved leave.")


class RejectedState(LeaveState):
    def approve(self, leave_request):
        raise ValueError("Cannot approve a rejected leave.")

    def reject(self, leave_request):
        raise ValueError("Leave already rejected.")


class Observer(ABC):
    @abstractmethod
    def update(self, leave_request, event: str):
        pass


class EmailNotifier(Observer):
    def update(self, leave_request, event: str):
        print(
            f"Email sent to {leave_request.employee.name}: "
            f"your leave request was {event}."
        )


class AuditLogger(Observer):
    def __init__(self):
        self.logs = []

    def update(self, leave_request, event: str):
        message = (
            f"[AUDIT] LeaveRequest for "
            f"{leave_request.employee.name}, "
            f"{leave_request.days} days -> {event}"
        )
        self.logs.append(message)
        print(message)

class LeaveRequest:
    _id_counter = itertools.count(1)
    def __init__(self, employee: Employee, days: int):
        self.request_id = next(self._id_counter)
        self.employee = employee
        self.days = days
        self.state = PendingState()
        self._observers = []

    def attach(self, observer: Observer):
        self._observers.append(observer)

    def detach(self, observer: Observer):
        self._observers.remove(observer)

    def notify(self, event: str):
        for observer in self._observers:
            observer.update(self, event)

    def approve(self):
        self.state.approve(self)
        # Reached only if the state transition succeeded.
        self.notify("approved")

    def reject(self):
        self.state.reject(self)
        # Reached only if the state transition succeeded.
        self.notify("rejected")

    def __repr__(self):
        return (
            f"LeaveRequest("
            f"employee={self.employee.name}, "
            f"days={self.days}, "
            f"state={type(self.state).__name__}"
            f"request_id={self.request_id}"
            f")"
        )




if __name__ == "__main__":
    mgr = EmployeeFactory.create_employee("Manager", "John Doe", 5000.0)
    dev = EmployeeFactory.create_employee("Developer", "Jane Smith", 4000.0)
    intern = EmployeeFactory.create_employee("Intern", "Bob Johnson", 2000.0)

    print(mgr)
    print(dev)
    print(intern)
    employees = [mgr, dev, intern]
    for e in employees:
        print(f"{e.name}: {e.calculate_salary()}")