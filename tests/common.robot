*** Settings ***
Library     OperatingSystem


*** Variables ***
${API_MODE_TEXT}                        ${0}
${API_MODE_BINARY}                      ${1}
${DEFAULT_RX_TIMEOUT}                   ${1}
${CLEAR_QUEUE_TIMEOUT_SEC}              ${2}
${ERROR_DEVICE_TYPE}                    Error!    Device type not found!
${BOOT_DELAY_SECONDS}                   ${3}
@{API_MODES}                            ${API_MODE_TEXT}    ${API_MODE_BINARY}
${settings}                             ${EMPTY}

#global variables
${settings_comport_IF820_central}       ${EMPTY}
${settings_comport_IF820_peripheral}    ${EMPTY}
${settings_comport_BT900_central}       ${EMPTY}
${settings_comport_BT900_peripheral}    ${EMPTY}
${settings_id_pp_central}               ${EMPTY}
${settings_id_pp_peripheral}            ${EMPTY}


*** Keywords ***
Fail on error
    [Arguments]    ${err}
    IF    ${err} != 0    Fail    Error! Response error: ${err}

Fail if not equal
    [Arguments]    ${expected_value}    ${my_value}
    IF    ${expected_value} != ${my_value}
        Fail    Error! Expected Value: ${expected_value} is NOT EQUAL to: ${my_value}
    END

Read Settings File
    ${settings_file}=    Get File    .vscode/settings.json
    ${settings}=    Evaluate    json.loads('''${settings_file}''')    json
    Set Global Variable    ${settings_comport_IF820_central}    ${settings["comport_IF820_device1"]}
    Set Global Variable    ${settings_comport_IF820_peripheral}    ${settings["comport_IF820_device2"]}
    Set Global Variable    ${settings_comport_BT900_central}    ${settings["comport_BT900_device1"]}
    Set Global Variable    ${settings_comport_BT900_peripheral}    ${settings["comport_BT900_device2"]}
    Set Global Variable    ${settings_id_pp_central}    ${settings["id_pico_probe_device1"]}
    Set Global Variable    ${settings_id_pp_peripheral}    ${settings["id_pico_probe_device2"]}
    RETURN    ${settings}

UTF8 Bytes to String
    [Arguments]    ${utf8_bytes}
    ${byte_string}=    Convert To Bytes    ${utf8_bytes}
    ${utf8_string}=    Convert To String    ${byte_string}
    RETURN    ${utf8_string}
