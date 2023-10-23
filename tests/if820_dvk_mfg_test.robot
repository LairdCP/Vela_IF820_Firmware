*** Settings ***
Documentation       IF820 DVK Manufacturing Test
...                 This test will test one IF820 DVK at a time.

Library             ..${/}common_lib${/}common_lib${/}DvkProbe.py

Default Tags        vela if820


*** Test Cases ***
DVK MFG Test
    DvkProbe.Program V1 Settings
