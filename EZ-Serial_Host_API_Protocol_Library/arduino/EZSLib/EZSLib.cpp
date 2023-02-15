/*******************************************************************************
* \file EZSLib.c
* \version 1.1.0
* \owner JROW
*
* \brief
* EZ-Serial host API protocol implementation for Arduino platform
*
* \details
* This file is part of the EZ-Serial host API protocol reference library. It
* provides implementations for the API protocol used to control EZ-Serial from
* an external host. Refer to the EZ-Serial Firmware User Guide for additional
* information concerning the API protocol and communication behavior.
*
* This implementation is specifically suited for the Arduino environment.
*
* Code Tested With:
* 1. Arduino 1.8.2 + Arduino Uno R3
*
********************************************************************************
* \copyright
* Copyright 2017, Cypress Semiconductor Corporation.
*
* This software is owned by Cypress Semiconductor Corporation (Cypress) and is
* protected by and subject to worldwide patent protection (United States and
* foreign), United States copyright laws and international treaty provisions.
* Cypress hereby grants to licensee a personal, non-exclusive, non-transferable
* license to copy, use, modify, create derivative works of, and compile the
* Cypress Source Code and derivative works for the sole purpose of creating
* custom software in support of licensee product to be used only in conjunction
* with a Cypress integrated circuit as specified in the applicable agreement.
* Any reproduction, modification, translation, compilation, or representation of
* this software except as specified above is prohibited without the express
* written permission of Cypress.
*
* Disclaimer: CYPRESS MAKES NO WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, WITH
* REGARD TO THIS MATERIAL, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
* WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
* Cypress reserves the right to make changes without further notice to the
* materials described herein. Cypress does not assume any liability arising out
* of the application or use of any product or circuit described herein. Cypress
* does not authorize its products for use as critical components in life-support
* systems where a malfunction or failure may reasonably be expected to result in
* significant injury to the user. The inclusion of Cypress' product in a life-
* support systems application implies that the manufacturer assumes all risk of
* such use and in doing so indemnifies Cypress against all charges. Use may be
* limited by and subject to the applicable Cypress software license agreement.
*******************************************************************************/

/* THIS FILE IS AUTOMATICALLY GENERATED FROM THE EZ-SERIAL JSON API DEFINITION */

#include <Arduino.h>        /* Arduino environment */
#include <avr/pgmspace.h>   /* flash memory constant read functions */
#include <stdarg.h>         /* va_args implementation */
#include "EZSLib.h"         /* EZ-Serial host API declarations */

uint8_t *ezs_rx_packet_buffer;
uint16_t ezs_rx_packet_length;
uint16_t ezs_rx_packet_length_expected;
uint8_t ezs_rx_packet_checksum;

ezs_packet_t ezs_rx_packet;
ezs_packet_t ezs_tx_packet;


/*******************************************************************************
* Command definition table with binary command/response method detail
*******************************************************************************/
const uint8_t ezs_tbl_cmd[] PROGMEM =
{
    0x02,0x01,  0x00,   0x00,                                   /*   0 | /  0, /PING (system_ping) */
    0x02,0x02,  0x00,   0x00,                                   /*   1 | /  1, /RBT (system_reboot) */
    0x02,0x03,  0x01,   0x01,T_U8,                              /*   2 | /  2, /DUMP (system_dump) */
    0x02,0x04,  0x00,   0x00,                                   /*   3 | /  3, /SCFG (system_store_config) */
    0x02,0x05,  0x00,   0x00,                                   /*   4 | /  4, /RFAC (system_factory_reset) */
    0x02,0x06,  0x00,   0x00,                                   /*   5 | /  5, /QFV (system_query_firmware_version) */
    0x02,0x07,  0x00,   0x00,                                   /*   6 | /  6, /QUID (system_query_unique_id) */
    0x02,0x08,  0x00,   0x00,                                   /*   7 | /  7, /QRND (system_query_random_number) */
    0x02,0x09,  0x81,   0x01,T_U8A,                             /*   8 | /  8, /AESE (system_aes_encrypt) */
    0x02,0x0A,  0x81,   0x01,T_U8A,                             /*   9 | /  9, /AESD (system_aes_decrypt) */
    0x02,0x0B,  0x83,   0x02,T_U16,T_U8A,                       /*  10 | / 10, /WUD (system_write_user_data) */
    0x02,0x0C,  0x03,   0x02,T_U16,T_U8,                        /*  11 | / 11, /RUD (system_read_user_data) */
    0x03,0x01,  0x01,   0x01,T_U8,                              /*  12 | / 12, /RDFU (dfu_reboot) */
    0x04,0x01,  0x13,   0x08,T_MAC,T_U8,T_U16,T_U16,T_U16,T_U16,T_U16,T_U16,
                                                                /*  13 | / 13, /C (gap_connect) */
    0x04,0x02,  0x00,   0x00,                                   /*  14 | / 14, /CX (gap_cancel_connection) */
    0x04,0x03,  0x07,   0x04,T_U8,T_U16,T_U16,T_U16,            /*  15 | / 15, /UCP (gap_update_conn_parameters) */
    0x04,0x04,  0x02,   0x02,T_U8,T_U8,                         /*  16 | / 16, /CUR (gap_send_connupdate_response) */
    0x04,0x05,  0x01,   0x01,T_U8,                              /*  17 | / 17, /DIS (gap_disconnect) */
    0x04,0x06,  0x07,   0x02,T_MAC,T_U8,                        /*  18 | / 18, /WLA (gap_add_whitelist_entry) */
    0x04,0x07,  0x07,   0x02,T_MAC,T_U8,                        /*  19 | / 19, /WLD (gap_delete_whitelist_entry) */
    0x04,0x08,  0x08,   0x06,T_U8,T_U8,T_U16,T_U8,T_U8,T_U16,   /*  20 | / 20, /A (gap_start_adv) */
    0x04,0x09,  0x00,   0x00,                                   /*  21 | / 21, /AX (gap_stop_adv) */
    0x04,0x0A,  0x0A,   0x07,T_U8,T_U16,T_U16,T_U8,T_U8,T_U8,T_U16,
                                                                /*  22 | / 22, /S (gap_start_scan) */
    0x04,0x0B,  0x00,   0x00,                                   /*  23 | / 23, /SX (gap_stop_scan) */
    0x04,0x0C,  0x01,   0x01,T_U8,                              /*  24 | / 24, /QPA (gap_query_peer_address) */
    0x04,0x0D,  0x01,   0x01,T_U8,                              /*  25 | / 25, /QSS (gap_query_rssi) */
    0x04,0x0E,  0x00,   0x00,                                   /*  26 | / 26, /QWL (gap_query_whitelist) */
    0x05,0x01,  0x89,   0x06,T_U16,T_U8,T_U8,T_U8,T_U16,T_LU8A, /*  27 | / 27, /CAC (gatts_create_attr) */
    0x05,0x02,  0x02,   0x01,T_U16,                             /*  28 | / 28, /CAD (gatts_delete_attr) */
    0x05,0x03,  0x00,   0x00,                                   /*  29 | / 29, /VGDB (gatts_validate_db) */
    0x05,0x04,  0x00,   0x00,                                   /*  30 | / 30, /SGDB (gatts_store_db) */
    0x05,0x05,  0x01,   0x01,T_U8,                              /*  31 | / 31, /DGDB (gatts_dump_db) */
    0x05,0x06,  0x04,   0x02,T_U16,T_U16,                       /*  32 | / 32, /DLS (gatts_discover_services) */
    0x05,0x07,  0x06,   0x03,T_U16,T_U16,T_U16,                 /*  33 | / 33, /DLC (gatts_discover_characteristics) */
    0x05,0x08,  0x08,   0x04,T_U16,T_U16,T_U16,T_U16,           /*  34 | / 34, /DLD (gatts_discover_descriptors) */
    0x05,0x09,  0x02,   0x01,T_U16,                             /*  35 | / 35, /RLH (gatts_read_handle) */
    0x05,0x0A,  0x84,   0x02,T_U16,T_LU8A,                      /*  36 | / 36, /WLH (gatts_write_handle) */
    0x05,0x0B,  0x84,   0x03,T_U8,T_U16,T_U8A,                  /*  37 | / 37, /NH (gatts_notify_handle) */
    0x05,0x0C,  0x84,   0x03,T_U8,T_U16,T_U8A,                  /*  38 | / 38, /IH (gatts_indicate_handle) */
    0x05,0x0D,  0x02,   0x02,T_U8,T_U8,                         /*  39 | / 39, /WRR (gatts_send_writereq_response) */
    0x06,0x01,  0x05,   0x03,T_U8,T_U16,T_U16,                  /*  40 | / 40, /DRS (gattc_discover_services) */
    0x06,0x02,  0x07,   0x04,T_U8,T_U16,T_U16,T_U16,            /*  41 | / 41, /DRC (gattc_discover_characteristics) */
    0x06,0x03,  0x09,   0x05,T_U8,T_U16,T_U16,T_U16,T_U16,      /*  42 | / 42, /DRD (gattc_discover_descriptors) */
    0x06,0x04,  0x03,   0x02,T_U8,T_U16,                        /*  43 | / 43, /RRH (gattc_read_handle) */
    0x06,0x05,  0x86,   0x04,T_U8,T_U16,T_U8,T_LU8A,            /*  44 | / 44, /WRH (gattc_write_handle) */
    0x06,0x06,  0x01,   0x01,T_U8,                              /*  45 | / 45, /CI (gattc_confirm_indication) */
    0x07,0x01,  0x00,   0x00,                                   /*  46 | / 46, /QB (smp_query_bonds) */
    0x07,0x02,  0x07,   0x02,T_MAC,T_U8,                        /*  47 | / 47, /BD (smp_delete_bond) */
    0x07,0x03,  0x05,   0x05,T_U8,T_U8,T_U8,T_U8,T_U8,          /*  48 | / 48, /P (smp_pair) */
    0x07,0x04,  0x00,   0x00,                                   /*  49 | / 49, /QRA (smp_query_random_address) */
    0x07,0x05,  0x03,   0x02,T_U8,T_U16,                        /*  50 | / 50, /PR (smp_send_pairreq_response) */
    0x07,0x06,  0x05,   0x02,T_U8,T_U32,                        /*  51 | / 51, /PE (smp_send_passkeyreq_response) */
    0x07,0x07,  0x82,   0x02,T_U8,T_U8A,                        /*  52 | / 52, /GOOB (smp_generate_oob_data) */
    0x07,0x08,  0x01,   0x01,T_U8,                              /*  53 | / 53, /COOB (smp_clear_oob_data) */
    0x08,0x01,  0x0B,   0x06,T_U8,T_U16,T_U16,T_U16,T_U16,T_U16,/*  54 | / 54, /LC (l2cap_connect) */
    0x08,0x02,  0x02,   0x01,T_U16,                             /*  55 | / 55, /LDIS (l2cap_disconnect) */
    0x08,0x03,  0x04,   0x02,T_U16,T_U16,                       /*  56 | / 56, /LRP (l2cap_register_psm) */
    0x08,0x04,  0x0B,   0x06,T_U8,T_U16,T_U16,T_U16,T_U16,T_U16,/*  57 | / 57, /LCR (l2cap_send_connreq_response) */
    0x08,0x05,  0x04,   0x02,T_U16,T_U16,                       /*  58 | / 58, /LSC (l2cap_send_credits) */
    0x08,0x06,  0x85,   0x03,T_U8,T_U16,T_LU8A,                 /*  59 | / 59, /LD (l2cap_send_data) */
    0x09,0x01,  0x01,   0x01,T_U8,                              /*  60 | / 60, /QIOL (gpio_query_logic) */
    0x09,0x02,  0x02,   0x02,T_U8,T_U8,                         /*  61 | / 61, /QADC (gpio_query_adc) */
    0x01,0x01,  0x01,   0x01,T_U8,                              /*  62 | S  0, SPPM (protocol_set_parse_mode) */
    0x01,0x03,  0x01,   0x01,T_U8,                              /*  63 | S  1, SPEM (protocol_set_echo_mode) */
    0x02,0x0D,  0x06,   0x01,T_MAC,                             /*  64 | S  2, SBA (system_set_bluetooth_address) */
    0x02,0x0F,  0x02,   0x01,T_U16,                             /*  65 | S  3, SECO (system_set_eco_parameters) */
    0x02,0x11,  0x01,   0x01,T_U8,                              /*  66 | S  4, SWCO (system_set_wco_parameters) */
    0x02,0x13,  0x01,   0x01,T_U8,                              /*  67 | S  5, SSLP (system_set_sleep_parameters) */
    0x02,0x15,  0x01,   0x01,T_U8,                              /*  68 | S  6, STXP (system_set_tx_power) */
    0x02,0x17,  0x01,   0x01,T_U8,                              /*  69 | S  7, ST (system_set_transport) */
    0x02,0x19,  0x0A,   0x07,T_U32,T_U8,T_U8,T_U8,T_U8,T_U8,T_U8,
                                                                /*  70 | S  8, STU (system_set_uart_parameters) */
    0x04,0x0F,  0x81,   0x01,T_STR,                             /*  71 | S  9, SDN (gap_set_device_name) */
    0x04,0x11,  0x02,   0x01,T_U16,                             /*  72 | S 10, SDA (gap_set_device_appearance) */
    0x04,0x13,  0x81,   0x01,T_U8A,                             /*  73 | S 11, SAD (gap_set_adv_data) */
    0x04,0x15,  0x81,   0x01,T_U8A,                             /*  74 | S 12, SSRD (gap_set_sr_data) */
    0x04,0x17,  0x09,   0x07,T_U8,T_U8,T_U16,T_U8,T_U8,T_U16,T_U8,
                                                                /*  75 | S 13, SAP (gap_set_adv_parameters) */
    0x04,0x19,  0x0A,   0x07,T_U8,T_U16,T_U16,T_U8,T_U8,T_U8,T_U16,
                                                                /*  76 | S 14, SSP (gap_set_scan_parameters) */
    0x04,0x1B,  0x0C,   0x06,T_U16,T_U16,T_U16,T_U16,T_U16,T_U16,
                                                                /*  77 | S 15, SCP (gap_set_conn_parameters) */
    0x05,0x0E,  0x01,   0x01,T_U8,                              /*  78 | S 16, SGSP (gatts_set_parameters) */
    0x06,0x07,  0x01,   0x01,T_U8,                              /*  79 | S 17, SGCP (gattc_set_parameters) */
    0x07,0x09,  0x03,   0x02,T_U8,T_U16,                        /*  80 | S 18, SPRV (smp_set_privacy_mode) */
    0x07,0x0B,  0x06,   0x06,T_U8,T_U8,T_U8,T_U8,T_U8,T_U8,     /*  81 | S 19, SSBP (smp_set_security_parameters) */
    0x09,0x03,  0x04,   0x04,T_U8,T_U8,T_U8,T_U8,               /*  82 | S 20, SIOF (gpio_set_function) */
    0x09,0x05,  0x06,   0x06,T_U8,T_U8,T_U8,T_U8,T_U8,T_U8,     /*  83 | S 21, SIOD (gpio_set_drive) */
    0x09,0x07,  0x03,   0x03,T_U8,T_U8,T_U8,                    /*  84 | S 22, SIOL (gpio_set_logic) */
    0x09,0x09,  0x04,   0x04,T_U8,T_U8,T_U8,T_U8,               /*  85 | S 23, SIOI (gpio_set_interrupt_mode) */
    0x09,0x0B,  0x08,   0x06,T_U8,T_U8,T_U8,T_U8,T_U16,T_U16,   /*  86 | S 24, SPWM (gpio_set_pwm_mode) */
    0x01,0x02,  0x00,   0x00,                                   /*  87 | G  0, GPPM (protocol_get_parse_mode) */
    0x01,0x04,  0x00,   0x00,                                   /*  88 | G  1, GPEM (protocol_get_echo_mode) */
    0x02,0x0E,  0x00,   0x00,                                   /*  89 | G  2, GBA (system_get_bluetooth_address) */
    0x02,0x10,  0x00,   0x00,                                   /*  90 | G  3, GECO (system_get_eco_parameters) */
    0x02,0x12,  0x00,   0x00,                                   /*  91 | G  4, GWCO (system_get_wco_parameters) */
    0x02,0x14,  0x00,   0x00,                                   /*  92 | G  5, GSLP (system_get_sleep_parameters) */
    0x02,0x16,  0x00,   0x00,                                   /*  93 | G  6, GTXP (system_get_tx_power) */
    0x02,0x18,  0x00,   0x00,                                   /*  94 | G  7, GT (system_get_transport) */
    0x02,0x1A,  0x00,   0x00,                                   /*  95 | G  8, GTU (system_get_uart_parameters) */
    0x04,0x10,  0x00,   0x00,                                   /*  96 | G  9, GDN (gap_get_device_name) */
    0x04,0x12,  0x00,   0x00,                                   /*  97 | G 10, GDA (gap_get_device_appearance) */
    0x04,0x14,  0x00,   0x00,                                   /*  98 | G 11, GAD (gap_get_adv_data) */
    0x04,0x16,  0x00,   0x00,                                   /*  99 | G 12, GSRD (gap_get_sr_data) */
    0x04,0x18,  0x00,   0x00,                                   /* 100 | G 13, GAP (gap_get_adv_parameters) */
    0x04,0x1A,  0x00,   0x00,                                   /* 101 | G 14, GSP (gap_get_scan_parameters) */
    0x04,0x1C,  0x00,   0x00,                                   /* 102 | G 15, GCP (gap_get_conn_parameters) */
    0x05,0x0F,  0x00,   0x00,                                   /* 103 | G 16, GGSP (gatts_get_parameters) */
    0x06,0x08,  0x00,   0x00,                                   /* 104 | G 17, GGCP (gattc_get_parameters) */
    0x07,0x0A,  0x00,   0x00,                                   /* 105 | G 18, GPRV (smp_get_privacy_mode) */
    0x07,0x0C,  0x00,   0x00,                                   /* 106 | G 19, GSBP (smp_get_security_parameters) */
    0x09,0x04,  0x01,   0x01,T_U8,                              /* 107 | G 20, GIOF (gpio_get_function) */
    0x09,0x06,  0x01,   0x01,T_U8,                              /* 108 | G 21, GIOD (gpio_get_drive) */
    0x09,0x08,  0x01,   0x01,T_U8,                              /* 109 | G 22, GIOL (gpio_get_logic) */
    0x09,0x0A,  0x01,   0x01,T_U8,                              /* 110 | G 23, GIOI (gpio_get_interrupt_mode) */
    0x09,0x0C,  0x01,   0x01,T_U8,                              /* 111 | G 24, GPWM (gpio_get_pwm_mode) */
    0x0A,0x01,  0x00,   0x00,                                   /* 112 | .  0, .CYSPPCHECK (p_cyspp_check) */
    0x0A,0x02,  0x00,   0x00,                                   /* 113 | .  1, .CYSPPSTART (p_cyspp_start) */
    0x0A,0x03,  0x13,   0x09,T_U8,T_U8,T_U16,T_U32,T_U32,T_U32,T_U8,T_U8,T_U8,
                                                                /* 114 | .  2, .CYSPPSP (p_cyspp_set_parameters) */
    0x0A,0x04,  0x00,   0x00,                                   /* 115 | .  3, .CYSPPGP (p_cyspp_get_parameters) */
    0x0A,0x05,  0x08,   0x04,T_U16,T_U16,T_U16,T_U16,           /* 116 | .  4, .CYSPPSH (p_cyspp_set_client_handles) */
    0x0A,0x06,  0x00,   0x00,                                   /* 117 | .  5, .CYSPPGH (p_cyspp_get_client_handles) */
    0x0A,0x07,  0x04,   0x04,T_U8,T_U8,T_U8,T_U8,               /* 118 | .  6, .CYSPPSK (p_cyspp_set_packetization) */
    0x0A,0x08,  0x00,   0x00,                                   /* 119 | .  7, .CYSPPGK (p_cyspp_get_packetization) */
    0x0B,0x01,  0x88,   0x07,T_U8,T_U8,T_U16,T_U8,T_U8,T_U8,T_U8A,
                                                                /* 120 | .  8, .CYCOMSP (p_cycommand_set_parameters) */
    0x0B,0x02,  0x00,   0x00,                                   /* 121 | .  9, .CYCOMGP (p_cycommand_get_parameters) */
    0x0C,0x01,  0x8A,   0x06,T_U8,T_U16,T_U16,T_U16,T_U16,T_U8A,/* 122 | . 10, .IBSP (p_ibeacon_set_parameters) */
    0x0C,0x02,  0x00,   0x00,                                   /* 123 | . 11, .IBGP (p_ibeacon_get_parameters) */
    0x0D,0x01,  0x85,   0x04,T_U8,T_U16,T_U8,T_U8A,             /* 124 | . 12, .EDDYSP (p_eddystone_set_parameters) */
    0x0D,0x02,  0x00,   0x00,                                   /* 125 | . 13, .EDDYGP (p_eddystone_get_parameters) */
};


/*******************************************************************************
* Event definition table with binary event methods detail
*******************************************************************************/
const uint8_t ezs_tbl_evt[] PROGMEM =
{
    0x02,0x01,  0x12,           /*   0, BOOT (system_boot) */
    0x02,0x02,  0x02,           /*   1, ERR (system_error) */
    0x02,0x03,  0x00,           /*   2, RFAC (system_factory_reset_complete) */
    0x02,0x04,  0x0C,           /*   3, TFAC (system_factory_test_entered) */
    0x02,0x05,  0x04,           /*   4, DBLOB (system_dump_blob) */
    0x03,0x01,  0x02,           /*   5, BDFU (dfu_boot) */
    0x03,0x02,  0x01,           /*   6, CDFU (dfu_client_status) */
    0x04,0x01,  0x07,           /*   7, WL (gap_whitelist_entry) */
    0x04,0x02,  0x02,           /*   8, ASC (gap_adv_state_changed) */
    0x04,0x03,  0x02,           /*   9, SSC (gap_scan_state_changed) */
    0x04,0x04,  0x0B,           /*  10, S (gap_scan_result) */
    0x04,0x05,  0x0F,           /*  11, C (gap_connected) */
    0x04,0x06,  0x03,           /*  12, DIS (gap_disconnected) */
    0x04,0x07,  0x09,           /*  13, UCR (gap_connection_update_requested) */
    0x04,0x08,  0x07,           /*  14, CU (gap_connection_updated) */
    0x05,0x01,  0x08,           /*  15, DL (gatts_discover_result) */
    0x05,0x02,  0x06,           /*  16, W (gatts_data_written) */
    0x05,0x03,  0x03,           /*  17, IC (gatts_indication_confirmed) */
    0x05,0x04,  0x0B,           /*  18, DGATT (gatts_db_entry_blob) */
    0x06,0x01,  0x09,           /*  19, DR (gattc_discover_result) */
    0x06,0x02,  0x03,           /*  20, RPC (gattc_remote_procedure_complete) */
    0x06,0x03,  0x06,           /*  21, D (gattc_data_received) */
    0x06,0x04,  0x05,           /*  22, WRR (gattc_write_response) */
    0x07,0x01,  0x08,           /*  23, B (smp_bond_entry) */
    0x07,0x02,  0x05,           /*  24, P (smp_pairing_requested) */
    0x07,0x03,  0x03,           /*  25, PR (smp_pairing_result) */
    0x07,0x04,  0x02,           /*  26, ENC (smp_encryption_status) */
    0x07,0x05,  0x05,           /*  27, PKD (smp_passkey_display_requested) */
    0x07,0x06,  0x01,           /*  28, PKE (smp_passkey_entry_requested) */
    0x08,0x01,  0x0B,           /*  29, LCR (l2cap_connection_requested) */
    0x08,0x02,  0x0B,           /*  30, LC (l2cap_connection_response) */
    0x08,0x03,  0x04,           /*  31, LD (l2cap_data_received) */
    0x08,0x04,  0x05,           /*  32, LDIS (l2cap_disconnected) */
    0x08,0x05,  0x05,           /*  33, LRCL (l2cap_rx_credits_low) */
    0x08,0x06,  0x05,           /*  34, LTCR (l2cap_tx_credits_received) */
    0x08,0x07,  0x05,           /*  35, LREJ (l2cap_command_rejected) */
    0x09,0x01,  0x09,           /*  36, INT (gpio_interrupt) */
    0x0A,0x01,  0x01,           /*  37, .CYSPP (p_cyspp_status) */
    0x0B,0x01,  0x01,           /*  38, .CYCOM (p_cycommand_status) */
};


/*******************************************************************************
* Application event handler callback for processing API responses and events.
* This must be defined as non-NULL in the "EZSerial_Start" call.
*******************************************************************************/
#define EZSerial_AppHandler EZSerial.appHandler


/*******************************************************************************
* Platform-specific output function for sending API commands. This must be
* defined as non-NULL in the "EZSerial_Start" call if you intend to use any of
* the library-provided "ezs_cmd_..." functions to send binary command packets.
*******************************************************************************/
#define EZSerial_HardwareOutput EZSerial.appOutput


/*******************************************************************************
* Platform-specific input function for reading API response and event data. This
* must be defined as non-NULL in the "EZSerial_Start" call if you intend to use
* any of the library-provided "EZS_CHECK_..." and "EZS_WAIT_..." macros.
*******************************************************************************/
#define EZSerial_HardwareInput EZSerial.appInput


/**
 * @brief Initialize EZ-Serial API parser/generator and host I/O handlers
 */
void EZSerial_Init()
{
    ezs_rx_packet_buffer = (uint8_t *)&ezs_rx_packet;
    ezs_rx_packet_length = 0;
} /* EZSerial_Init */


/**
 * @brief Parse incoming EZ-Serial response/event data from module
 * @param b Incoming byte to parse
 * @return Result code (non-zero indicates error)
 */
ezs_input_result_t EZSerial_Parse(uint8_t b)
{
    ezs_input_result_t result = 0;
    
    /* make sure our packet container is big enough (always at least +1 byte) */
    if (ezs_rx_packet_length + 1 >= sizeof(ezs_packet_t))
    {
        /* no memory left, reset the parser and generate an error */
        ezs_rx_packet_length = 0;
        result = EZS_INPUT_RESULT_BUFFER_OVERFLOW;
    }
    /* make sure data is valid (SOF response/event or already in packet) */
    else if (ezs_rx_packet_length != 0 || (b & EZS_BINARY_SOF_MASK) != 0)
    {
        /* initialize checksum if start-of-frame */
        if (ezs_rx_packet_length == 0)
        {
            ezs_rx_packet_checksum = EZS_BINARY_CHECKSUM_INITIAL_VALUE;
            
            /* calculate length in advance (4 header bytes + X payload + 1 checksum) */
            /* (3 MSB bits only) */
            ezs_rx_packet_length_expected = 5 + ((uint16_t)(b & 0x7) * 256);
        }
        else if (ezs_rx_packet_length == 1)
        {
            /* calculate length in advance (4 header bytes + X payload + 1 checksum) */
            /* (finish with 8 LSB bits) */
            ezs_rx_packet_length_expected += b;
        }
        
        /* append this byte to packet */
        ezs_rx_packet_buffer[ezs_rx_packet_length] = b;
        ezs_rx_packet_length++;
        
        /* check for a complete packet (including checksum byte) */
        if (ezs_rx_packet_length == ezs_rx_packet_length_expected)
        {
            /* verify checksum (last received byte) */
            if (ezs_rx_packet_checksum == b)
            {
                /* checksum is valid, check for packet type (response or event) */
                if (EZSerial_FillPacketMetaFromBinary(&ezs_rx_packet) == (ezs_input_result_t)EZS_INPUT_RESULT_PACKET_IDENTIFIED)
                {
                    /* packet found in command or event table, send to application handler */
                    EZSerial_AppHandler(&ezs_rx_packet);
                    result = EZS_INPUT_RESULT_PACKET_COMPLETE;
                }
                else
                {
                    /* packet passes structure validity checks but could not be identified */
                    result = EZS_INPUT_RESULT_UNHANDLED_PACKET;
                }
            }
            else
            {
                /* checksum is not valid */
                result = EZS_INPUT_RESULT_INVALID_CHECKSUM;
            }
            
            /* reset all packet metadata */
            ezs_rx_packet_length = 0;
        }
        else
        {
            /* packet is not complete, add byte to checksum value */
            ezs_rx_packet_checksum += b;
            result = EZS_INPUT_RESULT_IN_PROGRESS;
        }
    }
    
    return result;
} /* EZSerial_Parse */


/**
 * @brief Send EZ-Serial binary API command to module
 * @param[in] packet Packet structure to send to module
 * @return Result code (non-zero indicates error)
 */
ezs_output_result_t EZSerial_SendPacket(ezs_packet_t *packet)
{
    uint16_t packet_length;
    uint8_t checksum;
    uint16_t i;

    /* calculate packet length */
    packet_length = 4 + (((packet->header.type & 0x07) << 8) | packet->header.length);
    
    /* calculate checksum byte */
    checksum = EZS_BINARY_CHECKSUM_INITIAL_VALUE;
    for (i = 0; i < packet_length; i++)
    {
        checksum += ((uint8_t *)packet)[i];
    }
    
    /* write checksum byte just after payload in command buffer (always safe) */
    ((uint8_t *)packet)[i] = checksum;
    
    /* send command buffer + checksum byte */
    return EZSerial_HardwareOutput(packet_length + 1, (uint8_t *)packet);
} /* EZSerial_SendPacket */


ezs_input_result_t EZSerial_FillPacketMetaFromBinary(ezs_packet_t *packet)
{
    if ((packet->header.type & EZS_BINARY_TYPE_MASK) == EZS_BINARY_TYPE_CMDRSP)
    {
        /* look up packet in command table (response defs also there) */
        uint8_t *search = (uint8_t *)ezs_tbl_cmd;
        uint8_t idx;
        packet->packet_type = EZS_PACKET_TYPE_RESPONSE;
        for (idx = 0; idx < EZS_CMD_COUNT; idx++)
        {
            /* compare group/id bytes in header */
            if (packet->header.group == pgm_read_byte(&search[0]) && packet->header.id == pgm_read_byte(&search[1]))
            {
                packet->tbl_index = idx;
                packet->cmd_entry = (ezs_tbl_cmd_entry_t *)search;
                return EZS_INPUT_RESULT_PACKET_IDENTIFIED;
            }

            /* move search pointer to next table entry (if we haven't terminated early) */
            search +=
                EZS_TBL_ENTRY_COMMAND_LENGTH_BYTES_MIN +
                pgm_read_byte(&search[EZS_TBL_ENTRY_COMMAND_LENGTH_BYTES_MIN - 1]);
        }

        /* failure: known packet type, unknown group/method ID */
        return EZS_INPUT_RESULT_UNRECOGNIZED_RESPONSE;
    }
    else if ((packet->header.type & EZS_BINARY_TYPE_MASK) == EZS_BINARY_TYPE_EVENT)
    {
        /* look up packet in event table */
        uint8_t *search = (uint8_t *)ezs_tbl_evt;
        uint8_t idx;
        packet->packet_type = EZS_PACKET_TYPE_EVENT;
        for (idx = 0; idx < EZS_EVT_COUNT; idx++)
        {
            /* compare group/id bytes in header */
            if (packet->header.group == pgm_read_byte(&search[0]) && packet->header.id == pgm_read_byte(&search[1]))
            {
                packet->tbl_index = idx + EZS_CMD_COUNT; /* enumerated event index offset starts after last command index */
                packet->evt_entry = (ezs_tbl_evt_entry_t *)search;
                return EZS_INPUT_RESULT_PACKET_IDENTIFIED;
            }

            /* move search pointer to next table entry (if we haven't terminated early) */
            search += EZS_TBL_ENTRY_EVENT_LENGTH_BYTES;
        }

        /* known packet type, but unknown group/method ID */
        return EZS_INPUT_RESULT_UNRECOGNIZED_EVENT;
    }

    /* unknown packet type */
    return EZS_INPUT_RESULT_UNHANDLED_PACKET;
} /* EZSerial_FillPacketMetaFromBinary */


ezs_packet_t *EZSerial_WaitForPacket(ezs_packet_type_t type, uint16_t timeout)
{
    ezs_input_result_t result = 0;
    uint8_t b;
    
    if (timeout == 0)
    {
        /* just check, don't wait */
        if ((result = EZSerial_HardwareInput(&b, 0)) == EZS_INPUT_RESULT_BYTE_READ)
        {
            /* parse byte */
            result = EZSerial_Parse(b);
            
            /* check for completion and type */
            if (result == EZS_INPUT_RESULT_PACKET_COMPLETE &&
                type != EZS_PACKET_TYPE_ANY && 
                type != ezs_rx_packet.packet_type)
            {
                /* change the result so we don't exit early, but wait for another packet */
                result = EZS_INPUT_RESULT_BYTE_IGNORED;
            }
        }
    }        
    else
    {
        /* wait specified time, or forever */
        while (result != EZS_INPUT_RESULT_PACKET_COMPLETE)
        {
            /* attempt to read a byte */
            result = EZSerial_HardwareInput(&b, timeout);
            if (result == EZS_INPUT_RESULT_BYTE_READ)
            {
                /* byte read, send it to parser */
                result = EZSerial_Parse(b);
                
                /* check for completion and type */
                if (result == EZS_INPUT_RESULT_PACKET_COMPLETE &&
                    type != EZS_PACKET_TYPE_ANY && 
                    type != ezs_rx_packet.packet_type)
                {
                    /* change the result so we don't exit early, but wait for another packet */
                    result = EZS_INPUT_RESULT_BYTE_IGNORED;
                }
            }
            else if (result == EZS_INPUT_RESULT_TIMEOUT)
            {
                /* check for non-infinite timeout */
                if (timeout != 0xFFFF)
                {
                    /* timeout condition met, return null pointer */
                    return 0;
                }
            }
        }
    }
    
    /* send back a pointer to the received packet if successful */
    if (result == EZS_INPUT_RESULT_PACKET_COMPLETE)
    {
        /* ensure it's the right packet type */
        if (type != EZS_PACKET_TYPE_ANY && type != ezs_rx_packet.packet_type) {
            /* packet type mismatch, return null pointer */
            return 0;
        }
        
        /* correct type, packet complete */
        return &ezs_rx_packet;
    }
    
    /* no packet received by this point, return null */
    return 0;
}
    
ezs_output_result_t ezs_cmd_va(uint16_t index, uint8_t memory, ...)
{
    ezs_packet_t *packet = &ezs_tx_packet;
    uint8_t *search = (uint8_t *)ezs_tbl_cmd;
    uint8_t *payload = (uint8_t *)&ezs_tx_packet.payload;
    uint8_t i;
    uint16_t size;
    uint32_t value;
    uint8_t *pointer;
    va_list argv;
    
    /* validate command index */
    if (index >= EZS_IDX_CMD_MAX)
    {
        return EZS_OUTPUT_RESULT_UNRECOGNIZED_COMMAND;
    }
    
    /* jump to correct position in command table */
    for (i = 0; i < index; i++)
    {
        search +=
            EZS_TBL_ENTRY_COMMAND_LENGTH_BYTES_MIN +
            pgm_read_byte(&search[EZS_TBL_ENTRY_COMMAND_LENGTH_BYTES_MIN - 1]);
    }
    
    /* pull packet data from command table and initialize */
    packet->packet_type = EZS_PACKET_TYPE_COMMAND;
    packet->tbl_index = index;
    packet->cmd_entry = (ezs_tbl_cmd_entry_t *)search;
    packet->header.group = pgm_read_byte(search++);
    packet->header.id = pgm_read_byte(search++);
    packet->header.length = pgm_read_byte(search++) & ~EZS_TBL_ENTRY_COMMAND_VARLENGTH_MASK;
    packet->header.type = EZS_BINARY_TYPE_CMDRSP;
    
    /* apply flash memory scope if requested */
    if (memory != 0)
    {
        packet->header.type |= EZS_COMMAND_SCOPE_FLASH;
    }
    
    /* iterate over varargs */
    va_start(argv, memory);
    for (i = pgm_read_byte(search++); i != 0; i--)
    {
        size = 0;
        pointer = 0;
        switch (pgm_read_byte(search++))
        {
            case T_U32:
            case T_S32:
                /* 4 bytes */
                size = 4;
                value = va_arg(argv, uint32_t);
                break;
            case T_U16:
            case T_S16:
                /* 2 bytes, start with 1 and fall through one ++ */
                size = 1;
            case T_U8:
            case T_S8:
                /* 1 byte */
                size++;
                /* va_arg type is NEVER 1-byte wide due to C default argument promotion */
                value = va_arg(argv, uint16_t);
                break;

            case T_MAC:
                /* 6 bytes exactly, start with 4 and fall through two ++ */
                size = 4;
            case T_LU8A:
            case T_LSTR:
                /* 2 bytes minimum, start with 1 and fall through one ++ */
                size++;
            case T_U8A:
            case T_STR:
                /* 1 byte minimum */
                size++;
                pointer = (uint8_t *)va_arg(argv, uint8_t *);
                break;
                
            default:
                /* should never occur, all cases covered */
                break;
        }
        
        /* check for correct type */
        if (pointer != 0)
        {
            /* pointer to uint8a_t, longuint8a_t, or macaddr_t */
            if (size == 1)
            {
                /* uint8a_t, first byte is buffer length */
                size += pointer[0];
                
                /* adjust payload length in header */
                packet->header.length += pointer[0];
            }
            else if (size == 2)
            {
                /* longuint8a_t, first two bytes are buffer length */
                size += pointer[0] + (pointer[1] << 8);
                
                /* adjust payload length in header */
                packet->header.length += pointer[0] + (pointer[1] << 8);
            }
            else if (size == 6)
            {
                /* macaddr_t */
                /* copy 6 bytes directly */
            }
        }
        else
        {
            /* numeric value passed, use it directly */
            pointer = (uint8_t *)&value;
        }
        memcpy(payload, pointer, size);
        payload += size;
    }
    va_end(argv);
    
    return EZSerial_SendPacket(&ezs_tx_packet);
}


/******************************************************************************/
/***              Arduino-specific platform implementations                 ***/
/******************************************************************************/

void EZSLib::initialize(Stream *obj)
{
    EZSerial_Init();
    _initialized = 1;
    _module = obj;
}

void EZSLib::appHandler(ezs_packet_t *packet)
{
    /* reset timeout detection */
    _timeout_start_ref = 0;
    
    if (packet->packet_type == EZS_PACKET_TYPE_RESPONSE)
    {
        /* decrease pending response counter */
        _pending_response--;
    }
    
    /* send packet to app-level callback, if defined */
    if (ezsHandler)
    {
        ezsHandler(packet);
    }
}

ezs_output_result_t EZSLib::appOutput(uint16_t length, const uint8_t *data) {
    /* make sure we aren't already waiting for a response */
    if (_pending_response != 0)
    {
        /* only one pending response at a time is allowed */
        return EZS_OUTPUT_RESULT_RESPONSE_PENDING;
    }

    /* increment pending response counter */
    _pending_response++;
    
    /* send data out through UART */
    _module -> write((uint8_t *)data, length);
    
    return EZS_OUTPUT_RESULT_DATA_WRITTEN;
}

ezs_input_result_t EZSLib::appInput(uint8_t *inByte, uint16_t timeout) {
    uint16_t b;
    
    /* initialize timestamp for timeout detection if necessary */
    if (timeout != 0 && timeout != -1 && _timeout_start_ref == 0)
    {
        _timeout_start_ref = millis();
    }
    
    /* attempt to read a byte from UART */
    if ((b = _module -> read()) < 256)
    {
        /* data available */
        *inByte = b;
        return EZS_INPUT_RESULT_BYTE_READ;
    }
    else if (_pending_response != 0 && timeout != 0 && millis() - _timeout_start_ref > timeout)
    {
        /* no data available, timeout condition */
        _timeout_start_ref = 0;
        return EZS_INPUT_RESULT_TIMEOUT;
    }
    
    return EZS_INPUT_RESULT_NO_DATA;
}

void ezsHandler(ezs_packet_t *packet) __attribute__((weak));
EZSLib EZSerial;