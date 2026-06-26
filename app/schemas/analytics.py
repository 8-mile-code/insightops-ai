from datetime import date as Date

from pydantic import BaseModel


class DailyRevenueItem(BaseModel):
    date: Date
    revenue: float


class OrdersByStatusItem(BaseModel):
    status: str
    orders_count: int


class FailedPaymentsRead(BaseModel):
    failed_count: int
    failed_amount: float


class TopCustomerItem(BaseModel):
    customer_id: str
    revenue: float
