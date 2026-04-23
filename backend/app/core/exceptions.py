class EmailAlreadyExistsError(Exception):
    pass


class UsernameAlreadyExistsError(Exception):
    pass


class EmailNotFoundError(Exception):
    pass


class PasswordDoesNotMatchError(Exception):
    pass
