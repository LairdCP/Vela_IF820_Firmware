*** Settings ***
Documentation       System Group (ID=2 commands).

*** Variables ***
${API_CMD_PING}                   system_ping
${API_CMD_REBOOT}                 system_reboot
${API_CMD_DUMP}                   system_dump 
${API_CMD_STORE_CONFIG}           system_store_config
${API_CMD_FACTORY_RESET}          system_factory_reset
${API_CMD_QUERY_FW}               system_query_firmware_version
${API_CMD_QUERY_UID}              system_query_unique_id
${API_CMD_QUERY_RANDOM_NUM}       system_query_random_number 
${API_CMD_AES_ENCRYPT}            system_aes_encrypt 
${API_CMD_AES_DECRYPT}            system_aes_decrypt
${API_CMD_WRITE_USER_DATA}        system_write_user_data 
${API_CMD_READ_USER_DATA}         system_read_user_data 
${API_CMD_SET_BT_ADDR}            system_set_bluetooth_address 
${API_CMD_GET_BT_ADDR}            system_get_bluetooth_address 
${API_CMD_SET_ECO_PARAMS}         system_set_eco_parameters 
${API_CMD_GET_ECO_PARAMS}         system_get_eco_parameters 
${API_CMD_SET_WCO_PARAMS}         system_set_wco_parameters 
${API_CMD_GET_WCO_PARAMS}         system_get_wco_parameters
${API_CMD_SET_SLEEP_PARAMS}       system_set_sleep_parameters 
${API_CMD_GET_SLEEP_PARAMS}       system_get_sleep_parameters 
${API_CMD_SET_TX_POWER}           system_set_tx_power 
${API_CMD_GET_TX_POWER}           system_get_tx_power 
${API_CMD_SET_TRANSPORT}          system_set_transport 
${API_CMD_GET_TRANSPORT}          system_get_transport 
${API_CMD_SET_UART_PARAMS}        system_set_uart_parameters 
${API_CMD_GET_UART_PARAMS}        system_get_uart_parameters 

${EVENT_SYSTEM_BOOT}                       system_boot
${EVENT_SYSTEM_ERROR}                      system_error
${EVENT_SYSTEM_FACTORY_RESET_COMPLETE}     system_factory_reset_complete
${EVENT_SYSTEM_BOOT_FACTORY_TEST_ENTERED}  system_factory_test_entered
${EVENT_SYSTEM_BOOT_DUMP_BLOB}             system_dump_blob