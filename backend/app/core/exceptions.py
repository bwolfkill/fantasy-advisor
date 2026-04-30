from fastapi import HTTPException, status


class EmailAlreadyExistsError(Exception):
    pass


class UsernameAlreadyExistsError(Exception):
    pass


class EmailNotFoundError(Exception):
    pass


class PasswordDoesNotMatchError(Exception):
    pass


CredentialsException = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

InactiveUserException = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Inactive user",
)


class UserNotFoundError(Exception):
    pass


class SleeperUserNotFoundError(Exception):
    def __init__(self, username: str | None = None, user_id: str | None = None):
        super().__init__(f"Sleeper user not found: {username or user_id}")
        self.username = username
        self.user_id = user_id


class SleeperAPIError(Exception):
    def __init__(self, status_code: int, message: str):
        super().__init__(f"Sleeper API error {status_code}: {message}")
        self.status_code = status_code
        self.message = message
