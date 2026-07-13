"""Home / dashboard route."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from clinic.db.database import session_scope
from clinic.db.models import Doctor, Patient, Reception, Service
from clinic.web.dependencies import render, require_login

router = APIRouter()


@router.get("/")
def home(request: Request, _user: str = Depends(require_login)):
    with session_scope() as session:
        stats = {
            "patients": session.query(Patient).count(),
            "receptions": session.query(Reception).count(),
            "doctors": session.query(Doctor).filter(Doctor.is_active.is_(True)).count(),
            "services": session.query(Service).filter(Service.is_active.is_(True)).count(),
        }
    return render(request, "home.html", {"stats": stats})
