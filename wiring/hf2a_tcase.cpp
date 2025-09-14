// P.1019  fj_hdj_hdj-80_series_chassis.pdf
connectors:
#include "connectors/hf2a_tcase.yml"
#include "connectors/hf2a_tcase_relay.yml"

cables:
  hf2a_4wd_actuator:
    wirecount: 4
    colors: [ GNBU, GNBK, GNYE, GN ]
    // [ 2, 5, 6, 3 ]

  transfer_control_relay:
    wirecount: 9
    colors: [ GNBU, GNBK, GNYE, GN, WHBK, BKRD, BK, BKBU, BUBK ]
    // [ 4, 10, 5, 1, 2, 6, 9, 7, 3 ]

// connections:
