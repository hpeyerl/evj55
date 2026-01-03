connectors:
#include "connectors/ibooster_gen1.yml"

cables:
  ibooster_pedal_sensor:
    wirecount: 4
    colors: [ BU, GN, BN, YE ]

connections:
-
   - ibooster_gen1_pedal: [ 1, 2, 3, 4 ]
   - ibooster_pedal_sensor: [ 1, 2, 3, 4 ]
   - ibooster_gen1_ecu: [ 2, 22, 8, 23 ]
