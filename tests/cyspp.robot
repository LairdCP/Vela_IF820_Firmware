*** Settings ***
Documentation       CYSPP tests with Vela IF820 devices.

Resource            common.robot

Test Setup          Test Setup
Test Teardown       Test Teardown
Test Timeout        30 seconds

Default Tags        vela if820


*** Variables ***
${STATUS_CONNECTED}         ${53}
${CY_SPP_DATA}              abcdefghijklmnop
${OTA_LATENCY_SECONDS}      ${0.1}


*** Test Cases ***
CYSPP Binary Mode
    Set Tags    PROD-677
    ${rx_cyspp_data} =    CYSPP Test    ${API_MODE_BINARY}

CYSPP Text Mode
    Set Tags    PROD-679
    ${rx_cyspp_data} =    CYSPP Test    ${API_MODE_TEXT}


*** Keywords ***
Test Setup
    Find Boards and Settings

    Init Board    ${if820_board1}
    Init Board    ${if820_board2}

    DVK Probe Set IO Dir    ${if820_board1}    ${if820_board1.CP_ROLE}    ${0}
    DVK Probe Set IO Dir    ${if820_board1}    ${if820_board1.CYSPP}    ${0}
    DVK Probe Set IO Dir    ${if820_board2}    ${if820_board1.CP_ROLE}    ${0}
    DVK Probe Set IO Dir    ${if820_board2}    ${if820_board1.CYSPP}    ${0}

    ${fw_ver_central} =    Get DVK Probe Firmware Version    ${if820_board1}
    Log    ${fw_ver_central}
    ${fw_ver_peripheral} =    Get DVK Probe Firmware Version    ${if820_board2}
    Log    ${fw_ver_peripheral}

Test Teardown
    De-Init Board    ${if820_board1}
    De-Init Board    ${if820_board2}

Send and Receive data
    [Arguments]    ${sender}    ${receiver}    ${data}

    # clear any RX data on the receiver side to prepare for the TX data
    EZ Clear RX Buffer    ${receiver}
    # send the data
    EZ Send Raw    ${sender}    ${data}
    # wait for the data to be received over the air
    Sleep    ${OTA_LATENCY_SECONDS}
    # read the received data and verify it
    ${rx_data} =    EZ Read Raw    ${receiver}
    ${rx_string} =    UTF8 Bytes to String    ${rx_data}
    Should Be Equal As Strings    ${rx_string}    ${data}

CYSPP Test
    [Arguments]    ${api_format}

    EZ Set API Mode    ${if820_board1}    ${api_format}

    # Set Central CP_ROLE pin low to boot in central mode
    DVK Probe Set IO Dir    ${if820_board1}    ${if820_board1.CP_ROLE}    ${1}
    DVK Probe Set IO    ${if820_board1}    ${if820_board1.CP_ROLE}    ${0}
    EZ Send DUT1    ${lib_ez_serial_port.CMD_REBOOT}

    # wait for connection
    ${status} =    Set Variable    ${0}
    WHILE    ${status} != ${STATUS_CONNECTED}
        ${resp} =    EZ Wait Event DUT1    ${lib_ez_serial_port.EVENT_P_CYSPP_STATUS}
        ${status} =    Get Variable Value    ${resp.payload.status}
    END

    # The CYSPP pin should be low when a CYSPP Connection is active
    ${io_state_p} =    DVK Probe Read IO    ${if820_board2}    ${if820_board1.CYSPP}
    ${io_state_c} =    DVK Probe Read IO    ${if820_board1}    ${if820_board1.CYSPP}
    Builtin.Should Be Equal    ${0}    ${io_state_p}
    Builtin.Should Be Equal    ${0}    ${io_state_c}

    # send data central to peripheral
    Send and Receive data    ${if820_board1}    ${if820_board2}    ${CY_SPP_DATA}

    # send data peripheral to central
    Send and Receive data    ${if820_board2}    ${if820_board1}    ${CY_SPP_DATA}
