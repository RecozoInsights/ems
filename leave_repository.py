from employee import LeaveRequest, PendingState, ApprovedState, RejectedState

class LeaveRequestRepository:
    def __init__(self, conn):
        self.conn = conn
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS leave_requests (
                request_id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                days INTEGER NOT NULL,
                state TEXT NOT NULL DEFAULT 'PendingState',
                FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
            )
        """)
        self.conn.commit()

    def save(self, leave_request):
        if not isinstance(leave_request, LeaveRequest):
            raise TypeError("leave_request must be a LeaveRequest")
        if leave_request.request_id is not None:
            raise ValueError("LeaveRequest is already saved")
        state_name = type(leave_request.state).__name__
        cursor = self.conn.execute(
            "INSERT INTO leave_requests (employee_id, days, state) VALUES (?, ?, ?)",
            (leave_request.employee.employee_id, leave_request.days, state_name)
        )
        leave_request.request_id = cursor.lastrowid

    def get(self, request_id, department):
        cursor = self.conn.execute(
            "SELECT request_id, employee_id, days, state FROM leave_requests WHERE request_id = ?",
            (request_id,)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        (request_id, employee_id, days, state_name) = row
        employee = department.get_employee(employee_id)
        if employee is None:
            raise ValueError(f"Employee {employee_id} referenced by leave request {request_id} was not found.")
        state_map = {"PendingState": PendingState, "ApprovedState": ApprovedState, "RejectedState": RejectedState}
        state_class = state_map.get(state_name)
        leave_request = LeaveRequest(employee=employee, days=days, request_id=request_id)
        leave_request.state = state_class()
        return leave_request

    def list_all(self, department):
        cursor = self.conn.execute("""
            SELECT request_id
            FROM leave_requests
            ORDER BY request_id
        """)
        request_ids = [row[0] for row in cursor.fetchall()]
        return [self.get(request_id, department) for request_id in request_ids]

    def update(self, leave_request):
        if not isinstance(leave_request, LeaveRequest):
            raise TypeError("leave_request must be a LeaveRequest")
        if leave_request.request_id is None:
            raise ValueError("LeaveRequest must have a request_id before it can be updated")
        state_name = type(leave_request.state).__name__
        cursor = self.conn.execute(
            "UPDATE leave_requests SET state = ? WHERE request_id = ?",
            (state_name, leave_request.request_id)
        )
        if cursor.rowcount == 0:
            raise ValueError(f"LeaveRequest with id {leave_request.request_id} does not exist")

def approve_leave_request(lr, leave_repo, department):
    conn = leave_repo.conn
    try:
        lr.approve()
        leave_repo.update(lr)
        department.update_employee(lr.employee)
        conn.commit()
    except Exception:
        conn.rollback()
        raise

def reject_leave_request(lr, leave_repo, department):
    conn = leave_repo.conn
    try:
        lr.reject()
        leave_repo.update(lr)
        conn.commit()
    except Exception:
        conn.rollback()
        raise