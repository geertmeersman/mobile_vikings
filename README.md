<img src="https://github.com/geertmeersman/mobile_vikings/raw/main/images/brand/dark_logo.png"
     alt="Mobile Vikings"
     align="right"
     style="width: 200px;margin-right: 10px;" />

# Mobile Vikings for Home Assistant

A Home Assistant integration allowing to monitor your EV charging and manage your charging points

### Features

- 📱 Mobile data sensors
- 📞 Voice & sms sensors
- 💲 Out of bundle usage
- 💲 Vikings deals balance
- 📈 Invoice sensors
- 👱 User account information

---

<!-- [START BADGES] -->
<!-- Please keep comment here to allow auto update -->

[![MIT License](https://img.shields.io/github/license/geertmeersman/mobile_vikings?style=for-the-badge)](https://github.com/geertmeersman/mobile_vikings/blob/master/LICENSE)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/hacs/integration)
[![maintainer](https://img.shields.io/badge/maintainer-Geert%20Meersman-green?style=for-the-badge&logo=github)](https://github.com/geertmeersman)
[![buyme_coffee](https://img.shields.io/badge/Buy%20me%20a%20Duvel-donate-yellow?style=for-the-badge&logo=buymeacoffee)](https://www.buymeacoffee.com/geertmeersman)
[![discord](https://img.shields.io/discord/1094198226493636638?style=for-the-badge&logo=discord)](https://discord.gg/9w6UAsutdJ)

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

## Installation

### Using [HACS](https://hacs.xyz/) (recommended)

1. Simply search for `Mobile Vikings` in HACS and install it easily.
2. Restart Home Assistant
3. Add the 'Mobile Vikings' integration via HA Settings > 'Devices and Services' > 'Integrations'
4. Provide your Mobile Vikings username and password

### Manual

1. Copy the `custom_components/mobile_vikings` directory of this repository as `config/custom_components/mobile_vikings` in your Home Assistant instalation.
2. Restart Home Assistant
3. Add the 'Mobile Vikings' integration via HA Settings > 'Devices and Services' > 'Integrations'
4. Provide your Mobile Vikings username and password

This integration will set up the following platforms.

| Platform         | Description                                             |
| ---------------- | ------------------------------------------------------- |
| `mobile_vikings` | Home Assistant component for Mobile Vikings BE services |

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

## Troubleshooting

1. You can enable logging for this integration specifically and share your logs, so I can have a deep dive investigation. To enable logging, update your `configuration.yaml` like this, we can get more information in Configuration -> Logs page

```
logger:
  default: warning
  logs:
    custom_components.mobile_vikings: debug
```

## Screenshots

## Code origin

The code of this Home Assistant integration has been written by analysing the calls made by the Mobile Vikings website. Goal is to automate as much as possible and to monitor usage.

I have no link with Mobile Vikings
