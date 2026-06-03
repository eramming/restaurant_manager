# restaurant_manager
A full management service for a fake restaurant business scenario. It help to guide ingredient inventory, dynamic menu pricing, and potentially more down the line.


## Components
### Inventory Manager
An api which can store sales and newly purchased ingredients.

- POST /sale
- POST /ingredients/purchase

### Supply Gap Analyzer
The SupplyGapAnalyzer forecasts tomorrow's sales by using a moving average over the last 4 identical days of the week. It compares the demand to current ingredient supply and generates a report of needed ingredients. It also notes excess supply that is expiring tomorrow.

### Pricing Analyzer
The pricing analyzer receives the supply gap report. It hits the Kroger api to get the current price of all listed ingredients in the report. For each needed ingredient, a delta against its previous price is provided so that the end user can strategically update menu prices to keep profit steady. For each expiring ingredient, a potential financial loss value is provided so that the end user can create informed discounts on menu items containing the ingredient (to drive up demand). This pricing report is sent automatically to a SNS topic to which my personal email is subscribed.


## Data Flow
### Testing
1) ingredient purchases and sales history added all at once using seed_dynamo.py and inventory_manager_api
3) end-user triggers a supply gap analysis afterwards using api
4) SupplyGapAnalyzer automatically sends its report via SQS to forecast_listener
5) forecast_listener spawns a PricingAnalyzer which shares report via SNS to personal email
6) Optional: Could create script to "buy" the ingredients in the "needed" section of the report

### Real Life
1) end-user adds purchased ingredients using inventory_manager using api
2) Random sales occur throughout the day
3) end-user triggers a supply gap analysis at the end of day using api
4) SupplyGapAnalyzer automatically sends its report via SQS to forecast_listener
5) forecast_listener spawns a PricingAnalyzer which shares report via SNS to personal email
6) end-user buys needed ingredients and uses inventory_manager_api to reflect these purchases.

## AWS Components
. 3 EC2 instances for: inventory_manager_api.py, SupplyGapAnalyzer.py, and PricingAnalyzer.py
. 1 SQS queue to connect SupplyGapAnalyzer and PricingAnalyzer
. 1 SNS notification from PricingAnalyzer to my personal email
. Tables
.. Inventory
.. Sales
.. Menu
.. 
