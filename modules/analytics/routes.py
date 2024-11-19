from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.dependencies import get_db
from modules.analytics.services import get_comments_breakdown

router = APIRouter()


@router.get("/comments-daily-breakdown")
def comments_breakdown(
    date_from: str,
    date_to: str,
    db: Session = Depends(get_db)
):
    # Call the service function to fetch the daily breakdown
    return get_comments_breakdown(date_from, date_to, db)
