all: zombie.png

zombie.yml:  zombie.cpp connectors/bmw_pedal_v2.yml connectors/l110_ect_solenoid.yml connectors/l110_oil_pump.yml connectors/l110_shift_lever_position_sensor.yml connectors/l110_vehicle_speed_sensor.yml connectors/ls600hl_inverter.yml connectors/toyota_mg1_resolver_conn.yml connectors/toyota_mg2_resolver_conn.yml connectors/zombie56.yml
	cpp zombie.cpp -o zombie.yml

zombie.png: zombie.yml
	wireviz zombie.yml
