connectors:
#include "connectors/zombie56.yml"
#include "connectors/ls600hl_inverter.yml"
#include "connectors/l110_oil_pump.yml"
#include "connectors/l110_ect_solenoid.yml"
#include "connectors/l110_shift_lever_position_sensor.yml"
#include "connectors/toyota_mg1_resolver_conn.yml"
#include "connectors/toyota_mg2_resolver_conn.yml"
#include "connectors/l110_vehicle_speed_sensor.yml"
#include "connectors/bmw_pedal_v2.yml"
#include "connectors/12awg_heat_shrink_ring_terminal.yml"

// Inverter connector colors
//    colors: [ BN, WH, BK, WH, BN, BK, WH, BN, BU, BK,
//              BK, BN, WH, BK, WH, BK, YE, RD, WH, GN,
//              BN, WH, BK, WH, BK, BN, YE, RD, GN, WHBK,
//              WHBK, BN, WH, BK, BK, BN, WH, WH, BU, BK ]
cables:
  Inverter:
    wirecount: 8
    colors: [ WH, BK, WH, BK, WH, BK, WH, BK ]

  Trans_ECT:
    wirecount: 6

  Go-NoGo-Pedal:
    wirecount: 4
    color_code: DIN
    colors: [ YEBU, BNBU, WHBU, WHGN ]

  MG1_Resolver:
    wirecount: 6
    colors: [ BK, BU, WH, GN, RD, YE ]

  MG2_Resolver:
    wirecount: 6
    colors: [ GN, RD, YE, BU, WH, BK ]

  Oil_Pump:
    wirecount: 1
    colors: [ BK ]

  Oil_Pump_B:
    wirecount: 1
    colors: [ RD ]


connections:
  -
    - zombie56: [ 16-23 ]
    - Inverter: [1-8]
    - ls600hl_inverter: [33, 34, 13, 14, 2, 3, 22, 23 ]
  -
    - zombie56: [ 37-42 ]
    - Trans_ECT: [1-6]
    - l110_ect_solenoid: [ 3, 8, 7, 12, 10, 9 ]
  -
    - zombie56: [ 30 ]
    - Oil_Pump: [ 1]
    - l110_oil_pump: [ 6 ]
  -
    - l110_oil_pump: [ 5 ]
    - Oil_Pump_B: [ 1 ]
    - ring_terminal: [ 1 ]
  -
    - ls600hl_inverter: [ 33, 23, 24, 22, 35, 34 ]
    - MG1_Resolver: [ 1-6 ]
    - mg1_resolver_conn: [ 1, 2, 3, 5, 6, 7 ]
  -
    - ls600hl_inverter: [ 1, 14, 13, 11, 3, 2 ]
    - MG2_Resolver: [ 1-6 ]
    - mg2_resolver_conn: [ 1, 2, 3, 5, 6, 7 ]
  -
    - zombie56: [ 45-48]
    - Go-NoGo-Pedal: [ 1-4 ]
    - bmw_pedal_v2: [ 3, 2, 4, 6 ]
