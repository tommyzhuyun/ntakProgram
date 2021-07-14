.title test circuit

.control
  set units=degrees

  ******< Topology for CC, OR, IRN >******
  source ../Lib_Data/ng3.lib
  setcirc 1

  **********************************************
  *   Control for current consumption          *
  **********************************************
  ******<  >******
  foreach tempval -40 25 80
    set temp=$tempval
    foreach vddval $&psval_low $&psval $&psval_high
      * echo psval_low: $&psval_low
      * echo psval: $&psval
      * echo psval_high: $&psval_high
      * echo temp: $tempval
      echo vdd: $vddval
      alter vdd $vddval
      op
      * let ib = max(abs(i(vdd)),abs(i(vss)))
      * let pdis = $&ib*2*$vddval
      * echo ib=  $&ib
      * echo pdis= $&pdis
      print max(abs(i(vdd)),abs(i(vss)))
      print max(abs(i(vdd)),abs(i(vss)))*2*$vddval
    end
  end

  **********************************************
  *   Control for input refferred noise        *
  **********************************************
  echo
  echo calc IRN
  set temp=25
  noise V(out) VIN dec 10 0.1 1MEG
  print inoise_total

  **********************************************
  *   Control for output resistance            *
  **********************************************
  echo
  echo calc OR
  tf v(out) vin
  print all


  **********************************************
  *   Control for Total Harmonic Distortion    *
  **********************************************
  remcirc
  source ../Lib_Data/ngTHD.lib
  setcirc 1
  echo
  echo calc THD
  * echo TRAN 10n 1.001 $&tstart
  * TRAN 10n 1.001 $&tstart
  tran 10u 1.00
  fourier 100 V(out)


  **********************************************
  *   Control for Output Voltage Range         *
  **********************************************
  remcirc
  source ../Lib_Data/ngOVR.lib
  setcirc 1
  echo
  echo calc OVR
  ******< Simulation Command >******
  let vstart_ovr = 0.01
  let vstop_ovr = $&psvoltage/2
  let vincr_ovr = ($&vstop_ovr - 0.01)/1000
  * echo DC VIN $&vstart_ovr $&vstop_ovr $&vincr_ovr
  DC VIN $&vstart_ovr $&vstop_ovr $&vincr_ovr
  * print '1 - abs(V(out1,os)/V(in1))' '1 - abs(V(out2,os))/V(in1)'
  ******< Measure command >******
  * memo
  * param=’(tdiff < vout_diff) ?  1 :  0’
  let eval_ovrn = '1 - abs(V(out1,os))/V(in1)'
  let eval_ovrp = '1 - abs(V(out2,os))/V(in1)'
  let Vorn_o = 0
  let Vorp_o = 0
  meas DC Vorn_o find V(in1) When eval_ovrn=0.05 rise=1
  meas DC Vorp_o find V(in1) When eval_ovrp=0.05 rise=1

  let Vorn='($&Vorn_o) ? $&Vorn_o/2 : 0.5*$&psvoltage'
  let Vorp='($&Vorp_o) ? $&Vorp_o/2 : 0.5*$&psvoltage'
  * echo Vorn = $&Vorn
  * echo Vorp = $&Vorp

  let Vor = Vorp+Vorn
  let ovr = 100*Vor/$&psvoltage
  echo Vor = $&Vor
  echo ovr = $&ovr


  **********************************************
  *   Control for Common-Mode Rejection Ratio  *
  **********************************************
  remcirc
  source ../Lib_Data/ngCMRR.lib
  setcirc 1
  echo
  echo calc CMRR
  ******< Simulation Command >******
  ac dec 100 0.1 10G
  ******< Measure command >******
  let cmrr_data = vdb(od)-vdb(oc)
  meas ac cmrr max cmrr_data from=0.1 to=10G


  **********************************************
  *   Control for Power Supply Rejection Ratio *
  **********************************************
  remcirc
  source ../Lib_Data/ngPSRR.lib
  setcirc 1
  echo
  echo calc PSRR
  ******< Simulation Command >******
  ac dec 100 0.1 10G
  ******< Measure command >******
  let psrr_data_d = vdb(od,odd)
  let psrr_data_s = vdb(od,oss)
  meas ac pd find psrr_data_d at=0.1
  meas ac ps find psrr_data_s at=0.1
  let psrr = min(pd,ps)
  echo PSRR = $&psrr


  **********************************************
  *   Control for Common-Mode Input Range      *
  **********************************************
  remcirc
  source ../Lib_Data/ngCMIR.lib
  setcirc 1
  echo
  echo calc CMIR
  ******< Simulation Command >******
  *.dc srcnam vstart vstop vincr
  let vstart = 10m
  let vstop = $&psvoltage
  let vincr = '($&psvoltage - 10m)/1000'
  echo dc vin $&vstart $&vstop $&vincr
  dc vin $&vstart $&vstop $&vincr
  let gain = 0.5
  * print V(out1,os) '1 - abs(V(out1,os))/($&gain*V(in1))'
  * print V(out2,os) '1 - abs(V(out2,os))/($&gain*V(in1))'
  * print '1 - abs(V(out1,os))/($&gain*V(in1))' '1 - abs(V(out2,os))/($&gain*V(in1))'
  ******< Measure command >******
  let eval_virp = '1 - abs(V(out1,os))/($&gain*V(in1))'
  let eval_virn = '1 - abs(V(out2,os))/($&gain*V(in1))'
  let Vcmirpp = 0
  let Vcmirpn = 0
  let Vcmirnp = 0
  let Vcmirnn = 0
  meas DC Vcmirpp find V(in1) When eval_virp=0.05
  meas DC Vcmirpn find V(in1) When eval_virp=-0.05
  meas DC Vcmirnp find V(in1) When eval_virn=0.05
  meas DC Vcmirnn find V(in1) When eval_virn=-0.05
  if ( $&Vcmirpp | $&Vcmirpn )
    let Vcmirp='( $&Vcmirpp ) ? $&Vcmirpp : $&Vcmirpn'
  else
    let Vcmirp = 0.5*$&psvoltage
  end
  if ( $&Vcmirnp | $&Vcmirnn )
    let Vcmirn='( $&Vcmirnp ) ? $&Vcmirnp : $&Vcmirnn'
  else
    let Vcmirn = 0.5*$&psvoltage
  end
  * echo Vcmirp = $&Vcmirp
  * echo Vcmirn = $&Vcmirn
  let Vcmr = ($&Vcmirp + $&Vcmirn)
  let CMIR = 100*$&Vcmr/($&psvoltage)
  echo Vcmr = $&Vcmr
  echo CMIR = $&CMIR


  ********************************************************
  *   Control for Gain, Gain Bandwidth, and Phase Mergin *
  ********************************************************
  remcirc
  source ../Lib_Data/ngGain_GBW_PM.lib
  setcirc 1
  echo
  echo calc Gain, Gain Bandwidth, and Phase Mergin
  ******< Simulation Command >******
  op
  ac dec 100 0.1 10G
  print ac vdb(out) vp(out)
  ******< Measure command >******
  ** 直流利得[倍] **
  meas ac dcgain find V(out) at=0.1
  ** 直流利得[dB] **
  meas ac dcgain_dB find Vdb(out) at=0.1

  ** 利得帯域幅積 **
  * 直流利得[dB]の半分
  let half_dcgain_dB = 'dcgain_dB/2'
  * echo half_dcgain_dB = $&half_dcgain_dB

  * 直流利得が半分になったときの周波数
  meas ac half_dcgain_dB_freq when Vdb(out)=half_dcgain_dB fall=1

  * 直流利得が半分になった条件での利得帯域幅積[Hz]
  let gain_bandwidth_cond1 = 'half_dcgain_dB_freq*10^(half_dcgain_dB/20)'
  * echo Gain BandWidth Cond 1 = $&gain_bandwidth_cond1

  * ユニティゲイン周波数[Hz]
  meas ac unity_gain_freq when Vdb(out)=0 fall=1

  * 利得帯域幅積[Hz]
  let gain_bandwidth  = 'min(gain_bandwidth_cond1, unity_gain_freq)'
  echo Gain Bandwidth Product = $&gain_bandwidth

  ** 位相余裕 **
  * 利得が1での位相余裕
  let cph_out = cph(out)
  meas ac phase_cond1 find cph_out at=unity_gain_freq
  let phase_margin_cond1 = '180 - abs(phase_cond1)'
  echo Phase Margin Cond 1 = $&phase_margin_cond1

  * 0.1からユニティゲイン周波数の間で最も位相回転している周波数での位相
  meas ac phase_min min cph_out from=0.1 to=unity_gain_freq

  * 周波数が0.1[Hz]のときの位相
  meas ac phase_at_0freq find Vp(out) at=0.1

  * 0.1[Hz]からユニティゲイン周波数の間で最も位相回転している周波数を用いた位相余裕  180 - abs(最大位相)-0.1Hz時の位相
  let phase_margin_cond2 = '180 - abs(phase_min) - phase_at_0freq'
  * echo Phase Margin Cond 2 = phase_margin_cond2

  * 位相余裕[度]
  let phase_margin = min(phase_margin_cond1, phase_margin_cond2)
  echo Phase Margin = $&phase_margin

  ********************************************************
  *   Control for Slew Rate                              *
  ********************************************************
  remcirc
  source ../Lib_Data/ngSR1.lib
  setcirc 1
  echo
  echo calc Slew Rate 1
  ******< Simulation Command >******
  let vstart = 0.01
  let vstop = $&psvoltage/2
  let vincr = 0.01
  echo dc vin $&vstart $&vstop $&vincr
  dc vin $&vstart $&vstop $&vincr
  ******< Measure command >******
  let gain = 2
  let vpmax = 0
  let vnmax = 0
  let eval_vout1 = abs(V(out1,os)-V(in1)*$&gain)/V(in1)
  let eval_vout2 = abs(V(out2,os)-V(in1)*$&gain)/V(in1)
  meas dc vpmax find v(in1) when eval_vout1=0.05 rise=1
  meas dc vnmax find v(in1) when eval_vout2=0.05 rise=1
  let vpmax='$&vpmax ? $&vpmax : $&psvoltage/2'
  let vnmax='$&vnmax ? $&vnmax : $&psvoltage/2'
  let vp = min($&vpmax, $&vnmax)
  echo vp = $&vp

  remcirc
  source ../Lib_Data/ngSR2.lib
  setcirc 1
  echo
  echo calc Slew Rate 2
  ******< Simulation Command >******
  alterparam vp = $&vp
  reset
  * tran tstep tstop <tstart>
  let tstep = 10n
  let tstop = 200u
  * let tstep = 0.1n
  * let tstop = 4e-7
  tran $&tstep $&tstop

  ******< Measure command rise >******
  let diff_out1 = v(out1,os)
  meas tran vps find diff_out1 at=0    $ 立ち上がる前の電圧
  meas tran vpt find diff_out1 at=200u $ 立ち上がり後の電圧
  let vdiff_r = 'vpt - vps'
  let diff = 0.01

  echo
  echo calc voltage before rise
  let vps1 = (0.9 + diff/2)*vps
  let vps2 = (0.9 - diff/2)*vps
  meas tran t1_srr1 when diff_out1=vps1 cross=1
  meas tran t2_srr1 when diff_out1=vps2 cross=1
  meas tran v1_srr1 find diff_out1 at=t1_srr1
  meas tran v2_srr1 find diff_out1 at=t2_srr1
  let srr1 = (v2_srr1 - v1_srr1)/(t2_srr1 - t1_srr1)
  echo srr1 = $&srr1

  echo
  echo calc voltage at 0
  meas tran t1_srr2 when diff_out1=+$&diff cross=1
  meas tran t2_srr2 when diff_out1=-$&diff cross=1
  meas tran v1_srr2 find diff_out1 at=t1_srr2
  meas tran v2_srr2 find diff_out1 at=t2_srr2
  let srr2 = (v2_srr2 - v1_srr2)/(t2_srr2 - t1_srr2)
  echo srr2 = $&srr2

  echo
  echo calc voltage after rise
  let vpt1 = (0.9 + diff/2)*vpt
  let vpt2 = (0.9 - diff/2)*vpt
  meas tran t1_srr3 when diff_out1=vpt1 cross=1
  meas tran t2_srr3 when diff_out1=vpt2 cross=1
  meas tran v1_srr3 find diff_out1 at=t1_srr3
  meas tran v2_srr3 find diff_out1 at=t2_srr3
  let srr3 = (v2_srr3 - v1_srr3)/(t2_srr3 - t1_srr3)
  echo srr3 = $&srr3

  let srr = '(srr1+srr2+srr3)/3'
  echo average of rise SR = $&srr
  echo

  ******< Measure command fall >******
  let diff_out2 = v(out2,os)
  meas tran vns find diff_out2 at=0    $ 立ち上がる前の電圧
  meas tran vnt find diff_out2 at=200u $ 立ち上がり後の電圧
  let vdiff_f = 'vnt - vns'

  echo
  echo calc voltage before fall
  let vns1 = (0.9 + diff/2)*vns
  let vns2 = (0.9 - diff/2)*vns
  meas tran t1_srf1 when diff_out2=vns1 cross=1
  meas tran t2_srf1 when diff_out2=vns2 cross=1
  meas tran v1_srf1 find diff_out2 at=t1_srf1
  meas tran v2_srf1 find diff_out2 at=t2_srf1
  let srf1 = (v2_srf1 - v1_srf1)/(t2_srf1 - t1_srf1)
  echo srf1 = $&srf1

  echo
  echo calc voltage at 0
  meas tran t1_srf2 when diff_out2=+$&diff cross=1
  meas tran t2_srf2 when diff_out2=-$&diff cross=1
  meas tran v1_srf2 find diff_out2 at=t1_srf2
  meas tran v2_srf2 find diff_out2 at=t2_srf2
  let srf2 = (v2_srf2 - v1_srf2)/(t2_srf2 - t1_srf2)
  echo srf2 = $&srf2

  echo
  echo calc voltage after fall
  let vnt1 = (0.9 + diff/2)*vnt
  let vnt2 = (0.9 - diff/2)*vnt
  meas tran t1_srf3 when diff_out2=vnt1 cross=1
  meas tran t2_srf3 when diff_out2=vnt2 cross=1
  meas tran v1_srf3 find diff_out2 at=t1_srf3
  meas tran v2_srf3 find diff_out2 at=t2_srf3
  let srf3 = (v2_srf3 - v1_srf3)/(t2_srf3 - t1_srf3)
  echo srf3 = $&srf3

  let srf = '(srf1+srf2+srf3)/3'
  echo average of fall SR = $&srf

  let sr = 'min(abs(srr),abs(srf))'
  echo SR = $&sr

  print diff_out1 diff_out2
.endc
