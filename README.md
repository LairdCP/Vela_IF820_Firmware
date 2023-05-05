# Vela IF820 EZ-Serial Host

This repository contains samples and tests that demonstrate how a host can control the Vela IF820 module using the EZ-Serial API and serial protocol.

## Prerequisites

- A host with Python 3.x installed
- IF820 DVK(s)
- BT900 DVK(s) - Only for samples or tests involving the BT900

## Setup

### Python Samples

Before running any samples, be sure to install the Python dependencies:

```
pip3 install --user -r requirements.txt
```

### Robot Tests

It is recommended to use [Visual Studio Code (VS Code)](https://code.visualstudio.com/) for easy Robot Framework setup and for running the tests.

First install the following extensions for VS Code:

1. [Robocorp Code](https://marketplace.visualstudio.com/items?itemName=robocorp.robocorp-code)
2. [Robot Framework Language Server](https://marketplace.visualstudio.com/items?itemName=robocorp.robotframework-lsp)

Lastly, open the repository folder with VS Code or open the [workspace](if820_ezserial.code-workspace).

Once opened, VS Code will automatically setup Robot Framework and its dependencies. It can take a few minutes for this to complete.
