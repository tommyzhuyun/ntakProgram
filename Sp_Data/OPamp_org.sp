***-< DEPARTMENT 3 OPAMP >-***
.lib opamp
.param   psvoltage=3.0e+00
.csparam psvoltage=psvoltage
.subckt	opamp	inm	inp	out	vdd	vss

MB1 nb1 nb1 vss vss cmosn l=0.2u w=0.5u
MI3 ni1 inm ni3 vss cmosn l=0.2u w=6.8u
MI4 ni2 inp ni3 vss cmosn l=0.2u w=9u
MI5 ni3 nb1 vss vss cmosn l=0.2u w=0.5u
MO2 out nb1 vss vss cmosn l=0.2u w=0.2u
MI1 ni1 ni1 vdd vdd cmosp l=0.2u w=16u
MI2 ni2 ni1 vdd vdd cmosp l=0.2u w=16u
MO1 out ni2 vdd vdd cmosp l=0.2u w=15u
RB1 vdd nb1 1k
CO1 ni2 out 200.0f
.ends	opamp
.endl
