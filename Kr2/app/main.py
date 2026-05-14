from datetime import datetime
from typing import Annotated
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from app import auth
from app.models import CommonHeaders, LoginRequest, Product, UserCreate, UserProfile, validation_error_message
app = FastAPI(
    title="Control Work #2",
    description="FastAPI application covering user creation, products, cookies, and headers tasks.",
    version="1.0.0",
)
arr = [
    Product(product_id=123, name="Smartphone", category="Electronics", price=599.99),
    Product(product_id=456, name="Phone Case", category="Accessories", price=19.99),
    Product(product_id=789, name="Iphone", category="Electronics", price=1299.99),
    Product(product_id=101, name="Headphones", category="Accessories", price=99.99),
    Product(product_id=202, name="Smartwatch", category="Electronics", price=299.99),
]
PRODUCTS = arr
PRODUCTS_BY_ID = {}
for p in arr:
    PRODUCTS_BY_ID[p.product_id] = p
@app.exception_handler(auth.UnauthorizedError)
async def h1(_, __):
    return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"message": "Unauthorized"})
@app.exception_handler(auth.InvalidCredentialsError)
async def h2(_, __):
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"message": "Invalid credentials"},
    )
@app.exception_handler(auth.InvalidSessionError)
async def h3(_, __):
    return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"message": "Invalid session"})
@app.exception_handler(auth.SessionExpiredError)
async def h4(_, __):
    return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"message": "Session expired"})
async def parse_login_request(request: Request):
    ct = request.headers.get("content-type", "")
    try:
        if "application/json" in ct:
            d = await request.json()
        else:
            f = await request.form()
            d = dict(f)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request body") from e
    try:
        return LoginRequest.model_validate(d)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=validation_error_message(e.errors()),
        ) from e
def set_session_cookie(response: Response, token):
    response.set_cookie(
        key=auth.SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=False,
        max_age=auth.SESSION_TTL_SECONDS,
        samesite="lax",
    )
def get_current_user(request: Request, response: Response):
    tok = request.cookies.get(auth.SESSION_COOKIE_NAME)
    if not tok:
        raise auth.UnauthorizedError
    s = auth.parse_session_token(tok)
    u = auth.USER_PROFILES[s.user_id]
    if auth.should_refresh_session(s.last_activity):
        ntok = auth.create_session_token(u.user_id)
        set_session_cookie(response, ntok)
    return u
def get_common_headers(
    user_agent: Annotated[str | None, Header(alias="User-Agent")] = None,
    accept_language: Annotated[str | None, Header(alias="Accept-Language")] = None,
):
    try:
        return CommonHeaders.from_headers(user_agent=user_agent, accept_language=accept_language)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
AuthenticatedUser = Annotated[UserProfile, Depends(get_current_user)]
HeaderPayload = Annotated[CommonHeaders, Depends(get_common_headers)]
@app.get("/")
def read_root():
    return {"message": "FastAPI control work app is running"}
@app.post("/create_user", response_model=UserCreate)
def create_user(user: UserCreate):
    return user
@app.get("/products/search", response_model=list[Product])
def search_products(
    keyword: str = Query(..., min_length=1),
    category: str | None = Query(default=None, min_length=1),
    limit: int = Query(default=10, ge=1),
):
    k = keyword.lower()
    res = []
    for p in PRODUCTS:
        if k in p.name.lower():
            if category is None or p.category.lower() == category.lower():
                res.append(p)
    return res[:limit]
@app.get("/product/{product_id}", response_model=Product)
def get_product(product_id: int):
    p = PRODUCTS_BY_ID.get(product_id)
    if p is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return p
@app.post("/login")
async def login(request: Request, response: Response):
    d = await parse_login_request(request)
    u = auth.authenticate_user(d.username, d.password)
    tok = auth.create_session_token(u.user_id)
    set_session_cookie(response, tok)
    return {
        "message": "Login successful",
        "user": u.model_dump(),
    }
@app.get("/user")
def read_user_profile(current_user: AuthenticatedUser):
    return current_user.model_dump()
@app.get("/profile")
def read_profile(current_user: AuthenticatedUser):
    return {
        "message": "Profile loaded successfully",
        "user": current_user.model_dump(),
    }
@app.get("/headers")
def read_headers(headers: HeaderPayload):
    return headers.as_response_payload()
@app.get("/info")
def read_info(response: Response, headers: HeaderPayload):
    response.headers["X-Server-Time"] = datetime.now().isoformat(timespec="seconds")
    return {
        "message": "Р”РѕР±СЂРѕ РїРѕР¶Р°Р»РѕРІР°С‚СЊ! Р’Р°С€Рё Р·Р°РіРѕР»РѕРІРєРё СѓСЃРїРµС€РЅРѕ РѕР±СЂР°Р±РѕС‚Р°РЅС‹.",
        "headers": headers.as_response_payload(),
    }
