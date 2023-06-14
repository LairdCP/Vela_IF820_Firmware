*** Settings ***
Documentation       SPP tests with Vela IF820 devices.

Library             OperatingSystem
Library             ..${/}common${/}PicoProbe.py    WITH NAME    PP_Central
Library             ..${/}common${/}BT900SerialPort.py    WITH NAME    BT900_Peripheral
Library             ..${/}common${/}EzSerialPort.py    WITH NAME    IF820_Central
Library             ..${/}common${/}SerialPort.py    WITH NAME    IF820_SPP
Library             Collections
Resource            common.robot

Test Setup          Test Setup
Test Teardown       Test Teardown
Test Timeout        2 minute

Default Tags        vela if820


*** Variables ***
${MAC_ADDR_LEN}                 ${6}
${INQUIRY_DURATION_SEC}         ${15}
${WAIT_FOR_RESPONSE_TIME_MS}    200ms
${peripheral_address}           ${EMPTY}
${lib_bt900_peripheral}         ${EMPTY}
${lib_if820_central}            ${EMPTY}
${lib_pp_central}               ${EMPTY}
${bt900_peripheral_device}      ${EMPTY}
${ez_system_commands}           ${EMPTY}
${ez_bluetooth_commands}        ${EMPTY}
${ez_smp_commands}              ${EMPTY}
${SPP_DATA}                     abcdefghijklmnop
${OK}                           OK


*** Test Cases ***
SPP IF820->BT900 Binary Mode
    Set Tags    L2-118
    ${rx_spp_data} =    SPP Test    ${API_MODE_BINARY}
    Builtin.Should Not Be Empty    ${rx_spp_data[0]}
    Builtin.Should Not Be Empty    ${rx_spp_data[1]}

SPP IF820->BT900 Text Mode
    Set Tags    L2-120
    ${rx_spp_data} =    SPP Test    ${API_MODE_TEXT}
    Builtin.Should Not Be Empty    ${rx_spp_data[0]}
    Builtin.Should Not Be Empty    ${rx_spp_data[1]}


*** Keywords ***
Test Setup
    Read Settings File
    IF820_Central.Set Queue Timeout    ${CLEAR_QUEUE_TIMEOUT_SEC}

    # Get instances of python libraries needed
    ${lib_bt900_peripheral} =    Builtin.Get Library Instance    BT900_Peripheral
    ${lib_if820_central} =    Builtin.Get Library Instance    IF820_Central
    ${lib_pp_central} =    Builtin.Get Library Instance    PP_Central
    Set Global Variable    ${lib_bt900_peripheral}    ${lib_bt900_peripheral}
    Set Global Variable    ${lib_if820_central}    ${lib_if820_central}
    Set Global Variable    ${lib_pp_central}    ${lib_pp_central}
    ${bt900_peripheral_device} =    BT900_Peripheral.Get Device
    Set Global Variable    ${bt900_peripheral_device}    ${bt900_peripheral_device}
    ${ez_system_commands} =    IF820_Central.Get Sys Commands
    ${ez_bluetooth_commands} =    IF820_Central.Get Bluetooth Commands
    ${ez_smp_commands} =    IF820_Central.Get Smp Commands
    Set Global Variable    ${ez_system_commands}    ${ez_system_commands}
    Set Global Variable    ${ez_bluetooth_commands}    ${ez_bluetooth_commands}
    Set Global Variable    ${ez_smp_commands}    ${ez_smp_commands}

    # Open the Pico Probe used on the Central so we can terminate SPP mode via a gpio pin
    Open Pico Probe

    # open the serial ports for devices in test
    IF820_Central.close
    Call Method    ${bt900_peripheral_device}    close
    Sleep    ${1}
    IF820_Central.open    ${settings_comport_IF820_central}    ${lib_if820_central.IF820_DEFAULT_BAUD}
    Call Method
    ...    ${bt900_peripheral_device}
    ...    open
    ...    ${settings_comport_BT900_peripheral}
    ...    ${lib_bt900_peripheral.BT900_DEFAULT_BAUD}

    # IF820 Factory Reset
    IF820_Central.Clear Rx Queue
    ${response} =    IF820_Central.Send And Wait    ${ez_system_commands.CMD_FACTORY_RESET}
    Fail on error    ${response[0]}
    ${response} =    IF820_central.Wait Event    ${ez_system_commands.EVENT_SYSTEM_BOOT}
    Log    ${response}

Test Teardown
    Disconnect BT900
    Call Method    ${bt900_peripheral_device}    close
    IF820_Central.close
    Close Pico Probe
    Log    "Test Teardown Complete"

Disconnect BT900
    Call Method    ${bt900_peripheral_device}    send    ${lib_bt900_peripheral.BT900_SPP_DISCONNECT}
    Sleep    ${0.5}
    Call Method    ${bt900_peripheral_device}    send    ${lib_bt900_peripheral.BT900_EXIT}
    Sleep    ${0.5}

Open Pico Probe
    PP_Central.Open    ${settings_id_pp_central}
    PP_Central.Gpio To Input    ${lib_pp_central.GPIO_19}

Close Pico Probe
    # Setting high will terminate SPP
    PP_Central.Gpio To Output    ${lib_pp_central.GPIO_19}
    PP_Central.Gpio To Output High    ${lib_pp_central.GPIO_19}
    PP_Central.Gpio To Input    ${lib_pp_central.GPIO_19}
    PP_Central.Close

SPP Test
    [Arguments]    ${api_format}

    ${peripheral_address} =    BT900_Peripheral.Get Bt900 Bluetooth Mac

    ${response} =    BT900_Peripheral.Send And Wait For Response    ${lib_bt900_peripheral.BT900_CMD_MODE}
    Should Contain    ${response[1]}    ${OK}

    # bt900 delete all previous bonds
    ${response} =    BT900_Peripheral.Send And Wait For Response    ${lib_bt900_peripheral.BT900_CMD_BTC_BOND_DEL}
    Should Contain    ${response[1]}    ${OK}

    # bt900 set io cap
    ${response} =    BT900_Peripheral.Send And Wait For Response    ${lib_bt900_peripheral.BT900_CMD_BTC_IOCAP}
    Should Contain    ${response[1]}    ${OK}

    # bt900 set pairable
    ${response} =    BT900_Peripheral.Send And Wait For Response    ${lib_bt900_peripheral.BT900_CMD_SET_BTC_PAIRABLE}
    Should Contain    ${response[1]}    ${OK}

    # bt900 set connectable
    ${response} =    BT900_Peripheral.Send And Wait For Response
    ...    ${lib_bt900_peripheral.BT900_CMD_SET_BTC_CONNECTABLE}
    Should Contain    ${response[1]}    ${OK}

    # bt900 set discoverable
    ${response} =    BT900_Peripheral.Send And Wait For Response
    ...    ${lib_bt900_peripheral.BT900_CMD_SET_BTC_DISCOVERABLE}
    Should Contain    ${response[1]}    ${OK}

    # bt900 open spp port
    ${response} =    BT900_Peripheral.Send And Wait For Response    ${lib_bt900_peripheral.BT900_CMD_SPP_OPEN}
    Should Contain    ${response[1]}    ${OK}

    # IF820(central) connect to BT900 (peripheral)
    Reverse List    ${peripheral_address[1]}
    ${response} =    IF820_central.Send And Wait    command=${ez_bluetooth_commands.CMD_CONNECT}
    ...    apiformat=${api_format}
    ...    address=${peripheral_address[1]}
    ...    type=${1}
    Fail if not equal    ${response[0]}    ${0}
    ${conn_handle} =    Builtin.Get Variable Value    ${response[1].payload.conn_handle}
    Log    ${conn_handle}

    # IF820 Event (Text Info contains "P")
    ${response} =    IF820_central.Wait Event    event=${ez_smp_commands.EVENT_SMP_PAIRING_REQUESTED}
    Fail if not equal    ${response[0]}    ${0}

    # bt900 event (Text Info contains "Pair Req")
    ${bt900_event} =    BT900_Peripheral.Wait For Response
    ...    rx_timeout_sec=${lib_bt900_peripheral.DEFAULT_WAIT_TIME_SEC}
    ${string_event} =    BT900_Peripheral.Response To String    ${bt900_event}
    Should Contain    ${string_event}    ${lib_bt900_peripheral.BT900_PAIR_REQ}
    Call Method    ${bt900_peripheral_device}    clear_rx_queue

    # bt900 set pairable (Response is "OK")
    Log    Send Pair Response
    ${response} =    BT900_Peripheral.Send And Wait For Response    ${lib_bt900_peripheral.BT900_CMD_BTC_PAIR_RESPONSE}
    Should Contain    ${response[1]}    ${OK}
    Log    ${response[1]}

    # IF820 Event (Text Info contains "PR")
    Log    Wait for PR
    ${response} =    IF820_central.Wait Event    event=${ez_smp_commands.EVENT_SMP_PAIRING_RESULT}
    Log    ${response}
    Fail if not equal    ${response[0]}    ${0}

    # bt900 event (Text Info contains "Pair Result")
    Log    Wait for Pair Result
    ${bt900_event} =    BT900_Peripheral.Wait For Response
    ...    rx_timeout_sec=${lib_bt900_peripheral.DEFAULT_WAIT_TIME_SEC}
    Log    ${bt900_event}
    ${string_event} =    BT900_Peripheral.Response To String    ${bt900_event}
    Log    ${string_event}
    Should Contain    ${string_event}    ${lib_bt900_peripheral.BT900_PAIR_RESULT}

    # IF820 Event (Text Info contains "ENC")
    ${response} =    IF820_central.Wait Event    event=${ez_smp_commands.EVENT_SMP_ENCRYPTION_STATUS}
    Fail if not equal    ${response[0]}    ${0}

    # IF820 Event
    ${response} =    IF820_central.Wait Event    event=${ez_bluetooth_commands.EVENT_BT_CONNECTED}
    Fail if not equal    ${response[0]}    ${0}

    # bt900 event
    Log    Wait for SPP Connect
    ${bt900_event} =    BT900_Peripheral.Wait For Response    rx_timeout_sec=${10}
    Log    ${bt900_event}
    ${string_event} =    BT900_Peripheral.Response To String    ${bt900_event}
    Log    ${string_event}
    Should Contain    ${string_event}    ${lib_bt900_peripheral.BT900_SPP_CONNECT}
    # Call Method    ${bt900_peripheral_device}    clear_rx_queue

    # The two devices are connected.    We can now send data on SPP.
    # For the IF820 we need to close the ez_serial port instance and
    # then open a base serial port so we can send raw data with no processing.
    IF820_central.close
    Log    ${settings_comport_IF820_central}
    Log    ${lib_if820_central.IF820_DEFAULT_BAUD}
    IF820_SPP.open    ${settings_comport_IF820_central}    ${lib_if820_central.IF820_DEFAULT_BAUD}

    # send data from IF820 -> BT900
    Log    Send BT900->IF820
    ${length} =    Get Length    ${SPP_DATA}
    FOR    ${index}    IN RANGE    ${length}
        Log    ${SPP_DATA}[${index}]
        IF820_SPP.Send    ${SPP_DATA}[${index}]
        Sleep    20ms
    END

    # read data from BT900 Rx Queue
    Sleep    ${1}
    ${rx_data} =    Call Method    ${bt900_peripheral_device}    get_rx_queue
    ${utf8_string_bt900} =    UTF8 Bytes to String    ${rx_data}
    Log    rx_data = ${utf8_string_bt900}

    # send data from BT900 -> IF820
    Log    Send IF820->BT900
    ${data_to_send} =    Builtin.Catenate
    ...    ${lib_bt900_peripheral.BT900_SPP_WRITE_PREFIX}
    ...    ${SPP_DATA}
    ...    ${lib_bt900_peripheral.CR}
    ${response} =    BT900_Peripheral.Send And Wait For Response    ${data_to_send}
    Should Contain    ${response[1]}    ${OK}
    Log    ${response[1]}

    ${rx_data} =    IF820_SPP.Get Rx Queue
    ${utf8_string_if820} =    UTF8 Bytes to String    ${rx_data}
    Log    rx_data = ${utf8_string_if820}
    RETURN    ${utf8_string_bt900}, ${utf8_string_if820}
