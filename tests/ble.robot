*** Settings ***
Documentation       BLE Test Suite

Library             ..${/}common${/}EzSerialPort.py    WITH NAME    Peripheral
Library             ..${/}common${/}EzSerialPort.py    WITH NAME    Central
Library             String
Library             Collections

Test Timeout        2 minutes

Default Tags        Vela IF820


*** Variables ***
${PERIPHERAL_COM_PORT}              /dev/cu.usbmodem334203
${CENTRAL_COM_PORT}                 /dev/cu.usbmodem334303
${DEV_PERIPHERAL}                   Peripheral
${DEV_Central}                      Central
${BAUD_RATE}                        ${115200}
${BOOT_DELAY_SECONDS}               3
${API_MODE_TEXT}                    ${0}
${RX_TIMEOUT}                       ${1}
${SLEEP_LEVEL_NORMAL}               ${1}
${CYSPP_FLAGS_RX_FLOW_CONTROL}      ${0x02}
${COMPANY_ID}                       ${0x0077}
${ADV_MODE}                         ${2}
${ADV_TYPE}                         ${3}
${ADV_INTERVAL}                     ${1600}
${ADV_CHANNELS}                     ${0x07}
${ADV_TIMEOUT}                      ${0}
${ADV_FILTER}                       ${0}
${ADV_FLAGS_CUSTOM_DATA}            ${0x02}
# Short name my_sensor, VS data uint16 LSB
@{ADV_DATA}
...                                 ${0x0a}
...                                 ${0x08}
...                                 ${0x6d}
...                                 ${0x79}
...                                 ${0x5f}
...                                 ${0x73}
...                                 ${0x65}
...                                 ${0x6e}
...                                 ${0x73}
...                                 ${0x6f}
...                                 ${0x72}
...                                 ${0x05}
...                                 ${0xff}
...                                 ${0x77}
...                                 ${0x00}
...                                 ${0x01}
...                                 ${0x00}
${SCAN_MODE_GENERAL_DISCOVERY}      ${2}
${SCAN_FILTER_ACCEPT_ALL}           ${0}


*** Test Cases ***
BLE Custom Advertiser
    Set Tags    L2VV-31
    Open the Peripheral connection
    Reboot the Peripheral
    Stop advertising
    Disable CYSPP
    Set advertising params
    Set advertising data
    Start advertising
    Open the Central connection
    Reboot the Central
    Scan for custom Peripheral
    Close the Peripheral connection
    Close the Central connection


*** Keywords ***
Open the ${dev} connection
    IF    "${dev}" == "${DEV_PERIPHERAL}"
        Peripheral.Open    ${PERIPHERAL_COM_PORT}    ${BAUD_RATE}
    ELSE
        Central.Open    ${CENTRAL_COM_PORT}    ${BAUD_RATE}
    END
    Set API ${dev} format ${API_MODE_TEXT}

Close the ${dev} connection
    IF    "${dev}" == "${DEV_PERIPHERAL}"
        Peripheral.Close
    ELSE
        Central.Close
    END

Set API ${dev} format ${api}
    IF    "${dev}" == "${DEV_PERIPHERAL}"
        Peripheral.Set Api Format    ${api}
    ELSE
        Central.Set Api Format    ${api}
    END

Fail on error
    [Arguments]    ${err}
    ${err}=    Convert To Hex    ${err}    prefix=0x
    IF    ${err} != 0    Fail    Response error ${err}

Disable CYSPP
    ${res}=    Peripheral.Send And Wait
    ...    p_cyspp_set_parameters
    ...    rxtimeout=${RX_TIMEOUT}
    ...    enable=${0}
    ...    role=${0}
    ...    company=${COMPANY_ID}
    ...    local_key=${0}
    ...    remote_key=${0}
    ...    remote_mask=${0}
    ...    sleep_level=${SLEEP_LEVEL_NORMAL}
    ...    server_security=${0}
    ...    client_flags=${CYSPP_FLAGS_RX_FLOW_CONTROL}
    Fail on error    ${res[0]}

Set advertising params
    ${res}=    Peripheral.Send And Wait
    ...    gap_set_adv_parameters
    ...    rxtimeout=${RX_TIMEOUT}
    ...    mode=${ADV_MODE}
    ...    type=${ADV_TYPE}
    ...    interval=${ADV_INTERVAL}
    ...    channels=${ADV_CHANNELS}
    ...    filter=${0x0800}
    ...    timeout=${ADV_TIMEOUT}
    ...    flags=${ADV_FLAGS_CUSTOM_DATA}
    Fail on error    ${res[0]}

Set advertising data
    ${res}=    Peripheral.Send And Wait
    ...    gap_set_adv_data
    ...    rxtimeout=${RX_TIMEOUT}
    ...    data=@{ADV_DATA}
    Fail on error    ${res[0]}

Start advertising
    ${res}=    Peripheral.Send And Wait
    ...    gap_start_adv
    ...    rxtimeout=${RX_TIMEOUT}
    ...    mode=${ADV_MODE}
    ...    type=${ADV_TYPE}
    ...    interval=${ADV_INTERVAL}
    ...    channels=${ADV_CHANNELS}
    ...    filter=${ADV_FILTER}
    ...    timeout=${ADV_TIMEOUT}
    Fail on error    ${res[0]}

Stop advertising
    ${res}=    Peripheral.Send And Wait
    ...    gap_stop_adv
    ...    rxtimeout=${RX_TIMEOUT}
    Fail on error    ${res[0]}
    ${res}=    Peripheral.Wait Event
    ...    gap_adv_state_changed
    Fail on error    ${res[0]}

Reboot the ${dev}
    ${res}=    Set Variable    (-1, None)
    IF    "${dev}" == "${DEV_PERIPHERAL}"
        ${res}=    Peripheral.Send And Wait
        ...    system_reboot
        ...    rxtimeout=${RX_TIMEOUT}
        Fail on error    ${res[0]}
        ${res}=    Peripheral.Wait Event
        ...    system_boot
        Fail on error    ${res}[0]
        ${resp}=    Set Variable    ${res}[1]
        ${PERIPHERAL_ADDRESS}=    Set Variable    ${resp.payload.address}
        Set Suite Variable    ${PERIPHERAL_ADDRESS}
    ELSE
        ${res}=    Central.Send And Wait
        ...    system_reboot
        ...    rxtimeout=${RX_TIMEOUT}
        Fail on error    ${res[0]}
        ${res}=    Central.Wait Event
        ...    system_boot
        Fail on error    ${res[0]}
    END
    Log    ${res}[1]
    Sleep    ${BOOT_DELAY_SECONDS}

Scan for custom Peripheral
    ${res}=    Central.Send And Wait
    ...    gap_start_scan
    ...    rxtimeout=${RX_TIMEOUT}
    ...    mode=${SCAN_MODE_GENERAL_DISCOVERY}
    ...    interval=${0x100}
    ...    window=${0x100}
    ...    active=${0}
    ...    filter=${SCAN_FILTER_ACCEPT_ALL}
    ...    nodupe=${1}
    ...    timeout=${0}
    Fail on error    ${res[0]}
    WHILE    True
        ${res}=    Central.Wait Event
        ...    gap_scan_result
        Fail on error    ${res}[0]
        ${packet}=    Set Variable    ${res}[1]
        Log    ${packet}
        IF    ${PERIPHERAL_ADDRESS} == ${packet.payload.address}
            Log    Discovered peripheral!
            ${received_data}=    Set Variable    ${packet.payload.data}
            FOR    ${index}    ${e}    IN ENUMERATE    @{ADV_DATA}
                IF    ${e} != ${received_data}[${index}]
                    Fail    Advertising data does not match!
                END
            END
            BREAK
        END
    END
