*** Settings ***
Documentation       EZ-Serial Test Suite

Library             ..${/}common${/}EzSerialPort.py


*** Variables ***
${COM_PORT}             /dev/cu.usbmodem334304
${BAUD_RATE}            115200
${API_MODE_TEXT}        0
${API_MODE_BINARY}      1


*** Test Cases ***
Ping
    [Tags]    l2vv-3
    Open the connection
    Send Ping
    Close the connection

Reboot
    Open the connection
    Reboot the device
    Close the connection


*** Keywords ***
Open the connection
    EzSerialPort.Open    ${COM_PORT}    ${BAUD_RATE}

Close the connection
    EzSerialPort.Close

Send Ping
    ${res} =    EzSerialPort.Send And Wait    system_ping
    Fail on error    ${res}

Reboot the device
    [Arguments]    ${arg_api_mode}=${API_MODE_TEXT}
    # need to ensure this variable is sent as an int in the param
    ${api_mode} =    Convert To Integer    ${arg_api_mode}
    ${res} =    EzSerialPort.Send And Wait    system_reboot    rxtimeout=1    apiformat=${api_mode}
    Fail on error    ${res}
    ${res} =    EzSerialPort.Wait Event    system_boot
    Fail on error    ${res}[0]

Fail on error
    [Arguments]    ${err}
    IF    ${err} != 0    Fail    Response error ${err}
