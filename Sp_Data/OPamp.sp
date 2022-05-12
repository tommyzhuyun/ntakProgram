***-< OPAMP Topology >-***
.lib opamp
.param   psvoltage=3.0e+00
.csparam psvoltage=psvoltage
.subckt	opamp	inm	inp	vout	vdd	vss

M1 N001 inm  N003 N003 cmosn l=2u w=3.8u
M2 N002 N001 VDD VDD cmosp l=2u w=3.8u
M3 N002 inp  N003 N003 cmosn l=2u w=3.8u
M4 N001 N001 VDD VDD cmosp l=2u w=3.8u
M5 N003 N005 VSS VSS cmosn l=2u w=27u
M6 Vout N002 VDD VDD cmosp l=2u w=62u
M7 Vout N005 VSS VSS cmosn l=2u w=260u
M8 N005 N005 VSS VSS cmosn l=2u w=27u
C1 Vout N002 0.3p
R1 VDD N005 115k

.ends	opamp
.endl
