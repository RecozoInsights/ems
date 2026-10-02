from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


def generate_pdf_report(department, leave_requests, filename="department_report.pdf"):
    styles = getSampleStyleSheet()

    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    elements = []

    # 1. Title and timestamp
    elements.append(
        Paragraph("Department Report", styles["Title"])
    )

    elements.append(
        Paragraph(
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            styles["Normal"],
        )
    )

    elements.append(Spacer(1, 20))

    # 2. Employee table
    employees = department.list_employees()

    employee_data = [
        [
            "ID",
            "Name",
            "Role",
            "Base Salary",
            "Leave Balance",
            "Calculated Salary",
        ]
    ]

    for employee in employees:
        employee_data.append(
            [
                employee.employee_id,
                employee.name,
                type(employee).__name__,
                f"{employee.base_salary:.2f}",
                employee.leave_balance,
                f"{employee.calculate_salary():.2f}",
            ]
        )

    employee_table = Table(
        employee_data,
        repeatRows=1,
        colWidths=[35, 90, 75, 75, 75, 90],
    )

    employee_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2F5597")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ALIGN", (0, 0), (0, -1), "CENTER"),
                ("ALIGN", (3, 1), (-1, -1), "RIGHT"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1),
                 [colors.white, colors.HexColor("#EAF0F8")]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                ("TOPPADDING", (0, 0), (-1, 0), 8),
            ]
        )
    )

    elements.append(
        Paragraph("Employees", styles["Heading2"])
    )
    elements.append(employee_table)

    elements.append(Spacer(1, 20))

    # 3. Summary
    elements.append(
        Paragraph("Summary", styles["Heading2"])
    )

    total_payroll = department.total_payroll()
    headcount = department.headcount_by_role()

    summary_data = [
        ["Total Payroll", f"{total_payroll:.2f}"],
        ["Headcount", str(headcount)],
    ]

    summary_table = Table(
        summary_data,
        colWidths=[130, 300],
    )

    summary_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BACKGROUND", (0, 0), (0, -1),
                 colors.HexColor("#D9E2F3")),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )

    elements.append(summary_table)

    elements.append(Spacer(1, 20))

    # 4. Leave requests table
    elements.append(
        Paragraph("Leave Requests", styles["Heading2"])
    )

    if leave_requests:
        leave_data = [
            [
                "Request ID",
                "Employee",
                "Days",
                "State",
            ]
        ]

        for leave_request in leave_requests.values():
            leave_data.append(
                [
                    leave_request.request_id,
                    leave_request.employee.name,
                    leave_request.days,
                    type(leave_request.state).__name__,
                ]
            )

        leave_table = Table(
            leave_data,
            repeatRows=1,
            colWidths=[75, 150, 75, 100],
        )

        leave_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0),
                     colors.HexColor("#548235")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("ALIGN", (0, 0), (0, -1), "CENTER"),
                    ("ALIGN", (2, 1), (2, -1), "CENTER"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1),
                     [colors.white, colors.HexColor("#E2F0D9")]),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )

        elements.append(leave_table)

    else:
        elements.append(
            Paragraph(
                "No leave requests.",
                styles["Normal"],
            )
        )

    doc.build(elements)
