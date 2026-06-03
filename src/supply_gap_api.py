from fastapi import FastAPI
from SupplyGapAnalyzer import SupplyGapAnalyzer

app = FastAPI(title="Forecasted Supply Gap Service")


@app.get("/supply_gap")
def supply_gap():
    SupplyGapAnalyzer().send_supply_gap()
    return {"message": "Successfully generated and sent supply gap analysis."}