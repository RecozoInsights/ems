import sqlite3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from employee import EmployeeFactory, LeaveRequest, EmailNotifier, AuditLogger
from department import Department
from leave_repository import LeaveRequestRepository, approve_leave_request, reject_leave_request

app = FastAPI()

conn = sqlite3.connect("ems.db", check_same_thread=False)
department = Department("Engineering", conn=conn)
leave_repo = LeaveRequestRepository(conn)
audit_logger = AuditLogger()
email_notifier = EmailNotifier()


# ---------- Request Models ----------

class CreateEmployeeRequest(BaseModel):
    employee_type: str
    name: str
    base_salary: float
    hours_worked: int = 0
    hourly_rate: float = 0.0


class CreateLeaveRequest(BaseModel):
    employee_id: int
    days: int


# ---------- Response Models ----------

class EmployeeResponse(BaseModel):
    employee_id: int
    name: str
    role: str
    base_salary: float
    leave_balance: int
    calculated_salary: float


class LeaveRequestResponse(BaseModel):
    request_id: int
    employee_id: int
    employee_name: str
    days: int
    state: str


def to_employee_response(employee) -> EmployeeResponse:
    return EmployeeResponse(
        employee_id=employee.employee_id,
        name=employee.name,
        role=type(employee).__name__,
        base_salary=employee.base_salary,
        leave_balance=employee.leave_balance,
        calculated_salary=employee.calculate_salary(),
    )


def load_leave_request(request_id):
    lr = leave_repo.get(request_id, department)
    if lr is None:
        return None
    lr.attach(email_notifier)
    lr.attach(audit_logger)
    return lr


def to_leave_request_response(leave_request) -> LeaveRequestResponse:
    return LeaveRequestResponse(
        request_id=leave_request.request_id,
        employee_id=leave_request.employee.employee_id,
        employee_name=leave_request.employee.name,
        days=leave_request.days,
        state=type(leave_request.state).__name__,
    )


# ---------- Employee Routes ----------

@app.post("/employees", response_model=EmployeeResponse)
def create_employee(req: CreateEmployeeRequest):
    try:
        employee = EmployeeFactory.create_employee(
            req.employee_type, req.name, req.base_salary,
            hours_worked=req.hours_worked, hourly_rate=req.hourly_rate,
        )
        department.add_employee(employee)
        conn.commit()  # write committed here -- Department itself no longer commits
        return to_employee_response(employee)
    except (ValueError, TypeError) as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/employees", response_model=list[EmployeeResponse])
def list_employees():
    return [to_employee_response(e) for e in department.list_employees()]


@app.get("/employees/{employee_id}", response_model=EmployeeResponse)
def get_employee(employee_id: int):
    employee = department.get_employee(employee_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return to_employee_response(employee)


@app.delete("/employees/{employee_id}")
def delete_employee(employee_id: int):
    try:
        department.remove_employee(employee_id)
        conn.commit()
        return {"message": "Employee removed"}
    except ValueError as e:
        conn.rollback()
        raise HTTPException(status_code=404, detail=str(e))


# ---------- Department Routes ----------

@app.get("/department/payroll")
def get_payroll():
    return {"total_payroll": department.total_payroll()}


@app.get("/department/headcount")
def get_headcount():
    return department.headcount_by_role()


# ---------- Leave Request Routes ----------

@app.post("/leave-requests", response_model=LeaveRequestResponse)
def create_leave_request(req: CreateLeaveRequest):
    employee = department.get_employee(req.employee_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    try:
        leave_request = LeaveRequest(employee, req.days)
        leave_request.attach(email_notifier)
        leave_request.attach(audit_logger)
        leave_repo.save(leave_request)
        conn.commit()
        return to_leave_request_response(leave_request)
    except (ValueError, TypeError) as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/leave-requests", response_model=list[LeaveRequestResponse])
def list_leave_requests():
    return [to_leave_request_response(lr) for lr in leave_repo.list_all(department)]


@app.post("/leave-requests/{request_id}/approve", response_model=LeaveRequestResponse)
def approve_leave_request_route(request_id: int):
    leave_request = load_leave_request(request_id)
    if leave_request is None:
        raise HTTPException(status_code=404, detail="Leave request not found")
    try:
        approve_leave_request(leave_request, leave_repo, department)
        return to_leave_request_response(leave_request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/leave-requests/{request_id}/reject", response_model=LeaveRequestResponse)
def reject_leave_request_route(request_id: int):
    leave_request = load_leave_request(request_id)
    if leave_request is None:
        raise HTTPException(status_code=404, detail="Leave request not found")
    try:
        reject_leave_request(leave_request, leave_repo, department)
        return to_leave_request_response(leave_request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))