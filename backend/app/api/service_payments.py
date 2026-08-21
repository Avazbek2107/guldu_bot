from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_permission
from app.core.database import get_db
from app.models.service_payment import ServicePayment
from app.models.user import User
from app.schemas.service_payment import (
    ServicePaymentCreate,
    ServicePaymentOut,
    ServicePaymentUpdate,
    compute_payment_status,
)

router = APIRouter(prefix="/service-payments", tags=["service-payments"])


def _to_out(payment: ServicePayment) -> ServicePaymentOut:
    status_label, days_left = compute_payment_status(payment.due_date)
    return ServicePaymentOut(
        id=payment.id,
        name=payment.name,
        category=payment.category,
        amount=float(payment.amount) if payment.amount is not None else None,
        due_date=payment.due_date,
        responsible_person=payment.responsible_person,
        notes=payment.notes,
        status=status_label,
        days_left=days_left,
        created_at=payment.created_at,
        updated_at=payment.updated_at,
    )


@router.get("", response_model=list[ServicePaymentOut])
async def list_service_payments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("payments", "view")),
):
    result = await db.execute(select(ServicePayment).order_by(ServicePayment.due_date.asc()))
    return [_to_out(p) for p in result.scalars().all()]


@router.post("", response_model=ServicePaymentOut, status_code=status.HTTP_201_CREATED)
async def create_service_payment(
    payload: ServicePaymentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("payments", "create")),
):
    payment = ServicePayment(**payload.model_dump())
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    return _to_out(payment)


@router.patch("/{payment_id}", response_model=ServicePaymentOut)
async def update_service_payment(
    payment_id: int,
    payload: ServicePaymentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("payments", "edit")),
):
    payment = await db.get(ServicePayment, payment_id)
    if payment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Yozuv topilmadi")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(payment, field, value)

    await db.commit()
    await db.refresh(payment)
    return _to_out(payment)


@router.delete("/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service_payment(
    payment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("payments", "delete")),
):
    payment = await db.get(ServicePayment, payment_id)
    if payment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Yozuv topilmadi")
    await db.delete(payment)
    await db.commit()
