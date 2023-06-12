*** Settings ***
Documentation       Basic Commands Test Suite

Library             ..${/}common${/}EzSerialPort.py
Resource            common.robot

Test Setup          Test Setup
Test Timeout        2 minutes

Default Tags        Vela IF820


*** Variables ***
${API_MODE_TEXT}            0
${API_MODE_BINARY}          1
${REBOOT_COUNT}             10
${BOOT_DELAY_SECONDS}       3


*** Test Cases ***
Ping
    Set Tags    L2-70
    Open the connection
    Send Ping
    Close the connection

Query Firmware
    Set Tags    L2-71
    Open the connection
    Query Firmware Version
    Close the connection

Factory Reset
    Set Tags    L2-65
    Open the connection
    Send Factory Reset
    Close the connection

Reboot
    Set Tags    L2-66
    Open the connection
    Reboot the device
    Close the connection
    Sleep    ${BOOT_DELAY_SECONDS}

Reboot Loop Text Mode
    Set Tags    L2-72
    Open the connection
    Reboot Loop
    Close the connection

Reboot Loop Binary Mode
    Set Tags    L2-73
    Open the connection
    Reboot Loop    arg_api_mode=${API_MODE_BINARY}
    Close the connection


*** Keywords ***
Test Setup
    Read Settings File

Open the connection
    EzSerialPort.Open    ${settings_comport_IF820_central}    ${settings_default_baud}

Close the connection
    EzSerialPort.Close

Send Ping
    ${res} =    EzSerialPort.Send And Wait    system_ping
    Fail on error    ${res[0]}

Query Firmware Version
    ${res} =    EzSerialPort.Send And Wait    system_query_firmware_version
    Fail on error    ${res[0]}

Send Factory Reset
    EzSerialPort.Send    system_factory_reset
    #Bug L220D100-19
    #${res} =    EzSerialPort.Wait Event    system_factory_reset_complete
    #Fail on error    ${res}[0]
    ${res} =    EzSerialPort.Wait Event    system_boot
    Fail on error    ${res}[0]
    Sleep    ${BOOT_DELAY_SECONDS}

Reboot the device
    [Arguments]    ${arg_api_mode}=${API_MODE_TEXT}
    # need to ensure this variable is sent as an int in the param
    ${api_mode} =    Convert To Integer    ${arg_api_mode}
    ${res} =    EzSerialPort.Send And Wait    system_reboot    rxtimeout=1    apiformat=${api_mode}
    Fail on error    ${res[0]}
    ${res} =    EzSerialPort.Wait Event    system_boot
    Fail on error    ${res[0]}

Fail on error
    [Arguments]    ${err}
    IF    ${err} != 0    Fail    Response error ${err}

Reboot Loop
    [Timeout]    ${arg_timeout}
    [Arguments]    ${arg_loop_count}=${REBOOT_COUNT}    ${arg_api_mode}=${API_MODE_TEXT}    ${arg_timeout}=60 seconds
    FOR    ${counter}    IN RANGE    ${arg_loop_count}
        TRY
            Reboot the device    ${arg_api_mode}
        EXCEPT    AS    ${err}
            Fail    Loop iteration ${counter+1}: ${err}
        END
        Sleep    ${BOOT_DELAY_SECONDS}
    END
