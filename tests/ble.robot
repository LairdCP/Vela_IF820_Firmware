*** Settings ***
Documentation       BLE Test Suite

Library             ..${/}common${/}EzSerialPort.py    WITH NAME    Peripheral
Library             ..${/}common${/}EzSerialPort.py    WITH NAME    Central
Library             String
Library             Collections
Resource            common.robot

Test Setup          Test Setup
Test Timeout        2 minutes

Default Tags        vela if820


*** Variables ***
${central}                                  ${EMPTY}
${peripheral}                               ${EMPTY}
${DEV_PERIPHERAL}                           Peripheral
${DEV_Central}                              Central
${BOOT_DELAY_SECONDS}                       3
${API_MODE}                                 ${1}
${SLEEP_LEVEL_NORMAL}                       ${1}
${CYSPP_FLAGS_RX_FLOW_CONTROL}              ${0x02}
${COMPANY_ID}                               ${0x0077}
${ADV_MODE}                                 ${2}
${ADV_TYPE}                                 ${3}
${ADV_INTERVAL}                             ${0x40}
${ADV_CHANNELS}                             ${0x07}
${ADV_TIMEOUT}                              ${0}
${ADV_FILTER}                               ${0}
${ADV_FLAGS_CUSTOM_DATA}                    ${0x02}
${ADV_FLAGS_GATT}                           ${0x00}
# Flags, short name my_sensor, VS data uint16 LSB
@{ADV_DATA}
...                                         ${0x02}
...                                         ${0x01}
...                                         ${0x06}
...                                         ${0x0a}
...                                         ${0x08}
...                                         ${0x6d}
...                                         ${0x79}
...                                         ${0x5f}
...                                         ${0x73}
...                                         ${0x65}
...                                         ${0x6e}
...                                         ${0x73}
...                                         ${0x6f}
...                                         ${0x72}
...                                         ${0x05}
...                                         ${0xff}
...                                         ${0x77}
...                                         ${0x00}
...                                         ${0x01}
...                                         ${0x00}
${SCAN_MODE}                                ${2}
${SCAN_FILTER_ACCEPT_ALL}                   ${0}
@{DIRECT_ADDR}                              ${0}    ${0}    ${0}    ${0}    ${0}    ${0}

${GATT_ATTR_TYPE_STRUCTURE}                 ${0}
${GATT_ATTR_TYPE_VALUE}                     ${1}
${GATT_ATTR_PERMISSION_READ}                ${0x02}
${GATT_ATTR_PERMISSION_READ_AUTH_WRITE}     ${0x42}
${GATT_ATTR_PERMISSION_READ_WRITE_ACK}      ${0x0A}
${BATTERY_LEVEL}                            ${95}
${battery_value_handle}                     ${EMPTY}


*** Test Cases ***
BLE Custom Advertiser
    Set Tags    L2-68
    Open the Peripheral connection
    Reboot the Peripheral
    Stop advertising
    Set advertising params    ${ADV_MODE}    ${ADV_FLAGS_CUSTOM_DATA}
    Set advertising data    ${ADV_DATA}
    Start advertising    ${ADV_MODE}    ${ADV_FLAGS_CUSTOM_DATA}
    Open the Central connection
    Reboot the Central
    Scan for custom Peripheral
    Close the Peripheral connection
    Close the Central connection

BLE Custom GATT
    Set Tags    L2-102
    Open the Peripheral connection
    Reboot the Peripheral
    Open the Central connection
    Reboot the Central
    Stop advertising
    Setup Battery Service
    Start advertising    ${ADV_MODE}    ${ADV_FLAGS_GATT}
    Connect to Peripheral
    Read Battery Voltage
    Close the Peripheral connection
    Close the Central connection


*** Keywords ***
Test Setup
    Read Settings File
    ${c}=    Get Library Instance    Central
    ${p}=    Get Library Instance    Peripheral
    Set Global Variable    ${central}    ${c}
    Set Global Variable    ${peripheral}    ${p}

Open the ${dev} connection
    IF    "${dev}" == "${DEV_PERIPHERAL}"
        Peripheral.Open    ${settings_comport_IF820_peripheral}    ${settings_default_baud}
    ELSE
        Central.Open    ${settings_comport_IF820_central}    ${settings_default_baud}
    END
    Set API ${dev} format ${API_MODE}

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

Set advertising params
    [Arguments]    ${mode}    ${flags}
    ${res}=    Peripheral.Send And Wait
    ...    ${peripheral.CMD_GAP_SET_ADV_PARAMETERS}
    ...    mode=${mode}
    ...    type=${ADV_TYPE}
    ...    interval=${ADV_INTERVAL}
    ...    channels=${ADV_CHANNELS}
    ...    high_interval=${ADV_INTERVAL}
    ...    high_duration=${0}
    ...    low_interval=${ADV_INTERVAL}
    ...    low_duration=${0}
    ...    flags=${flags}
    ...    directAddr=${DIRECT_ADDR}
    ...    directAddrType=${0}
    Fail on error    ${res[0]}

Set advertising data
    [Arguments]    ${data}
    ${res}=    Peripheral.Send And Wait
    ...    ${peripheral.CMD_GAP_SET_ADV_DATA}
    ...    data=@{data}
    Fail on error    ${res[0]}

Start advertising
    [Arguments]    ${mode}    ${flags}
    ${res}=    Peripheral.Send And Wait
    ...    ${peripheral.CMD_GAP_START_ADV}
    ...    mode=${mode}
    ...    type=${ADV_TYPE}
    ...    channels=${ADV_CHANNELS}
    ...    high_interval=${ADV_INTERVAL}
    ...    high_duration=${0}
    ...    low_interval=${ADV_INTERVAL}
    ...    low_duration=${0}
    ...    flags=${flags}
    ...    directAddr=${DIRECT_ADDR}
    ...    directAddrType=${0}
    Fail on error    ${res[0]}

Stop advertising
    ${res}=    Peripheral.Send And Wait
    ...    ${peripheral.CMD_GAP_STOP_ADV}
    Fail on error    ${res[0]}

Reboot the ${dev}
    ${res}=    Set Variable    (-1, None)
    IF    "${dev}" == "${DEV_PERIPHERAL}"
        ${res}=    Peripheral.Send And Wait
        ...    ${peripheral.CMD_REBOOT}
        Fail on error    ${res[0]}
        ${res}=    Peripheral.Wait Event
        ...    ${peripheral.EVENT_SYSTEM_BOOT}
        Fail on error    ${res}[0]
        ${resp}=    Set Variable    ${res}[1]
        ${PERIPHERAL_ADDRESS}=    Set Variable    ${resp.payload.address}
        Set Suite Variable    ${PERIPHERAL_ADDRESS}
    ELSE
        ${res}=    Central.Send And Wait
        ...    ${central.CMD_REBOOT}
        Fail on error    ${res[0]}
        ${res}=    Central.Wait Event
        ...    ${central.EVENT_SYSTEM_BOOT}
        Fail on error    ${res[0]}
    END
    Log    ${res}[1]
    Sleep    ${BOOT_DELAY_SECONDS}

Scan for custom Peripheral
    ${res}=    Central.Send And Wait
    ...    ${central.CMD_GAP_START_SCAN}
    ...    mode=${SCAN_MODE}
    ...    interval=${0x100}
    ...    window=${0x100}
    ...    active=${0}
    ...    filter=${SCAN_FILTER_ACCEPT_ALL}
    ...    nodupe=${1}
    ...    timeout=${120}
    Fail on error    ${res[0]}
    WHILE    True
        ${res}=    Central.Wait Event
        ...    ${central.EVENT_GAP_SCAN_RESULT}
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

Setup Battery Service
    # Create battery service descriptor
    ${data}=    Evaluate    bytearray.fromhex('00280F18')
    ${res}=    Peripheral.Send And Wait
    ...    ${peripheral.CMD_GATTS_CREATE_ATTR}
    ...    type=${GATT_ATTR_TYPE_STRUCTURE}
    ...    perm=${GATT_ATTR_PERMISSION_READ}
    ...    length=${4}
    ...    data=${data}
    Fail on error    ${res[0]}
    # Create battery level characteristic descriptor
    ${data}=    Evaluate    bytearray.fromhex('0328121800192A')
    ${res}=    Peripheral.Send And Wait
    ...    ${peripheral.CMD_GATTS_CREATE_ATTR}
    ...    type=${GATT_ATTR_TYPE_STRUCTURE}
    ...    perm=${GATT_ATTR_PERMISSION_READ}
    ...    length=${7}
    ...    data=${data}
    Fail on error    ${res[0]}
    # Create battery level characteristic value descriptor and set value
    ${data}=    Evaluate    bytearray([${BATTERY_LEVEL}])
    ${res}=    Peripheral.Send And Wait
    ...    ${peripheral.CMD_GATTS_CREATE_ATTR}
    ...    type=${GATT_ATTR_TYPE_VALUE}
    ...    perm=${GATT_ATTR_PERMISSION_READ_AUTH_WRITE}
    ...    length=${1}
    ...    data=${data}
    Fail on error    ${res[0]}
    Set Global Variable    ${battery_value_handle}    ${res[1].payload.handle}
    # Create battery level Client Characteristic Configuration descriptor
    ${data}=    Evaluate    bytearray.fromhex('02290000')
    ${res}=    Peripheral.Send And Wait
    ...    ${peripheral.CMD_GATTS_CREATE_ATTR}
    ...    type=${GATT_ATTR_TYPE_STRUCTURE}
    ...    perm=${GATT_ATTR_PERMISSION_READ_WRITE_ACK}
    ...    length=${4}
    ...    data=${data}
    Fail on error    ${res[0]}

Connect to Peripheral
    [Timeout]    20 seconds
    ${packet}=    Set Variable    ${EMPTY}
    ${res}=    Central.Send And Wait
    ...    ${central.CMD_GAP_START_SCAN}
    ...    mode=${SCAN_MODE}
    ...    interval=${0x100}
    ...    window=${0x100}
    ...    active=${0}
    ...    filter=${SCAN_FILTER_ACCEPT_ALL}
    ...    nodupe=${1}
    ...    timeout=${120}
    Fail on error    ${res[0]}
    WHILE    True
        ${res}=    Central.Wait Event
        ...    ${central.EVENT_GAP_SCAN_RESULT}
        Fail on error    ${res}[0]
        ${packet}=    Set Variable    ${res}[1]
        Log    ${packet}
        IF    ${PERIPHERAL_ADDRESS} == ${packet.payload.address}
            Log    Discovered peripheral!
            BREAK
        END
    END
    ${res}=    Central.Send And Wait
    ...    ${central.CMD_GAP_CONNECT}
    ...    address=${PERIPHERAL_ADDRESS}
    ...    type=${packet.payload.address_type}
    ...    interval=${6}
    ...    slave_latency=${0}
    ...    supervision_timeout=${100}
    ...    scan_interval=${0x0100}
    ...    scan_window=${0x0100}
    ...    scan_timeout=${0}

    # Wait for connection to be established
    ${res}=    Central.Wait Event
    ...    ${central.EVENT_GAP_CONNECTED}
    Fail on error    ${res}[0]

Read Battery Voltage
    [Timeout]    20 seconds
    ${res}=    Central.Send And Wait
    ...    ${central.CMD_GATTC_READ_HANDLE}
    ...    conn_handle=${0}
    ...    attr_handle=${battery_value_handle}
    Fail on error    ${res[0]}
    ${res}=    Central.Wait Event
    ...    ${central.EVENT_GATTC_DATA_RECEIVED}
    Fail on error    ${res}[0]
    IF    ${res[1].payload.attr_handle} == ${battery_value_handle}
        IF    ${res[1].payload.data[0]} != ${BATTERY_LEVEL}
            Fail    Battery level is not ${BATTERY_LEVEL}
        END
    ELSE
        Fail    Unexpected attribute handle
    END
