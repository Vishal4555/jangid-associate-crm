from collections import defaultdict
from datetime import date, datetime, timezone
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.billing_month import BankMonthlyBillingSnapshot, BankMonthlyPayment, BillingMonth
from app.models.case import Case
from app.models.case_visit import CaseVisit
from app.models.master import Company, Executive
from app.models.user import User
from app.schemas.billing_reports import (CompanyBillingReport, CompanyBillingReportRow,
    ExecutiveBankSummaryRow, ExecutivePerformanceReport, ExecutiveSummaryRow, ExecutiveVisitDetail, ReportMetadata)
from app.services.monthly_billing_service import (VisitBillingItem, resolve_monthly_bank_rate,
    resolve_monthly_executive_rate)
from app.services.payout_rate_service import normalized


def _months(start: date, end: date):
    cursor = start.replace(day=1)
    while cursor <= end:
        yield cursor
        cursor = date(cursor.year + (cursor.month == 12), 1 if cursor.month == 12 else cursor.month + 1, 1)


def _metadata(db: Session, start: date, end: date) -> ReportMetadata:
    periods = {x.billing_month: x for x in db.scalars(select(BillingMonth).where(
        BillingMonth.billing_month >= start.replace(day=1), BillingMonth.billing_month <= end.replace(day=1))).all()}
    finalized, draft = [], []
    for month in _months(start, end):
        (finalized if periods.get(month) and periods[month].status == "FINALIZED" else draft).append(month.strftime("%Y-%m"))
    return ReportMetadata(state="FINALIZED" if finalized and not draft else "DRAFT" if draft and not finalized else "MIXED",
        contains_draft=bool(draft), contains_finalized=bool(finalized), finalized_months=finalized,
        draft_months=draft, generated_at=datetime.now(timezone.utc), limitations=[])


def _executive_address(executive: Executive | None) -> str | None:
    if executive is None: return None
    value = ", ".join(str(x).strip() for x in (executive.address, executive.city, executive.district_name, executive.pincode) if x and str(x).strip())
    return value or None


def _visits(db, start, end, company_ids, executive_name=None, company_id=None, bank=None,
            district_id=None, city=None, executive=None, visit_type=None, status=None):
    stmt = select(Case, CaseVisit).join(CaseVisit, CaseVisit.case_id == Case.id).where(CaseVisit.receive_date.between(start, end))
    if company_ids is not None: stmt = stmt.where(Case.company_id.in_(company_ids))
    if company_id is not None: stmt = stmt.where(Case.company_id == company_id)
    if district_id is not None: stmt = stmt.where(CaseVisit.district_id == district_id)
    for column, value in ((Case.bank, bank), (CaseVisit.city, city), (CaseVisit.executive, executive_name or executive),
                          (CaseVisit.visit_type, visit_type), (CaseVisit.status, status)):
        if value: stmt = stmt.where(func.lower(func.trim(column)) == normalized(value))
    return [VisitBillingItem(case, visit) for case, visit in db.execute(stmt.order_by(CaseVisit.receive_date, CaseVisit.id)).all()]


def _payment_status(db, item):
    month = item.receive_date.replace(day=1)
    row = db.scalar(select(BankMonthlyPayment).where(BankMonthlyPayment.billing_month == month,
        BankMonthlyPayment.company == (item.company or ""), BankMonthlyPayment.bank == (item.bank or ""),
        BankMonthlyPayment.district == (item.district or "")))
    return row.status if row else "Pending"


def _frozen_visits(db, start, end):
    rows = db.execute(select(BankMonthlyBillingSnapshot, BillingMonth).join(
        BillingMonth, BillingMonth.id == BankMonthlyBillingSnapshot.billing_month_id).where(
        BillingMonth.status == "FINALIZED", BankMonthlyBillingSnapshot.date.between(start, end))).all()
    return {snapshot.visit_id: snapshot for snapshot, _ in rows if snapshot.visit_id is not None}


def company_report(db: Session, user: User, company_ids, company_id: int | None, date_from: date,
                   date_to: date, **filters):
    if date_from > date_to: raise HTTPException(status_code=422, detail="date_from must be on or before date_to")
    if company_id is None: raise HTTPException(status_code=422, detail="company_id is required")
    if company_ids is not None and company_id not in company_ids: raise HTTPException(status_code=403, detail="Company is not assigned to this user")
    if db.get(Company, company_id) is None: raise HTTPException(status_code=404, detail="Company not found")
    own = user.executive_name if user.role == "Executive" else None
    items = _visits(db, date_from, date_to, company_ids, own, company_id, **{k:v for k,v in filters.items() if k != "payment_status"})
    rows = []
    frozen = _frozen_visits(db, date_from, date_to)
    for item in items:
        snapshot = frozen.get(item.visit_id)
        bank_rate, exec_rate = resolve_monthly_bank_rate(db, item), resolve_monthly_executive_rate(db, item)
        payment = _payment_status(db, item)
        if filters.get("payment_status") and normalized(payment) != normalized(filters["payment_status"]): continue
        rows.append(CompanyBillingReportRow(date=item.receive_date, los=item.los_no, bank=item.bank,
            visit_type=item.visit_type, applicant=item.applicant, address=item.address, dist=item.district,
            city=item.city, mobile_number=item.mobile, executive=item.executive, status=item.status,
            executive_rate=snapshot.executive_rate if snapshot else exec_rate.amount,
            executive_rate_status=snapshot.executive_rate_status if snapshot else exec_rate.status,
            company_rate=snapshot.rate if snapshot else bank_rate.amount,
            company_rate_status=snapshot.rate_status if snapshot else bank_rate.status, payment_status=payment))
    metadata = _metadata(db, date_from, date_to)
    register_keys = {(item.receive_date.replace(day=1), item.company or "", item.bank or "", item.district or "") for item in items}
    registers = db.scalars(select(BankMonthlyPayment).where(BankMonthlyPayment.billing_month.between(
        date_from.replace(day=1), date_to.replace(day=1)), BankMonthlyPayment.company == db.get(Company, company_id).name)).all()
    relevant_registers = [x for x in registers if (x.billing_month, x.company, x.bank, x.district) in register_keys]
    return CompanyBillingReport(items=rows, totals={"total_visits": len(rows),
        "pending": sum(x.status == "Pending" for x in rows), "positive": sum(x.status == "Positive" for x in rows),
        "negative": sum(x.status == "Negative" for x in rows),
        "executive_payment_total": sum((x.executive_rate for x in rows if x.executive_rate is not None), Decimal()),
        "company_billing_total": sum((x.company_rate for x in rows if x.company_rate is not None), Decimal()),
        "paid_total": sum((x.received_amount for x in relevant_registers), Decimal()),
        "balance_total": sum((x.balance_amount for x in relevant_registers), Decimal()),
        "missing_executive_rate_count": sum(x.executive_rate is None for x in rows),
        "missing_company_rate_count": sum(x.company_rate is None for x in rows)},
        applied_filters={"company_id": company_id, "date_from": date_from.isoformat(), "date_to": date_to.isoformat(), **filters}, metadata=metadata)


def executive_report(db: Session, user: User, company_ids, date_from: date, date_to: date, **filters):
    if date_from > date_to: raise HTTPException(status_code=422, detail="date_from must be on or before date_to")
    own = user.executive_name if user.role == "Executive" else None
    items = _visits(db, date_from, date_to, company_ids, own, filters.pop("company_id", None), **filters)
    masters = {normalized(x.full_name): x for x in db.scalars(select(Executive)).all()}
    frozen = _frozen_visits(db, date_from, date_to)
    groups = defaultdict(list)
    for item in items: groups[((item.executive or "Unspecified").strip(), (item.bank or "Unspecified").strip())].append(item)
    bank_rows = []
    for (executive, bank), visits in sorted(groups.items()):
        matches = [resolve_monthly_executive_rate(db, x) for x in visits]
        for index, visit in enumerate(visits):
            snapshot = frozen.get(visit.visit_id)
            if snapshot is not None:
                matches[index] = type(matches[index])(snapshot.executive_rate_status or "MISSING", amount=snapshot.executive_rate)
        status = "MISSING" if any(x.status == "MISSING" for x in matches) else "AMBIGUOUS" if any(x.status == "AMBIGUOUS" for x in matches) else "MATCHED"
        master = masters.get(normalized(executive))
        bank_rows.append(ExecutiveBankSummaryRow(executive=executive, bank_finance_company=bank,
            address=_executive_address(master), mobile=master.mobile if master else None, total_cases_visits=len(visits),
            pending=sum(x.status == "Pending" for x in visits), positive=sum(x.status == "Positive" for x in visits),
            negative=sum(x.status == "Negative" for x in visits), rate_status=status,
            executive_rate_total=sum((x.amount for x in matches if x.amount is not None), Decimal()) if status == "MATCHED" else None,
            details=[ExecutiveVisitDetail(date=visit.receive_date, los=visit.los_no, applicant=visit.applicant,
                visit_type=visit.visit_type, company=visit.company, bank=visit.bank, district=visit.district,
                city=visit.city, status=visit.status, executive_rate=match.amount,
                executive_rate_status=match.status) for visit, match in zip(visits, matches)]))
    summaries = []
    for executive in sorted({x.executive for x in bank_rows}):
        rows = [x for x in bank_rows if x.executive == executive]; master = masters.get(normalized(executive))
        ok = all(x.rate_status == "MATCHED" for x in rows)
        summaries.append(ExecutiveSummaryRow(executive=executive, address=_executive_address(master), mobile=master.mobile if master else None,
            total_visits=sum(x.total_cases_visits for x in rows), pending=sum(x.pending for x in rows),
            positive=sum(x.positive for x in rows), negative=sum(x.negative for x in rows),
            total_payment=sum((x.executive_rate_total or Decimal() for x in rows), Decimal()) if ok else None,
            rate_status="MATCHED" if ok else "MISSING"))
    return ExecutivePerformanceReport(items=bank_rows, executive_summary=summaries,
        totals={"total_visits": len(items), "pending": sum(x.status == "Pending" for x in items),
            "positive": sum(x.status == "Positive" for x in items), "negative": sum(x.status == "Negative" for x in items),
            "executive_rate_total": sum((x.total_payment for x in summaries if x.total_payment is not None), Decimal()),
            "missing_rate_count": sum(detail.executive_rate is None for row in bank_rows for detail in row.details)},
        applied_filters={"date_from": date_from.isoformat(), "date_to": date_to.isoformat(), **filters}, metadata=_metadata(db, date_from, date_to))
