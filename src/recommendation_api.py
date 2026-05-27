from fastapi import FastAPI
from RecommendationEngine import RecommendationEngine

app = FastAPI(title="Demand Forecasting Service")


@app.post("/recommend")
def recommend():
    RecommendationEngine().recommend()
    return {"message": "Successfully generated and sent recommendations."}