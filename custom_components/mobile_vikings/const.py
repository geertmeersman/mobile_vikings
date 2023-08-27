"""Constants used by MobileVikings."""
from datetime import timedelta
import json
import logging
from pathlib import Path
from typing import Final

from homeassistant.const import Platform

from .models import MobileVikingsEnvironment

SHOW_DEBUG_AS_WARNING = False

_LOGGER = logging.getLogger(__name__)

PLATFORMS: Final = [Platform.SENSOR]

ATTRIBUTION: Final = "Data provided by MobileVikings"

DEFAULT_MOBILEVIKINGS_ENVIRONMENT = MobileVikingsEnvironment(
    api_endpoint="https://mobilevikings.be/nl/my-viking",
    uwa_endpoint="https://uwa.mobilevikings.be",
    deals_endpoint="https://vikingdeals.be",
    authority="uwa.mobilevikings.be",
    logincheck="https://budskap.mobilevikings.be/mv/notifications/?context=/my-viking/login",
)

BASE_HEADERS = {
    "accept-language": "nl-BE,nl;q=0.9",
    "sec-ch-ua": '" Not A;Brand";v="99", "Chromium";v="100", "Google Chrome";v="100"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "Windows",
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
}

DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S%z"
PRODUCT_DATA = ["product"]
BUNDLES_DATA = ["bundles"]
BALANCE_DATA = [
    "credit",
    "out_of_bundle_cost",
    "out_of_bundle_cost_threshold",
    "regionality",
    "data_throttled",
]
SUBSCRIPTION_DATA = ["id", "type", "sim", "next_bill_run"]
BUNDLE_DATA = ["valid_from", "valid_until", "total", "used"]

COORDINATOR_UPDATE_INTERVAL = timedelta(minutes=15)
CONNECTION_RETRY = 5
REQUEST_TIMEOUT = 20
WEBSITE = "https://mobilevikings.be/nl/my-viking"

DEFAULT_ICON = "mdi:help-circle-outline"

manifestfile = Path(__file__).parent / "manifest.json"
with open(manifestfile) as json_file:
    manifest_data = json.load(json_file)

DOMAIN = manifest_data.get("domain")
NAME = manifest_data.get("name")
VERSION = manifest_data.get("version")
ISSUEURL = manifest_data.get("issue_tracker")
STARTUP = f"""
-------------------------------------------------------------------
{NAME}
Version: {VERSION}
This is a custom component
If you have any issues with this you need to open an issue here:
{ISSUEURL}
-------------------------------------------------------------------
"""
