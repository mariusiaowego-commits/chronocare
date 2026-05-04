"""PDF Report API — download weekly/monthly reports."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from io import BytesIO

from chronocare.database import get_db
from chronocare.services.pdf_report import generate_weekly_report, generate_monthly_report

router = APIRouter(prefix="/api/pdf-report", tags=["PDF Report"])


@router.get("/weekly")
async def download_weekly_report(
    person_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Download weekly health report as PDF."""
    try:
        pdf_bytes = await generate_weekly_report(person_id, db)
        
        return StreamingResponse(
            BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=weekly_report_{person_id}.pdf"
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")


@router.get("/monthly")
async def download_monthly_report(
    person_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Download monthly health report as PDF."""
    try:
        pdf_bytes = await generate_monthly_report(person_id, db)
        
        return StreamingResponse(
            BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=monthly_report_{person_id}.pdf"
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")
