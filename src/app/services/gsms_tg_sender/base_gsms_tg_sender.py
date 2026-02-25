from abc import ABC, abstractmethod


class BaseTgSender(ABC):
    @abstractmethod
    async def send(self, tel: str, code: str| None = None) -> str:
        pass
