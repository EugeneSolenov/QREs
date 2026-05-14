from itertools import count
from threading import Lock

from fastapi import Depends, FastAPI, HTTPException, Query, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import select

from .database import get_db
from .exceptions import AppException, ConditionFailedException, ResourceNotFoundException
from .models import Product
from .schemas import ErrorResponse, ProductOut, UserIn, UserOut, UserValidationIn, UserValidationOut


app = FastAPI(title="Control Work 4 FastAPI")

db = {}
seq = count(start=1)
lock = Lock()


@app.exception_handler(ConditionFailedException)
async def h1(_, exc: ConditionFailedException):
    print(f"Condition error: {exc.message}")
    er = ErrorResponse(
        status_code=exc.status_code,
        error_code=exc.error_code,
        message=exc.message,
    )
    return JSONResponse(status_code=exc.status_code, content=er.model_dump())


@app.exception_handler(ResourceNotFoundException)
async def h2(_, exc: ResourceNotFoundException):
    print(f"Resource error: {exc.message}")
    er = ErrorResponse(
        status_code=exc.status_code,
        error_code=exc.error_code,
        message=exc.message,
    )
    return JSONResponse(status_code=exc.status_code, content=er.model_dump())


@app.exception_handler(RequestValidationError)
async def h3(_, exc: RequestValidationError):
    print(f"Validation error: {exc.errors()}")
    arr = []
    for e in exc.errors():
        arr.append(
            {
                "field": ".".join(str(x) for x in e["loc"]),
                "message": e["msg"],
                "type": e["type"],
            }
        )
    er = ErrorResponse(
        status_code=422,
        error_code="validation_error",
        message="Request validation failed",
        details=arr,
    )
    return JSONResponse(status_code=422, content=er.model_dump())


def next_user_id():
    with lock:
        return next(seq)


def reset_user_storage():
    global seq
    with lock:
        db.clear()
        seq = count(start=1)


@app.get("/")
def f0():
    return {"message": "Control Work 4 FastAPI application"}


@app.get("/errors/condition", responses={400: {"model": ErrorResponse}})
def f1(value: int = Query(...)):
    if value < 0:
        raise ConditionFailedException("value must be greater than or equal to 0")
    return {"value": value, "status": "ok"}


@app.get("/errors/resources/{resource_id}", responses={404: {"model": ErrorResponse}})
def f2(resource_id: int):
    if resource_id != 1:
        raise ResourceNotFoundException(f"resource {resource_id} was not found")
    return {"id": resource_id, "name": "demo resource"}


@app.post("/validation/users", response_model=UserValidationOut, status_code=201)
def f3(payload: UserValidationIn):
    return UserValidationOut(
        username=payload.username,
        age=payload.age,
        email=payload.email,
        phone=payload.phone,
    )


@app.post("/users", response_model=UserOut, status_code=201)
def f4(user: UserIn):
    uid = next_user_id()
    db[uid] = user.model_dump()
    return {"id": uid, **db[uid]}


@app.get("/users/{user_id}", response_model=UserOut)
def f5(user_id: int):
    if user_id not in db:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": user_id, **db[user_id]}


@app.delete("/users/{user_id}", status_code=204)
def f6(user_id: int):
    if db.pop(user_id, None) is None:
        raise HTTPException(status_code=404, detail="User not found")
    return Response(status_code=204)


@app.get("/products", response_model=list[ProductOut])
def f7(db1 = Depends(get_db)):
    return list(db1.scalars(select(Product).order_by(Product.id)))
