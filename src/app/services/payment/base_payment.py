from abc import ABC, abstractmethod
from typing import Any


class BasePayment(ABC):
    @abstractmethod
    def make_payment(self, amount: int, **kwargs) -> dict[str, Any]:
        raise NotImplementedError("Method not implemented")
