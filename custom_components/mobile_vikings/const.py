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

MOBILE_VIKINGS = "Mobile Vikings"
JIM_MOBILE = "Jim Mobile"

# Client ID for OAuth2 authentication FPID2.2.MCaIbSP%2FL5s3sb2U72khFTgLJ68VabpnVuB6HzKd494%3D.1737890525
CLIENT_ID = "orIbwDyPep4Cju3CksWC4AXiIezY6JVHDix8I9pL"

# Client secret for OAuth2 authentication
CLIENT_SECRET = "QquFECtjqYev6DgApjrBsOzTPFwCEv8DTBQOBMSNs77YtwIzxPGagNhDpwwt8wxOwP8B4nd4gCTvVZfuWccTfKCPSh1xVruqHjrFBs1fH4Y8lSSRcw7PPL1QlcZwAY24"

CLIENT_SECRET_TAG = "client_secret"

# FPID2.2.MCaIbSP%2FL5s3sb2U72khFTgLJ68VabpnVuB6HzKd494%3D.1737890525
# A6c%2FYSmmzklFbQjSNVYlBYUW8yKw%2B2jtxx1ELlyjKIAGOMlgVy5gNfXIvQVFm5dnd071iUbocu3BG6SEl4i5PDGTLqkYqSwu%2FVWaZxAixWOEYMiHxfPmJuIjuF0izA%3D%3D
# client_id: f14262155486a64ebfba
# client_secret: 2e8e068c57a3cf799771b66ef96ab79d0ac1beed

CLIENT_SECRET_TAG_JIMMOBILE = "grant_type"
CLIENT_SECRET_VALUE_JIMMOBILE = "password"
# Client ID for OAuth2 authentication FPID2.2.RdkG7KHis21lWOa3dqN6USEXGLYXTisE7R9hgqY5sJY%3D.1737890466
CLIENT_ID_JIMMOBILE = "JIM"

# Client secret for OAuth2 authentication NLNZtPR68KdXyYQ1Ee1v3LtfMf447RHFtX4g9B0tAvArAYl04yGm4y3mTZbv2VbimrnLxVzwC%2BIp%2FZtgABI4NVIOpc7BmIKuLUW53ZzMYf1kAljzjzaLYu2D0uPDAg%3D%3D
CLIENT_SECRET_JIMMOBILE = "NZtPR68KdXyYQ1Ee1v3LtfMf447RHFtX4g9B0tAvArAYl04yGm4y3mTZbv2VbimrnLxVzwC%2BIp%2FZtgABI4NVIOpc7BmIKuLUW53ZzMYf1kAljzjzaLYu2D0uPDAg"

# Base URL for the Mobile Vikings API
BASE_URL = "https://uwa.mobilevikings.be/latest/mv"

# Base URL for the JimMobile API
BASE_URL_JIMMOBILE = "https://uwa.mobilevikings.be/jim"

COORDINATOR_UPDATE_INTERVAL = timedelta(minutes=15)
CONNECTION_RETRY = 5
REQUEST_TIMEOUT = 20
WEBSITE = "https://mobilevikings.be/nl/my-viking"
WEBSITE_JIMMOBILE = "https://jimmobile.be/nl/"

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
