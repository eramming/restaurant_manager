# restaurant_manager
A full management service for a fake restaurant business scenario. It help to guide ingredient inventory, dynamic menu pricing, and potentially more down the line.


## AWS Components
- 3 EC2 instances for: inventory_manager_api.py, SupplyGapAnalyzer.py, and PricingAnalyzer.py
- 2 SQS queue to connect inventory_management_api, SupplyGapAnalyzer, and PricingAnalyzer
- 1 SNS notification from PricingAnalyzer to my personal email
- Tables
    - Inventory
    - Sales
    - Menu 



## EC2 Instance Manual Config
Launch whatever service is appropriate.
- _Inventory Management Service_: 
    1) `uv run python scripts/seed_dynamo.py`
    2) `cd src`
    3) `uv run uvicorn inventory_manager_api:app --host 0.0.0.0 --port 8000`
- _Supply Gap Service_:
    1) `cd src`
    2) `uv run python supply_change_listener.py`
- _Pricing Service_:
    1) `cd src`
    2) `uv run python supply_gap_listener.py`