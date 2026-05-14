import secrets
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from config import DOCS_PASSWORD, DOCS_USER, MODE
from database import (
    create_todo,
    create_user,
    delete_todo,
    find_user_by_username,
    get_todo,
    init_db,
    list_todos,
    update_todo,
)
from models import LoginRequest, Message, TodoCreate, TodoOut, TodoUpdate, Token, User, UserInDB
from rate_limiter import enforce_rate_limit
from security import (
    authenticate_user,
    create_access_token,
    get_current_user,
    get_password_hash,
    require_roles,
    verify_password,
)


basic_scheme = HTTPBasic()

ROLE_PERMISSIONS = {
    "admin": {"create", "read", "update", "delete"},
    "user": {"read", "update"},
    "guest": {"read"},
}


@asynccontextmanager
async def lifespan(_):
    init_db()
    yield


app = FastAPI(
    title="KR3 FastAPI Auth and CRUD",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    lifespan=lifespan,
)


def docs_auth(credentials: HTTPBasicCredentials = Depends(basic_scheme)):
    u = secrets.compare_digest(credentials.username.encode("utf-8"), DOCS_USER.encode("utf-8"))
    p = secrets.compare_digest(credentials.password.encode("utf-8"), DOCS_PASSWORD.encode("utf-8"))

    if not (u and p):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid documentation credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return True


def auth_user(credentials: HTTPBasicCredentials = Depends(basic_scheme)):
    u = find_user_by_username(credentials.username)
    if u is None or not verify_password(credentials.password, u["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    return UserInDB(
        username=u["username"],
        hashed_password=u["password"],
        role=u["role"],
    )


if MODE == "DEV":

    @app.get("/openapi.json", include_in_schema=False)
    async def f1(_: bool = Depends(docs_auth)):
        return get_openapi(title=app.title, version=app.version, routes=app.routes)

    @app.get("/docs", include_in_schema=False)
    async def f2(_: bool = Depends(docs_auth)):
        return get_swagger_ui_html(
            openapi_url="/openapi.json",
            title=f"{app.title} - Swagger UI",
        )


@app.get("/", response_model=Message)
async def f3():
    return Message(message=f"Application is running in {MODE} mode")


@app.post("/register", response_model=Message, status_code=status.HTTP_201_CREATED)
async def f4(user: User, request: Request):
    if find_user_by_username(user.username) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists",
        )

    enforce_rate_limit(request, "register", limit=1, window_seconds=60)
    hp = get_password_hash(user.password)
    create_user(user.username, hp, user.role)
    return Message(message="New user created")


@app.get("/login")
async def f5(current_user: UserInDB = Depends(auth_user)):
    return {
        "message": f"Welcome, {current_user.username}!",
        "secret_message": "You got my secret, welcome",
    }


@app.post("/login", response_model=Token)
async def f6(credentials: LoginRequest, request: Request):
    u = find_user_by_username(credentials.username)
    if u is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    enforce_rate_limit(
        request,
        "login",
        limit=5,
        window_seconds=60,
        identifier=credentials.username,
    )

    au = authenticate_user(credentials.username, credentials.password)
    if au is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization failed",
        )

    return Token(
        access_token=create_access_token(au["username"], au["role"]),
        token_type="bearer",
    )


@app.get("/protected_resource")
async def f7(_: UserInDB = Depends(require_roles("admin", "user"))):
    return {"message": "Access granted"}


@app.get("/rbac/read")
async def f8(current_user: UserInDB = Depends(get_current_user)):
    return {
        "message": "Read access granted",
        "role": current_user.role,
        "permissions": sorted(ROLE_PERMISSIONS[current_user.role]),
    }


@app.post("/rbac/create")
async def f9(_: UserInDB = Depends(require_roles("admin"))):
    return {"message": "Create access granted"}


@app.put("/rbac/update")
async def f10(_: UserInDB = Depends(require_roles("admin", "user"))):
    return {"message": "Update access granted"}


@app.delete("/rbac/delete")
async def f11(_: UserInDB = Depends(require_roles("admin"))):
    return {"message": "Delete access granted"}


@app.post("/todos", response_model=TodoOut, status_code=status.HTTP_201_CREATED)
async def f12(todo: TodoCreate):
    return TodoOut(**create_todo(todo.title, todo.description))


@app.get("/todos", response_model=list[TodoOut])
async def f13():
    res = []
    for x in list_todos():
        res.append(TodoOut(**x))
    return res


@app.get("/todos/{todo_id}", response_model=TodoOut)
async def f14(todo_id: int):
    t = get_todo(todo_id)
    if t is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found",
        )
    return TodoOut(**t)


@app.put("/todos/{todo_id}", response_model=TodoOut)
async def f15(todo_id: int, todo: TodoUpdate):
    t = update_todo(
        todo_id,
        title=todo.title,
        description=todo.description,
        completed=todo.completed,
    )
    if t is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found",
        )
    return TodoOut(**t)


@app.delete("/todos/{todo_id}", response_model=Message)
async def f16(todo_id: int):
    if not delete_todo(todo_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Todo not found",
        )
    return Message(message="Todo deleted successfully")
