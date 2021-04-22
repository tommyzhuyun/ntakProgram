.title testbench for hspice

*****< Option >*****
.lib '../Lib_Data/Option.lib' hspice_2

*****< MOSFET MODEL >*****
.lib '../Lib_Data/tsmc018.lib' model27

*****< Main Stage >*****
.lib '../Sp_Data/OPamp.sp' opamp

.LIB '../Lib_Data/hsSR2.lib' SR2
