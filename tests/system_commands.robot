*** Settings ***
Documentation       System Command Tests.
...                 Will test system commands on an IF820 device.

Resource            common.robot

Suite Setup         Suite Setup
Suite Teardown      Suite Teardown
Test Timeout        2 minutes

Default Tags        vela if820


*** Variables ***
${MAC_ADDR_LEN}             ${6}
${REBOOT_COUNT}             5
${BOOT_DELAY_SECONDS}       1


*** Test Cases ***
Ping
    Set Tags    PROD-675
    Send Command    ${ez_system_commands.CMD_PING}

Query Firmware
    Set Tags    PROD-684
    Send Command    ${ez_system_commands.CMD_QUERY_FW}

Get MAC Addr
    Set Tags    PROD-690
    Send Command    ${ez_system_commands.CMD_GET_BT_ADDR}

Get Sleep Params
    Set Tags    PROD-688
    Send Command    ${ez_system_commands.CMD_GET_SLEEP_PARAMS}

Get Tx Power
    Set Tags    PROD-687
    Send Command    ${ez_system_commands.CMD_GET_TX_POWER}

Get Transport
    Set Tags    PROD-686
    Send Command    ${ez_system_commands.CMD_GET_TRANSPORT}

Get Uart Params
    Set Tags    PROD-689
    FOR    ${flow}    IN    @{UART_FLOW_TYPES}
        Setup Uarts    ${flow}
        FOR    ${api_mode}    IN    @{API_MODES}
            EZ Send DUT1
            ...    ${ez_system_commands.CMD_GET_UART_PARAMS}
            ...    ${api_mode}
            ...    uart_type=${0}
        END
        EZ Port Close    ${settings_if820_board1}
    END

Factory Reset
    Set Tags    PROD-682
    FOR    ${flow}    IN    @{UART_FLOW_TYPES}
        Setup Uarts    ${flow}
        FOR    ${api_mode}    IN    @{API_MODES}
            EZ Send DUT1
            ...    ${ez_system_commands.CMD_FACTORY_RESET}
            ...    ${api_mode}
            EZ Wait Event DUT1    ${ez_system_commands.EVENT_SYSTEM_BOOT}
        END
        EZ Port Close    ${settings_if820_board1}
    END

Reboot
    Set Tags    PROD-678
    FOR    ${flow}    IN    @{UART_FLOW_TYPES}
        Setup Uarts    ${flow}
        FOR    ${api_mode}    IN    @{API_MODES}
            Reboot Command    ${api_mode}
        END
        EZ Port Close    ${settings_if820_board1}
    END

Reboot Loop
    Set Tags    PROD-699
    FOR    ${api_mode}    IN    @{API_MODES}
        FOR    ${flow}    IN    @{UART_FLOW_TYPES}
            Setup Uarts    ${flow}
            FOR    ${counter}    IN RANGE    ${REBOOT_COUNT}
                Reboot Command    ${api_mode}
                Sleep    ${BOOT_DELAY_SECONDS}
            END
            EZ Port Close    ${settings_if820_board1}
        END
    END


*** Keywords ***
Suite Setup
    Find Boards and Settings
    Init Board    ${settings_if820_board1}
    EZ Port Close    ${settings_if820_board1}

Suite Teardown
    De-Init Board    ${settings_if820_board1}

Send Command
    [Arguments]    ${cmd}
    FOR    ${flow}    IN    @{UART_FLOW_TYPES}
        Setup Uarts    ${flow}
        FOR    ${api_mode}    IN    @{API_MODES}
            EZ Send DUT1    ${cmd}    ${api_mode}
        END
        EZ Port Close    ${settings_if820_board1}
    END

Set Uart Params
    [Arguments]    ${flow}
    EZ Send DUT1
    ...    ${ez_system_commands.CMD_SET_UART_PARAMS}
    ...    ${API_MODE_TEXT}
    ...    baud=${lib_ez_serial_port.IF820_DEFAULT_BAUD}
    ...    autobaud=${0}
    ...    autocorrect=${0}
    ...    flow=${flow}
    ...    databits=${8}
    ...    parity=${0}
    ...    stopbits=${1}
    ...    uart_type=${0}

Setup Uarts
    [Arguments]    ${flow}
    EZ Port Open    ${settings_if820_board1}    ${flow}
    Sleep    ${1}
    Set Uart Params    ${flow}

Reboot Command
    [Arguments]    ${api_mode}
    EZ Send DUT1
    ...    ${ez_system_commands.CMD_REBOOT}
    ...    ${api_mode}
    EZ Wait Event DUT1    ${ez_system_commands.EVENT_SYSTEM_BOOT}
