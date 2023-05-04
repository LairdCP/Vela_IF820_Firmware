*** Settings ***
Documentation       IF820 Manufacturing Test
...                 This test will continue to loop to test IF820 modules

Library             ..${/}common${/}PicoProbe.py
Library             ..${/}common${/}EzSerialPort.py    WITH NAME    IF820_Device
Library             ..${/}common${/}HciProgrammer.py    WITH NAME    IF820_Programmer
Library             ..${/}common${/}HciSerialPort.py    WITH NAME    IF820_HciPort
Library             Dialogs
Resource            common.robot

Test Setup          Test Setup
Test Teardown       Test Teardown

Default Tags        vela if820


*** Variables ***
${lib_if820_device}         ${EMPTY}
${ez_system_commands}       ${EMPTY}
${MINI_DRIVER}              ../files/minidriver-20820A1-uart-patchram.hex
${FIRMWARE}                 ../files/20230412_ezserial_app_CYBT-243053-EVAL_140606_v1.4.6.6_download.hex
${PROGRAM_BAUD_RATE}        3000000


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

Test Teardown
    IF820_Device.Close
    Log    "Test Teardown Complete"

Program firmware
    [Timeout]    30 seconds
    # Set module HCI CTS low to enter programming mode
    IF820_HciPort.open    ${settings_hci_port_IF820_central}    ${lib_if820_device.IF820_DEFAULT_BAUD}
    PicoProbe.Open    ${settings_id_pp_central}
    # Reset the module to enter programming mode
    PicoProbe.Reset Device
    # Close the HCI serial port so the programmer can open it
    IF820_HciPort.Close
    IF820_Programmer.Init
    ...    ${MINI_DRIVER}
    ...    ${settings_hci_port_IF820_central}
    ...    ${lib_if820_device.IF820_DEFAULT_BAUD}
    IF820_Programmer.Program Firmware    ${PROGRAM_BAUD_RATE}    ${FIRMWARE}
    # Reset the module to boot the firmware
    PicoProbe.Reset Device
    PicoProbe.Close
    # Open the serial connection to communicate with EZ-Serial
    IF820_Device.Open    ${settings_comport_IF820_central}    ${lib_if820_device.IF820_DEFAULT_BAUD}
    # Wait for the module to boot
    ${res} =    IF820_Device.Wait Event    ${ez_system_commands.EVENT_SYSTEM_BOOT}
    Fail on error    ${res}[0]

Manufacturing Test Loop
    WHILE    $True
        TRY
            ${barcode} =    Get Value From User    Enter Barcode
        EXCEPT
            Pass Execution    User stopped test
        END
        Log    Barcode: ${barcode}
        Program firmware
    END
