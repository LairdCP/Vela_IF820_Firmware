/*******************************************************************************
* Project Name      : EZSerial_Host_Demo
* File Name         : main.c
* Version           : 1.1.1
* Device Used       : CY8C4245AXI-483
* Software Used     : PSoC Creator 4.1 build 2686
* Compiler          : ARM GCC 5.4-2016-q2-update
* Related Hardware  : CY8CKIT-042 PSoC 4 Pioneer Kit
*                   : CY8CKIT-042-BLE Bluetooth Low Energy Pioneer Kit 
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
* 5LP microcontrollers.
*
* HARDWARE CONNECTIVITY
* ---------------------
* You must connect the hardware UART interface from the Pioneer Kit (P0[4] and
* P0[5] on J4 as RX and TX respectively) to the UART interface of a separate
* CYBLE-212019-00 module (P1[5] and P1[4] as TX and RX, respectively). Module
* serial parameters match EZ-Serial's factory default of 115200,8/N/1. Flow
* control is not used for this demo.
*
* To monitor debug output, open the virtual serial port provided by the Pioneer
* kit's USB interface and ensure the P12[6] pin on J8 and P0[0] pin on J2 on the
* Pioneer kit are connected via a jumper wire. This interface also runs at
* 115200, 8/N/1.
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
* PSOC COMPONENTS
* ---------------
* The project schematic involves one SCB component for module communication, one
* TX-only debug software UART component for debug output, and a timer component
* to manage response timeout detection. No other GPIO signals are involved for
* this demo, although more complex EZ-Serial host projects may use GPIOs to
* monitor for incoming data, connection state, power state, and CYSPP state if
* using CYSPP.
*
* TROUBLESHOOTING
* ---------------
* If you have both a standard Pioneer Kit and a BLE Pioneer Kit connected to
* your PC via USB and you compile and flash the Pioneer Kit with this firmware
* using PSoC Creator, the programmer detection within PSoC Creator will trigger
* a reset on both devices into a debug/program test mode before flashing the
* firmware into the correct target. The BLE Pioneer Kit must be reset once
* using the SW1 RESET button before it will return to the standard EZ-Serial
* application mode; until you do this, communication from the host example will
* fail.
*
* FURTHER READING
* ---------------
* Refer to the PSoC 4 Pioneer Kit User Guide and the EZ-Serial Firmware User
* Guide for details.
********************************************************************************
* Hardware connection for testing:
*   Debug UART  - J8 P12[6] to J2 P0[0] (jumper wire on the Pioneer kit), optional
*   Module UART - Pioneer kit J4 P0[4] (RX) to CYBLE module P1[5] (TX)
*               - Pioneer kit J4 P0[5] (TX) to CYBLE module P1[4] (RX)
*******************************************************************************/

#include <project.h>
#include "ezsapi.h"
#include "handlers.h"

/* enable this to verify required compiler endianness and packing behavior
 * (PSoC 4 will always pass, but you should use this if porting to another platform)
 */
#define TEST_COMPILER_ENDIANNESS_PACKING (0)

/* wait up to 1.5 seconds for a response before assuming communication failed */
/* (EZ-Serial's own command parser timeout is 1 second, so this is conservative) */
#define COMMAND_TIMEOUT_MS (1500)

/* convenience functions for pretty-printing binary data as zero-padded hexadecimal */
void printHex(uint8_t *data, uint8_t bytes, uint8_t reverse, uint8_t separator);
#define printHex8(VARIABLE)     printHex((uint8_t *)&VARIABLE, 1, 1, 0)
#define printHex16(VARIABLE)    printHex((uint8_t *)&VARIABLE, 2, 1, 0)
#define printHex32(VARIABLE)    printHex((uint8_t *)&VARIABLE, 4, 1, 0)
#define printHexMac(VARIABLE)   printHex((uint8_t *)&VARIABLE, 6, 1, ':')

/* main entry point and top-level application logic */
int main()
{
    /* packet pointer for working with response/event data */
    ezs_packet_t *packet;
    
    /* enable global interrupts */
    CyGlobalIntEnable;
    
    /* initialize software serial connection to host */
    UDEBUG_Start();
    UDEBUG_PutString("\r\nEZ-Serial API communication demo started\r\n");
    
    /* code to verify that compiler is little-endian and has functional structure packing */
    #if TEST_COMPILER_ENDIANNESS_PACKING == 1
    {
        /* manually build "rsp_system_get_uart_parameters" response packet */
        uint8_t test_compiler_packing[] = {
            0xC0, 0x0C, 0x02, 0x1A, /* system_get_uart_parameters response header (0x1A020CC0 little-endian) */
            0x11, 0x22,             /* result = 0x2211 test value */
            0x00, 0xC2, 0x01, 0x00, /* baud = 0x0001C200 (115200) test value */
            0xAA, /* autobaud test value */
            0xBB, /* autocorrect test value */
            0xCC, /* flow test value */
            0xDD, /* databits test value */
            0xEE, /* parity test value */
            0xFF  /* stopbits test value */
        };
        
        /* create packet structure pointer to buffer */
        ezs_packet_t *test_packet = (ezs_packet_t *)test_compiler_packing;
        
        /* verify endianness */
        if (test_packet->int_header != 0x1A020CC0)
        {
            /* endianness failed, compiler is using big-endian byte ordering */
            UDEBUG_PutString("\r\nINCOMPATIBLE COMPILER BEHAVIOR:\r\n");
            UDEBUG_PutString("EZ-Serial API byte stream requires little-endian, compiler is big-endian.\r\n");
            UDEBUG_PutString("Please review compiler flags for your toolchain to verify whether it is\r\n");
            UDEBUG_PutString("possible to switch to little-endian data storage.\r\n\r\n");
            while (1)
            {
                /* loop forever, cannot communicate */
            }
        }
        else
        {
            /* successful 32-bit integer byte order comparison */
            UDEBUG_PutString("Compiler endianness passes verification\r\n");
        }
        
        /* verify packing/alignment */
        if (test_packet->payload.rsp_system_get_uart_parameters.result      != 0x2211 ||
            test_packet->payload.rsp_system_get_uart_parameters.baud        != 0x0001C200 ||
            test_packet->payload.rsp_system_get_uart_parameters.autobaud    != 0xAA ||
            test_packet->payload.rsp_system_get_uart_parameters.autocorrect != 0xBB ||
            test_packet->payload.rsp_system_get_uart_parameters.flow        != 0xCC ||
            test_packet->payload.rsp_system_get_uart_parameters.databits    != 0xDD ||
            test_packet->payload.rsp_system_get_uart_parameters.parity      != 0xEE ||
            test_packet->payload.rsp_system_get_uart_parameters.stopbits    != 0xFF)
        {
            /* packing failed, compiler is not tightly packing and/or properly aligning structures */
            UDEBUG_PutString("\r\nINCOMPATIBLE COMPILER BEHAVIOR:\r\n");
            UDEBUG_PutString("Structures must be fully packed, but compiler is generating padding.\r\n");
            UDEBUG_PutString("Please review and modify the __PACKDEF macro definition in ezsapi.h.\r\n\r\n");
            while (1)
            {
                /* loop forever, cannot communicate */
            }
        }
        else
        {
            /* successful read back from packed structure */
            UDEBUG_PutString("Compiler structure packing passes verification\r\n");
        }
    }   
    #endif /* TEST_COMPILER_ENDIANNESS_PACKING */
    
    /* initialize hardware serial connection to module */
    UART_Start();
    
    /* initialize timer interrupt handler */
    TIMERINT_StartEx(TimerInterruptHandler);
    
    /* initialize EZ-Serial interface and callbacks */
    EZSerial_Init(appHandler, appOutput, appInput);
    
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
        UDEBUG_PutString("Ping test timed out, check communication settings and reset module\r\n");
    }
    else
    {
        /* "system_ping" response packet received */
        UDEBUG_PutString("Ping test successful, getting firmware version\r\n");
        
        /* send "system_query_firmware_version" command, then wait for response in loop below */
        ezs_cmd_system_query_firmware_version();
    }
    
    /* run forever waiting for new API packets */
    for (;;)
    {
        /**********************************************************/
        /*** This method demonstrates a non-blocking check for  ***/
        /*** new packets. If there is any data available from   ***/
        /*** the configured module serial interface, the API    ***/
        /*** library will automatically parse it and, if a full ***/
        /*** packet has arrived, trigger a callback to handle   ***/
        /*** the packet via the "ezsHandler" function.          ***/
        /**********************************************************/
        
        /* non-blocking test for incoming data */
        EZS_CHECK_FOR_PACKET();
        
        /* see appHandler() function in "handlers.c" for API response/event handler */
        /* (handles internal response count tracking and then passes to ezsHandler() below) */
    }
}

void ezsHandler(ezs_packet_t *packet)
{
    switch (packet->tbl_index)
    {
        case EZS_IDX_RSP_SYSTEM_PING:
            UDEBUG_PutString("RX: rsp_system_ping: result=");
            printHex16(packet->payload.rsp_system_ping.result);
            UDEBUG_PutString(", runtime=");
            printHex32(packet->payload.rsp_system_ping.runtime);
            UDEBUG_PutString(", fraction=");
            printHex16(packet->payload.rsp_system_ping.fraction);
            break;

        case EZS_IDX_RSP_SYSTEM_QUERY_FIRMWARE_VERSION:
            UDEBUG_PutString("RX: rsp_system_query_firmware_version: app=");
            printHex32(packet->payload.rsp_system_query_firmware_version.app);
            UDEBUG_PutString(", stack=");
            printHex32(packet->payload.rsp_system_query_firmware_version.stack);
            UDEBUG_PutString(", protocol=");
            printHex16(packet->payload.rsp_system_query_firmware_version.protocol);
            UDEBUG_PutString(", hardware=");
            printHex8(packet->payload.rsp_system_query_firmware_version.hardware);
            
            /* check for protocol version older than v1.3 */
            if (packet->payload.rsp_system_query_firmware_version.protocol < 0x0103)
            {
                UDEBUG_PutString("\r\n*** PLEASE UPDATE TARGET MODULE TO LATEST VERISON OF EZ-SERIAL FIRMWARE");
            }
            break;
            
        case EZS_IDX_RSP_SYSTEM_REBOOT:
            UDEBUG_PutString("RX: rsp_system_reboot: result=");
            printHex16(packet->payload.rsp_system_ping.result);
            break;

        case EZS_IDX_EVT_SYSTEM_BOOT:
            UDEBUG_PutString("RX: evt_system_boot: app=");
            printHex32(packet->payload.evt_system_boot.app);
            UDEBUG_PutString(", stack=");
            printHex32(packet->payload.evt_system_boot.stack);
            UDEBUG_PutString(", protocol=");
            printHex16(packet->payload.evt_system_boot.protocol);
            UDEBUG_PutString(", hardware=");
            printHex8(packet->payload.evt_system_boot.hardware);
            UDEBUG_PutString(", cause=");
            printHex8(packet->payload.evt_system_boot.cause);
            UDEBUG_PutString(", address=");
            printHexMac(packet->payload.evt_system_boot.address);
            break;

        case EZS_IDX_EVT_GAP_ADV_STATE_CHANGED:
            UDEBUG_PutString("RX: evt_gap_adv_state_changed: state=");
            printHex8(packet->payload.evt_gap_adv_state_changed.state);
            UDEBUG_PutString(", reason=");
            printHex8(packet->payload.evt_gap_adv_state_changed.reason);
            break;

        case EZS_IDX_EVT_GAP_SCAN_STATE_CHANGED:
            UDEBUG_PutString("RX: evt_gap_scan_state_changed: state=");
            printHex8(packet->payload.evt_gap_scan_state_changed.state);
            UDEBUG_PutString(", reason=");
            printHex8(packet->payload.evt_gap_scan_state_changed.reason);
            break;

        case EZS_IDX_EVT_GAP_CONNECTED:
            UDEBUG_PutString("RX: evt_gap_connected: conn_handle=");
            printHex8(packet->payload.evt_gap_connected.conn_handle);
            UDEBUG_PutString(", address=");
            printHexMac(packet->payload.evt_gap_connected.address);
            UDEBUG_PutString(", type=");
            printHex8(packet->payload.evt_gap_connected.type);
            UDEBUG_PutString(", interval=");
            printHex16(packet->payload.evt_gap_connected.interval);
            UDEBUG_PutString(", slave_latency=");
            printHex16(packet->payload.evt_gap_connected.slave_latency);
            UDEBUG_PutString(", supervision_timeout=");
            printHex16(packet->payload.evt_gap_connected.supervision_timeout);
            UDEBUG_PutString(", bond=");
            printHex8(packet->payload.evt_gap_connected.bond);
            break;

        case EZS_IDX_EVT_GAP_DISCONNECTED:
            UDEBUG_PutString("RX: evt_gap_disconnected: conn_handle=");
            printHex8(packet->payload.evt_gap_disconnected.conn_handle);
            UDEBUG_PutString(", reason=");
            printHex16(packet->payload.evt_gap_disconnected.reason);
            break;

        case EZS_IDX_EVT_P_CYSPP_STATUS:
            UDEBUG_PutString("RX: evt_p_cyspp_status: status=");
            printHex8(packet->payload.evt_p_cyspp_status.status);
            break;
            
        default:
            UDEBUG_PutString("RX: unhandled packet: ");
            printHex8(packet->header.group);
            UDEBUG_PutChar('/');
            printHex8(packet->header.id);
            break;
    }
    
    UDEBUG_PutString("\r\n");
}
        
void printHex(uint8_t *data, uint8_t bytes, uint8_t reverse, uint8_t separator)
{
    if (reverse) data += bytes;
    while (bytes)
    {
        if (reverse) data--;
        UDEBUG_PutChar(((*data >> 4) & 0xF) < 10 ? ('0' + ((*data >> 4) & 0xF)) : ('A' - 10 + ((*data >> 4) & 0xF)));
        UDEBUG_PutChar(( *data       & 0xF) < 10 ? ('0' + ( *data       & 0xF)) : ('A' - 10 + ( *data       & 0xF)));
        if (!reverse) data++;
        bytes--;
        if (bytes && separator) UDEBUG_PutChar(separator);
    }
}

/* [] END OF FILE */
