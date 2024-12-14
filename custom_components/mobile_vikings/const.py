"""Constants used by MobileVikings."""
from datetime import timedelta
import json
import logging
from pathlib import Path
from typing import Final

from homeassistant.const import Platform

_LOGGER = logging.getLogger(__name__)

PLATFORMS: Final = [Platform.SENSOR, Platform.BINARY_SENSOR]

ATTRIBUTION: Final = "Data provided by MobileVikings"

# Date and time format used in the Mobile Vikings API responses
DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S%z"

# Client ID for OAuth2 authentication
CLIENT_ID = "orIbwDyPep4Cju3CksWC4AXiIezY6JVHDix8I9pL"

# Client secret for OAuth2 authentication
CLIENT_SECRET = "QquFECtjqYev6DgApjrBsOzTPFwCEv8DTBQOBMSNs77YtwIzxPGagNhDpwwt8wxOwP8B4nd4gCTvVZfuWccTfKCPSh1xVruqHjrFBs1fH4Y8lSSRcw7PPL1QlcZwAY24"

# Base URL for the Mobile Vikings API
BASE_URL = "https://uwa.mobilevikings.be/mv"

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
