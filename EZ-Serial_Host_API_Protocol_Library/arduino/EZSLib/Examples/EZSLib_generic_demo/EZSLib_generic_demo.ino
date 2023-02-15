/*******************************************************************************
* Project Name      : EZSLib_generic_demo
* File Name         : EZSLib_generic_demo.ino
* Version           : 1.1.0
* Device Used       : Arduino Uno (ATMEGA328P)
* Software Used     : Arduino IDE v1.8.2
* Related Hardware  : Arduino Uno R3
*                   : CYBLE-212019-SHIELD
*                   : CYBLE-212019-00 EZ-BLE module
*                   : CYBLE-212019-EVAL module
* Owner             : JROW
*
********************************************************************************
* Copyright 2017, Cypress Semiconductor Corporation. All Rights Reserved.
********************************************************************************
* This software is owned by Cypress Semiconductor Corporation (Cypress)
* and is protected by and subject to worldwide patent protection (United
* States and foreign), United States copyright laws and international treaty
* provisions. Cypress hereby grants to licensee a personal, non-exclusive,
* non-transferable license to copy, use, modify, create derivative works of,
* and compile the Cypress Source Code and derivative works for the sole
* purpose of creating custom software in support of licensee product to be
* used only in conjunction with a Cypress integrated circuit as specified in
* the applicable agreement. Any reproduction, modification, translation,
* compilation, or representation of this software except as specified above 
* is prohibited without the express written permission of Cypress.
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
* such use and in doing so indemnifies Cypress against all charges. 
*
* Use of this Software may be limited by and subject to the applicable Cypress
* software license agreement. 
*******************************************************************************/

/*******************************************************************************
*                           THEORY OF OPERATION
********************************************************************************
* This project demonstrates basic host API protocol control of a Cypress EZ-BLE
* module running EZ-Serial firmware. It uses the standard host API protocol
* reference library that is provided with the EZ-Serial firmware, and it shows
* how to use commands, wait for responses, and handle events.
*
* PROTOCOL PACKET STRUCTURE
* -------------------------
* Since the API protocol uses a packed byte stream, the API host library expects
* matching byte ordering and packet structure mapping in order to avoid any
* extra processing overhead. The module (and low-level Bluetooth spec) uses
* little-endian byte ordering, so the host must also for all multi-byte integer
* data. 
*
* To assist in porting to other platforms, this project includes a block of code 
* which verifies proper support and configuration of byte ordering and structure
* packing. While it is not possible to provide a single, comprehensive cross-
* platform implementation of a structure packing macro due to variations between 
* compilers, it is possible to definitively identify whether the existing code
* will work properly. This can quickly identify and avoid potential problems
* that are otherwise very difficult to troubleshoot. Refer to the compile macro
* TEST_COMPILER_ENDIANNESS_PACKING and conditional code block in the main()
* function for the verification code.
*
* The endianness and packing test code will always succeed on PSoC 4 and PSoC
* 5LP microcontrollers. The Arduino Uno is also compatible. For this test code,
* please refer to the EZ-Serial host API example project for the CY8CKIT-042.
*
* HARDWARE CONNECTIVITY
* ---------------------
* You must connect the SoftwareSerial pins from the Arduino Uno (10 and 11 as
* host RX and TX respectively) to the UART interface of a CYBLE-212019-00 module
* (P1[5] and P1[4] as TX and RX, respectively). MODULE SERIAL PARAMETERS MUST BE
* CHANGED TO 9600 BAUD rather than using EZ-Serial's factory default of 115200,
* 8/N/1. Flow control is not used for this demo. The baud reconfiguration may be
* done with these commands sent in text mode (first set, then store in flash):
*
*   STU,B=2580
*   /SCFG
*
* In binary mode, use these API calls:
*
*   ezs_cmd_system_set_uart_parameters(9600, 0, 0, 0, 8, 0, 1);
*       [switch to 9600 baud here]
*   ezs_cmd_system_store_config();
*
* The CYBLE-212019-SHIELD Arduino Shield has a special default baud rate value
* set to 9600 instead of the 115200 value used on the bare module. If you are
* using the shield from Cypress, there is no need to reconfigure this setting.
*
* To monitor debug output, open the Arduino Serial Monitor from within the IDE.
* This interface also runs at 9600, 8/N/1.
*
* COMMUNICATION DEMONSTRATION
* ---------------------------
* The demo begins by sending the "system_ping" command and waiting for the
* expected response via the EZS_SEND_AND_WAIT() macro. While this method makes
* program flow more obvious, it also blocks execution. As an alternative, you
* can simply call the command method ("ezs_cmd_...") and then place the
* EZS_CHECK_FOR_PACKET() macro in your main program loop. When any response or
* event packet comes back, the API parser will call the application handler
* callback function assigned during initialization, and you can update the
* program state as desired. See "handlers.c" for detail.
*
* FURTHER READING
* ---------------
* Refer to the online Arduino reference material and the EZ-Serial Firmware User
* Guide for details.
********************************************************************************
* Hardware connection required for testing:
*   Module UART - Arduino Pin 10 (SW RX) to CYBLE module P1[5] (TX)
*               - Arduino Pin 11 (SW TX) to CYBLE module P1[4] (RX)
*******************************************************************************/

#include <SoftwareSerial.h>
#include <EZSLib.h>

/* wait up to 1.5 seconds for a response before assuming communication failed */
/* (EZ-Serial's own command parser timeout is 1 second, so this is conservative) */
#define COMMAND_TIMEOUT_MS  (1500)

/* use bit-banged (software) serial for module communication, leave hardware UART for host */
SoftwareSerial modSerial(10, 11); /* 10=RX, 11=TX */

/* convenience function and macros for pretty-printing binary data as zero-padded hexadecimal */
void printHex(Stream *out, uint8_t *data, uint8_t bytes, uint8_t reverse, uint8_t separator);
#define printHex8(VARIABLE)     printHex(&Serial, (uint8_t *)&VARIABLE, 1, 1, 0)
#define printHex16(VARIABLE)    printHex(&Serial, (uint8_t *)&VARIABLE, 2, 1, 0)
#define printHex32(VARIABLE)    printHex(&Serial, (uint8_t *)&VARIABLE, 4, 1, 0)
#define printHexMac(VARIABLE)   printHex(&Serial, (uint8_t *)&VARIABLE, 6, 1, ':')

/* Arduino "setup()" function runs once after boot/reset */
void setup()
{
    /* packet pointer for working with response/event data */
    ezs_packet_t *packet;

    /* initialize hardware serial connection to host */
    Serial.begin(9600);
    Serial.println(F("\r\nEZ-Serial API communication demo started"));

    /* initialize software serial connection to module */
    modSerial.begin(9600);

    /* initialize EZ-Serial interface (EZSLib code handles platform I/O callbacks internally) */
    EZSerial.initialize(&modSerial);

    /**********************************************************/
    /*** This method demonstrates a blocking send-and-wait  ***/
    /*** call for transmitting a command packet and then    ***/
    /*** waiting for a response packet to come back before  ***/
    /*** proceeding. This approach can be convenient for    ***/
    /*** command/response cycles, but cannot be used for    ***/
    /*** events.                                            ***/
    /***                                                    ***/
    /*** NOTE: response packets will also cause a callback  ***/
    /*** to be triggered via the "ezsHandler" function. You ***/
    /*** do not need to process it there, but you can if    ***/
    /*** needed.                                            ***/
    /**********************************************************/
    
    /* send "system_ping" command to test module connectivity */
    if ((packet = EZS_SEND_AND_WAIT(ezs_cmd_system_ping(), COMMAND_TIMEOUT_MS)) == 0)
    {
        /* "system_ping" response packet not received */
        Serial.println(F("Ping test timed out, check communication settings and reset module"));
    }
    else
    {
        /* "system_ping" response packet received */
        Serial.println(F("Ping test successful, getting firmware version"));

        /* send "system_query_firmware_version" command, then wait for response in loop below */
        ezs_cmd_system_query_firmware_version();
    }
}

/* Arduino "loop()" function runs forever after "setup()" finishes */
void loop()
{
    /**********************************************************/
    /*** This method demonstrates a non-blocking check for  ***/
    /*** new packets. If there is any data available from   ***/
    /*** the configured module serial interface, the API    ***/
    /*** library will automatically parse it and, if a full ***/
    /*** packet has arrived, trigger a callback to handle   ***/
    /*** the packet via the "ezsHandler" function.          ***/
    /**********************************************************/

    /* constantly check for new incoming data (non-blocking) */
    EZS_CHECK_FOR_PACKET();
}

/* ezsHandler defined here is called every time a packet is parsed successfully */
/* (see EZSLib.h for prototype and EZSLib.cpp for weak implementation) */
void ezsHandler(ezs_packet_t *packet)
{
    switch (packet->tbl_index)
    {
        case EZS_IDX_RSP_SYSTEM_PING:
            Serial.print(F("RX: rsp_system_ping: result="));
            printHex16(packet->payload.rsp_system_ping.result);
            Serial.print(F(", runtime="));
            printHex32(packet->payload.rsp_system_ping.runtime);
            Serial.print(F(", fraction="));
            printHex16(packet->payload.rsp_system_ping.fraction);
            break;

        case EZS_IDX_RSP_SYSTEM_QUERY_FIRMWARE_VERSION:
            Serial.print(F("RX: rsp_system_query_firmware_version: app="));
            printHex32(packet->payload.rsp_system_query_firmware_version.app);
            Serial.print(F(", stack="));
            printHex32(packet->payload.rsp_system_query_firmware_version.stack);
            Serial.print(F(", protocol="));
            printHex16(packet->payload.rsp_system_query_firmware_version.protocol);
            Serial.print(F(", hardware="));
            printHex8(packet->payload.rsp_system_query_firmware_version.hardware);
            
            /* check for protocol version older than v1.3 */
            if (packet->payload.rsp_system_query_firmware_version.protocol < 0x0103)
            {
                Serial.print(F("\r\n*** PLEASE UPDATE TARGET MODULE TO LATEST VERISON OF EZ-SERIAL FIRMWARE"));
            }
            break;
            
        case EZS_IDX_RSP_SYSTEM_REBOOT:
            Serial.print(F("RX: rsp_system_reboot: result="));
            printHex16(packet->payload.rsp_system_ping.result);
            break;

        case EZS_IDX_EVT_SYSTEM_BOOT:
            Serial.print(F("RX: evt_system_boot: app="));
            printHex32(packet->payload.evt_system_boot.app);
            Serial.print(F(", stack="));
            printHex32(packet->payload.evt_system_boot.stack);
            Serial.print(F(", protocol="));
            printHex16(packet->payload.evt_system_boot.protocol);
            Serial.print(F(", hardware="));
            printHex8(packet->payload.evt_system_boot.hardware);
            Serial.print(F(", cause="));
            printHex8(packet->payload.evt_system_boot.cause);
            Serial.print(F(", address="));
            printHexMac(packet->payload.evt_system_boot.address);
            break;

        case EZS_IDX_EVT_GAP_ADV_STATE_CHANGED:
            Serial.print(F("RX: evt_gap_adv_state_changed: state="));
            printHex8(packet->payload.evt_gap_adv_state_changed.state);
            Serial.print(F(", reason="));
            printHex8(packet->payload.evt_gap_adv_state_changed.reason);
            break;

        case EZS_IDX_EVT_GAP_SCAN_STATE_CHANGED:
            Serial.print(F("RX: evt_gap_scan_state_changed: state="));
            printHex8(packet->payload.evt_gap_scan_state_changed.state);
            Serial.print(F(", reason="));
            printHex8(packet->payload.evt_gap_scan_state_changed.reason);
            break;

        case EZS_IDX_EVT_GAP_CONNECTED:
            Serial.print(F("RX: evt_gap_connected: conn_handle="));
            printHex8(packet->payload.evt_gap_connected.conn_handle);
            Serial.print(F(", address="));
            printHexMac(packet->payload.evt_gap_connected.address);
            Serial.print(F(", type="));
            printHex8(packet->payload.evt_gap_connected.type);
            Serial.print(F(", interval="));
            printHex16(packet->payload.evt_gap_connected.interval);
            Serial.print(F(", slave_latency="));
            printHex16(packet->payload.evt_gap_connected.slave_latency);
            Serial.print(F(", supervision_timeout="));
            printHex16(packet->payload.evt_gap_connected.supervision_timeout);
            Serial.print(F(", bond="));
            printHex8(packet->payload.evt_gap_connected.bond);
            break;

        case EZS_IDX_EVT_GAP_DISCONNECTED:
            Serial.print(F("RX: evt_gap_disconnected: conn_handle="));
            printHex8(packet->payload.evt_gap_disconnected.conn_handle);
            Serial.print(F(", reason="));
            printHex16(packet->payload.evt_gap_disconnected.reason);
            break;

        case EZS_IDX_EVT_P_CYSPP_STATUS:
            Serial.print(F("RX: evt_p_cyspp_status: status="));
            printHex8(packet->payload.evt_p_cyspp_status.status);
            break;
            
        default:
            Serial.print(F("RX: unhandled packet: "));
            printHex8(packet->header.group);
            Serial.write('/');
            printHex8(packet->header.id);
            break;
    }
    
    Serial.print(F("\r\n"));
}

/* convenience function for pretty-printing binary data as zero-padded hexadecimal */
void printHex(Stream *out, uint8_t *data, uint8_t bytes, uint8_t reverse, uint8_t separator)
{
    if (reverse) data += bytes;
    while (bytes)
    {
        if (reverse) data--;
        out->write(((*data >> 4) & 0xF) < 10 ? ('0' + ((*data >> 4) & 0xF)) : ('A' - 10 + ((*data >> 4) & 0xF)));
        out->write(( *data       & 0xF) < 10 ? ('0' + ( *data       & 0xF)) : ('A' - 10 + ( *data       & 0xF)));
        if (!reverse) data++;
        bytes--;
        if (bytes && separator) out->write(separator);
    }
}