
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional

app = FastAPI()

# Store deliveries in memory
deliveries = {}
next_id = 1

VALID_STATUSES = ["created", "in_transit", "delivered"]


class DeliveryCreate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    recipient: str = Field(min_length=1)
    address: str = Field(min_length=1)


class DeliveryStatusUpdate(BaseModel):
    status: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/deliveries", status_code=201)
def create_delivery(delivery: DeliveryCreate):
    global next_id

    recipient = delivery.recipient.strip()
    address = delivery.address.strip()

    if not recipient or not address:
        raise HTTPException(status_code=400, detail="Recipient and address are required")

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
def update_delivery_status(
    delivery_id: int,
    update: DeliveryStatusUpdate,
):
    if delivery_id not in deliveries:
        raise HTTPException(status_code=404, detail="Delivery not found")

    if update.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid status")

    delivery = deliveries[delivery_id]
    current_status = delivery["status"]

    allowed_transitions = {
        "created": "in_transit",
        "in_transit": "delivered",
    }

    if allowed_transitions.get(current_status) != update.status:
        raise HTTPException(
            status_code=409,
            detail="Invalid status transition",
        )

    delivery["status"] = update.status
    return delivery


@app.delete("/deliveries/{delivery_id}", status_code=204)
def delete_delivery(delivery_id: int):
    if delivery_id not in deliveries:
        raise HTTPException(status_code=404, detail="Delivery not found")

    if deliveries[delivery_id]["status"] == "delivered":
        raise HTTPException(
            status_code=409,
            detail="Cannot delete a delivered delivery",
        )

    del deliveries[delivery_id]
    return Response(status_code=204)
