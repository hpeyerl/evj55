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

cables:
  Inverter:
    wirecount: 8

  Trans_ECT:
    wirecount: 6

  Go-NoGo-Pedal:
    wirecount: 4
    color_code: DIN
    colors: [ YEBU, BNBU, WHBU, WHGN ]

  MG1_Resolver:
    wirecount: 6

  MG2_Resolver:
    wirecount: 6


connections:
  -
    - zombie56: [ 16-23 ]
    - Inverter: [1-8]
    - ls600hl_inverter: [20, 29, 38, 39, 7, 8, 26, 27 ]
  -
    - zombie56: [ 37-42 ]
    - Trans_ECT: [1-6]
    - l110_ect_solenoid: [ 3, 8, 7, 12, 10, 9 ]
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
