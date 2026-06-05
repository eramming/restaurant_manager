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
- 3 EC2 instances for: inventory_manager_api.py, SupplyGapAnalyzer.py, and PricingAnalyzer.py
- 1 SQS queue to connect SupplyGapAnalyzer and PricingAnalyzer
- 1 SNS notification from PricingAnalyzer to my personal email
- Tables
    - Inventory
    - Sales
    - Menu 



## EC2 Instance Manual Config
As of now, you will have to:
- `chown -R ec2-user:ec2-user restaurant_manager` from /home/ec2-user
- `cd restaurant_manager`
- `chmod +x scripts/ec2_setup.sh`
- `scripts/ec2_setup.sh`
- `git pull`
- whatever command lauches that particular service

Also, I deleted the Github ssh key that JHU AWS stuff was using, so will need to recreate one:
- add to github account
- copy into cloudformation.yaml
- copy into scripts/ec2_setup.sh



1) Github private ssh key.

    For some reason we can pull this ssh key from AWS secrets manager, but when attempting to use it it fails. It's the correct looking key, so idk. Instead, I've been manually copying a local version of it to the ec2 instance. Now you can clone the restuarant_manager repo from within the instance. You may need to switch to the appropriate branch.

    - `scp -i ../.ssh/jhu_aws_ssh_key.pem id_ed25519 ec2-user@<instance-public-ip-addy>:/home/ec2-user/.ssh`
    - `git clone git@github.com:eramming/restaurant_manager.git`

2) Install `uv` and install packages.
    1) `curl -LsSf https://astral.sh/uv/install.sh | sh`
    2) `uv python install 3.14`
    3) `uv venv --python 3.14`
    4) `uv sync`


3) Launch whatever service is appropriate.
    - _Inventory Management Service_: 
        1) `uv run python scripts/seed_dynamo.py`
        2) `cd src`
        3) `uv run uvicorn inventory_manager_api:app --host 0.0.0.0 --port 8000`
    - _Supply Gap Service_:
        1) `cd src`
        2) `uv run uvicorn supply_gap_api:app --host 0.0.0.0 --port 8000`
    - _Pricing Service_:
        1) `cd src`
        2) `uv run python supply_gap_listener.py`