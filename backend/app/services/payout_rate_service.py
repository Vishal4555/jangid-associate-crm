from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models.billing import Billing
from app.models.billing_month import BankMonthlyBillingSnapshot
from app.models.case import Case
from app.models.master import Bank, Company, District, Executive, LoanType, ProductType
from app.models.payout_rate import BankPayoutRate, ExecutivePayoutRate
from app.models.user import User
from app.schemas.payout_rate import (
    BankRateBulkCreate, BankRateBulkResponse, BankRateCreate, BankRateResponse, ExecutiveRateCreate, ExecutiveRateResponse,
    RateImportRequest, RateImportResponse, RateImportResultRow,
)


def normalized(value: str | None) -> str | None:
    return value.strip().casefold() if value and value.strip() else None


def _same(column, value: str | None):
    return func.lower(func.trim(func.coalesce(column, ""))) == (normalized(value) or "")


def district_scope_for(rate, district: District | None = None) -> str:
    """Read explicit scope, with compatibility for rows predating the column."""
    if getattr(rate, "district_scope", None):
        return rate.district_scope
    if rate.district_id is None:
        return "RAJASTHAN_EXCEPT_JAIPUR"
    return "JAIPUR_ONLY" if district and normalized(district.name) == "jaipur" else "SELECTED_DISTRICTS"


def _normalize_bank_scope(db: Session, data: dict) -> None:
    if data.get("company_id") is None:
        return
    district = db.get(District, data["district_id"]) if data.get("district_id") is not None else None
    scope = data.get("district_scope") or ("RAJASTHAN_EXCEPT_JAIPUR" if district is None else
        "JAIPUR_ONLY" if normalized(district.name) == "jaipur" else "SELECTED_DISTRICTS")
    data["district_scope"] = scope
    if scope == "RAJASTHAN_EXCEPT_JAIPUR" and (district is not None or normalized(data.get("city")) is not None):
        raise HTTPException(status_code=422, detail="Rajasthan Except Jaipur rules cannot specify district or city")
    if scope == "JAIPUR_ONLY" and (district is None or normalized(district.name) != "jaipur"):
        raise HTTPException(status_code=422, detail="Jaipur Only scope must reference Jaipur district")
    if scope == "SELECTED_DISTRICTS" and district is None:
        raise HTTPException(status_code=422, detail="Selected Districts scope requires a district")


def _overlap(model, data: dict, exclude_id: int | None = None):
    end = data["effective_to"] or date.max
    query = select(model.id).where(
        model.effective_from <= end,
        or_(model.effective_to.is_(None), model.effective_to >= data["effective_from"]),
    )
    dimensions = ["bank_id", "city", "loan_type", "product_type"]
    if model is BankPayoutRate and (data.get("company_id") is not None or data.get("district_id") is not None):
        dimensions = ["company_id", "bank_id", "district_scope", "district_id", "city"]
    if model is ExecutivePayoutRate:
        dimensions.insert(0, "executive_id")
    for field in dimensions:
        value = data.get(field)
        column = getattr(model, field)
        query = query.where(column == value) if field.endswith("_id") else query.where(_same(column, value))
    if exclude_id is not None:
        query = query.where(model.id != exclude_id)
    return query


def _ensure_refs(db: Session, data: dict, executive: bool = False) -> None:
    if not executive:
        _normalize_bank_scope(db, data)
    bank = db.get(Bank, data["bank_id"]) if data.get("bank_id") is not None else None
    if data.get("bank_id") is not None and bank is None:
        raise HTTPException(status_code=422, detail="Bank does not exist")
    if executive and db.get(Executive, data["executive_id"]) is None:
        raise HTTPException(status_code=422, detail="Executive does not exist")
    structured_bank_rate = not executive and data.get("company_id") is not None
    company = db.get(Company, data.get("company_id")) if structured_bank_rate else None
    district = db.get(District, data.get("district_id")) if structured_bank_rate and data.get("district_id") is not None else None
    if structured_bank_rate and (company is None or not company.is_active):
        raise HTTPException(status_code=422, detail="Active company does not exist")
    if structured_bank_rate and data.get("district_id") is not None and (district is None or not district.is_active):
        raise HTTPException(status_code=422, detail="Active district does not exist")
    if structured_bank_rate:
        if (district is None or normalized(district.name) != "jaipur") and normalized(data.get("city")) is not None:
            raise HTTPException(status_code=422, detail="City-specific rates are allowed only for Jaipur district.")


def _ensure_no_overlap(db: Session, model, data: dict, exclude_id: int | None = None) -> None:
    if not data.get("is_active", True):
        return
    query = _overlap(model, data, exclude_id).where(model.is_active.is_(True))
    if db.scalar(query) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Effective dates overlap an existing rate with identical matching dimensions")


def _bank_response(rate: BankPayoutRate) -> BankRateResponse:
    return BankRateResponse.model_validate({**rate.__dict__, "bank_name": rate.bank.name if rate.bank else None,
        "company_name": rate.company.name if rate.company else None,
        "district_name": rate.district.name if rate.district else None})


def _executive_response(rate: ExecutivePayoutRate) -> ExecutiveRateResponse:
    return ExecutiveRateResponse.model_validate({
        **rate.__dict__, "executive_name": rate.executive.full_name,
        "bank_name": rate.bank.name if rate.bank else None,
    })


def list_rates(db: Session, kind: str, search: str | None = None, active: bool | None = None,
        company_id: int | None = None, bank_id: int | None = None, district_id: int | None = None,
        scope: str | None = None):
    model = BankPayoutRate if kind == "bank" else ExecutivePayoutRate
    query = db.query(model).options(joinedload(model.bank))
    if kind == "bank": query = query.options(joinedload(BankPayoutRate.company), joinedload(BankPayoutRate.district))
    if kind == "executive":
        query = query.options(joinedload(ExecutivePayoutRate.executive))
    if active is not None:
        query = query.filter(model.is_active == active)
    if kind == "bank":
        if company_id is not None: query = query.filter(BankPayoutRate.company_id == company_id)
        if bank_id is not None: query = query.filter(BankPayoutRate.bank_id == bank_id)
        if district_id is not None: query = query.filter(BankPayoutRate.district_id == district_id)
        if scope == "rajasthan_except_jaipur": query = query.filter(BankPayoutRate.district_scope == "RAJASTHAN_EXCEPT_JAIPUR")
        elif scope == "jaipur": query = query.filter(BankPayoutRate.district_scope == "JAIPUR_ONLY")
        elif scope == "specific": query = query.filter(BankPayoutRate.district_scope == "SELECTED_DISTRICTS")
    rows = query.order_by(model.effective_from.desc(), model.id.desc()).all()
    responses = [_bank_response(row) if kind == "bank" else _executive_response(row) for row in rows]
    if search:
        term = normalized(search) or ""
        responses = [row for row in responses if term in normalized(" ".join(str(value or "") for value in row.model_dump().values()))]
    return responses


def create_rate(db: Session, kind: str, payload, user: User, commit: bool = True):
    model = BankPayoutRate if kind == "bank" else ExecutivePayoutRate
    data = payload.model_dump()
    _ensure_refs(db, data, kind == "executive")
    _ensure_no_overlap(db, model, data)
    rate = model(**data, created_by_user_id=user.id, updated_by_user_id=user.id)
    db.add(rate)
    db.flush()
    if commit:
        db.commit()
        db.refresh(rate)
    # Relationships can be unavailable until refresh in transaction imports.
    if not commit:
        return rate
    return _bank_response(rate) if kind == "bank" else _executive_response(rate)


def create_bank_rates_bulk(db: Session, payload: BankRateBulkCreate, user: User) -> BankRateBulkResponse:
    bank_ids = list(dict.fromkeys(payload.bank_ids or [None]))
    if payload.district_scope == "JAIPUR_ONLY":
        jaipur = db.scalar(select(District).where(func.lower(func.trim(District.name)) == "jaipur", District.is_active.is_(True)))
        if jaipur is None: raise HTTPException(status_code=422, detail="Active Jaipur district does not exist")
        supplied_districts = [jaipur.id]
    elif payload.district_scope == "RAJASTHAN_EXCEPT_JAIPUR":
        supplied_districts = [None]
    else:
        supplied_districts = payload.district_ids or ([payload.district_id] if payload.district_id is not None else [])
        if not supplied_districts: raise HTTPException(status_code=422, detail="Select at least one district")
    district_ids = list(dict.fromkeys(supplied_districts))
    common = payload.model_dump(exclude={"bank_ids", "district_ids", "district_id"})
    validated: list[dict] = []
    errors: list[str] = []
    conflict = False
    for bank_id in bank_ids:
        for district_id in district_ids:
            bank = db.get(Bank, bank_id) if bank_id is not None else None
            district = db.get(District, district_id) if district_id is not None else None
            label = f"{bank.name if bank else 'All Banks'} / {district.name if district else 'All Rajasthan'}"
            data = {**common, "bank_id": bank_id, "district_id": district_id}
            try:
                _ensure_refs(db, data)
                _ensure_no_overlap(db, BankPayoutRate, data)
                validated.append(data)
            except HTTPException as exc:
                conflict = conflict or exc.status_code == status.HTTP_409_CONFLICT
                errors.append(f"{label}: {exc.detail}")
    if errors:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT if conflict else 422, detail="; ".join(errors))
    rows = [BankPayoutRate(**data, created_by_user_id=user.id, updated_by_user_id=user.id) for data in validated]
    try:
        db.add_all(rows)
        db.flush()
        ids = [row.id for row in rows]
        db.commit()
    except Exception:
        db.rollback()
        raise
    saved = db.query(BankPayoutRate).options(joinedload(BankPayoutRate.bank), joinedload(BankPayoutRate.company),
        joinedload(BankPayoutRate.district)).filter(BankPayoutRate.id.in_(ids)).order_by(BankPayoutRate.id).all()
    return BankRateBulkResponse(created_count=len(saved), failed_count=0,
        items=[_bank_response(row) for row in saved], errors=[])


def update_rate(db: Session, kind: str, rate_id: int, payload, user: User):
    model = BankPayoutRate if kind == "bank" else ExecutivePayoutRate
    rate = db.get(model, rate_id)
    if rate is None:
        raise HTTPException(status_code=404, detail="Payout rate not found")
    data = payload.model_dump()
    _ensure_refs(db, data, kind == "executive")
    _ensure_no_overlap(db, model, data, rate_id)
    for field, value in data.items():
        setattr(rate, field, value)
    rate.updated_by_user_id = user.id
    db.commit()
    db.refresh(rate)
    return _bank_response(rate) if kind == "bank" else _executive_response(rate)


def delete_bank_rate(db: Session, rate_id: int) -> None:
    rate = db.get(BankPayoutRate, rate_id)
    if rate is None:
        raise HTTPException(status_code=404, detail="Bank rate not found")
    used_by_billing = db.scalar(select(Billing.id).where(Billing.bank_payout_rate_id == rate_id).limit(1)) is not None
    used_by_snapshot = db.scalar(select(BankMonthlyBillingSnapshot.id).where(
        BankMonthlyBillingSnapshot.bank_payout_rate_id == rate_id).limit(1)) is not None
    if used_by_billing or used_by_snapshot:
        raise HTTPException(status_code=409, detail="This rate is part of finalized billing history and cannot be deleted. Deactivate it instead.")
    try:
        db.delete(rate)
        db.commit()
    except Exception:
        db.rollback()
        raise


@dataclass
class RateMatch:
    status: str
    rate_id: int | None = None
    amount: Decimal | None = None


def _dimension_match(rate, case_value: str | None, field: str) -> bool:
    rate_value = normalized(getattr(rate, field))
    return rate_value is None or rate_value == normalized(case_value)


def _resolve(rows, case_item: Case, dimensions: tuple[str, ...]) -> RateMatch:
    matching = [row for row in rows if all(_dimension_match(row, getattr(case_item, field), field) for field in dimensions)]
    if not matching:
        return RateMatch("MISSING")
    scores = {row.id: sum(normalized(getattr(row, field)) is not None for field in dimensions) for row in matching}
    best_score = max(scores.values())
    best = [row for row in matching if scores[row.id] == best_score]
    if len(best) != 1:
        return RateMatch("AMBIGUOUS")
    return RateMatch("MATCHED", best[0].id, best[0].payout_rate)


def resolve_rates(db: Session, case_item: Case) -> tuple[RateMatch, RateMatch]:
    on_date = case_item.receive_date
    if on_date is None:
        return RateMatch("MISSING"), RateMatch("MISSING")
    active_date = lambda model: and_(model.is_active.is_(True), model.effective_from <= on_date, or_(model.effective_to.is_(None), model.effective_to >= on_date))
    bank = db.scalar(select(Bank).where(func.lower(func.trim(Bank.name)) == (normalized(case_item.bank) or "")))
    executive = db.scalar(select(Executive).where(func.lower(func.trim(Executive.full_name)) == (normalized(case_item.executive) or "")))
    if bank is None:
        bank_match = RateMatch("MISSING")
    elif case_item.company_id is not None and case_item.district_id is not None:
        bank_rows = db.scalars(select(BankPayoutRate).where(BankPayoutRate.company_id == case_item.company_id,
            or_(BankPayoutRate.bank_id.is_(None), BankPayoutRate.bank_id == bank.id),
            or_(BankPayoutRate.district_id.is_(None), BankPayoutRate.district_id == case_item.district_id),
            BankPayoutRate.payout_rate > 0,
            active_date(BankPayoutRate))).all()
        district = db.get(District, case_item.district_id)
        jaipur = bool(district and normalized(district.name) == "jaipur")
        ranked = []
        for row in bank_rows:
            scope = district_scope_for(row, district if row.district_id == case_item.district_id else None)
            exact_city = normalized(row.city) is not None and normalized(row.city) == normalized(case_item.city)
            if jaipur:
                if scope != "JAIPUR_ONLY" or (normalized(row.city) is not None and not exact_city): continue
                rank = (4 if row.bank_id is not None and exact_city else 3 if row.bank_id is not None else 2 if exact_city else 1)
            else:
                if normalized(row.city) is not None or scope == "JAIPUR_ONLY": continue
                specific = scope == "SELECTED_DISTRICTS" and row.district_id == case_item.district_id
                broad = scope == "RAJASTHAN_EXCEPT_JAIPUR" and row.district_id is None
                if not specific and not broad: continue
                rank = (4 if row.bank_id is not None and specific else 3 if specific else 2 if row.bank_id is not None else 1)
            ranked.append((rank, row))
        top = max((rank for rank, _ in ranked), default=0)
        candidates = [row for rank, row in ranked if rank == top]
        bank_match = RateMatch("MISSING") if not candidates else RateMatch("AMBIGUOUS") if len(candidates) != 1 else RateMatch("MATCHED", candidates[0].id, candidates[0].payout_rate)
    elif case_item.company_id is None and case_item.district_id is None:
        bank_rows = db.scalars(select(BankPayoutRate).where(BankPayoutRate.company_id.is_(None), BankPayoutRate.district_id.is_(None),
            BankPayoutRate.bank_id == bank.id, active_date(BankPayoutRate))).all()
        bank_match = _resolve(bank_rows, case_item, ("city", "loan_type", "product_type"))
    else:
        bank_match = RateMatch("MISSING")
    executive_rows = [] if executive is None else db.scalars(select(ExecutivePayoutRate).where(
        ExecutivePayoutRate.executive_id == executive.id,
        or_(ExecutivePayoutRate.bank_id.is_(None), ExecutivePayoutRate.bank_id == (bank.id if bank else -1)),
        active_date(ExecutivePayoutRate),
    )).all()
    return (
        bank_match,
        _resolve_executive(executive_rows, case_item, bank),
    )


def _resolve_executive(rows, case_item: Case, bank: Bank | None) -> RateMatch:
    matching = [row for row in rows if (row.bank_id is None or (bank and row.bank_id == bank.id)) and all(
        _dimension_match(row, getattr(case_item, field), field) for field in ("city", "loan_type", "product_type")
    )]
    if not matching:
        return RateMatch("MISSING")
    scores = {row.id: int(row.bank_id is not None) + sum(normalized(getattr(row, f)) is not None for f in ("city", "loan_type", "product_type")) for row in matching}
    top = max(scores.values())
    best = [row for row in matching if scores[row.id] == top]
    return RateMatch("AMBIGUOUS") if len(best) != 1 else RateMatch("MATCHED", best[0].id, best[0].payout_rate)


def import_rates(db: Session, kind: str, request: RateImportRequest, user: User) -> RateImportResponse:
    bank_names = {normalized(x.name): x.id for x in db.query(Bank).all()}
    executive_names = {normalized(x.full_name): x.id for x in db.query(Executive).all()}
    loan_names = {normalized(x.name) for x in db.query(LoanType).all()}
    product_names = {normalized(x.name) for x in db.query(ProductType).all()}
    company_names = {normalized(x.name): x.id for x in db.query(Company).filter(Company.is_active.is_(True)).all()}
    district_names = {normalized(x.name): x.id for x in db.query(District).filter(District.is_active.is_(True)).all()}
    results, payloads = [], []
    seen = set()
    for row in request.rows:
        errors = []
        bank_id = bank_names.get(normalized(row.bank))
        executive_id = executive_names.get(normalized(row.executive)) if kind == "executive" else None
        company_id = company_names.get(normalized(row.company)) if kind == "bank" else None
        district_id = district_names.get(normalized(row.district)) if kind == "bank" else None
        if not bank_id and (kind == "bank" or row.bank): errors.append("Bank not found")
        if kind == "executive" and not executive_id: errors.append("Executive not found")
        if kind == "bank" and not company_id: errors.append("Company not found")
        if kind == "bank" and not district_id: errors.append("District not found")
        if kind == "bank" and district_id and normalized(row.district) != "jaipur" and normalized(row.city):
            errors.append("City-specific rates are allowed only for Jaipur district.")
        if row.location and row.location.strip(): errors.append("Location is unavailable because cases have no structured location field")
        if row.loan_type and normalized(row.loan_type) not in loan_names: errors.append("Loan Type not found")
        if row.product_type and normalized(row.product_type) not in product_names: errors.append("Product Type not found")
        if row.payout_rate is None or row.payout_rate < 0: errors.append("Payout Rate must be nonnegative")
        if row.effective_from is None: errors.append("Effective From is required")
        if row.effective_to and row.effective_from and row.effective_to < row.effective_from: errors.append("Effective To precedes Effective From")
        key = (executive_id, company_id, bank_id, district_id, normalized(row.city), normalized(row.loan_type), normalized(row.product_type), row.effective_from, row.effective_to)
        if key in seen: errors.append("Duplicate row in import")
        seen.add(key)
        payload = {
            "executive_id": executive_id, "company_id": company_id, "bank_id": bank_id, "district_id": district_id, "state": row.state or "Rajasthan",
            "city": row.city, "loan_type": row.loan_type, "product_type": row.product_type,
            "payout_rate": row.payout_rate, "effective_from": row.effective_from,
            "effective_to": row.effective_to, "is_active": row.active, "remarks": row.remarks,
        }
        if not errors:
            schema = ExecutiveRateCreate if kind == "executive" else BankRateCreate
            if kind == "executive": payload.pop("state"); payload.pop("company_id"); payload.pop("district_id")
            else: payload.pop("executive_id")
            try:
                parsed = schema.model_validate(payload)
                _ensure_no_overlap(db, ExecutivePayoutRate if kind == "executive" else BankPayoutRate, parsed.model_dump())
                current = parsed.model_dump()
                dimension_fields = ("executive_id", "bank_id", "city", "loan_type", "product_type") if kind == "executive" else ("company_id", "bank_id", "district_id", "city")
                for _, prior in payloads:
                    previous = prior.model_dump()
                    same_dimensions = all(
                        previous.get(field) == current.get(field) if field.endswith("_id")
                        else normalized(previous.get(field)) == normalized(current.get(field))
                        for field in dimension_fields
                    )
                    dates_overlap = previous["effective_from"] <= (current["effective_to"] or date.max) and current["effective_from"] <= (previous["effective_to"] or date.max)
                    if same_dimensions and dates_overlap:
                        raise ValueError("Effective dates overlap another import row with identical matching dimensions")
                payloads.append((row.row_number, parsed))
            except (HTTPException, ValueError) as exc:
                errors.append(exc.detail if isinstance(exc, HTTPException) else str(exc))
        results.append(RateImportResultRow(row_number=row.row_number, valid=not errors, errors=errors))
    invalid = sum(not result.valid for result in results)
    imported = 0
    if request.confirm:
        if invalid:
            raise HTTPException(status_code=422, detail="Import contains invalid rows; nothing was imported")
        try:
            for _, payload in payloads:
                create_rate(db, kind, payload, user, commit=False)
                imported += 1
            db.commit()
        except Exception:
            db.rollback()
            raise
    return RateImportResponse(valid_count=len(results) - invalid, invalid_count=invalid, imported_count=imported, rows=results)
