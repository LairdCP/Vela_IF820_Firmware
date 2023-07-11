*** Settings ***
Documentation       IF820 DVK Manufacturing Test
...                 This test will test one IF820 DVK at a time.

Library             ..${/}common${/}PicoProbe.py

Default Tags        vela if820


*** Test Cases ***
DVK MFG Test
    PicoProbe.Program V1 Settings
