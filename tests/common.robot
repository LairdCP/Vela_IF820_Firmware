*** Settings ***
Library     OperatingSystem
Library     ..${/}common_lib${/}common_lib${/}If820Board.py    WITH NAME    IF820_Board


*** Variables ***
${API_MODE_TEXT}                            ${0}
${API_MODE_BINARY}                          ${1}
${UART_FLOW_CNTRL_NONE}                     ${0}
${UART_FLOW_CNTRL_ENABLE}                   ${1}
${DEFAULT_RX_TIMEOUT}                       ${1}
${CLEAR_QUEUE_TIMEOUT_SEC}                  ${2}
${ERROR_DEVICE_TYPE}                        Error! Device type not found!
${BOOT_DELAY_SECONDS}                       ${3}
@{API_MODES}                                ${API_MODE_TEXT}    ${API_MODE_BINARY}
@{UART_FLOW_TYPES}                          ${UART_FLOW_CNTRL_NONE}    ${UART_FLOW_CNTRL_ENABLE}
${settings}                                 ${EMPTY}

# global variables
${settings_comport_IF820_central}           ${EMPTY}
${settings_comport_IF820_peripheral}        ${EMPTY}
${settings_hci_port_IF820_central}          ${EMPTY}
${settings_hci_port_IF820_peripheral}       ${EMPTY}
${settings_comport_BT900}                   ${EMPTY}
${settings_id_pp_central}                   ${EMPTY}
${settings_id_pp_peripheral}                ${EMPTY}
${settings_default_baud}                    ${EMPTY}


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
    ${settings_file}=    Get File    ${CURDIR}${/}..${/}.vscode${/}settings.json
    ${settings}=    Evaluate    json.loads('''${settings_file}''')    json

    @{if820_boards}=    IF820_Board.Get Connected Boards
    ${num_boards}=    Get Length    ${if820_boards}
    Log    ${num_boards} IF820 Boards Found!

    Set Global Variable    ${settings_default_baud}    ${settings["default_baud"]}
    Set Global Variable    ${settings_comport_BT900}    ${settings["comport_BT900_device1"]}

    IF    ${num_boards} == ${0}
        Fail    Error! No IF820 boards found!
    ELSE IF    ${num_boards} >= ${1}
        Set Global Variable    ${settings_comport_IF820_central}    ${if820_boards[0].puart_port_name}
        Set Global Variable    ${settings_hci_port_IF820_central}    ${if820_boards[0].hci_port_name}
        Set Global Variable    ${settings_id_pp_central}    ${if820_boards[0].probe.id}
        Set Global Variable    ${settings_comport_IF820_peripheral}    ${if820_boards[0].puart_port_name}
        Set Global Variable    ${settings_hci_port_IF820_peripheral}    ${if820_boards[0].hci_port_name}
        Set Global Variable    ${settings_id_pp_peripheral}    ${if820_boards[0].probe.id}
    END

    IF    ${num_boards} >= ${2}
        Set Global Variable    ${settings_comport_IF820_peripheral}    ${if820_boards[1].puart_port_name}
        Set Global Variable    ${settings_hci_port_IF820_peripheral}    ${if820_boards[1].hci_port_name}
        Set Global Variable    ${settings_id_pp_peripheral}    ${if820_boards[1].probe.id}
    END

    RETURN    ${settings}

UTF8 Bytes to String
    [Arguments]    ${utf8_bytes}
    ${byte_string}=    Convert To Bytes    ${utf8_bytes}
    ${utf8_string}=    Convert To String    ${byte_string}
    RETURN    ${utf8_string}
