from fastapi import HTTPException, status

CredentialsException = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def standard_response(code: int = 200, message="ok", **kwargs):
    resp = {
        "code": code,
        "message": message,
    }
    if kwargs:
        resp.update(kwargs)
    return resp


if __name__ == '__main__':
    r = standard_response(data={111})
    print(r)
