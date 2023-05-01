*** Settings ***
Documentation       System Command Tests.
...                 Will test system commands on an IF820 devcie.

Library             ..${/}common${/}EzSerialPort.py    WITH NAME    IF820_Device
Resource            common.robot

Test Setup          Test Setup
Test Teardown       Test Teardown
Test Timeout        2 minute

Default Tags        vela if820


*** Variables ***
${MAC_ADDR_LEN}             ${6}
${lib_if820_device}         ${EMPTY}
${ez_system_commands}       ${EMPTY}


*** Test Cases ***
Ping
    Send Command    ${ez_system_commands.CMD_PING}

Query Firmware
    Send Command    ${ez_system_commands.CMD_QUERY_FW}

Get MAC Addr
    Send Command    ${ez_system_commands.CMD_GET_BT_ADDR}

Get ECO Params
    # not working Bug L220D100-30
    Send Command    ${ez_system_commands.CMD_GET_ECO_PARAMS}

Get WCO Params
    # not working Bug L220D100-31
    Send Command    ${ez_system_commands.CMD_GET_WCO_PARAMS}

Get Sleep Params
    Send Command    ${ez_system_commands.CMD_GET_SLEEP_PARAMS}

Get Tx Power
    Send Command    ${ez_system_commands.CMD_GET_TX_POWER}

Get Uart Params
    # not working in binary mode Bug L220D100-32
    Send Command    ${ez_system_commands.CMD_GET_UART_PARAMS}

Get Transport
    Send Command    ${ez_system_commands.CMD_GET_TRANSPORT}

Factory Reset
    FOR    ${api_mode}    IN    @{API_MODES}
        IF820_Device.Send    command=${ez_system_commands.CMD_FACTORY_RESET}    apiformat=${api_mode}
        ${res} =    IF820_Device.Wait Event    ${ez_system_commands.EVENT_SYSTEM_BOOT}
        Fail on error    ${res[0]}
    END


*** Keywords ***
Test Setup
    Read Settings File

    #Get instances of python libraries needed
    ${lib_if820_device} =    Builtin.Get Library Instance    IF820_Device
    Set Global Variable    ${lib_if820_device}    ${lib_if820_device}

    ${ez_system_commands} =    IF820_Device.Get Sys Commands
    Set Global Variable    ${ez_system_commands}    ${ez_system_commands}

    #open the serial port
    IF820_Device.Close
    Sleep    ${1}
    IF820_Device.open    ${settings_comport_IF820_peripheral}    ${lib_if820_device.IF820_DEFAULT_BAUD}
    Sleep    ${1}

Test Teardown
    IF820_Device.Close
    Log    "Test Teardown Complete"

Send Command
    [Arguments]    ${cmd}
    FOR    ${api_mode}    IN    @{API_MODES}
        ${res} =    IF820_Device.Send And Wait    command=${cmd}    apiformat=${api_mode}
        Fail on error    ${res[0]}
    END
