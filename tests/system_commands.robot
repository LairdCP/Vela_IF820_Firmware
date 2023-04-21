*** Settings ***
Documentation       System Command Tests.
...                 Will loop both central and perhipheral devcies and api modes.

Resource            serial_port.robot
Resource            system_command_defs.robot
Resource            common.robot

Test Timeout        2 minute

Default Tags        Vela IF820

Test Setup          Test Setup
Test Teardown       Test Teardown

*** Variables ***
${MAC_ADDR_LEN}            ${6}
@{DUTS}                    ${DEV_PERIPHERAL}   ${DEV_CENTRAL}

*** Test Cases ***
Ping
    Send Command    ${API_CMD_PING}

Query Firmware
    Send Command    ${API_CMD_QUERY_FW}

Get MAC Addr
    Send Command    ${API_CMD_GET_BT_ADDR}

Get ECO Params
    # not working Bug L220D100-30
    Send Command    ${API_CMD_GET_ECO_PARAMS}

Get WCO Params
    # not working Bug L220D100-31
    Send Command    ${API_CMD_GET_WCO_PARAMS}

Get Sleep Params
    Send Command    ${API_CMD_GET_SLEEP_PARAMS}

Get Tx Power
    Send Command    ${API_CMD_GET_TX_POWER}

Get Uart Params
    # not working in binary mode Bug L220D100-32
    Send Command    ${API_CMD_GET_UART_PARAMS}

Get Transport
    Send Command    ${API_CMD_GET_TRANSPORT}

Factory Reset
    FOR    ${api_mode}    IN    @{API_MODES}
        FOR    ${device}    IN    @{DUTS}
            serial_port.Send    api_cmd=${API_CMD_FACTORY_RESET}    device=${device}    api_format=${api_mode}
            ${res} =    serial_port.Wait For Event   ${EVENT_SYSTEM_BOOT}    ${device}
            Fail on error    ${res[0]}
        END
    END

*** Keywords ***
Test Setup
    #open the serial ports for devices in test
    FOR    ${device}    IN    @{DUTS}
        Close the connection    ${device}
        ${result} =     Open the connection     ${device}
        IF     ${result} == ${true}
            Log  "Test Setup Complete"
        ELSE
            Fail  "Cannot Open Peripheral Device."
        END
    END

Test Teardown
    FOR    ${device}    IN    @{DUTS}
        Close the connection    ${device}
    END
    Log  "Test Teardown Complete"

Send Command
    [Arguments]    ${cmd}
    FOR    ${api_mode}    IN    @{API_MODES}
        FOR    ${device}    IN    @{DUTS}
            ${res} =    serial_port.Send And Wait     api_cmd=${cmd}    device=${device}    api_format=${api_mode}
            Fail on error    ${res[0]}
        END
    END