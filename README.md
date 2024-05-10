# Vela IF820 Firmware

This repository contains samples and tests that demonstrate how a host can control the Vela IF820 module using the EZ-Serial API and serial protocol.

## Prerequisites

- Install Python 3.9 to 3.11. Python 3.12 is not supported.
- One or two IF820 DVKs. The second DVK is only required for samples and tests requiring two DVKs.
- One BT900 DVK - Only for samples or tests involving the BT900

## Setup

### Checkout the Firmware

```
git clone --recurse-submodules https://github.com/LairdCP/Vela_IF820_Firmware.git
```

### Python Samples and Tests

Before running any samples or tests, be sure to install the Python dependencies:

```
pip3 install -r requirements.txt
```

## Documentation

Please see the [Vela IF820 Software User Guide](https://lairdcp.github.io/guides/vela_if820_user_guide/latest.html) for all documentation.
