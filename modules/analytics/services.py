from sqlalchemy.orm import Session
from sqlalchemy import func, case
from datetime import datetime
import models
from fastapi import HTTPException


def get_comments_breakdown(date_from: str, date_to: str, db: Session):
    try:
        # Convert date strings to datetime objects
        start_date = datetime.strptime(date_from, "%Y-%m-%d")
        end_date = datetime.strptime(date_to, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    # Query the database for daily comment breakdown
    daily_comments = (
        db.query(
            func.date(models.Comment.created_at).label('date'),
            func.count(models.Comment.id).label('total_comments'),
            func.sum(case((models.Comment.is_blocked == True, 1), else_=0)).label('blocked_comments')
        )
        .filter(models.Comment.created_at >= start_date, models.Comment.created_at <= end_date)
        .group_by(func.date(models.Comment.created_at))
        .order_by(func.date(models.Comment.created_at))  # Ensuring the results are ordered by date
        .all()
    )

    # Return the results as a list of dictionaries
    return [
        {
            "date": record.date,
            "total_comments": record.total_comments,
            "blocked_comments": record.blocked_comments
        } for record in daily_comments
    ]
