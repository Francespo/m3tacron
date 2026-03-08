from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlmodel import Session, select, func
from typing import List
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
        
        tiers = [
            FundTier(
                name="Hosting & Infrastructure",
                target=120.0,
                current=min(total_raised, 120.0),
                description="Ensures the site stays live and fast (Annual target)."
            ),
            FundTier(
                name="Developer Fund",
                target=500.0,
                current=min(total_raised, 500.0),
                description="Supports the massive time and effort put into building M3taCron."
            ),
            FundTier(
                name="Next Milestone: Auto-Alerts",
                target=1000.0,
                current=min(total_raised, 1000.0),
                description="Funding for automated Discord/Telegram tournament alerts."
            )
        ]

        return FundStatusResponse(total_raised=total_raised, tiers=tiers)

@router.get("/supporters", response_model=List[SupporterResponse])
def get_supporters():
    """
    Returns the latest public supporters for the Hall of Heroes.
    """
    with Session(engine) as session:
        # Get public contributions with supporter names
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
                ko_fi_transaction_id=transaction_id
            )
            session.add(contribution)
            
            # Update supporter total
            supporter.total_contributed += amount
            supporter.last_contribution = datetime.now()
            session.add(supporter)
            
            session.commit()

    return {"status": "success"}
