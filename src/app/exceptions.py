class EntityError(ValueError):
    http_status = 400

    def __init__(self, message=None, description=None, num=0, path=None):
        self.message = message
        self.num = num
        self.description = description or message
        self.path = path


class UnfoundEntity(EntityError):
    http_status = 404


class InaccessibleEntity(EntityError):
    http_status = 403


class UnprocessableEntity(EntityError):
    http_status = 422


class DuplicateEntity(EntityError):
    http_status = 409


class ListOfEntityError(ValueError):
    def __init__(self, errors: list[EntityError], description: str, http_status: int):
        self.errors = errors
        self.description = description
        self.http_status = http_status


def raise_if_none(data, message="not found", **error_kwargs):
    if data is None:
        raise UnfoundEntity(message=message, **error_kwargs)

def raise_if_duplicate(data, message='duplicate', **error_kwargs):
    if data is not None:
        raise DuplicateEntity(message=message, **error_kwargs)