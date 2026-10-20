from fastapi import FastAPI, HTTPException, Response, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from typing import Optional

app = FastAPI()

# @app.exception_handler(HTTPException)
# async def http_exception_handler(request: Request, exc: HTTPException):
#     return JSONResponse(
#         status_code=exc.status_code,
#         content={"error": exc.detail},
#     )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException
):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": str(exc.detail)},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
):
    return JSONResponse(
        status_code=422,
        content={"error": "Invalid request"},
    )

deliveries = {}
next_id = 1

VALID_STATUSES = ["created", "in_transit", "delivered"]

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/deliveries", status_code=201)
async def create_delivery(request: Request):
    global next_id

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Body is not a valid JSON object")

    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="Body must be a JSON object")

    recipient = body.get("recipient")
    address = body.get("address")

    if recipient is None or address is None:
        raise HTTPException(status_code=400, detail="Recipient and address are required")

    if not isinstance(recipient, str) or not isinstance(address, str):
        raise HTTPException(status_code=400, detail="Recipient and address must be strings")

    recipient = recipient.strip()
    address = address.strip()

    if not recipient or not address:
        raise HTTPException(status_code=400, detail="Recipient and address cannot be empty")

    new_delivery = {
        "id": next_id,
        "recipient": recipient,
        "address": address,
        "status": "created",
    }

    deliveries[next_id] = new_delivery
    next_id += 1

    return new_delivery

@app.get("/deliveries")
def list_deliveries(status: Optional[str] = None):
    if status is not None and status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid status")

    result = list(deliveries.values())

    if status is not None:
        result = [item for item in result if item["status"] == status]

    return result

@app.get("/deliveries/{delivery_id}")
def get_delivery(delivery_id: int):
    if delivery_id not in deliveries:
        raise HTTPException(status_code=404, detail="Delivery not found")

    return deliveries[delivery_id]

@app.patch("/deliveries/{delivery_id}/status")
async def update_delivery_status(delivery_id: int, request: Request):
    if delivery_id not in deliveries:
        raise HTTPException(status_code=404, detail="Delivery not found")

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    if not isinstance(body, dict) or "status" not in body:
        raise HTTPException(status_code=400, detail="Status is required")

    new_status = body["status"]

    if not isinstance(new_status, str) or new_status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    # new_status = body["status"]

    # if new_status not in VALID_STATUSES:
    #     raise HTTPException(status_code=400, detail="Invalid status")

    delivery = deliveries[delivery_id]
    current_status = delivery["status"]

    allowed_transitions = {
        "created": "in_transit",
        "in_transit": "delivered",
    }

    if allowed_transitions.get(current_status) != new_status:
        raise HTTPException(
            status_code=409,
            detail="Invalid status transition",
        )

    delivery["status"] = new_status
    return delivery


@app.delete("/deliveries/{delivery_id}", status_code=204)
def delete_delivery(delivery_id: int):
    if delivery_id not in deliveries:
        raise HTTPException(
            status_code=404,
            detail="Delivery not found",
        )

    if deliveries[delivery_id]["status"] != "created":
        raise HTTPException(
            status_code=409,
            detail="Cannot delete a delivery unless its status is created",
        )

    del deliveries[delivery_id]
    return Response(status_code=204)


# @app.delete("/deliveries/{delivery_id}", status_code=204)
# def delete_delivery(delivery_id: int):
#     if delivery_id not in deliveries:
#         raise HTTPException(status_code=404, detail="Delivery not found")

#     # if deliveries[delivery_id]["status"] == "delivered":
#     #     raise HTTPException(
#     #         status_code=409,
#     #         detail="Cannot delete a delivered delivery",
#     #     )

#     if deliveries[delivery_id]["status"] != "created":
#         raise HTTPException(
#             status_code=409,
#             detail="Cannot delete a delivery unless its status is created",
#         )
#     del deliveries[delivery_id]
#     return Response(status_code=204)