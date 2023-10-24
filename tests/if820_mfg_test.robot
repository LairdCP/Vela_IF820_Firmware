*** Settings ***
Documentation       IF820 Manufacturing Test
...                 This test will continue to loop to test IF820 modules

Library             ..${/}common_lib${/}common_lib${/}DvkProbe.py
Library             ..${/}common_lib${/}common_lib${/}If820Board.py    WITH NAME    IF820_Board
Library             ..${/}common_lib${/}common_lib${/}EzSerialPort.py    WITH NAME    IF820_Device
Library             ..${/}common_lib${/}common_lib${/}HciProgrammer.py    WITH NAME    IF820_Programmer
Library             ..${/}common_lib${/}common_lib${/}HciSerialPort.py    WITH NAME    IF820_HciPort
Library             Dialogs
Library             Collections
Library             DateTime
Resource            common.robot

Test Setup          Test Setup
Test Teardown       Test Teardown

Default Tags        vela if820


*** Variables ***
${lib_if820_board}              ${EMPTY}
${lib_if820_device}             ${EMPTY}
${ez_system_commands}           ${EMPTY}
${MINI_DRIVER}                  ${CURDIR}${/}..${/}files${/}minidriver-20820A1-uart-patchram.hex
${FIRMWARE}
...                             ${CURDIR}${/}..${/}files${/}v1.4.12.12-candidate_int-ant/202309011_ezserial_app_VELA-IF820-INT-ANT-EVK_141212_v1.4.12.12_download.hex
${PROGRAM_BAUD_RATE}            3000000
${PROGRAM_FIRMWARE_TIMEOUT}     30 seconds
${TEST_TIMEOUT_SHORT}           2 seconds
@{module_result}                ${EMPTY}
${RESULTE_FILE_NAME}            if820_mfg_results
${result_file}                  ${EMPTY}

# Pairs of GPIO pins for loopback testing. First pin in the pair is the output.
# TODO: Need different GPIO pairs for integrated antenna module and external antenna module
@{GPIO_SETS}                    ${EMPTY}

@{GPIO_TEST_STATES}             ${1}    ${0}
${GPIO_CONFIG_OUTPUT}           ${0x4000}
${GPIO_CONFIG_INPUT}            ${0x0000}
${GPIO_OP_IMMEDIATE}            ${0}
${GPIO_OP_RELEASE}              ${4}


*** Test Cases ***
MFG Test
    Set Tags    L2-67
    Manufacturing Test Loop


*** Keywords ***
Test Setup
    Read Settings File

    # Get instances of python libraries needed
    ${lib_if820_board} =    Builtin.Get Library Instance    IF820_Board
    Set Global Variable    ${lib_if820_board}    ${lib_if820_board}

    ${lib_if820_device} =    Builtin.Get Library Instance    IF820_Device
    Set Global Variable    ${lib_if820_device}    ${lib_if820_device}

    ${ez_system_commands} =    IF820_Device.Get Sys Commands
    Set Global Variable    ${ez_system_commands}    ${ez_system_commands}

    # Setup test result file
    ${current_time} =    Get Current Date    result_format=%Y%m%d-%H%M%S
    ${result_file} =    Set Variable    ${OUTPUT_DIR}${/}${RESULTE_FILE_NAME}_${current_time}.txt
    Set Global Variable    ${result_file}    ${result_file}
    Create File    path=${result_file}

    # Setup GPIO pairs for integrated antenna module. These pairs are specified as the CYW20820 port pins (P15, P8, etc.).
    # The first pin in the pair is the output pin and the second pin is the input pin.
    # 15 -> 8 : module pin 6 -> 7
    # 2 -> 3 : module pin 8 -> 9
    # 6 -> 17 : module pin 10 -> 11
    # 13 -> 9 : module pin 12 -> 13
    ${gpio_sets} =    Evaluate    [[15, 8], [2, 3], [6, 17], [13, 9]]    # TODO: Need to add all pairs
    Set Global Variable    ${GPIO_SETS}    ${gpio_sets}

Test Teardown
    IF820_Device.Close
    Log    "Test Teardown Complete"

Init Module Result
    ${module_result} =    Create List
    Set Global Variable    ${module_result}    ${module_result}

Log Result
    [Arguments]    ${result}
    Append To List    ${module_result}    ${result}

Program firmware
    [Timeout]    ${PROGRAM_FIRMWARE_TIMEOUT}
    [Arguments]    ${skip}=${False}
    DvkProbe.Open    ${settings_id_pp_central}
    IF    not ${skip}
        # Set module HCI CTS low to enter programming mode
        IF820_HciPort.open    ${settings_hci_port_IF820_central}    ${lib_if820_device.IF820_DEFAULT_BAUD}
        # Reset the module to enter programming mode
        DvkProbe.Reset Device
        # Close the HCI serial port so the programmer can open it
        IF820_HciPort.Close
        IF820_Programmer.Init
        ...    ${MINI_DRIVER}
        ...    ${settings_hci_port_IF820_central}
        ...    ${lib_if820_device.IF820_DEFAULT_BAUD}
        IF820_Programmer.Program Firmware    ${PROGRAM_BAUD_RATE}    ${FIRMWARE}    ${True}
    END
    # Reset the module to boot the firmware
    DvkProbe.Reset Device
    DvkProbe.Close
    # Open the serial connection to communicate with EZ-Serial
    IF820_Device.Open    ${settings_comport_IF820_central}    ${lib_if820_device.IF820_DEFAULT_BAUD}
    # Wait for the module to boot
    ${res} =    IF820_Device.Wait Event    ${ez_system_commands.EVENT_SYSTEM_BOOT}
    Fail on error    ${res[0]}

Query Firmware Version
    [Timeout]    ${TEST_TIMEOUT_SHORT}
    ${res} =    IF820_Device.Send And Wait    ${ez_system_commands.CMD_QUERY_FW}
    Fail on error    ${res[0]}
    ${app_ver} =    Convert To Hex    ${res[1].payload.app}    prefix=0x    length=8
    Log Result    ${app_ver}
    Log    Firmware version: ${app_ver}

Query Bluetooth Address
    [Timeout]    ${TEST_TIMEOUT_SHORT}
    ${res} =    IF820_Device.Send And Wait    ${ez_system_commands.CMD_GET_BT_ADDR}
    Fail on error    ${res[0]}
    ${mac_string} =    Call Method
    ...    ${lib_if820_board}
    ...    if820_mac_addr_response_to_mac_as_string
    ...    ${res[1].payload.address}
    Log Result    ${mac_string}
    Log    Bluetooth address: ${mac_string}

Test GPIO
    [Timeout]    ${PROGRAM_FIRMWARE_TIMEOUT}
    FOR    ${pins}    IN    @{GPIO_SETS}
        # Config output pin
        ${res} =    IF820_Device.Send And Wait    ${lib_if820_device.CMD_GPIO_SET_DRIVE}
        ...    pin=${pins[0]}
        ...    pin_config=${GPIO_CONFIG_OUTPUT}
        ...    pin_out_value=${0}
        ...    pin_operation=${GPIO_OP_IMMEDIATE}
        Fail on error    ${res[0]}
        # Config input pin
        ${res} =    IF820_Device.Send And Wait    ${lib_if820_device.CMD_GPIO_SET_DRIVE}
        ...    pin=${pins[1]}
        ...    pin_config=${GPIO_CONFIG_INPUT}
        ...    pin_out_value=${0}
        ...    pin_operation=${GPIO_OP_IMMEDIATE}
        Fail on error    ${res[0]}
        # Set and read state
        FOR    ${state}    IN    @{GPIO_TEST_STATES}
            ${res} =    IF820_Device.Send And Wait    ${lib_if820_device.CMD_GPIO_SET_LOGIC}
            ...    pin=${pins[0]}
            ...    pin_out_value=${state}
            Fail on error    ${res[0]}
            ${res} =    IF820_Device.Send And Wait    ${lib_if820_device.CMD_GPIO_GET_LOGIC}
            ...    pin=${pins[1]}
            ...    direction=${0}
            Fail on error    ${res[0]}
            Log    ${res}
            IF    ${res[1].payload.logic} != ${state}
                Fail    GPIO ${pins[0]} state ${res[1].payload.logic} should be ${state}
            END
        END
        # Release pins from control
        ${res} =    IF820_Device.Send And Wait    ${lib_if820_device.CMD_GPIO_SET_DRIVE}
        ...    pin=${pins[0]}
        ...    pin_config=${0}
        ...    pin_out_value=${0}
        ...    pin_operation=${GPIO_OP_RELEASE}
        Fail on error    ${res[0]}
        ${res} =    IF820_Device.Send And Wait    ${lib_if820_device.CMD_GPIO_SET_DRIVE}
        ...    pin=${pins[1]}
        ...    pin_config=${0}
        ...    pin_out_value=${0}
        ...    pin_operation=${GPIO_OP_RELEASE}
        Fail on error    ${res[0]}
    END

Record Result
    Log    ${module_result}
    ${result_string} =    Set Variable    ${EMPTY}
    ${result_length} =    Get Length    ${module_result}
    FOR    ${index}    IN RANGE    ${result_length}
        ${value} =    Set Variable    ${module_result[${index}]}
        ${result_string} =    Set Variable    ${result_string}${value}
        IF    ${index} < ${result_length-1}
            ${result_string} =    Set Variable    ${result_string},
        ELSE
            ${result_string} =    Set Variable    ${result_string}${\n}
        END
    END
    Append To File    ${result_file}    ${result_string}

Manufacturing Test Loop
    WHILE    $True
        Init Module Result
        TRY
            ${barcode} =    Get Value From User    Enter Barcode
        EXCEPT
            Pass Execution    User stopped test
        END
        Log Result    ${barcode}
        Log    Barcode: ${barcode}
        Program firmware
        Query Bluetooth Address
        Query Firmware Version
        Test GPIO
        # TODO: Set TX power and start advertising
        # TODO: Measure TX power
        Record Result
    END
