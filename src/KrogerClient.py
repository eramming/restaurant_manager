import os
import requests
import base64
from decimal import Decimal
from typing import Any
from dataclasses import dataclass
from logging import Logger, getLogger

LOG: Logger = getLogger(__name__)

@dataclass
class PriceResult:
    ingredient: str
    unit_price: Decimal
    product_description: str

class KrogerClient:

    def __init__(self):
        self.host_url: str = "https://api-ce.kroger.com/v1"
        self.location_id = os.getenv("KROGER_LOCATION_ID", None)
        self.client_id = os.getenv("KROGER_CLIENT_ID", None)
        self.client_secret = os.getenv("KROGER_CLIENT_SECRET", None)
        self._ensure_env_vars()
        self.access_token: str = self._get_kroger_access_token()

    def _ensure_env_vars(self) -> None:
        if not any([self.location_id, self.client_id, self.client_secret]):
            raise ValueError("Expected `KROGER_LOCATION_ID`, `KROGER_CLIENT_ID`, & "
                             "`KROGER_CLIENT_SECRET` environment variables to be set.")
        
    def price_of(self, ingredient: str) -> PriceResult:
        """
        Uses Kroger product search and picks the first product with price data.
        """

        params = {
            "filter.term": ingredient,
            "filter.limit": 10,
            # "filter.locationId": self.location_id
        }

        LOG.info(f"Making Kroger api call: {self.host_url}/products with params={params}")
        response = requests.get(
            f"{self.host_url}/products",
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Accept": "application/json",
            },
            params=params,
            timeout=10
        )
        if not response.ok:
            LOG.error(response.text)
            LOG.error(response.status_code)
        response.raise_for_status()
        
        return self.parse_results(response.json(), ingredient)

        
    def parse_results(self, json: dict, ingr: str) -> PriceResult:
        products = json.get("data", [])

        for product in products:
            price: Decimal = self._extract_price(product)

            if price is not None:
                return PriceResult(
                    ingredient=ingr,
                    unit_price=price,
                    product_description=product.get("description", ingr),
                )
        raise ValueError(f"No Kroger price found for ingredient: {ingr}")

    def _get_kroger_access_token(self) -> str:
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")

        LOG.info(f"Making Kroger api call: {self.host_url}/connect/oauth2/token")
        response = requests.post(
            f"{self.host_url}/connect/oauth2/token",
            headers={
                "Authorization": f"Basic {encoded_credentials}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "grant_type": "client_credentials",
                "scope": "product.compact",
            },
            timeout=10,
        )
        response.raise_for_status()
        return response.json()["access_token"]

    def _extract_price(self, product: dict[str, Any]) -> Decimal | None:
        for item in product.get("items", []):
            if "price" in item:
                price_data: dict = item.get("price")
                price: float = price_data["promo"] if "promo" in price_data else price_data.get("regular")
                if price is not None:
                    return Decimal(str(price))
        return None