all: evj55.png

evj55.yml:  evj55.cpp connectors/bmw_pedal_v2.yml connectors/gs450h_inverter.yml connectors/l110_ect_solenoid.yml connectors/l110_oil_pump.yml connectors/l110_shift_lever_position_sensor.yml connectors/l110_vehicle_speed_sensor.yml connectors/ls600hl_inverter.yml connectors/toyota_mg1_resolver_conn.yml connectors/toyota_mg2_resolver_conn.yml connectors/zombie56.yml
	cpp evj55.cpp -o evj55.yml

evj55.png: evj55.yml
	wireviz evj55.yml
