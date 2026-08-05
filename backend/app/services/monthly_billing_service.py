from __future__ import annotations

from calendar import monthrange
from collections import defaultdict
from datetime import date, datetime, timezone
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import delete, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.models.case import Case
from app.models.case_visit import CaseVisit
from app.models.master import District, Executive
from app.models.payout_rate import BankPayoutRate, ExecutivePayoutRate
from app.models.user import User
from app.models.billing_month import BillingMonth, ExecutiveMonthlyBillingSnapshot, ExecutiveMonthlyPayment, BankMonthlyBillingSnapshot, BankMonthlyPayment
from app.schemas.monthly_billing import (BankMonthlyRow, ExecutiveMonthlyRow, MonthlyBillingResponse,
    MonthlySummary, PaymentRegisterResponse, PaymentRegisterUpdate, MonthStatusResponse,
    BankPaymentUpdate, BankPaymentResponse, BillingDashboardResponse)
from app.services.payout_rate_service import RateMatch, district_scope_for, normalized


def month_bounds(month: str) -> tuple[date, date]:
    try:
        year, number = (int(part) for part in month.split("-"))
        start = date(year, number, 1)
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail="month must use YYYY-MM format")
    return start, date(year, number, monthrange(year, number)[1])


def _effective(model, on_date: date):
    return model.is_active.is_(True), model.effective_from <= on_date, or_(model.effective_to.is_(None), model.effective_to >= on_date)


def _master_by_name(db: Session, model, column, value: str | None):
    key = normalized(value)
    if not key:
        return None
    return db.scalar(select(model).where(func.lower(func.trim(column)) == key))


def resolve_monthly_executive_rate(db: Session, case_item: Case) -> RateMatch:
    if case_item.receive_date is None:
        return RateMatch("MISSING")
    executive = _master_by_name(db, Executive, Executive.full_name, case_item.executive)
    if executive is None:
        return RateMatch("MISSING")
    rows = db.scalars(select(ExecutivePayoutRate).where(
        ExecutivePayoutRate.executive_id == executive.id,
        ExecutivePayoutRate.bank_id.is_(None), ExecutivePayoutRate.city.is_(None),
        ExecutivePayoutRate.loan_type.is_(None), ExecutivePayoutRate.product_type.is_(None),
        *_effective(ExecutivePayoutRate, case_item.receive_date),
    )).all()
    if not rows: return RateMatch("MISSING")
    if len(rows) > 1: return RateMatch("AMBIGUOUS")
    return RateMatch("MATCHED", rows[0].id, rows[0].payout_rate)


def resolve_monthly_bank_rate(db: Session, case_item: Case) -> RateMatch:
    if case_item.receive_date is None:
        return RateMatch("MISSING")
    from app.models.master import Bank
    bank = _master_by_name(db, Bank, Bank.name, case_item.bank)
    if bank is None: return RateMatch("MISSING")
    if case_item.company_id is not None and case_item.district_id is not None:
        rows = db.scalars(select(BankPayoutRate).where(BankPayoutRate.company_id == case_item.company_id,
            or_(BankPayoutRate.bank_id.is_(None), BankPayoutRate.bank_id == bank.id),
            or_(BankPayoutRate.district_id.is_(None), BankPayoutRate.district_id == case_item.district_id),
            BankPayoutRate.payout_rate > 0, *_effective(BankPayoutRate, case_item.receive_date))).all()
        district = db.get(District, case_item.district_id)
        jaipur = bool(district and normalized(district.name) == "jaipur")
        ranked = []
        for row in rows:
            scope = district_scope_for(row, district if row.district_id == case_item.district_id else None)
            exact_city = normalized(row.city) is not None and normalized(row.city) == normalized(case_item.city)
            if jaipur:
                if scope != "JAIPUR_ONLY" or (normalized(row.city) is not None and not exact_city): continue
                rank = (4 if row.bank_id is not None and exact_city else 3 if row.bank_id is not None else
                    2 if exact_city else 1)
            else:
                if normalized(row.city) is not None or scope == "JAIPUR_ONLY": continue
                specific = scope == "SELECTED_DISTRICTS" and row.district_id == case_item.district_id
                broad = scope == "RAJASTHAN_EXCEPT_JAIPUR" and row.district_id is None
                if not specific and not broad: continue
                rank = (4 if row.bank_id is not None and specific else 3 if specific else
                    2 if row.bank_id is not None else 1)
            ranked.append((rank, row))
        if ranked:
            top = max(rank for rank, _ in ranked)
            rows = [row for rank, row in ranked if rank == top]
        else:
            rows = []
    elif case_item.company_id is None and case_item.district_id is None and normalized(case_item.city):
        rows = db.scalars(select(BankPayoutRate).where(BankPayoutRate.company_id.is_(None),
            BankPayoutRate.district_id.is_(None), BankPayoutRate.bank_id == bank.id,
            func.lower(func.trim(BankPayoutRate.city)) == normalized(case_item.city),
            BankPayoutRate.loan_type.is_(None), BankPayoutRate.product_type.is_(None),
            *_effective(BankPayoutRate, case_item.receive_date))).all()
    else:
        return RateMatch("MISSING")
    if not rows: return RateMatch("MISSING")
    if len(rows) > 1: return RateMatch("AMBIGUOUS")
    return RateMatch("MATCHED", rows[0].id, rows[0].payout_rate)


class VisitBillingItem:
    """Case identity/commercial fields combined with one visit's operational fields."""
    def __init__(self, case: Case, visit: CaseVisit):
        for field in ("id", "case_no", "los_no", "bank", "company_id", "company", "loan_type", "product_type", "applicant", "mobile"):
            setattr(self, field, getattr(case, field))
        self.case_id = case.id
        self.visit_id = visit.id
        self.visit_type = visit.visit_type
        for field in ("receive_date", "closed_date", "district_id", "district", "city", "address", "executive", "status", "remarks"):
            setattr(self, field, getattr(visit, field))


def _eligible_cases(db: Session, month: str, executive=None, bank=None, city=None, case_status=None, company=None, district=None):
    start, end = month_bounds(month)
    query = select(Case, CaseVisit).join(CaseVisit, CaseVisit.case_id == Case.id).where(
        CaseVisit.receive_date.between(start, end),
        func.lower(func.trim(CaseVisit.status)).in_(("positive", "negative")))
    for column, value in ((CaseVisit.executive, executive), (Case.company, company), (Case.bank, bank), (CaseVisit.district, district), (CaseVisit.city, city), (CaseVisit.status, case_status)):
        if value:
            query = query.where(func.lower(func.trim(column)) == normalized(value))
    rows = db.execute(query.order_by(CaseVisit.receive_date, Case.id, CaseVisit.id)).all()
    items = [VisitBillingItem(case, visit) for case, visit in rows]
    # Transitional compatibility: cases are billed from legacy fields only until
    # their migration-created visit exists. A parent with any visit is never counted.
    legacy = select(Case).where(
        ~select(CaseVisit.id).where(CaseVisit.case_id == Case.id).exists(),
        Case.receive_date.between(start, end),
        func.lower(func.trim(Case.status)).in_(("positive", "negative")),
    )
    for column, value in ((Case.executive, executive), (Case.company, company), (Case.bank, bank), (Case.district, district), (Case.city, city), (Case.status, case_status)):
        if value:
            legacy = legacy.where(func.lower(func.trim(column)) == normalized(value))
    items.extend(db.scalars(legacy.order_by(Case.receive_date, Case.id)).all())
    return items


def _derived_status(paid: Decimal, net: Decimal, finalized: bool = False) -> str:
    if paid == 0: return "Pending"
    if paid < net: return "Partially Paid"
    return "Paid"


def _period(db: Session, month: str) -> BillingMonth | None:
    start, _ = month_bounds(month)
    return db.scalar(select(BillingMonth).where(BillingMonth.billing_month == start))


def month_status(db: Session, month: str) -> MonthStatusResponse:
    row = _period(db, month)
    return MonthStatusResponse(month=month, status=row.status if row else "DRAFT",
        revision_number=row.revision_number if row else 0, finalized_at=row.finalized_at if row else None,
        reopened_at=row.reopened_at if row else None, notes=row.notes if row else None)


def _snapshot_report(db: Session, month: str, period: BillingMonth) -> MonthlyBillingResponse:
    executives = db.scalars(select(ExecutiveMonthlyBillingSnapshot).where(ExecutiveMonthlyBillingSnapshot.billing_month_id == period.id).order_by(ExecutiveMonthlyBillingSnapshot.executive_name)).all()
    banks = db.scalars(select(BankMonthlyBillingSnapshot).where(BankMonthlyBillingSnapshot.billing_month_id == period.id).order_by(BankMonthlyBillingSnapshot.date, BankMonthlyBillingSnapshot.id)).all()
    payments = {x.executive_id: x for x in db.scalars(select(ExecutiveMonthlyPayment).where(ExecutiveMonthlyPayment.billing_month == period.billing_month)).all()}
    executive_rows = [ExecutiveMonthlyRow(executive_id=x.executive_id, executive=x.executive_name, rate=None,
        rate_display=x.rate_display, bank_counts=x.bank_counts, total_points=x.total_points, gross_payment=x.gross_payment,
        advance=x.advance_amount, net_payment=x.net_payment, paid=x.paid_amount, balance=x.balance_amount,
        payment_status=x.payment_status, rate_status=x.rate_status, register_id=payments[x.executive_id].id if x.executive_id in payments else None, is_finalized=True,
        payment_date=payments[x.executive_id].payment_date if x.executive_id in payments else None,
        payment_reference=payments[x.executive_id].payment_reference if x.executive_id in payments else None,
        remarks=x.remarks, snapshot_revision=period.revision_number) for x in executives]
    bank_rows = [BankMonthlyRow(case_id=x.case_id, date=x.date, company=x.company, bank=x.bank, los_no=x.los_no, name=x.applicant,
        address=x.address, district=x.district, city=x.city, mobile=x.mobile, status=x.case_status, remark=x.remark, rate=x.rate,
        rate_status=x.rate_status, bank_rate_id=x.bank_payout_rate_id) for x in banks]
    return MonthlyBillingResponse(month=month, executive_billing=executive_rows, bank_billing=bank_rows,
        summary=MonthlySummary(total_cases=len(banks), billable_cases=len(banks), missing_executive_rates=0,
        missing_bank_rates=0, ambiguous_rates=0, total_executive_payment=sum((x.gross_payment for x in executives), Decimal()),
        total_bank_billing=sum((x.rate for x in banks), Decimal())), month_status=month_status(db, month))


def monthly_billing(db: Session, month: str, executive=None, bank=None, city=None, case_status=None, company=None, district=None) -> MonthlyBillingResponse:
    period = _period(db, month)
    if period and period.status == "FINALIZED":
        report = _snapshot_report(db, month, period)
        if executive: report.executive_billing = [x for x in report.executive_billing if normalized(x.executive) == normalized(executive)]
        if company: report.bank_billing = [x for x in report.bank_billing if normalized(x.company) == normalized(company)]
        if bank: report.bank_billing = [x for x in report.bank_billing if normalized(x.bank) == normalized(bank)]
        if district: report.bank_billing = [x for x in report.bank_billing if normalized(x.district) == normalized(district)]
        if city: report.bank_billing = [x for x in report.bank_billing if normalized(x.city) == normalized(city)]
        if case_status: report.bank_billing = [x for x in report.bank_billing if normalized(x.status) == normalized(case_status)]
        return report
    start, end = month_bounds(month)
    total_query = select(func.count(Case.id)).where(Case.receive_date.between(start, end))
    for column, value in ((Case.executive, executive), (Case.company, company), (Case.bank, bank), (Case.district, district), (Case.city, city), (Case.status, case_status)):
        if value:
            total_query = total_query.where(func.lower(func.trim(column)) == normalized(value))
    cases = _eligible_cases(db, month, executive, bank, city, case_status, company, district)
    registers = {normalized(row.executive.full_name): row for row in db.scalars(select(ExecutiveMonthlyPayment).options(joinedload(ExecutiveMonthlyPayment.executive)).where(ExecutiveMonthlyPayment.billing_month == start)).all()}
    groups = defaultdict(list)
    bank_rows, missing_bank, ambiguous = [], 0, 0
    for item in cases:
        groups[normalized(item.executive) or ""].append(item)
        match = resolve_monthly_bank_rate(db, item)
        missing_bank += match.status == "MISSING"
        ambiguous += match.status == "AMBIGUOUS"
        bank_rows.append(BankMonthlyRow(case_id=getattr(item, "case_id", item.id), visit_id=getattr(item, "visit_id", None), visit_type=getattr(item, "visit_type", None), date=item.receive_date, company=item.company, bank=item.bank, los_no=item.los_no,
            name=item.applicant, address=item.address, district=item.district, city=item.city, mobile=item.mobile, status=item.status,
            remark=item.remarks, rate=match.amount, rate_status=match.status, bank_rate_id=match.rate_id))

    executive_rows, missing_executive, total_executive = [], 0, Decimal("0")
    for key, items in groups.items():
        matches = [resolve_monthly_executive_rate(db, item) for item in items]
        statuses = {match.status for match in matches}
        overall = "AMBIGUOUS" if "AMBIGUOUS" in statuses else "MISSING" if "MISSING" in statuses else "MATCHED"
        missing_executive += overall == "MISSING"
        ambiguous += overall == "AMBIGUOUS"
        amounts = [match.amount for match in matches if match.amount is not None]
        gross = sum(amounts, Decimal("0")) if overall == "MATCHED" else None
        distinct = sorted(set(amounts))
        rate = distinct[0] if overall == "MATCHED" and len(distinct) == 1 else None
        rate_display = f"{rate:.2f}" if rate is not None else "Multiple rates" if overall == "MATCHED" else overall.title()
        executive_master = _master_by_name(db, Executive, Executive.full_name, items[0].executive)
        register = registers.get(key)
        shown_gross = register.gross_payment if register and register.is_finalized else gross
        advance = register.advance_amount if register else Decimal("0")
        paid = register.paid_amount if register else Decimal("0")
        net = register.net_payment if register and register.is_finalized else (shown_gross - advance if shown_gross is not None else None)
        balance = net - paid if net is not None else None
        payment_status = register.status if register and register.is_finalized else (_derived_status(paid, net) if net is not None else "Pending")
        counts = defaultdict(int)
        for item in items: counts[(item.bank or "Unspecified").strip() or "Unspecified"] += 1
        if shown_gross is not None: total_executive += shown_gross
        executive_rows.append(ExecutiveMonthlyRow(executive_id=executive_master.id if executive_master else None,
            executive=(items[0].executive or "Unspecified").strip(), rate=rate, rate_display=rate_display,
            bank_counts=dict(sorted(counts.items())), total_points=len(items), gross_payment=shown_gross,
            advance=advance, net_payment=net, paid=paid, balance=balance, payment_status=payment_status,
            rate_status=overall, register_id=register.id if register else None, is_finalized=bool(register and register.is_finalized)))
    executive_rows.sort(key=lambda row: row.executive.casefold())
    return MonthlyBillingResponse(month=month, executive_billing=executive_rows, bank_billing=bank_rows,
        summary=MonthlySummary(total_cases=db.scalar(total_query) or 0, billable_cases=len(cases),
            missing_executive_rates=missing_executive, missing_bank_rates=missing_bank, ambiguous_rates=ambiguous,
            total_executive_payment=total_executive,
            total_bank_billing=sum((row.rate for row in bank_rows if row.rate is not None), Decimal("0"))),
        month_status=month_status(db, month))


def save_payment_register(db: Session, payload: PaymentRegisterUpdate, user: User) -> PaymentRegisterResponse:
    start, _ = month_bounds(payload.billing_month)
    executive = db.get(Executive, payload.executive_id)
    if executive is None: raise HTTPException(status_code=404, detail="Executive not found")
    current = db.scalar(select(ExecutiveMonthlyPayment).where(ExecutiveMonthlyPayment.billing_month == start, ExecutiveMonthlyPayment.executive_id == executive.id).with_for_update())
    period = _period(db, payload.billing_month)
    snapshot = db.scalar(select(ExecutiveMonthlyBillingSnapshot).where(
        ExecutiveMonthlyBillingSnapshot.billing_month_id == period.id,
        ExecutiveMonthlyBillingSnapshot.executive_id == executive.id).with_for_update()) if period and period.status == "FINALIZED" else None
    if snapshot:
        gross = snapshot.gross_payment
    elif current and current.is_finalized and not payload.regenerate:
        gross = current.gross_payment
    else:
        cases = _eligible_cases(db, payload.billing_month, executive=executive.full_name)
        if not cases: raise HTTPException(status_code=422, detail="No eligible cases for this executive and month")
        matches = [resolve_monthly_executive_rate(db, item) for item in cases]
        if any(match.status != "MATCHED" for match in matches):
            rate_status = "AMBIGUOUS" if any(match.status == "AMBIGUOUS" for match in matches) else "MISSING"
            raise HTTPException(status_code=422, detail=f"Cannot save payment register: executive rate is {rate_status}")
        gross = sum((match.amount for match in matches if match.amount is not None), Decimal("0"))
    if payload.advance_amount > gross: raise HTTPException(status_code=422, detail="advance_amount cannot exceed gross_payment")
    net = gross - payload.advance_amount
    if payload.paid_amount > net: raise HTTPException(status_code=422, detail="paid_amount cannot exceed net_payment")
    values = dict(gross_payment=gross, advance_amount=payload.advance_amount, net_payment=net,
        paid_amount=payload.paid_amount, balance_amount=net - payload.paid_amount,
        status=_derived_status(payload.paid_amount, net, payload.finalize), payment_date=payload.payment_date,
        payment_reference=payload.payment_reference.strip() if payload.payment_reference else None,
        remarks=payload.remarks.strip() if payload.remarks else None, is_finalized=payload.finalize,
        updated_by_user_id=user.id)
    if current:
        for field, value in values.items(): setattr(current, field, value)
    else:
        current = ExecutiveMonthlyPayment(billing_month=start, executive_id=executive.id,
            created_by_user_id=user.id, **values); db.add(current)
    if snapshot:
        snapshot.advance_amount = payload.advance_amount; snapshot.net_payment = net
        snapshot.paid_amount = payload.paid_amount; snapshot.balance_amount = net-payload.paid_amount
        snapshot.payment_status = values["status"]; snapshot.remarks = values["remarks"]
    try: db.commit(); db.refresh(current)
    except IntegrityError as exc: db.rollback(); raise HTTPException(status_code=409, detail="Payment register was concurrently updated") from exc
    return PaymentRegisterResponse.model_validate({**current.__dict__, "executive": executive.full_name})


def _validate_report(report: MonthlyBillingResponse) -> None:
    if report.summary.missing_bank_rates or report.summary.missing_executive_rates or report.summary.ambiguous_rates:
        raise HTTPException(status_code=422, detail={"message": "All rates must be matched before finalization",
            "missing_bank_rates": report.summary.missing_bank_rates, "missing_executive_rates": report.summary.missing_executive_rates,
            "ambiguous_rates": report.summary.ambiguous_rates})


def _replace_snapshots(db: Session, period: BillingMonth, report: MonthlyBillingResponse, regeneration: bool) -> None:
    existing_payments = {x.executive_id: x for x in db.scalars(select(ExecutiveMonthlyPayment).where(ExecutiveMonthlyPayment.billing_month == period.billing_month)).all()}
    if regeneration:
        conflicts = []
        for row in report.executive_billing:
            payment = existing_payments.get(row.executive_id)
            gross = row.gross_payment or Decimal()
            net = gross - (payment.advance_amount if payment else Decimal())
            if payment and payment.paid_amount > net:
                conflicts.append({"executive": row.executive, "paid": str(payment.paid_amount), "new_net": str(net)})
        if conflicts:
            raise HTTPException(status_code=409, detail={"message": "Regeneration would make executives overpaid", "conflicts": conflicts})
        db.execute(delete(ExecutiveMonthlyBillingSnapshot).where(ExecutiveMonthlyBillingSnapshot.billing_month_id == period.id))
        db.execute(delete(BankMonthlyBillingSnapshot).where(BankMonthlyBillingSnapshot.billing_month_id == period.id))
    for row in report.executive_billing:
        payment = existing_payments.get(row.executive_id)
        advance = payment.advance_amount if payment else row.advance
        paid = payment.paid_amount if payment else row.paid
        gross = row.gross_payment or Decimal()
        net = gross - advance
        db.add(ExecutiveMonthlyBillingSnapshot(billing_month_id=period.id, executive_id=row.executive_id,
            executive_name=row.executive, rate_display=row.rate_display, total_points=row.total_points,
            gross_payment=gross, advance_amount=advance, net_payment=net, paid_amount=paid,
            balance_amount=net-paid, payment_status=_derived_status(paid, net), bank_counts=row.bank_counts,
            rate_status=row.rate_status, remarks=payment.remarks if payment else None))
    for row in report.bank_billing:
        db.add(BankMonthlyBillingSnapshot(billing_month_id=period.id, case_id=row.case_id, date=row.date,
            company=row.company, bank=row.bank, los_no=row.los_no, applicant=row.name, address=row.address,
            district=row.district, city=row.city,
            mobile=row.mobile, case_status=row.status, remark=row.remark, rate=row.rate or Decimal(), rate_status=row.rate_status,
            bank_payout_rate_id=row.bank_rate_id))
    totals = defaultdict(Decimal)
    for row in report.bank_billing:
        totals[((row.company or "").strip(), (row.bank or "Unspecified").strip(), (row.district or "").strip())] += row.rate or Decimal()
    prior = {(x.company, x.bank, x.district): x for x in db.scalars(select(BankMonthlyPayment).where(BankMonthlyPayment.billing_month == period.billing_month)).all()}
    for (company, bank, district), billed in totals.items():
        payment = prior.get((company, bank, district))
        if payment:
            if payment.received_amount > billed:
                raise HTTPException(status_code=409, detail=f"Regeneration would overpay {company} / {bank} / {district}")
            payment.billed_amount = billed; payment.balance_amount = billed-payment.received_amount
            if payment.status != "Cancelled": payment.status = _derived_status(payment.received_amount, billed)
            payment.is_finalized = True
        else:
            db.add(BankMonthlyPayment(billing_month=period.billing_month, company=company, bank=bank, district=district, city="",
                billed_amount=billed, received_amount=0, balance_amount=billed, status="Pending", is_finalized=True))


def finalize_month(db: Session, month: str, notes: str | None, user: User, regenerate: bool = False) -> MonthStatusResponse:
    start, _ = month_bounds(month)
    period = _period(db, month)
    if regenerate:
        if not period or period.status != "REOPENED": raise HTTPException(status_code=409, detail="Only a reopened month can be regenerated")
    elif period and period.status == "FINALIZED":
        raise HTTPException(status_code=409, detail="Month is already finalized; reopen it first")
    report = monthly_billing(db, month)
    _validate_report(report)
    now = datetime.now(timezone.utc)
    try:
        if not period:
            period = BillingMonth(billing_month=start, status="DRAFT"); db.add(period); db.flush()
        _replace_snapshots(db, period, report, regenerate)
        period.status = "FINALIZED"; period.finalized_at = now; period.finalized_by_user_id = user.id
        period.notes = notes if notes is not None else period.notes
        if regenerate: period.revision_number += 1
        db.commit(); db.refresh(period)
    except HTTPException:
        db.rollback(); raise
    except IntegrityError as exc:
        db.rollback(); raise HTTPException(status_code=409, detail="Month was concurrently finalized") from exc
    return month_status(db, month)


def reopen_month(db: Session, month: str, reason: str, user: User) -> MonthStatusResponse:
    period = _period(db, month)
    if not period or period.status != "FINALIZED": raise HTTPException(status_code=409, detail="Only a finalized month can be reopened")
    period.status = "REOPENED"; period.reopened_at = datetime.now(timezone.utc); period.reopened_by_user_id = user.id
    period.notes = reason.strip(); db.commit(); db.refresh(period)
    return month_status(db, month)


def save_bank_payment(db: Session, payload: BankPaymentUpdate, user: User) -> BankPaymentResponse:
    start, _ = month_bounds(payload.billing_month)
    row = db.scalar(select(BankMonthlyPayment).where(BankMonthlyPayment.billing_month == start,
        BankMonthlyPayment.company == payload.company.strip(), BankMonthlyPayment.bank == payload.bank.strip(),
        BankMonthlyPayment.district == payload.district.strip()).with_for_update())
    if not row: raise HTTPException(status_code=404, detail="Bank payment register row not found; finalize the month first")
    if payload.received_amount > row.billed_amount: raise HTTPException(status_code=422, detail="received_amount cannot exceed billed_amount")
    cancelled = payload.status == "Cancelled"
    old = row.received_amount
    row.received_amount = payload.received_amount; row.balance_amount = row.billed_amount-payload.received_amount
    row.status = "Cancelled" if cancelled else _derived_status(payload.received_amount, row.billed_amount)
    row.payment_date = payload.payment_date or (date.today() if old == 0 and payload.received_amount > 0 else row.payment_date)
    if payload.received_amount == 0 and not cancelled: row.payment_date = None
    row.payment_reference = payload.payment_reference.strip() if payload.payment_reference else None
    row.remarks = payload.remarks.strip() if payload.remarks else None; row.updated_by_user_id = user.id
    db.commit(); db.refresh(row); return BankPaymentResponse.model_validate(row)


def billing_dashboard(db: Session, month: str, company: str | None = None, bank: str | None = None, district: str | None = None) -> BillingDashboardResponse:
    report = monthly_billing(db, month, bank=bank, company=company, district=district)
    start, _ = month_bounds(month)
    query = select(BankMonthlyPayment).where(BankMonthlyPayment.billing_month == start)
    for column, value in ((BankMonthlyPayment.company, company), (BankMonthlyPayment.bank, bank), (BankMonthlyPayment.district, district)):
        if value: query = query.where(func.lower(func.trim(column)) == normalized(value))
    banks = db.scalars(query.order_by(BankMonthlyPayment.company, BankMonthlyPayment.bank, BankMonthlyPayment.district)).all()
    bank_rows = [BankPaymentResponse.model_validate(x) for x in banks]
    bank_total = report.summary.total_bank_billing
    bank_received = sum((x.received_amount for x in banks if x.status != "Cancelled"), Decimal())
    executive_total = sum((x.net_payment or Decimal() for x in report.executive_billing), Decimal())
    executive_paid = sum((x.paid for x in report.executive_billing if x.payment_status != "Cancelled"), Decimal())
    return BillingDashboardResponse(month=month, month_status=report.month_status, total_bank_billing=bank_total,
        bank_received=bank_received, bank_outstanding=bank_total-bank_received, total_executive_payout=executive_total,
        executive_paid=executive_paid, executive_outstanding=executive_total-executive_paid,
        expected_gross_margin=bank_total-executive_total, realized_cash_margin=bank_received-executive_paid,
        bank_summary=bank_rows, executive_summary=report.executive_billing)
