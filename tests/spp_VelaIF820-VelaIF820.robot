*** Settings ***
Documentation       SPP tests with Vela IF820 devices.

Library             ..${/}common${/}PicoProbe.py    WITH NAME    PP_Peripheral
Library             ..${/}common${/}PicoProbe.py    WITH NAME    PP_Central
Library             ..${/}common${/}EzSerialPort.py    WITH NAME    IF820_Central
Library             ..${/}common${/}EzSerialPort.py    WITH NAME    IF820_Peripheral
Library             ..${/}common${/}SerialPort.py    WITH NAME    IF820_Central_SPP
Library             ..${/}common${/}SerialPort.py    WITH NAME    IF820_Peripheral_SPP
Resource            common.robot

Test Setup          Test Setup
Test Teardown       Test Teardown
Test Timeout        2 minute

Default Tags        vela if820


*** Variables ***
${DEV_CENTRAL}                  Central
${DEV_PERIPHERAL}               Peripheral
${MAC_ADDR_LEN}                 ${6}
${INQUIRY_DURATION_SEC}         ${15}
${FLAG_INQUIRY_NAME}            ${1}
${Connection_Handle}            0
${SPP_DATA}                     abcdefghijklmnop
${peripheral_address}           ${EMPTY}
${lib_if820_central}            ${EMPTY}
${lib_if820_peripheral}         ${EMPTY}
${lib_spp_central}              ${EMPTY}
${lib_spp_peripheral}           ${EMPTY}
${lib_pp_central}               ${EMPTY}
${lib_pp_peripheral}            ${EMPTY}
${bt900_peripheral_device}      ${EMPTY}
${ez_system_commands}           ${EMPTY}
${ez_bluetooth_commands}        ${EMPTY}


*** Test Cases ***
Ping
    ${res} =    IF820_Central.Send And Wait    ${ez_system_commands.CMD_PING}
    Fail on error    ${res[0]}
    ${res} =    IF820_Peripheral.Send And Wait    ${ez_system_commands.CMD_PING}
    Fail on error    ${res[0]}

SPP Test Binary Mode
    ${rx_spp_data} =    SPP Test    ${API_MODE_BINARY}
    Builtin.Should Be Equal    ${rx_spp_data}    ${SPP_DATA}

Spp Test Text Mode
    ${rx_spp_data} =    SPP Test    ${API_MODE_TEXT}
    Builtin.Should Be Equal    ${rx_spp_data}    ${SPP_DATA}


*** Keywords ***
Test Setup
    Read Settings File
    IF820_Central.Set Queue Timeout    ${CLEAR_QUEUE_TIMEOUT_SEC}
    IF820_Peripheral.Set Queue Timeout    ${CLEAR_QUEUE_TIMEOUT_SEC}

    #Get instances of python libraries needed
    ${lib_if820_central} =    Builtin.Get Library Instance    IF820_Central
    ${lib_if820_peripheral} =    Builtin.Get Library Instance    IF820_Peripheral
    ${lib_pp_central} =    Builtin.Get Library Instance    PP_Central
    ${lib_pp_peripheral} =    Builtin.Get Library Instance    PP_Peripheral
    ${lib_spp_central} =    Builtin.Get Library Instance    IF820_Central_SPP
    ${lib_spp_peripheral} =    Builtin.Get Library Instance    IF820_Peripheral_SPP
    Set Global Variable    ${lib_if820_central}    ${lib_if820_central}
    Set Global Variable    ${lib_if820_peripheral}    ${lib_if820_peripheral}
    Set Global Variable    ${lib_spp_central}    ${lib_spp_central}
    Set Global Variable    ${lib_spp_peripheral}    ${lib_spp_peripheral}
    Set Global Variable    ${lib_pp_central}    ${lib_pp_central}
    Set Global Variable    ${lib_pp_peripheral}    ${lib_pp_peripheral}

    Open Pico Probes

    ${ez_system_commands} =    IF820_Central.Get Sys Commands
    ${ez_bluetooth_commands} =    IF820_Central.Get Bluetooth Commands
    Set Global Variable    ${ez_system_commands}    ${ez_system_commands}
    Set Global Variable    ${ez_bluetooth_commands}    ${ez_bluetooth_commands}

    ${fw_ver_central} =    Get Pico Probe Firmware Version    ${DEV_CENTRAL}
    Log    ${fw_ver_central}
    ${fw_ver_peripheral} =    Get Pico Probe Firmware Version    ${DEV_PERIPHERAL}
    Log    ${fw_ver_peripheral}

    #open the serial ports for devices in test
    IF820_Central.Close
    IF820_Peripheral.Close
    Sleep    ${1}
    IF820_Central.open    ${settings_comport_IF820_central}    ${lib_if820_central.IF820_DEFAULT_BAUD}
    IF820_Peripheral.open    ${settings_comport_IF820_peripheral}    ${lib_if820_peripheral.IF820_DEFAULT_BAUD}
    Sleep    ${1}

    #IF820 Factory Reset
    IF820_Central.send    ${ez_system_commands.CMD_FACTORY_RESET}
    ${response} =    IF820_central.Wait Event    ${ez_system_commands.EVENT_SYSTEM_BOOT}

    IF820_Peripheral.send    ${ez_system_commands.CMD_FACTORY_RESET}
    ${response} =    IF820_Peripheral.Wait Event    ${ez_system_commands.EVENT_SYSTEM_BOOT}

Test Teardown
    Close Pico Probes
    IF820_Central.close
    IF820_Peripheral.close
    Log    "Test Teardown Complete"

Get Peripheral Bluetooth Address
    [Arguments]    ${api_format}
    ${resp} =    IF820_Peripheral.Send And Wait
    ...    command=${ez_system_commands.CMD_GET_BT_ADDR}
    ...    api_format=${api_format}
    Fail on error    ${resp[0]}
    ${peripheral_address} =    Builtin.Get Variable Value    ${resp[1].payload.address}
    RETURN    ${peripheral_address}

Connect to Peripheral
    [Documentation]    Request Central to connect to Periperal via Bluetooth
    [Arguments]    ${peripheral_address}
    ...    ${api_format}

    ${resp} =    IF820_Central.Send And Wait
    ...    command=${ez_bluetooth_commands.CMD_CONNECT}
    ...    api_format=${api_format}
    ...    address=${peripheral_address}
    ...    type=${1}
    Fail on error    ${resp[0]}
    RETURN    ${resp}

Open Pico Probes
    PP_Central.Open    ${settings_id_pp_central}
    PP_Central.Gpio To Input    ${lib_pp_central.GPIO_16}
    PP_Peripheral.Open    ${settings_id_pp_peripheral}
    PP_Peripheral.Gpio To Input    ${lib_pp_peripheral.GPIO_16}

Close Pico Probes
    #Setting high will terminate SPP
    PP_Central.Gpio To Output    ${lib_pp_central.GPIO_16}
    PP_Central.Gpio To Output High    ${lib_pp_central.GPIO_16}
    PP_Central.Gpio To Input    ${lib_pp_central.GPIO_16}
    PP_Central.Close

    PP_Peripheral.Gpio To Output    ${lib_pp_peripheral.GPIO_16}
    PP_Peripheral.Gpio To Output High    ${lib_pp_peripheral.GPIO_16}
    PP_Peripheral.Gpio To Input    ${lib_pp_peripheral.GPIO_16}
    PP_Peripheral.Close

Get Pico Probe Firmware Version
    [Documentation]    Deivce refers to what the probe is connected to
    ...    Either "Central" or "Peripheral"
    [Arguments]    ${device}
    ${ids} =    PP_Peripheral.Get Dap Ids

    IF    "${device}" == "${DEV_CENTRAL}"
        ${fw_ver} =    PP_Central.Get Dap Info1    ${ids.PRODUCT_FW_VERSION}
    ELSE IF    "${device}" == "${DEV_PERIPHERAL}"
        ${fw_ver} =    PP_Peripheral.Get Dap Info1    ${ids.PRODUCT_FW_VERSION}
    END
    RETURN    ${fw_ver}

SPP Test
    [Arguments]    ${api_format}
    ${peripheral_address} =    Get Peripheral Bluetooth Address    ${api_format}
    Log    ${peripheral_address}

    ${resp} =    Connect to Peripheral    ${peripheral_address}    ${api_format}
    ${conn_handle} =    Builtin.Get Variable Value    ${resp[1].payload.conn_handle}
    Log    conn_handle = ${conn_handle}

    ${resp} =    IF820_Central.Wait Event    ${ez_bluetooth_commands.EVENT_BT_CONNECTED}
    Fail on error    ${resp[0]}
    IF820_Central.Close
    IF820_Peripheral.Close

    # The IO should be low when a SPP Connection is active
    ${io_state_p} =    PP_Peripheral.Gpio Read    ${lib_pp_peripheral.GPIO_16}
    ${io_state_c} =    PP_Central.Gpio Read    ${lib_pp_central.GPIO_16}
    Builtin.Should Be Equal    ${0}    ${io_state_p}
    Builtin.Should Be Equal    ${0}    ${io_state_c}

    #send data from central to peripheral
    ${open_result} =    IF820_Central_SPP.open
    ...    ${settings_comport_IF820_central}
    ...    ${lib_if820_central.IF820_DEFAULT_BAUD}
    Should Be True    ${open_result}

    ${open_result} =    IF820_Peripheral_SPP.open
    ...    ${settings_comport_IF820_peripheral}
    ...    ${lib_if820_peripheral.IF820_DEFAULT_BAUD}
    Should Be True    ${open_result}

    ${length} =    Get Length    ${SPP_DATA}
    FOR    ${index}    IN RANGE    ${length}
        Log    ${SPP_DATA}[${index}]
        IF820_Central_SPP.Send    ${SPP_DATA}[${index}]
        Sleep    20ms
    END

    #read data from BT900 Rx Queue
    Sleep    ${1}
    ${rx_data} =    IF820_Peripheral_SPP.Get Rx Queue
    ${utf8_string} =    UTF8 Bytes to String    ${rx_data}
    Log    ${utf8_string}
    RETURN    ${utf8_string}
