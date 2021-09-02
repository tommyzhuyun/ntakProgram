.title testbench for hspice

*****< Option >*****
.lib '../Lib_Data/Option.lib' hspice_1

*****< MOSFET MODEL >*****
*.lib '/home/cad/models/tsmc_65nm/hspice/crn65gplus_2d5_lk_v1d0.l' TT_18
.lib '../Lib_Data/tsmc018.lib' model27

*****< Main Stage >*****
.lib '../Sp_Data/OPamp.sp' opamp

**@@@@@@< ALTER Command >@@@@@@*

**-< Testbench for CC >-----------*
.LIB '../Lib_Data/hsCC.lib' CC

**-< Testbench for IRN >-----------*
.ALTER $IRN
.DEL LIB '../Lib_Data/hsCC.lib' CC
.LIB '../Lib_Data/hsIRN.lib' IRN

**-< Testbench for OR >-----------*
.ALTER $OR
.DEL LIB '../Lib_Data/hsIRN.lib' IRN
.LIB '../Lib_Data/hsOR.lib' OR

**-< Testbench for THD >-----------*
.ALTER $THD
.DEL LIB '../Lib_Data/hsOR.lib' OR
.LIB '../Lib_Data/hsTHD.lib' THD

**-< Testbench for OVR >-----------*
.ALTER $OVR
.DEL LIB '../Lib_Data/hsTHD.lib' THD
.LIB '../Lib_Data/hsOVR.lib' OVR

**-< Testbench for CMRR >-----------*
.ALTER $CMRR
.DEL LIB '../Lib_Data/hsOVR.lib' OVR
.LIB '../Lib_Data/hsCMRR.lib' CMRR

**-< Testbench for PSRR >-----------*
.ALTER $PSRR
.DEL LIB '../Lib_Data/hsCMRR.lib' CMRR
.LIB '../Lib_Data/hsPSRR.lib' PSRR

**-< Testbench for CMIR >-----------*
.ALTER $CMIR
.DEL LIB '../Lib_Data/hsPSRR.lib' PSRR
.LIB '../Lib_Data/hsCMIR.lib' CMIR


*****< Option >*****
.DEL LIB '../Lib_Data/Option.lib' hspice_1
.lib '../Lib_Data/Option.lib' hspice_2

**-< Testbench for Gain and GBW and PM >------*
.ALTER $GAIN
.DEL LIB '../Lib_Data/hsCMIR.lib' CMIR
.LIB '../Lib_Data/hsGain_GBW_PM.lib' Gain_GBW_PM

**-< Testbench for SR1 >-----------*
.ALTER $SR1
.DEL LIB '../Lib_Data/hsGain_GBW_PM.lib' Gain_GBW_PM
.LIB '../Lib_Data/hsSR1.lib' SR1

* .ALTER $SR2
* .del LIB '../Lib_Data/hsSR1.lib' SR1
* .LIB '../Lib_Data/hsSR2.lib' SR2

.end
