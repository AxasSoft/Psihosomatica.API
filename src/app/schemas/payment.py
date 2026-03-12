from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from uuid import UUID

class TinkoffNotificationPayment(BaseModel):
    # NotificationPayment Base Fields
    terminal_key: str | None = Field(None, alias="TerminalKey")
    amount: int | None = Field(None, alias="Amount")
    order_id: str | None = Field(None, alias="OrderId")
    success: bool | None = Field(None, alias="Success")
    status: str | None = Field(None, alias="Status")
    payment_id: int | None = Field(None, alias="PaymentId")
    error_code: str | None = Field(None, alias="ErrorCode")
    token: str | None = Field(None, alias="Token")
    # NotificationPayment Fields
    message: str | None = Field(None, alias="Message")
    details: str | None = Field(None, alias="Details")
    rebill_id: int | None = Field(None, alias="RebillId")
    card_id: int | None = Field(None, alias="CardId")
    pan: str | None = Field(None, alias="Pan")
    exp_date: str | None = Field(None, alias="ExpDate")
    data: dict | None = Field(None, alias="DATA")
    # NotificationPaymentFiscalization Fields
    error_message: str | None = Field(None, alias="ErrorMessage")
    fiscal_number: int | None = Field(None, alias="FiscalNumber")
    shift_number: int | None = Field(None, alias="ShiftNumber")
    receipt_datetime: str | None = Field(None, alias="ReceiptDatetime")
    fn_number: str | None = Field(None, alias="FnNumber")
    ecr_reg_number: str | None = Field(None, alias="EcrRegNumber")
    fiscal_doc_number: int | None = Field(None, alias="FiscalDocumentNumber")
    fiscal_doc_attr: int | None = Field(None, alias="FiscalDocumentAttribute")
    receipt: dict | None = Field(None, alias="Receipt")
    type: str | None = Field(None, alias="Type")
    ofd: str | None = Field(None, alias="Ofd")
    url: str | None = Field(None, alias="Url")
    qr_code_url: str | None = Field(None, alias="QrCodeUrl")
    calculation_place: str | None = Field(None, alias="CalculationPlace")
    cashier_name: str | None = Field(None, alias="CashierName")
    settle_place: str | None = Field(None, alias="SettlePlace")

    def __str__(self):
        return f"CALLBACK TinkoffNotification: {self.dict(exclude_unset=True)}"


"""
{
  "TerminalKey": "TinkoffBankTest",
  "Amount": 100000,
  "OrderId": "21050",
  "Success": true,
  "Status": "string",
  "PaymentId": "13660",
  "ErrorCode": "0",
  "Message": "string",
  "Details": "string",
  "RebillId": 3207469334,
  "CardId": 10452089,
  "Pan": "string",
  "ExpDate": "0229",
  "Token": "7241ac8307f349afb7bb9dda760717721bbb45950b97c67289f23d8c69cc7b96",
  "DATA": {
    "Route": "TCB",
    "Source": "Installment",
    "CreditAmount": 10000
  }
}

status:
AUTHORIZED	Деньги захолдированы на карте клиента. Ожидается подтверждение операции *
CONFIRMED	Операция подтверждена
PARTIAL_REVERSED	Частичная отмена
REVERSED	Операция отменена
PARTIAL_REFUNDED	Произведён частичный возврат
REFUNDED	Произведён возврат
REJECTED	Списание денежных средств закончилась ошибкой
3DS_CHECKING **	Автоматическое закрытие сессии, которая превысила срок пребывания в статусе 3DS_CHECKING (более 36 часов)
"""


class PaymentBase(BaseModel):
    description: Optional[str] = None
    amount: int = Field(...)

    pay_link: Optional[str] = None
    ofd_url: Optional[str] = None
    return_url: Optional[str] = None
    os: Optional[str] = None

    user_id: Optional[int] = None


class PaymentCreate(PaymentBase):
    pass


class PaymentUpdate(BaseModel):
    pass



