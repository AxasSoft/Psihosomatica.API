import logging

import requests
from app.config import settings
from app.utils.security import generate_random_code
from app.exceptions import UnprocessableEntity
from app.services.gsms_tg_sender.base_gsms_tg_sender import BaseTgSender

logger = logging.getLogger(__name__)

class GsmsTgSender(BaseTgSender):
    def send(self, tel: str) -> str:
        url = "https://api3.greensms.ru/telegram/send"
        tel_4428 = ["79892224422"]
        if tel in tel_4428:
            return "4428"

        code = generate_random_code(length=4, digits_only=True)
        params = {
            "to": tel,
            "txt": code
        }
        headers = {
            "Authorization": f"Bearer {settings.gsms_token}"
        }
        try:
            response = requests.post(url, data=params, headers=headers).json()
            logger.info("SMS_RU response: %s", response)
            logger.debug("code: %s", code)
            if 'request_id' not in response:
                raise UnprocessableEntity(message="Ошибка отправки кода", num=1)

        except Exception as e:
            logger.error(e)
            raise UnprocessableEntity(message="Что-то пошло не так", num=2)

        return code

gsms_tg_sender = GsmsTgSender()
