all: zombie.png
ZOMBIE_DIR=gs450h_ls600hl_zombie_vcu

CONNECTORS=  \
             ${ZOMBIE_DIR}/connectors/bmw_pedal_v2.yml \
             ${ZOMBIE_DIR}/connectors/honda_fit_pedal.yml \
             ${ZOMBIE_DIR}/connectors/l110_ect_solenoid.yml \
             ${ZOMBIE_DIR}/connectors/l110_oil_pump.yml \
             ${ZOMBIE_DIR}/connectors/l110_shift_lever_position_sensor.yml \
             ${ZOMBIE_DIR}/connectors/l110_vehicle_speed_sensor.yml \
             ${ZOMBIE_DIR}/connectors/ls600hl_inverter.yml \
             ${ZOMBIE_DIR}/connectors/toyota_mg1_resolver_conn.yml \
             ${ZOMBIE_DIR}/connectors/toyota_mg2_resolver_conn.yml \
             ${ZOMBIE_DIR}/connectors/zombie56.yml  \
             ${ZOMBIE_DIR}/connectors/12awg_heat_shrink_ring_terminal.yml

zombie.yml:  ${ZOMBIE_DIR}/zombie.cpp  ${CONNECTORS}
	cpp ${ZOMBIE_DIR}/zombie.cpp -o zombie.yml

zombie.png: zombie.yml
	wireviz zombie.yml
