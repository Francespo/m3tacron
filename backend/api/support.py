from fastapi import APIRouter, HTTPException, Request
from sqlmodel import Session, select, func
from datetime import datetime
import os
import json

from ..database import engine
from ..models import Supporter, Contribution
from .schemas import FundStatusResponse, FundTier, SupporterResponse

router = APIRouter(prefix="/api/support", tags=["support"])

@router.get("/fund-status", response_model=FundStatusResponse)
def get_fund_status():
    """
    Returns the current status of the Project Evolution Fund.
    """
    with Session(engine) as session:
        # Sum of all contributions
        total_query = select(func.sum(Contribution.amount))
        total_raised = session.exec(total_query).one()
        total_raised = float(total_raised) if total_raised else 0.0
        
        # Calculate monthly raised (current month)
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
                description="M3-TA droid works tirelessly to keep the power grid online and the database reactors stable. (15€ / month)"
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
def get_supporters():
    """
    Returns the latest public supporters for the Hall of Heroes.

    Monthly vs one-time is not decided by only the latest row: a donor who
    first tips (Donation) and later starts a Subscription should appear as
    monthly as soon as any subscription payment within the last 35 days
    exists. Internally we persist is_subscription_payment / type per
    Contribution and at read time check whether this supporter has any
    (public) subscription payment within the grace window.
    """
    with Session(engine) as session:
        # All public contributions, newest-first. We dedup per supporter but
        # keep the full list so we can look for *any* recent subscription,
        # not just the latest row.
        query = (
            select(Contribution, Supporter)
            .join(Supporter)
            .where(Supporter.is_anonymous == False)
            .order_by(Contribution.date.desc())
        )
        all_rows = session.exec(query).all()

        from datetime import timedelta
        grace = datetime.now() - timedelta(days=35)

        # supporter_id -> list[(Contribution, Supporter)] newest-first
        from collections import defaultdict
        grouped: dict[int, list] = defaultdict(list)
        name_by_id: dict[int, str] = {}
        for con, sup in all_rows:
            grouped[sup.id].append((con, sup))
            name_by_id[sup.id] = sup.name

        monthly: list[SupporterResponse] = []
        onetime: list[SupporterResponse] = []

        for sid, rows in grouped.items():
            # Display entry is built from the latest contribution (amount/date/message)
            con_latest, sup_latest = rows[0]
            # But isMonthly checks the entire history within the window
            recent_sub_con = None
            for con, _ in rows:
                if con.date and con.date >= grace and bool(
                    con.is_subscription_payment or (con.type == "Subscription")
                ):
                    recent_sub_con = con
                    break
            is_monthly_active = recent_sub_con is not None
            entry = SupporterResponse(
                name=sup_latest.name,
                amount=con_latest.amount,
                date=con_latest.date,
                message=con_latest.message,
                isMonthly=is_monthly_active,
                tierName=(recent_sub_con.tier_name if is_monthly_active and recent_sub_con else None),
            )
            if is_monthly_active:
                monthly.append(entry)
            else:
                onetime.append(entry)

        # Monthly first, then one-time, both newest-first within group
        monthly.sort(key=lambda s: s.date, reverse=True)
        onetime.sort(key=lambda s: s.date, reverse=True)
        return (monthly + onetime)[:30]

@router.post("/webhook/ko-fi")
async def kofi_webhook(request: Request):
    """
    Handles incoming webhooks from Ko-fi to update supporter recognition.
    """
    try:
        # Ko-fi usually sends data as a form field 'data' containing JSON
        # We try manual parsing first to avoid python-multipart dependency issues in some environments
        content_type = request.headers.get("content-type", "")
        body = await request.body()
        
        payload = None
        
        if "application/x-www-form-urlencoded" in content_type:
            from urllib.parse import parse_qs
            form_data = parse_qs(body.decode())
            if "data" in form_data:
                payload = json.loads(form_data["data"][0])
            else:
                # Flat form
                payload = {k: v[0] for k, v in form_data.items()}
        
        if not payload:
            # Try parsing as direct JSON
            try:
                payload = json.loads(body)
            except:
                pass
                
        if not payload:
            # Last resort: Try standard FastAPI form parsing
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

    # Verify token
    expected_token = os.getenv("KO_FI_WEBHOOK_TOKEN")
    if expected_token and payload.get("verification_token") != expected_token:
        # We don't raise 401 to keep it silent vs scanners, but log it internally
        return {"status": "unauthorized"}

    if payload.get("type") not in ["Donation", "Subscription", "Tip", "Shop Order", "Commission"]:
        return {"status": "ignored", "type": payload.get("type")}

    name = payload.get("from_name", "Anonymous Supporter")
    email = payload.get("email")
    amount = float(payload.get("amount", 0.0))
    currency = payload.get("currency", "USD")
    message = payload.get("message")
    is_public = payload.get("is_public", True)
    transaction_id = payload.get("kofi_transaction_id")
    kofi_type = payload.get("type")
    is_subscription_payment = payload.get("is_subscription_payment")
    is_first_subscription_payment = payload.get("is_first_subscription_payment")
    tier_name = payload.get("tier_name")

    with Session(engine) as session:
        # Find or create supporter
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
            # Update anonymity if they chose to be public/private now
            supporter.is_anonymous = not is_public
            if supporter.name == "Anonymous Supporter" and name != "Anonymous Supporter":
                supporter.name = name

        # Avoid duplicate transactions
        existing_con = session.exec(select(Contribution).where(Contribution.ko_fi_transaction_id == transaction_id)).first()
        if not existing_con:
            contribution = Contribution(
                supporter_id=supporter.id,
                amount=amount,
                currency=currency,
                message=message,
                ko_fi_transaction_id=transaction_id,
                type=kofi_type,
                is_subscription_payment=bool(is_subscription_payment) if is_subscription_payment is not None else None,
                is_first_subscription_payment=bool(is_first_subscription_payment) if is_first_subscription_payment is not None else None,
                tier_name=tier_name,
            )
            session.add(contribution)
            
            # Update supporter total
            supporter.total_contributed += amount
            supporter.last_contribution = datetime.now()
            session.add(supporter)
            
            session.commit()

    return {"status": "success"}
