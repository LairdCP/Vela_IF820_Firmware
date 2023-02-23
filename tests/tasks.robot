*** Settings ***
Documentation       EZ-Serial Test Suite

Library             ..${/}common${/}EzSerialPort.py


*** Variables ***
${COM_PORT} =       /dev/cu.usbmodem134304
${BAUD_RATE} =      115200


*** Tasks ***
Ping
    Open the connection
    Send Ping


*** Keywords ***
Open the connection
    EzSerialPort.Open    ${COM_PORT}    ${BAUD_RATE}

Send Ping
    ${res} =    EzSerialPort.Send And Wait    system_ping
    IF    ${res} != 0    Fail    Response error ${res}
