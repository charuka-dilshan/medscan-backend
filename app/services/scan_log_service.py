from typing import Any

from sqlalchemy.orm import Session

from app.models import ScanLog


def save_scan_log(
    db: Session,
    scan_type: str,
    predicted_label: str | None,
    confidence: float | None,
    allow_ai_processing: bool,
    status: str,
    message: str | None,
    user_id: int | None = None,
) -> ScanLog:
    scan_log = ScanLog(
        user_id=user_id,
        scan_type=scan_type,
        predicted_label=predicted_label,
        confidence=confidence,
        allow_ai_processing=allow_ai_processing,
        status=status,
        message=message,
    )

    try:
        db.add(scan_log)
        db.commit()
        db.refresh(scan_log)
        return scan_log

    except Exception:
        db.rollback()
        raise


def serialize_scan_log(scan_log: ScanLog) -> dict[str, Any]:
    return {
        "id": scan_log.id,
        "scan_type": scan_log.scan_type,
        "extracted_text": getattr(scan_log, "extracted_text", None),
        "predicted_label": scan_log.predicted_label,
        "confidence": scan_log.confidence,
        "allow_ai_processing": scan_log.allow_ai_processing,
        "status": scan_log.status,
        "message": scan_log.message,
        "created_at": (
            scan_log.created_at.isoformat()
            if scan_log.created_at
            else None
        ),
    }