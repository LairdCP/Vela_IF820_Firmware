*** Settings ***
Documentation       System Command Tests.
...                 Will test system commands on an IF820 devcie.

Library             ..${/}common${/}EzSerialPort.py    WITH NAME    IF820_Device
Resource            common.robot

Test Setup          Test Setup
Test Teardown       Test Teardown
Test Timeout        4 minutes

Default Tags        vela if820


*** Variables ***
${MAC_ADDR_LEN}             ${6}
${lib_if820_device}         ${EMPTY}
${ez_system_commands}       ${EMPTY}
${REBOOT_COUNT}             10
${BOOT_DELAY_SECONDS}       3


*** Test Cases ***
Ping
    Set Tags    L2-70
    Send Command    ${ez_system_commands.CMD_PING}

Query Firmware
    Set Tags    L2-71
    Send Command    ${ez_system_commands.CMD_QUERY_FW}

Get MAC Addr
    Set Tags    L2-162
    Send Command    ${ez_system_commands.CMD_GET_BT_ADDR}

Get Sleep Params
    Set Tags    L2-163
    Send Command    ${ez_system_commands.CMD_GET_SLEEP_PARAMS}

Get Tx Power
    Set Tags    L2-164
    Send Command    ${ez_system_commands.CMD_GET_TX_POWER}

Get Transport
    Set Tags    L2-166
    Send Command    ${ez_system_commands.CMD_GET_TRANSPORT}

Get Uart Params
    Set Tags    L2-165
    FOR    ${flow}    IN    @{UART_FLOW_TYPES}
        Setup Uarts    ${flow}
        FOR    ${api_mode}    IN    @{API_MODES}
            ${res} =    IF820_Device.Send And Wait
            ...    command=${ez_system_commands.CMD_GET_UART_PARAMS}
            ...    apiformat=${api_mode}
            ...    uart_type=${0}
            Fail on error    ${res[0]}
        END
        IF820_Device.Close
    END

Factory Reset
    Set Tags    L2-65
    FOR    ${flow}    IN    @{UART_FLOW_TYPES}
        Setup Uarts    ${flow}
        FOR    ${api_mode}    IN    @{API_MODES}
            ${res} =    IF820_Device.Send And Wait
            ...    command=${ez_system_commands.CMD_FACTORY_RESET}
            ...    apiformat=${api_mode}
            Fail on error    ${res[0]}
            ${res} =    IF820_Device.Wait Event    ${ez_system_commands.EVENT_SYSTEM_BOOT}
            Fail on error    ${res[0]}
        END
        IF820_Device.Close
    END

Reboot
    Set Tags    L2-66
    FOR    ${flow}    IN    @{UART_FLOW_TYPES}
        Setup Uarts    ${flow}
        FOR    ${api_mode}    IN    @{API_MODES}
            Reboot Command    ${api_mode}
        END
        IF820_Device.Close
    END

Reboot Loop
    Set Tags    L2-167
    FOR    ${api_mode}    IN    @{API_MODES}
        FOR    ${flow}    IN    @{UART_FLOW_TYPES}
            Setup Uarts    ${flow}
            FOR    ${counter}    IN RANGE    ${REBOOT_COUNT}
                Reboot Command    ${api_mode}
                Sleep    ${BOOT_DELAY_SECONDS}
            END
            IF820_Device.Close
        END
    END


*** Keywords ***
Test Setup
    Read Settings File

    # Get instances of python libraries needed
    ${lib_if820_device} =    Builtin.Get Library Instance    IF820_Device
    Set Global Variable    ${lib_if820_device}    ${lib_if820_device}

    ${ez_system_commands} =    IF820_Device.Get Sys Commands
    Set Global Variable    ${ez_system_commands}    ${ez_system_commands}

    # ensure the serial port is closed
    IF820_Device.Close
    Sleep    ${1}

Test Teardown
    IF820_Device.Close
    Log    "Test Teardown Complete"

Send Command
    [Arguments]    ${cmd}
    FOR    ${flow}    IN    @{UART_FLOW_TYPES}
        Setup Uarts    ${flow}
        FOR    ${api_mode}    IN    @{API_MODES}
            ${res} =    IF820_Device.Send And Wait    command=${cmd}    apiformat=${api_mode}
            Fail on error    ${res[0]}
        END
        IF820_Device.Close
    END

Set Uart Params
    [Arguments]    ${flow}
    ${res} =    IF820_Device.Send And Wait
    ...    command=${ez_system_commands.CMD_SET_UART_PARAMS}
    ...    apiformat=${API_MODE_TEXT}
    ...    baud=${lib_if820_device.IF820_DEFAULT_BAUD}
    ...    autobaud=${0}
    ...    autocorrect=${0}
    ...    flow=${flow}
    ...    databits=${8}
    ...    parity=${0}
    ...    stopbits=${1}
    ...    uart_type=${0}
    Fail on error    ${res[0]}

Setup Uarts
    [Arguments]    ${flow}
    # open host uart
    IF820_Device.open    ${settings_comport_IF820_central}    ${lib_if820_device.IF820_DEFAULT_BAUD}    ${flow}
    Sleep    ${1}
    # set flow control on device
    Set Uart Params    ${flow}

Reboot Command
    [Arguments]    ${api_mode}
    ${res} =    IF820_Device.Send And Wait
    ...    command=${ez_system_commands.CMD_REBOOT}
    ...    apiformat=${api_mode}
    Fail on error    ${res[0]}
    ${res} =    IF820_Device.Wait Event    ${ez_system_commands.EVENT_SYSTEM_BOOT}
    Fail on error    ${res[0]}
