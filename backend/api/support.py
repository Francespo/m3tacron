from fastapi import APIRouter, HTTPException, Request
from sqlmodel import Session, select, func
from datetime import datetime
import os
import json

from ..database import engine, create_db_and_tables
from ..models import Supporter, Contribution
from .schemas import FundStatusResponse, FundTier, SupporterResponse
from ..cache import persistent_cache

router = APIRouter(prefix="/api/support", tags=["support"])


@router.get("/fund-status", response_model=FundStatusResponse)
@persistent_cache.cached(ttl=3600)
def get_fund_status():
    """
    Returns the current status of the Project Evolution Fund.
    """
    create_db_and_tables()

    with Session(engine) as session:
        total_query = select(func.sum(Contribution.amount))
        total_raised = session.exec(total_query).one()
        total_raised = float(total_raised) if total_raised else 0.0

        now = datetime.now()
        first_of_month = datetime(now.year, now.month, 1)
        monthly_query = select(func.sum(Contribution.amount)).where(Contribution.date >= first_of_month)
        monthly_raised = session.exec(monthly_query).one()
        monthly_raised = float(monthly_raised) if monthly_raised else 0.0

        tiers = [
            FundTier(
                name="Server Cost",
                target=15.0,
                current=min(monthly_raised, 15.0),
                description="M3-TA droid works tirelessly to keep the power grid online and the database reactors stable. (15\u20ac / month)"
            ),
            FundTier(
                name="Maintenance & Development",
                target=None,
                current=max(0.0, monthly_raised - 15.0),
                description="Overflow credits beyond basic maintenance needs. This pool directly sustains the long hours spent building new modules and upgrading the station."
            )
        ]

        return FundStatusResponse(total_raised=total_raised, tiers=tiers)


@router.get("/supporters", response_model=list[SupporterResponse])
@persistent_cache.cached(ttl=3600)
def get_supporters():
    """
    Returns the latest public supporters for the Hall of Heroes.
    """
    create_db_and_tables()

    with Session(engine) as session:
        query = select(Contribution, Supporter).join(Supporter).where(Supporter.is_anonymous == False).order_by(Contribution.date.desc()).limit(20)
        results = session.exec(query).all()

        return [
            SupporterResponse(
                name=sup.name,
                amount=con.amount,
                date=con.date,
                message=con.message
            ) for con, sup in results
        ]


@router.post("/webhook/ko-fi")
async def kofi_webhook(request: Request):
    """
    Handles incoming webhooks from Ko-fi to update supporter recognition.
    """
    create_db_and_tables()

    try:
        content_type = request.headers.get("content-type", "")
        body = await request.body()

        payload = None

        if "application/x-www-form-urlencoded" in content_type:
            from urllib.parse import parse_qs
            form_data = parse_qs(body.decode())
            if "data" in form_data:
                payload = json.loads(form_data["data"][0])
            else:
                payload = {k: v[0] for k, v in form_data.items()}

        if not payload:
            try:
                payload = json.loads(body)
            except:
                pass

        if not payload:
            if "multipart/form-data" in content_type:
                try:
                    form_data = await request.form()
                    if "data" in form_data:
                        payload = json.loads(form_data["data"])
                    else:
                        payload = dict(form_data)
                except:
                    pass

        if not payload:
            raise ValueError("No data found")

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse Ko-fi payload: {e}")

    expected_token = os.getenv("KO_FI_WEBHOOK_TOKEN")
    if expected_token and payload.get("verification_token") != expected_token:
        return {"status": "unauthorized"}

    if payload.get("type") not in ["Donation", "Subscription"]:
        return {"status": "ignored", "type": payload.get("type")}

    name = payload.get("from_name", "Anonymous Supporter")
    email = payload.get("email")
    amount = float(payload.get("amount", 0.0))
    currency = payload.get("currency", "USD")
    message = payload.get("message")
    is_public = payload.get("is_public", True)
    transaction_id = payload.get("kofi_transaction_id")

    with Session(engine) as session:
        supporter = None
        if email:
            supporter = session.exec(select(Supporter).where(Supporter.email == email)).first()

        if not supporter and name != "Anonymous Supporter":
            supporter = session.exec(select(Supporter).where(Supporter.name == name)).first()

        if not supporter:
            supporter = Supporter(name=name, email=email, is_anonymous=not is_public)
            session.add(supporter)
            session.commit()
            session.refresh(supporter)
        else:
            supporter.is_anonymous = not is_public
            if supporter.name == "Anonymous Supporter" and name != "Anonymous Supporter":
                supporter.name = name

        existing_con = session.exec(select(Contribution).where(Contribution.ko_fi_transaction_id == transaction_id)).first()
        if not existing_con:
            contribution = Contribution(
                supporter_id=supporter.id,
                amount=amount,
                currency=currency,
                message=message,
                ko_fi_transaction_id=transaction_id
            )
            session.add(contribution)

            supporter.total_contributed += amount
            supporter.last_contribution = datetime.now()
            session.add(supporter)

            session.commit()

    return {"status": "success"}
