*** Settings ***
Documentation       Helper functions to open and close the serial port.
Library             ..${/}common${/}EzSerialPort.py    WITH NAME    Central
Library             ..${/}common${/}EzSerialPort.py    WITH NAME    Peripheral
Resource            common.robot

*** Variables ***
${COM_PORT_CENTRAL}             /dev/cu.usbmodem33203
${COM_PORT_PERIPHERAL}          /dev/cu.usbmodem33303
${BAUD_RATE}                    115200

*** Keywords ***
Open the connection
    [Arguments]    ${Device}
    [Documentation]     Open the serial port with default settings.
    ...                 Device argument must be either Peripheral or Central.
    ${success} =     Set Variable    ${true}
    IF     "${Device}" == "${DEV_PERIPHERAL}"
        Log     Open Peripheral
        Peripheral.Open    ${COM_PORT_PERIPHERAL}    ${BAUD_RATE}
        Enable Serial Port Debugging    ${DEV_PERIPHERAL}
    ELSE IF     "${Device}" == "${DEV_CENTRAL}"
        Log     Open Central
        Central.Open    ${COM_PORT_CENTRAL}    ${BAUD_RATE}
        Enable Serial Port Debugging    ${DEV_CENTRAL}
    ELSE
        ${success} =    Set Variable     ${false}
        Fail    ${ERROR_DEVICE_TYPE}
    END
    [return]    ${success}

Close the connection
    [Arguments]    ${Device}
    [Documentation]     Close the serial port.
    ...                 Device argument must be either Peripheral or Central.
    IF     "${Device}" == "${DEV_PERIPHERAL}"
        Log    "Device is Peripheral, Close"
        Peripheral.Close
    ELSE IF     "${Device}" == "${DEV_CENTRAL}"
        Central.Close
        Log     Close Central
    ELSE
        Fail    ${ERROR_DEVICE_TYPE}
    END
Send And Wait
    [Arguments]    ${api_cmd}    ${device}   ${rx_timeout}=${DEFAULT_RX_TIMEOUT}    ${api_format}=${API_MODE_BINARY}
    ${res}=    Set Variable    ${-1}
    IF     "${device}" == "${DEV_PERIPHERAL}"
        ${res} =    Peripheral.Send And Wait    command=${api_cmd}    rxtimeout=${rx_timeout}    apiformat=${api_format}
    ELSE IF     "${device}" == "${DEV_CENTRAL}"
        ${res} =    Central.Send And Wait   command=${api_cmd}    rxtimeout=${rx_timeout}    apiformat=${api_format}
    ELSE
        Log    ${ERROR_DEVICE_TYPE}
    END
    RETURN     ${res}

Send
    [Arguments]    ${api_cmd}    ${device}   ${rx_timeout}=${DEFAULT_RX_TIMEOUT}    ${api_format}=${API_MODE_BINARY}
    ${res}=    Set Variable    ${1}
    IF     "${device}" == "${DEV_PERIPHERAL}"
        ${res} =    Peripheral.Send    command=${api_cmd}    rxtimeout=${rx_timeout}    apiformat=${api_format}
    ELSE IF     "${device}" == "${DEV_CENTRAL}"
        ${res} =    Central.Send   command=${api_cmd}    rxtimeout=${rx_timeout}    apiformat=${api_format}
    ELSE
        Log    ${ERROR_DEVICE_TYPE}
    END
    RETURN     ${res}

Wait For Event
    [Arguments]    ${api_cmd}    ${device}    ${rx_timeout}=${DEFAULT_RX_TIMEOUT}
    ${res}=    Set Variable    ${-1, None}
    IF     "${device}" == "${DEV_PERIPHERAL}"
        ${res} =    Peripheral.Wait Event    event=${api_cmd}    rxtimeout=${rx_timeout}
    ELSE IF     "${device}" == "${DEV_CENTRAL}"
        ${res} =    Central.Wait Event    event=${api_cmd}    rxtimeout=${rx_timeout}
    ELSE
        Log    ${ERROR_DEVICE_TYPE}
    END
    RETURN     ${res}

Enable Serial Port Debugging
    [Arguments]    ${device}
    ${res}=    Set Variable    ${0}
    ${LogLevel} =    Get Library Instance    Peripheral

    IF     "${device}" == "${DEV_PERIPHERAL}"
        Peripheral.Configure App Logging    level=${LogLevel.NOTSET}    file_level=${LogLevel.NOTSET}
    ELSE IF     "${device}" == "${DEV_CENTRAL}"
        Central.Configure App Logging    level=${LogLevel.NOTSET}    file_level=${LogLevel.NOTSET}
    ELSE
        Log    ${ERROR_DEVICE_TYPE}
        ${res}=    Set Variable    ${-1}
    END
    RETURN     ${res}

Disable Serial Port Debugging
    [Arguments]    ${device}
    ${res}=    Set Variable    ${0}
    IF     "${device}" == "${DEV_PERIPHERAL}"
        Peripheral.Disable Logging
    ELSE IF     "${device}" == "${DEV_CENTRAL}"
        Central.Disable Logging
    ELSE
        Log    ${ERROR_DEVICE_TYPE}
        ${res}=    Set Variable    ${-1}
    END
    RETURN     ${res}
