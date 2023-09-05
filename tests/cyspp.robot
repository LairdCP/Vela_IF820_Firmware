*** Settings ***
Documentation       CYSPP tests with Vela IF820 devices.

Library             ..${/}common${/}DvkProbe.py    WITH NAME    PP_Peripheral
Library             ..${/}common${/}DvkProbe.py    WITH NAME    PP_Central
Library             ..${/}common${/}EzSerialPort.py    WITH NAME    IF820_Central
Library             ..${/}common${/}EzSerialPort.py    WITH NAME    IF820_Peripheral
Library             ..${/}common${/}SerialPort.py    WITH NAME    IF820_Central_CYSPP
Library             ..${/}common${/}SerialPort.py    WITH NAME    IF820_Peripheral_CYSPP
Resource            common.robot

Test Setup          Test Setup
Test Teardown       Test Teardown
Test Timeout        1 minute

Default Tags        vela if820


*** Variables ***
${DEV_CENTRAL}                  Central
${DEV_PERIPHERAL}               Peripheral
${MAC_ADDR_LEN}                 ${6}
${INQUIRY_DURATION_SEC}         ${15}
${FLAG_INQUIRY_NAME}            ${1}
${STATUS_CONNECTED}             ${53}
${Connection_Handle}            0
${CY_SPP_DATA}                  abcdefghijklmnop
${peripheral_address}           ${EMPTY}
${lib_if820_central}            ${EMPTY}
${lib_if820_peripheral}         ${EMPTY}
${lib_cyspp_central}            ${EMPTY}
${lib_cyspp_peripheral}         ${EMPTY}
${lib_pp_central}               ${EMPTY}
${lib_pp_peripheral}            ${EMPTY}
${bt900_peripheral_device}      ${EMPTY}
${ez_system_commands}           ${EMPTY}
${ez_cyspp_commands}            ${EMPTY}


*** Test Cases ***
CYSPP Binary Mode
    Set Tags    L2-146
    ${rx_cyspp_data} =    CYSPP Test    ${API_MODE_BINARY}
    Builtin.Should Be Equal    ${rx_cyspp_data}    ${CY_SPP_DATA}

CYSPP Text Mode
    Set Tags    L2-148
    ${rx_cyspp_data} =    CYSPP Test    ${API_MODE_TEXT}
    Builtin.Should Be Equal    ${rx_cyspp_data}    ${CY_SPP_DATA}


*** Keywords ***
Test Setup
    # The last test may have reboot the device, give it time to boot.
    Sleep    ${5}
    Read Settings File
    IF820_Central.Set Queue Timeout    ${CLEAR_QUEUE_TIMEOUT_SEC}
    IF820_Peripheral.Set Queue Timeout    ${CLEAR_QUEUE_TIMEOUT_SEC}

    # Get instances of python libraries needed
    ${lib_if820_central} =    Builtin.Get Library Instance    IF820_Central
    ${lib_if820_peripheral} =    Builtin.Get Library Instance    IF820_Peripheral
    ${lib_pp_central} =    Builtin.Get Library Instance    PP_Central
    ${lib_pp_peripheral} =    Builtin.Get Library Instance    PP_Peripheral
    ${lib_cyspp_central} =    Builtin.Get Library Instance    IF820_Central_CYSPP
    ${lib_cyspp_peripheral} =    Builtin.Get Library Instance    IF820_Peripheral_CYSPP
    Set Global Variable    ${lib_if820_central}    ${lib_if820_central}
    Set Global Variable    ${lib_if820_peripheral}    ${lib_if820_peripheral}
    Set Global Variable    ${lib_cyspp_central}    ${lib_cyspp_central}
    Set Global Variable    ${lib_cyspp_peripheral}    ${lib_cyspp_peripheral}
    Set Global Variable    ${lib_pp_central}    ${lib_pp_central}
    Set Global Variable    ${lib_pp_peripheral}    ${lib_pp_peripheral}

    Open Pico Probes

    ${ez_system_commands} =    IF820_Central.Get Sys Commands
    ${ez_cyspp_commands} =    IF820_Central.Get Cyspp Commands
    Set Global Variable    ${ez_system_commands}    ${ez_system_commands}
    Set Global Variable    ${ez_cyspp_commands}    ${ez_cyspp_commands}

    ${fw_ver_central} =    Get Pico Probe Firmware Version    ${DEV_CENTRAL}
    Log    ${fw_ver_central}
    ${fw_ver_peripheral} =    Get Pico Probe Firmware Version    ${DEV_PERIPHERAL}
    Log    ${fw_ver_peripheral}

    # open the serial ports for devices in test
    IF820_Central.Close
    IF820_Peripheral.Close
    Sleep    ${1}
    IF820_Central.open    ${settings_comport_IF820_central}    ${lib_if820_central.IF820_DEFAULT_BAUD}
    IF820_Peripheral.open    ${settings_comport_IF820_peripheral}    ${lib_if820_peripheral.IF820_DEFAULT_BAUD}
    Sleep    ${1}

    # IF820 Factory Reset
    IF820_Central.Clear Rx Queue
    ${response} =    IF820_Central.Send And Wait    ${ez_system_commands.CMD_FACTORY_RESET}
    Fail on error    ${response[0]}
    ${response} =    IF820_Central.Wait Event    ${ez_system_commands.EVENT_SYSTEM_BOOT}

    IF820_Peripheral.Clear Rx Queue
    ${response} =    IF820_Peripheral.Send And Wait    ${ez_system_commands.CMD_FACTORY_RESET}
    Fail on error    ${response[0]}
    ${response} =    IF820_Peripheral.Wait Event    ${ez_system_commands.EVENT_SYSTEM_BOOT}

Test Teardown
    IF820_Central.close
    IF820_Peripheral.close
    # note rebooting the pico probe will reset the if820 device and all i/o.
    PP_Central.Reboot
    PP_Peripheral.Reboot
    PP_Central.Close
    PP_Peripheral.Close
    Log    "Test Teardown Complete"

Open Pico Probes
    PP_Central.Open    ${settings_id_pp_central}
    PP_Central.Gpio To Input    ${lib_pp_central.GPIO_19}
    PP_Central.Gpio To Input    ${lib_pp_central.GPIO_18}

    PP_Peripheral.Open    ${settings_id_pp_peripheral}
    PP_Peripheral.Gpio To Input    ${lib_pp_peripheral.GPIO_19}
    PP_Peripheral.Gpio To Input    ${lib_pp_peripheral.GPIO_18}

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

CYSPP Test
    [Arguments]    ${api_format}

    # Set Central CY_ROLE pin low to boot in central mode
    PP_Central.Gpio To Output    ${lib_pp_central.GPIO_18}
    PP_Central.Gpio To Output Low    ${lib_pp_central.GPIO_18}
    ${response} =    IF820_Central.Send And Wait    ${ez_system_commands.CMD_REBOOT}    ${api_format}
    Fail on error    ${response[0]}

    # wait for connection
    ${status} =    Set Variable    0
    WHILE    ${status} != ${STATUS_CONNECTED}
        ${resp} =    IF820_Central.Wait Event    ${ez_cyspp_commands.EVENT_P_CYSPP_STATUS}
        ${status} =    Builtin.Get Variable Value    ${resp[1].payload.status}
        Log    cyspp_status = ${status}
    END

    # devices are connected, send data
    IF820_Central.Close
    IF820_Peripheral.Close

    # The IO should be low when a CYSPP Connection is active
    ${io_state_p} =    PP_Peripheral.Gpio Read    ${lib_pp_peripheral.GPIO_19}
    ${io_state_c} =    PP_Central.Gpio Read    ${lib_pp_central.GPIO_19}
    Builtin.Should Be Equal    ${0}    ${io_state_p}
    Builtin.Should Be Equal    ${0}    ${io_state_c}

    # send data from central to peripheral
    ${open_result} =    IF820_Central_CYSPP.open
    ...    ${settings_comport_IF820_central}
    ...    ${lib_if820_central.IF820_DEFAULT_BAUD}
    Should Be True    ${open_result}

    ${open_result} =    IF820_Peripheral_CYSPP.open
    ...    ${settings_comport_IF820_peripheral}
    ...    ${lib_if820_peripheral.IF820_DEFAULT_BAUD}
    Should Be True    ${open_result}

    ${length} =    Get Length    ${CY_SPP_DATA}
    FOR    ${index}    IN RANGE    ${length}
        Log    ${CY_SPP_DATA}[${index}]
        IF820_Central_CYSPP.Send    ${CY_SPP_DATA}[${index}]
        Sleep    20ms
    END

    Sleep    ${1}
    ${rx_data} =    IF820_Peripheral_CYSPP.Get Rx Queue
    ${utf8_string} =    UTF8 Bytes to String    ${rx_data}
    Log    ${utf8_string}
    RETURN    ${utf8_string}
