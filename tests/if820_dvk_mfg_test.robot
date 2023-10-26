*** Settings ***
Documentation       IF820 DVK Manufacturing Test
...                 This test will test one IF820 DVK at a time.

Resource            common.robot

Default Tags        vela if820


*** Variables ***
${PROBE_SETTING_TARGET_DEVICE_VENDOR}=      ARM
${PROBE_SETTING_TARGET_DEVICE_NAME}=        cortex_m
${PROBE_SETTING_BOARD_VENDOR}=              Laird Connectivity
${PROBE_SETTING_BOARD_NAME}=                Vela IF820 DVK


*** Test Cases ***
DVK MFG Test
    Find Boards and Settings

    Init Board    ${settings_if820_board1}    ${False}

    Call Method
    ...    ${settings_if820_board1.probe}
    ...    program_v1_settings
    ...    ${PROBE_SETTING_BOARD_VENDOR}
    ...    ${PROBE_SETTING_BOARD_NAME}
    ...    ${PROBE_SETTING_TARGET_DEVICE_VENDOR}
    ...    ${PROBE_SETTING_TARGET_DEVICE_NAME}

    De-Init Board    ${settings_if820_board1}
