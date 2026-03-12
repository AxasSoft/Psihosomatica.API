# https://www.tbank.ru/kassa/dev/payments/

import copy
import json
import logging
from hashlib import sha256
from typing import Any
import requests
import uuid

from app.models import User
from app.services.payment.base_payment import BasePayment

logger = logging.getLogger(__name__)

class TinkoffPayment(BasePayment):
    def __init__(
        self,
        user: User,
        amount: int,
        os: str,
        order_id: uuid.UUID,
        comission_amount: int = 0,
    ) -> None:
        self.user = user
        self.amount = int(amount)
        self.description = "Оплата Тарифа"
        self.base_url = "https://securepay.tinkoff.ru/v2/"
        self.order_id = str(order_id)
        self.notification_url = "http://82.97.253.35:60/api/v1/callback/tinkoff/"
        #self.success_url = ("http://92.51.39.116:71/api/v1/success/")
        #self.fail_url = ("https://time-gid.com/fail.html")
        self.os=os
        self.comission_amount = int(comission_amount)
        self.token = None

        self.terminal_key = "1725524088306"
        self.password = "oj9%6PsfAsC833Fa"

    def create_token(self, payload: dict) -> None:
        payload.pop("Receipt")
        payload.pop("DATA") if "DATA" in payload else None
        payload["Password"] = self.password
        s = "".join([str(payload[k]) for k in sorted(payload)])
        self.token = sha256(s.encode()).hexdigest()

    def make_payment(self, **kwargs) -> dict[str, Any]:
        "help: https://www.tbank.ru/kassa/dev/payments/"

        params = {
            "TerminalKey": self.terminal_key,
            "Amount": self.amount,
            "OrderId": self.order_id,
            "Description": self.description,
            "NotificationURL": self.notification_url,
            #"SuccessURL": self.success_url,
            #"FailURL": self.fail_url,
            "DATA": {"DeviceOs": self.os},
            "Receipt": {
                "Phone": f"+{self.user.phone}",
                "Taxation": "osn",
                "FfdVersion": "1.2",
                "Items":[{
                    "Name": "Оплата подписки",
                    "Price": self.amount,
                    "Quantity": 1,
                    "Amount": self.amount,
                    "Tax": "vat0",
                    "PaymentMethod": "full_payment",
                    "PaymentObject": "service",
                    "MeasurementUnit": "шт",
                }],
            },
        }
        if self.user.email:
            params["Receipt"]["Email"] = self.user.email

        self.create_token(copy.deepcopy(params))
        params["Token"] = self.token
        logging.info(params)
        headers = {"content-type": "application/json"}
        response = requests.request(
            "POST",
            f"{self.base_url}Init",
            data=json.dumps(params),
            headers=headers,
            verify=False,
        )
        logger.info("Tinkoff response.text: %s", response.text)
        """
        response.text='{"Success":true,"ErrorCode":"0","TerminalKey":"1690217460401DEMO","Status":"NEW",
        "PaymentId":"4712852285", "Amount":420000,
        "PaymentURL":"https://securepayments.tinkoff.ru/HCpmR5x0"}'
        """
        return {
            "pay_link": response.json().get("PaymentURL"),
            "payment_id": response.json().get("PaymentId"),
        }
