.title testbench for hspice

*****< Option >*****
.lib '../Lib_Data/Option.lib' hspice_2

*****< MOSFET MODEL >*****
* .lib '/home/cad/models/tsmc_65nm/hspice/crn65gplus_2d5_lk_v1d0.l' TT_18
.lib '../Lib_Data/tsmc018.lib' model27

*****< Main Stage >*****
.lib '../Sp_Data/OPamp.sp' opamp

.LIB '../Lib_Data/hsSR2.lib' SR2
