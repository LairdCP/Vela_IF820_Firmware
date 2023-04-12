*** Settings ***

*** Variables ***
${API_MODE_TEXT}             ${0}
${API_MODE_BINARY}           ${1}
${DEV_PERIPHERAL}            Peripheral
${DEV_CENTRAL}               Central
${DEFAULT_RX_TIMEOUT}        ${1}
${ERROR_DEVICE_TYPE}         Error!  Device type not found!
${BOOT_DELAY_SECONDS}        ${3}
@{API_MODES}                 ${API_MODE_TEXT}    ${API_MODE_BINARY}

*** Keywords ***
Fail on error
    [Arguments]    ${err}
    IF    ${err} != 0    Fail    Error! Response error: ${err}

Fail if not equal    
    [Arguments]    ${expected_value}    ${my_value}
    IF    ${expected_value} != ${my_value}    Fail    Error! Expected Value: ${expected_value} is NOT EQUAL to: ${my_value}