<img src="https://github.com/geertmeersman/mobile_vikings/raw/main/images/brand/dark_logo.png"
     alt="Mobile Vikings"
     align="right"
     style="width: 200px;margin-right: 10px;" />

# Mobile Vikings for Home Assistant

A Home Assistant integration to monitor Mobile Vikings BE services

## Features

- View **Customer Info** such as name and account details.
- Track **Loyalty Points**: Available, blocked, and pending points.
- Monitor **Invoices**: Paid invoices, unpaid invoices, and the next expiration date.
- Access subscription details, including:
  - **Data Usage**: Remaining data and percentage used.
  - **Voice Balance**: Minutes usage details.
  - **SMS Balance**: SMS usage details.
  - **Out of Bundle Costs**.
  - **Credit Balance**.
  - **Subscription Product Information**.
  - **SIM Alias**.

---

<!-- [START BADGES] -->
<!-- Please keep comment here to allow auto update -->

[![maintainer](https://img.shields.io/badge/maintainer-Geert%20Meersman-green?style=for-the-badge&logo=github)](https://github.com/geertmeersman)
[![buyme_coffee](https://img.shields.io/badge/Buy%20me%20an%20Omer-donate-yellow?style=for-the-badge&logo=buymeacoffee)](https://www.buymeacoffee.com/geertmeersman)
[![discord](https://img.shields.io/discord/1094198226493636638?style=for-the-badge&logo=discord)](https://discord.gg/9w6UAsutdJ)

[![discord](http://invidget.switchblade.xyz/9w6UAsutdJ)](https://discord.gg/9w6UAsutdJ)

[![MIT License](https://img.shields.io/github/license/geertmeersman/mobile_vikings?style=flat-square)](https://github.com/geertmeersman/mobile_vikings/blob/master/LICENSE)
[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg?style=flat-square)](https://github.com/hacs/integration)

[![Open your Home Assistant instance and open the repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg?style=flat-square)](https://my.home-assistant.io/redirect/hacs_repository/?owner=geertmeersman&repository=mobile_vikings&category=integration)

[![GitHub issues](https://img.shields.io/github/issues/geertmeersman/mobile_vikings)](https://github.com/geertmeersman/mobile_vikings/issues)
[![Average time to resolve an issue](http://isitmaintained.com/badge/resolution/geertmeersman/mobile_vikings.svg)](http://isitmaintained.com/project/geertmeersman/mobile_vikings)
[![Percentage of issues still open](http://isitmaintained.com/badge/open/geertmeersman/mobile_vikings.svg)](http://isitmaintained.com/project/geertmeersman/mobile_vikings)
[![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-brightgreen.svg)](https://github.com/geertmeersman/mobile_vikings/pulls)

[![Hacs and Hassfest validation](https://github.com/geertmeersman/mobile_vikings/actions/workflows/validate.yml/badge.svg)](https://github.com/geertmeersman/mobile_vikings/actions/workflows/validate.yml)
[![Python](https://img.shields.io/badge/Python-FFD43B?logo=python)](https://github.com/geertmeersman/mobile_vikings/search?l=python)

[![manifest version](https://img.shields.io/github/manifest-json/v/geertmeersman/mobile_vikings/master?filename=custom_components%2Fmobile_vikings%2Fmanifest.json)](https://github.com/geertmeersman/mobile_vikings)
[![github release](https://img.shields.io/github/v/release/geertmeersman/mobile_vikings?logo=github)](https://github.com/geertmeersman/mobile_vikings/releases)
[![github release date](https://img.shields.io/github/release-date/geertmeersman/mobile_vikings)](https://github.com/geertmeersman/mobile_vikings/releases)
[![github last-commit](https://img.shields.io/github/last-commit/geertmeersman/mobile_vikings)](https://github.com/geertmeersman/mobile_vikings/commits)
[![github contributors](https://img.shields.io/github/contributors/geertmeersman/mobile_vikings)](https://github.com/geertmeersman/mobile_vikings/graphs/contributors)
[![github commit activity](https://img.shields.io/github/commit-activity/y/geertmeersman/mobile_vikings?logo=github)](https://github.com/geertmeersman/mobile_vikings/commits/main)

<!-- [END BADGES] -->

## Table of Contents

- [Mobile Vikings for Home Assistant](#mobile-vikings-for-home-assistant)
  - [Features](#features)
  - [Table of Contents](#table-of-contents)
  - [Installation](#installation)
    - [Using HACS (recommended)](#using-hacs-recommended)
    - [Manual](#manual)
  - [Available Sensors](#available-sensors)
    - [Account Details](#account-details)
    - [Invoices](#invoices)
    - [Subscription Details](#subscription-details)
  - [Contributions are welcome!](#contributions-are-welcome)
  - [Troubleshooting](#troubleshooting)
    - [Enable debug logging](#enable-debug-logging)
    - [Disable debug logging and download logs](#disable-debug-logging-and-download-logs)
  - [Screenshots](#screenshots)
  - [Code origin](#code-origin)

## Installation

### Using [HACS](https://hacs.xyz/) (recommended)

**Click on this button:**

[![Open your Home Assistant instance and open the repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg?style=flat-square)](https://my.home-assistant.io/redirect/hacs_repository/?owner=geertmeersman&repository=mobile_vikings&category=integration)

**or follow these steps:**

1. Simply search for `Mobile Vikings` in HACS and install it easily.
2. Restart Home Assistant
3. Add the 'Mobile Vikings' integration via HA Settings > 'Devices and Services' > 'Integrations'
4. Provide your Mobile Vikings username and password

### Manual

1. Copy the `custom_components/mobile_vikings` directory of this repository as `config/custom_components/mobile_vikings` in your Home Assistant installation.
2. Restart Home Assistant
3. Add the 'Mobile Vikings' integration via HA Settings > 'Devices and Services' > 'Integrations'
4. Provide your Mobile Vikings username and password

This integration will set up the following platforms.

| Platform         | Description                                             |
| ---------------- | ------------------------------------------------------- |
| `mobile_vikings` | Home Assistant component for Mobile Vikings BE services |

## Available Sensors

### Account Details

| Sensor Key                 | Description              | Unit     |
| -------------------------- | ------------------------ | -------- |
| `customer_info`            | Customer's first name    | Text     |
| `loyalty_points_available` | Available loyalty points | € (Euro) |
| `loyalty_points_blocked`   | Blocked loyalty points   | € (Euro) |
| `loyalty_points_pending`   | Pending loyalty points   | € (Euro) |

### Invoices

| Sensor Key                | Description                  | Unit      |
| ------------------------- | ---------------------------- | --------- |
| `paid_invoices`           | Total paid invoices          | Count     |
| `unpaid_invoices`         | Unpaid invoices total amount | € (Euro)  |
| `next_invoice_expiration` | Next invoice expiration date | Timestamp |

### Subscription Details

| Sensor Key           | Description                    | Unit       |
| -------------------- | ------------------------------ | ---------- |
| `data_balance`       | Data usage percentage          | %          |
| `data_remaining`     | Data remaining                 | GB         |
| `remaining_days`     | Days left in billing cycle     | Days       |
| `period_percentage`  | Billing cycle usage percentage | %          |
| `voice_balance`      | Voice usage percentage         | %          |
| `sms_balance`        | SMS usage percentage           | %          |
| `out_of_bundle_cost` | Out-of-bundle cost             | € (Euro)   |
| `credit`             | Available credit balance       | € (Euro)   |
| `product_info`       | Subscription product details   | Text/Price |
| `sim_alias`          | SIM alias                      | Text       |

---

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

## Troubleshooting

[![discord](http://invidget.switchblade.xyz/9w6UAsutdJ)](https://discord.gg/9w6UAsutdJ)

### Enable debug logging

To enable debug logging, go to Settings -> Devices & Services and then click the triple dots for the Nexxtmove integration and click Enable Debug Logging.

![enable-debug-logging](https://raw.githubusercontent.com/geertmeersman/mobile_vikings/main/images/screenshots/enable-debug-logging.gif)

### Disable debug logging and download logs

Once you enable debug logging, you ideally need to make the error happen. Run your automation, change up your device or whatever was giving you an error and then come back and disable Debug Logging. Disabling debug logging is the same as enabling, but now you will see Disable Debug Logging. After you disable debug logging, it will automatically prompt you to download your log file. Please provide this logfile.

![disable-debug-logging](https://raw.githubusercontent.com/geertmeersman/mobile_vikings/main/images/screenshots/disable-debug-logging.gif)

## Screenshots

## Code origin

The code of this Home Assistant integration has been written initially by analysing the calls made by the Mobile Vikings website.

The current version uses the MV Api as documented here: [https://docs.api.unleashed.be/](https://docs.api.unleashed.be/)

I have no link with Mobile Vikings
