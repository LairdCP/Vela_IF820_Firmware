*** Settings ***
Library     OperatingSystem
Library     ..${/}common_lib${/}common_lib${/}EzSerialPort.py    WITH NAME    EZ_Serial_Port
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

Find Boards and Settings
    # Delay in case boards are re-enumerating over USB
    Sleep    ${2}

    ${ez_system_commands}=    EZ_Serial_Port.Get Sys Commands
    Set Global Variable    ${ez_system_commands}    ${ez_system_commands}

    ${lib_ez_serial_port}=    Get Library Instance    EZ_Serial_Port
    Set Global Variable    ${lib_ez_serial_port}    ${lib_ez_serial_port}

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
        Set Global Variable    ${settings_if820_board1}    ${if820_boards[0]}
        Set Global Variable    ${settings_if820_board2}    ${if820_boards[0]}
        Set Global Variable    ${settings_comport_IF820_central}    ${if820_boards[0].puart_port_name}
        Set Global Variable    ${settings_hci_port_IF820_central}    ${if820_boards[0].hci_port_name}
        Set Global Variable    ${settings_id_pp_central}    ${if820_boards[0].probe.id}
        Set Global Variable    ${settings_comport_IF820_peripheral}    ${if820_boards[0].puart_port_name}
        Set Global Variable    ${settings_hci_port_IF820_peripheral}    ${if820_boards[0].hci_port_name}
        Set Global Variable    ${settings_id_pp_peripheral}    ${if820_boards[0].probe.id}
    END

    IF    ${num_boards} >= ${2}
        Set Global Variable    ${settings_if820_board2}    ${if820_boards[1]}
        Set Global Variable    ${settings_comport_IF820_peripheral}    ${if820_boards[1].puart_port_name}
        Set Global Variable    ${settings_hci_port_IF820_peripheral}    ${if820_boards[1].hci_port_name}
        Set Global Variable    ${settings_id_pp_peripheral}    ${if820_boards[1].probe.id}
    END

    RETURN    ${settings}

Init Board
    [Arguments]    ${board}

    ${board_ready}=    Set Variable    ${board.is_initialized}
    IF    ${board_ready} == False
        Call Method    ${board}    open_and_init_board
    END

De-Init Board
    [Arguments]    ${board}

    ${board_ready}=    Set Variable    ${board.is_initialized}
    IF    ${board_ready} == True
        Call Method    ${board}    close_ports_and_reset
    END

EZ Set API Mode
    [Arguments]    ${board}    ${apiformat}

    Call Method    ${board.p_uart}    set_api_format    ${apiformat}

EZ Send
    [Arguments]    ${board}    ${command}    ${apiformat}=${API_MODE_TEXT}    &{kwargs}

    ${res}=    Call Method    ${board.p_uart}    send_and_wait    ${command}    ${apiformat}    &{kwargs}
    Fail on error    ${res[0]}

EZ Wait Event
    [Arguments]    ${board}    ${event}    ${timeout}=${DEFAULT_RX_TIMEOUT}

    ${res}=    Call Method    ${board.p_uart}    wait_event    ${event}    ${timeout}
    Fail on error    ${res[0]}

EZ Send DUT1
    [Arguments]    ${command}    ${apiformat}=${API_MODE_TEXT}    &{kwargs}

    EZ Send    ${settings_if820_board1}    ${command}    ${apiformat}    &{kwargs}

EZ Wait Event DUT1
    [Arguments]    ${event}    ${timeout}=${DEFAULT_RX_TIMEOUT}

    EZ Wait Event    ${settings_if820_board1}    ${event}    ${timeout}

EZ Port Open
    [Arguments]    ${board}    ${flow_control}=${False}

    ${res}=    Call Method
    ...    ${board.p_uart}
    ...    open
    ...    ${board.puart_port_name}
    ...    ${board.p_uart.IF820_DEFAULT_BAUD}
    ...    ${flow_control}
    IF    "${res[1]}" == ${None}
        Fail    Error! Failed to open port: ${board.puart_port_name}
    END

EZ Port Close
    [Arguments]    ${board}

    Call Method    ${board.p_uart}    close

UTF8 Bytes to String
    [Arguments]    ${utf8_bytes}
    ${byte_string}=    Convert To Bytes    ${utf8_bytes}
    ${utf8_string}=    Convert To String    ${byte_string}
    RETURN    ${utf8_string}
