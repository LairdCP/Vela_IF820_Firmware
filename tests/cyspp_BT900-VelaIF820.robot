*** Settings ***
Documentation       SPP tests with Vela IF820 devices.

Library             OperatingSystem
Library             ..${/}common${/}DvkProbe.py    WITH NAME    PP_Peripheral
Library             ..${/}common${/}BT900SerialPort.py    WITH NAME    BT900_Central
Library             ..${/}common${/}EzSerialPort.py    WITH NAME    IF820_Peripheral
Library             ..${/}common${/}SerialPort.py    WITH NAME    IF820_CYSPP
Library             ..${/}common${/}CommonLib.py    WITH NAME    Common_Lib
Library             Collections
Resource            common.robot

Test Setup          Test Setup
Test Teardown       Test Teardown
Test Timeout        1 minute

Default Tags        vela if820


*** Variables ***
${MAC_ADDR_LEN}                 ${6}
${WAIT_FOR_RESPONSE_TIME_MS}    200ms
${peripheral_address}           ${EMPTY}
${lib_bt900_central}            ${EMPTY}
${lib_if820_peripheral}         ${EMPTY}
${lib_pp_peripheral}            ${EMPTY}
${bt900_central_device}         ${EMPTY}
${ez_system_commands}           ${EMPTY}
${ez_cyspp_commands}            ${EMPTY}
${ez_gatt_server_commands}      ${EMPTY}
${ez_gap_commands}              ${EMPTY}
${CYSPP_DATA}                   abcdefghijklmnop
${OK}                           OK


*** Test Cases ***
SPP BT900->IF820 Binary Mode
    Set Tags    L2-154
    ${rx_spp_data} =    CYSPP Test    ${API_MODE_BINARY}
    Builtin.Should Not Be Empty    ${rx_spp_data[0]}
    Builtin.Should Not Be Empty    ${rx_spp_data[1]}

SPP BT900->IF820 Text Mode
    Set Tags    L2-152
    ${rx_spp_data} =    CYSPP Test    ${API_MODE_TEXT}
    Builtin.Should Not Be Empty    ${rx_spp_data[0]}
    Builtin.Should Not Be Empty    ${rx_spp_data[1]}


*** Keywords ***
Test Setup
    Read Settings File
    IF820_Peripheral.Set Queue Timeout    ${CLEAR_QUEUE_TIMEOUT_SEC}

    # Get instances of python libraries needed
    ${lib_bt900_central} =    Builtin.Get Library Instance    BT900_Central
    ${lib_if820_peripheral} =    Builtin.Get Library Instance    IF820_Peripheral
    ${lib_pp_peripheral} =    Builtin.Get Library Instance    PP_Peripheral
    Set Global Variable    ${lib_bt900_central}    ${lib_bt900_central}
    Set Global Variable    ${lib_if820_peripheral}    ${lib_if820_peripheral}
    Set Global Variable    ${lib_pp_peripheral}    ${lib_pp_peripheral}
    ${bt900_central_device} =    BT900_Central.Get Device
    Set Global Variable    ${bt900_central_device}    ${bt900_central_device}
    ${ez_system_commands} =    IF820_Peripheral.Get Sys Commands
    ${ez_cyspp_commands} =    IF820_Peripheral.Get Cyspp Commands
    ${ez_gatt_server_commands} =    IF820_Peripheral.Get Gatt Server Commands
    ${ez_gap_commands} =    IF820_Peripheral.Get Gap Commands
    Set Global Variable    ${ez_system_commands}    ${ez_system_commands}
    Set Global Variable    ${ez_cyspp_commands}    ${ez_cyspp_commands}
    Set Global Variable    ${ez_gatt_server_commands}    ${ez_gatt_server_commands}
    Set Global Variable    ${ez_gap_commands}    ${ez_gap_commands}

    # Open the Pico Probe used on the Central so we can terminate SPP mode via a gpio pin
    Open Pico Probe

    # open the serial ports for devices in test
    IF820_Peripheral.close
    Call Method    ${bt900_central_device}    close
    Sleep    ${1}
    IF820_Peripheral.open    ${settings_comport_IF820_peripheral}    ${lib_if820_peripheral.IF820_DEFAULT_BAUD}
    Call Method
    ...    ${bt900_central_device}
    ...    open
    ...    ${settings_comport_BT900_central}
    ...    ${lib_bt900_central.BT900_DEFAULT_BAUD}

    Sleep    ${1}

    # IF820 Factory Reset
    IF820_Peripheral.Clear Rx Queue
    ${response} =    IF820_Peripheral.Send And Wait    ${ez_system_commands.CMD_FACTORY_RESET}
    Fail on error    ${response[0]}
    ${response} =    IF820_Peripheral.Wait Event    ${ez_system_commands.EVENT_SYSTEM_BOOT}
    Fail on error    ${response[0]}

Test Teardown
    Disconnect BT900
    Call Method    ${bt900_central_device}    close
    IF820_Peripheral.close
    Close Pico Probe
    Log    "Test Teardown Complete"

Disconnect BT900
    Call Method    ${bt900_central_device}    send    ${lib_bt900_central.BT900_GATTC_CLOSE}
    Sleep    ${0.5}
    Call Method    ${bt900_central_device}    send    ${lib_bt900_central.BT900_CYSPP_DISCONNECT}
    Sleep    ${0.5}
    Call Method    ${bt900_central_device}    send    ${lib_bt900_central.BT900_EXIT}
    Sleep    ${0.5}

Open Pico Probe
    PP_Peripheral.Open    ${settings_id_pp_peripheral}
    PP_Peripheral.Gpio To Output    ${lib_pp_peripheral.GPIO_19}
    PP_Peripheral.Gpio To Output High    ${lib_pp_peripheral.GPIO_19}
    PP_Peripheral.Gpio To Input    ${lib_pp_peripheral.GPIO_19}

Close Pico Probe
    # Setting high will terminate SPP
    PP_Peripheral.Gpio To Output    ${lib_pp_peripheral.GPIO_19}
    PP_Peripheral.Gpio To Output High    ${lib_pp_peripheral.GPIO_19}
    PP_Peripheral.Gpio To Input    ${lib_pp_peripheral.GPIO_19}
    PP_Peripheral.Close

CYSPP Test
    [Arguments]    ${api_format}

    ${resp} =    IF820_Peripheral.Send And Wait
    ...    command=${ez_gap_commands.CMD_GAP_STOP_ADV}
    ...    api_format=${api_format}
    Fail on error    ${resp[0]}

    ${resp} =    IF820_Peripheral.Send And Wait
    ...    command=${ez_system_commands.CMD_GET_BT_ADDR}
    ...    apiformat=${api_format}
    Fail on error    ${resp[0]}
    ${peripheral_address} =    Builtin.Get Variable Value    ${resp[1].payload.address}
    Log    ${peripheral_address}
    ${str_mac} =    Common_Lib.If820 Mac Addr Response To Mac As String    ${peripheral_address}
    Log    ${str_mac}
    ${str_mac} =    Set Variable    01${str_mac}

    ${response} =    BT900_Central.Send And Wait For Response    ${lib_bt900_central.BT900_CMD_MODE}
    Should Contain    ${response[1]}    ${OK}

    # if820 advertise
    ${resp} =    IF820_Peripheral.Send And Wait
    ...    command=${ez_gap_commands.CMD_GAP_START_ADV}
    ...    api_format=${api_format}
    ...    mode=${2}
    ...    type=${3}
    ...    channels=${7}
    ...    high_interval=${48}
    ...    high_duration=${30}
    ...    low_interval=${2048}
    ...    low_duration=${60}
    ...    flags=${0}
    ...    directAddr=${0}
    ...    directAddrType=${0}
    Fail on error    ${resp[0]}

    # bt900 cyspp connect
    # note:    the bt900 central could scan for devices and pick out the appropriate device to connect to.
    # however for simplicity since we already know its address we will skip that step and just connect.
    Log    ${lib_bt900_central.BT900_CYSPP_CONNECT}
    ${connect_command} =    Set Variable
    ...    ${lib_bt900_central.BT900_CYSPP_CONNECT}${str_mac} 50 30 30 50 ${lib_bt900_central.CR}
    ${response} =    BT900_Central.Send And Wait For Response    ${connect_command}
    Should Contain    ${response[1]}    ${OK}

    # IF820 Event (Text Info contains "C" for connect)
    ${response} =    IF820_Peripheral.Wait Event    event=${ez_gap_commands.EVENT_GAP_CONNECTED}
    Fail if not equal    ${response[0]}    ${0}

    # IF820 Event (Text Info contains "CU" for connection updated)
    ${response} =    IF820_Peripheral.Wait Event    event=${ez_gap_commands.EVENT_GAP_CONNECTION_UPDATED}
    Fail if not equal    ${response[0]}    ${0}

    # bt900 open gattc
    ${response} =    BT900_Central.Send And Wait For Response    ${lib_bt900_central.BT900_GATTC_OPEN}
    Should Contain    ${response[1]}    ${OK}

    # bt900 enable notifications
    ${response} =    BT900_Central.Send And Wait For Response    ${lib_bt900_central.BT900_ENABLE_CYSPP_NOT}
    Should Contain    ${response[1]}    ${OK}

    # IF820 Event (Text Info contains "W" for gatts data written)
    ${response} =    IF820_Peripheral.Wait Event    event=${ez_gatt_server_commands.EVENT_GATTS_DATA_WRITTEN}
    Fail if not equal    ${response[0]}    ${0}

    # The two devices are connected.    We can now send data on CYSPP.
    # For the IF820 we need to close the ez_serial port instance and
    # then open a base serial port so we can send raw data with no processing.
    IF820_Peripheral.close
    IF820_CYSPP.open    ${settings_comport_IF820_peripheral}    ${lib_if820_peripheral.IF820_DEFAULT_BAUD}

    # send data from IF820 -> BT900
    Log    Send IF820->BT900
    ${length} =    Get Length    ${CYSPP_DATA}
    FOR    ${index}    IN RANGE    ${length}
        Log    ${CYSPP_DATA}[${index}]
        IF820_CYSPP.Send    ${CYSPP_DATA}[${index}]
        Sleep    20ms
    END

    # read data from BT900 Rx Queue
    Sleep    ${1}
    ${rx_data} =    Call Method    ${bt900_central_device}    get_rx_queue
    ${utf8_string_bt900} =    UTF8 Bytes to String    ${rx_data}
    Log    rx_data = ${utf8_string_bt900}

    # send data from BT900 -> IF820
    Log    Send BT900->IF820
    ${data_to_send} =    Builtin.Catenate
    ...    ${lib_bt900_central.BT900_CYSPP_WRITE_DATA_STRING}
    ...    ${CYSPP_DATA}
    ...    ${lib_bt900_central.CR}
    ${response} =    BT900_Central.Send And Wait For Response    ${data_to_send}
    Log    ${response[1]}

    # read data from IF820 Rx Queue
    ${rx_data} =    IF820_CYSPP.Get Rx Queue
    ${utf8_string_if820} =    UTF8 Bytes to String    ${rx_data}
    Log    rx_data = ${utf8_string_if820}
    RETURN    ${utf8_string_bt900}, ${utf8_string_if820}
