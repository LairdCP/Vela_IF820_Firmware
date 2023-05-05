*** Settings ***
Documentation       IF820 Manufacturing Test
...                 This test will continue to loop to test IF820 modules

Library             ..${/}common${/}PicoProbe.py
Library             ..${/}common${/}EzSerialPort.py    WITH NAME    IF820_Device
Library             ..${/}common${/}HciProgrammer.py    WITH NAME    IF820_Programmer
Library             ..${/}common${/}HciSerialPort.py    WITH NAME    IF820_HciPort
Library             ../common/CommonLib.py
Library             Dialogs
Library             Collections
Library             DateTime
Resource            common.robot

Test Setup          Test Setup
Test Teardown       Test Teardown

Default Tags        vela if820


*** Variables ***
${lib_if820_device}             ${EMPTY}
${ez_system_commands}           ${EMPTY}
${MINI_DRIVER}                  ../files/minidriver-20820A1-uart-patchram.hex
${FIRMWARE}
...                             ../files/20230412_ezserial_app_CYBT-243053-EVAL_140606_v1.4.6.6_download.hex
${PROGRAM_BAUD_RATE}            3000000
${PROGRAM_FIRMWARE_TIMEOUT}     30 seconds
${TEST_TIMEOUT_SHORT}           2 seconds
@{module_result}                ${EMPTY}
${RESULTE_FILE_NAME}            if820_mfg_results
${result_file}                  ${EMPTY}


*** Test Cases ***
MFG Test
    Set Tags    L2VV-40
    Manufacturing Test Loop


*** Keywords ***
Test Setup
    Read Settings File

    # Get instances of python libraries needed
    ${lib_if820_device} =    Builtin.Get Library Instance    IF820_Device
    Set Global Variable    ${lib_if820_device}    ${lib_if820_device}

    ${ez_system_commands} =    IF820_Device.Get Sys Commands
    Set Global Variable    ${ez_system_commands}    ${ez_system_commands}

    # Setup test result file
    ${current_time} =    Get Current Date    result_format=%Y%m%d-%H%M%S
    ${result_file} =    Set Variable    ${OUTPUT_DIR}${/}${RESULTE_FILE_NAME}_${current_time}.txt
    Set Global Variable    ${result_file}    ${result_file}
    Create File    path=${result_file}

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
    PicoProbe.Open    ${settings_id_pp_central}
    IF    not ${skip}
        # Set module HCI CTS low to enter programming mode
        IF820_HciPort.open    ${settings_hci_port_IF820_central}    ${lib_if820_device.IF820_DEFAULT_BAUD}
        # Reset the module to enter programming mode
        PicoProbe.Reset Device
        # Close the HCI serial port so the programmer can open it
        IF820_HciPort.Close
        IF820_Programmer.Init
        ...    ${MINI_DRIVER}
        ...    ${settings_hci_port_IF820_central}
        ...    ${lib_if820_device.IF820_DEFAULT_BAUD}
        IF820_Programmer.Program Firmware    ${PROGRAM_BAUD_RATE}    ${FIRMWARE}
    END
    # Reset the module to boot the firmware
    PicoProbe.Reset Device
    PicoProbe.Close
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
    ${mac_string} =    CommonLib.If820 Mac Addr Response To Mac As String    ${res[1].payload.address}
    Log Result    ${mac_string}
    Log    Bluetooth address: ${mac_string}

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
        Record Result
    END
