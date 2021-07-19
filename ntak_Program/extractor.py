# -*- coding: utf-8 -*-
import math
import re
import fileinput
import numpy as np

from spice import *
from decimal import *


class Extractor:
    """
    出力結果から数値を抽出するクラス
    """

    """ Constants """
    CC = 'CC'  # 消費電流:無信号時の消費電流
    PD = 'PD'  # 消費電力:申告された電源電圧×消費電流
    current_delta = False  # 消費電流変動率判定
    CMIR = 'CMIR'  # 同相入力範囲 Common Mode Input Range
    CMRR = 'CMRR'  # 同相除去比(真値) Common Mode Rejection Ratio
    CMRR_DB = 'CMRR_DB'  # 同相除去比 [dB] Common Mode Rejection Ratio
    GAIN_SIM = 'GAIN_SIM'  # 直流利得 DC Gain(シミュレーション値) [倍]
    GAIN = 'GAIN'  # 直流利得 DC Gain(補正済) [倍]
    GAIN_DB_SIM = 'GAIN_DB_SIM'  # 直流利得 DC Gain(シミュレーション値) [dB]
    GAIN_DB = 'GAIN_DB'  # 直流利得 DC Gain(補正済) [dB]
    GBW = 'GBW'  # ゲイン帯域幅 Gain Bandwidth Product
    PM = 'PM'  # 位相余裕 Phase Margin
    IRN = 'IRN'  # 入力換算雑音 Input Referred Noise
    OR_SIM = 'OR_SIM'  # 出力抵抗 Output Resistance(シミュレーション値)
    OR = 'OR'  # 出力抵抗 Output Resistance(補正済)
    OVR = 'OVR'  # 出力電圧範囲 Output Voltage Range
    PSRR = 'PSRR'  # 電源電圧変動除去比(真値) Power Supply Rejection Ratio
    PSRR_DB = 'PSRR_DB'  # 電源電圧変動除去比[dB] Power Supply Rejection Ratio
    SR = 'SR'  # スルーレート Srew Rate
    THD = 'THD'  # 全高調波歪 Total Harmonic Distortion
    CA = 'CA'  # 占有面積 Chip Area
    PSVOLTAGE = 'PSVOLTAGE'  # 電源電圧

    # 出力結果
    SIM_RESULT_STR_1ST = ""

    # Hspice の場合、SR を取得するのに、２回シミュレーションを行う
    # SR 取得中かどうかのフラグ
    ACQ_SR_FLAG = False

    # Hspice の１回目のシミュレーションで得た vp の値
    # SRの値が条件を満たすかどうかのチェックに使用する
    SR_VP = ""

    def __init__(self, sim_result_str, spice, cir_file, out_file):
        """
        spiceによるシミュレーション結果をセットし、そこから各項目の値の
        抽出を行う

        Parameters
        ----------
        sim_result:_str str
            シミュレーション結果文字列
        spice: Spice
            Spiceクラスのインスタンス
        cir_file: str
            回路ファイルパス
        out_file: str
            出力用ファイルパス
        """
        self.sim_result_str = sim_result_str
        self.spice = spice
        # 回路ファイルパス
        self.cir_file = cir_file
        self.out_file = out_file

        # 出力抵抗計算済みフラグ
        self.result_or = None
        self.result_gain = None
        self.or_sim = None
        self.gain_sim = None

        # パラメータ
        self.valr1 = None
        self.valr2 = None
        self.valrl = None
        self.beta = None

        # 電源電圧
        self.psvoltage = None

        # numpy.dArray の指数表示設定
        np.set_printoptions(formatter={'float': '{:.6e}'.format})

        # Decimal の有効桁数 6桁
        getcontext().prec = 6

        # SR のチェックメッセージを表示
        self.SR_msg_flag = False

    def set_sim_result_str(self, sim_result_str):
        """
        spiceによるシミュレーション結果文字列をセット

        Parameters
        ----------
        sim_result_str: str
            シミュレーション結果文字列
        """
        self.sim_result_str = sim_result_str

    def get_each_elem(self, item):
        if item == self.CC:
            return self.get_cc()
        elif item == self.PD:
            return self.get_pd()
        elif item == self.IRN:
            return self.get_irn()
        elif item == self.OR_SIM:
            return self.get_or_sim()
        elif item == self.OR:
            return self.get_or()
        elif item == self.THD:
            return self.get_thd()
        elif item == self.OVR:
            return self.get_ovr()
        elif item == self.CMRR_DB:
            return self.get_cmrr_db()
        elif item == self.CMRR:
            return self.get_cmrr()
        elif item == self.PSRR_DB:
            return self.get_psrr_db()
        elif item == self.PSRR:
            return self.get_psrr()
        elif item == self.CMIR:
            return self.get_cmir()
        elif item == self.GAIN_SIM:
            return self.get_gain_sim()
        elif item == self.GAIN:
            return self.get_gain()
        elif item == self.GAIN_DB_SIM:
            return self.get_gain_db_sim()
        elif item == self.GAIN_DB:
            return self.get_gain_db()
        elif item == self.GBW:
            return self.get_gbw()
        elif item == self.PM:
            return self.get_pm()
        elif item == self.SR:
            return self.get_sr()
        elif item == self.CA:
            return self.get_ca()
        elif item == self.PSVOLTAGE:
            return self.get_psvoltage()
        else:
            raise IllegalArgumentException("Extracter.get_each_elem(): " + item)

    def extract(self, pattern_str, digit_flag=False, delim="=", eliminate=None):
        """
        指定パターン文字列にマッチする行を抽出し、その値(右辺)返す

        Parameters
        ----------
        pattern_str: str
            抽出パターン文字列
        digit_flag: bool (Default: False)
            抽出した値を数値へ変換する場合は True、
            str にする場合は False
        delim: str (Default: "=")
            トークンに分割する際のデリミタ。
        eliminate: str
            トークンから除去する空白文字以外の文字列
        Returns
        -------
            結果値。結果値が１つの場合は float もしくは str として返す。
            複数の場合は、値の入った配列を返す。抽出結果なしの場合は、空の配列を返す。
        """
        val = []
        result = re.findall(pattern_str, self.sim_result_str, re.MULTILINE)
        for tmp_str in result:
            tmp_str = tmp_str.split(delim)[1]
            if eliminate:
                tmp_str = tmp_str.replace(eliminate, " ")
            tmp_val = tmp_str.strip()
            # print(tmp_val)

            if len(result) == 1:
                # 抽出結果が１つの場合
                if digit_flag:
                    return float(tmp_val)
                else:
                    return tmp_val
            else:
                if digit_flag:
                    val.append(float(tmp_val))
                else:
                    val.append(tmp_val)

        # 抽出結果が複数ある場合は、配列で返す。結果なしの場合、空の配列を返す
        return val

    @classmethod
    def rewrite_file(cls, file_path, pattern_str, replace_str):
        """
        ファイルの書き換えを行う。元のファイルは *.bak に rename される

        Parameters
        ----------
        file_path : str
            パラメータ名
        pattern_str : str
            書き換え対象となるパターン
        replace_str : str
            書き換え後の文字列
        """
        with fileinput.FileInput(file_path, inplace=True, backup=".bak") as f:
            for line in f:
                tmp_str = line
                if re.search(pattern_str, line) is not None:
                    tmp_str = re.sub(pattern_str, replace_str, line)
                print(tmp_str, end='')

    def get_cc(self):
        """
        消費電流を抽出。単位: [A]

        Returns
        -------
            消費電流の配列(3x3)。単位: [A]
        """
        result = None
        try:
            result = self.extract(self.spice.CC_PATTERN)
            result = np.array(result)
            result = np.reshape(result, [3, 3])  # 3x3 の配列へ変換
        except ValueError as e:
            raise ItemExtractException("Extracter.get_cc(): check result")

        return result

    def get_pd(self):
        """
        消費電力を抽出。単位: [W]

        Returns
        -------
            消費電力の配列(3x3)。単位: [W]
        """
        result = self.extract(self.spice.PD_PATTERN)
        result = np.array(result)
        result = np.reshape(result, [3, 3])  # 3x3 の配列へ変換
        return result

    def get_irn(self):
        """
        入力換算雑音を抽出。単位: [Hz]

        Returns
        -------
            入力換算雑音。単位: [Hz]
        """
        if isinstance(self.spice, Hspice):
            # Hspice の場合、複数行がマッチ。最後の要素のみ返す
            result = self.extract(self.spice.IRN_PATTERN)
            if len(result) > 0:
                return result[len(result) - 1]
            else:
                return None
        # Ngspice の場合、マッチするのは１行のみ
        return self.extract(self.spice.IRN_PATTERN)

    def get_or_sim(self):
        """
        出力抵抗(シミュレーション値)を抽出。単位: [Ω]

        Returns
        -------
            出力抵抗(シミュレーション値)。単位: [Ω]
        """

        # 出力抵抗(シミュレーション結果) を取得
        return self.extract(self.spice.OR_SIM_PATTERN)

    def get_or(self):
        """
        出力抵抗(補正済)を抽出。単位: [Ω]

        Returns
        -------
            出力抵抗。単位: [Ω]
        """

        # 出力抵抗(シミュレーション結果) を取得
        self.or_sim = self.get_or_sim()

        # 直流利得のシミュレーション結果
        self.gain_sim = self.get_gain_sim()

        """
        #(float による計算)
        # 帰還率 (R1/(R1+R2))
        self.valr1 = self.spice.conf["valr1"]
        self.valr2 = self.spice.conf["valr2"]
        self.valrl = self.spice.conf["valrl"]
        self.beta = self.valr1/(self.valr1+self.valr2)

        num = 1 + float(self.beta) * float(self.gain_sim)

        denom = 1/float(self.or_sim) \
                - 1/(self.valr1+self.valr2) \
                - self.beta*float(self.gain_sim)/self.valrl

        tmp = num/denom
        self.result_or = str(tmp)

        return str(tmp)
        """

        # (Decimal による計算)
        # 帰還率 (R1/(R1+R2))
        self.valr1 = self.spice.conf["valr1"]
        self.valr2 = self.spice.conf["valr2"]
        self.valrl = self.spice.conf["valrl"]
        self.beta = Decimal(str(self.valr1)) / (Decimal(str(self.valr1)) + Decimal(str(self.valr2)))

        num = 1 + Decimal(str(self.beta)) * Decimal(self.gain_sim)
        tmp = self.valr1 + self.valr2
        tmp2 = self.beta * Decimal(str(self.gain_sim))
        denom = (Decimal('1.0')/Decimal(self.or_sim))-(Decimal('1.0')/Decimal(str(tmp)))-(tmp2/Decimal(str(self.valrl)))
        # 計算途中詳細確認用
        #denom1 = Decimal('1.0')/Decimal(self.or_sim)
        #denom2 = Decimal('1.0')/Decimal(str(tmp))
        #denom3 = tmp2/Decimal(str(self.valrl))
        #denom = denom1 - denom2 - denom3
        tmp = Decimal(str(num)) / denom
        self.result_or = str("{:e}".format(tmp))
        
        return str(tmp)

    def get_thd(self):
        """
        全高調波歪を抽出。単位: [%]

        Returns
        -------
            全高調波歪。単位: [%]
        """
        if isinstance(self.spice, Ngspice):
            return self.extract(self.spice.THD_PATTERN, True, ":", "%")
        elif isinstance(self.spice, Hspice):
            return self.extract(self.spice.THD_PATTERN, True, "=", "percent")
        else:
            pass

    def get_ovr(self):
        """
        出力電圧範囲を抽出。単位: [%]

        Returns
        -------
            出力電圧範囲。単位: [%]
        """
        if isinstance(self.spice, Ngspice):
            return self.extract(self.spice.OVR_PATTERN)

        elif isinstance(self.spice, Hspice):
            vorn_str = self.extract("^ vorn=.*$")
            vorp_str = self.extract("^ vorp=.*$")
            ovr_str = self.extract(self.spice.OVR_PATTERN)

            if self.psvoltage is None:
                self.get_psvoltage()

            if (vorn_str != "failed") and (vorp_str != "failed"):
                return ovr_str
            else:
                vorn = float(self.psvoltage)
                vorp = float(self.psvoltage)
                if vorn_str != "failed":
                    vorn = float(vorn_str)
                if vorp_str != "failed":
                    vorp = float(vorp_str)
                return ((vorn+vorp) / (2*float(self.psvoltage))) * 100

        else:
            pass

    def get_cmrr_db(self):
        """
        同相除去比を抽出。単位: [dB]

        Returns
        -------
            同相除去比。単位: [dB]
        """
        return self.extract(self.spice.CMRR_PATTERN, True, "=", "at")

    def get_cmrr(self):
        """
        同相除去比を抽出。単位: [倍]

        Returns
        -------
            同相除去比。単位: [倍]
        """
        cmrr_db = float(self.get_cmrr_db())
        return pow(10.0, cmrr_db/20)

    def get_psrr_db(self):
        """
        電源電圧変動除去比を抽出。単位: [dB]

        Returns
        -------
            電源電圧変動除去比。単位: [dB]
        """
        return self.extract(self.spice.PSRR_PATTERN)

    def get_psrr(self):
        """
        電源電圧変動除去比を抽出。単位: [倍]

        Returns
        -------
            電源電圧変動除去比。単位: [倍]
        """
        psrr_db = float(self.get_psrr_db())
        return pow(10.0, psrr_db/20)

    def get_cmir(self):
        """
        同相入力範囲を抽出。単位: [%]

        Returns
        -------
            同相入力範囲。単位: [%]
        """

        if isinstance(self.spice, Ngspice):
            return self.extract(self.spice.CMIR_PATTERN)
        elif isinstance(self.spice, Hspice):
            lines = self.sim_result_str.splitlines()
            index = 0
            for index, line in enumerate(lines):
                if re.search(self.spice.CMIR_PATTERN, line) is not None:
                    # 「$cmr」の3行下に 「x」の行があるか？
                    if (lines[index+3] is not None) and (re.match("^x$", lines[index+3]) is not None):
                        break
            # 「$cmr」の7行下からデータ開始
            data = []
            for index, line in enumerate(lines[index+7:]):
                if re.match("^y$", line) is not None:
                    break
                data.append(line.split())

            np_data = np.array(data, dtype='float64')
            np_data.reshape(-1, 3)

            # abs() > 0.05 を最初に超えた時点のインデックスを取得
            # 1-abs(v(out1,os))/((0.5)*v(in1))
            vcmirp_list = np_data[np.where(abs(np_data[:, 1]) > 0.05), 0]
            # 0.05 を超える点がない場合は、vcmirp = psvoltage/2
            if self.psvoltage is None:
                self.get_psvoltage()
            vcmirp = float(self.psvoltage)/2
            if vcmirp_list.size != 0:
                # abs() > 0.05 を最初に超えた時点のインデックスを取得
                vcmirp = vcmirp_list[0][0]

            # abs() > 0.05 を最初に超えた時点のインデックスを取得
            # 1-abs(v(out2,os))/((0.5)*v(in1))
            vcmirn_list = np_data[np.where(abs(np_data[:, 2]) > 0.05), 0]
            # 0.05 を超える点がない場合は、vcmirp = psvoltage/2
            vcmirn = float(self.psvoltage)/2
            if vcmirn_list.size != 0:
                # abs() > 0.05 を最初に超えた時点のインデックスを取得
                vcmirn = vcmirn_list[0][0]
            vcmr = Decimal(vcmirp) + Decimal(vcmirn)
            cmir = Decimal(str(100*vcmr))/(Decimal(self.psvoltage))
            return cmir
        else:
            # Hspice, Ngspice 以外
            pass

    def get_gain_sim(self):
        """
        直流利得 DC Gain(シミュレーション値) を抽出

        Returns
        -------
            直流利得 DC Gain(シミュレーション値)
        """
        return self.extract(self.spice.GAIN_SIM_PATTERN)

    def get_gain(self):
        """
        直流利得 DC Gain(補正済) を抽出

        Returns
        -------
            直流利得 DC Gain(補正済み)
        """

        # 既に出力抵抗を計算済み
        #   → 出力抵抗および直流利得のシミュレーション値を計算済み

        # だったらその値を使用する
        if self.result_or is None:
            self.get_or()

        num = Decimal(self.valrl) + Decimal(self.result_or)
        denom = Decimal(self.valrl)

        tmp = Decimal(str(num)) / Decimal(str(denom)) * Decimal(self.gain_sim)
        self.result_gain = str(tmp)
        return str("{:e}".format(tmp))

    def get_gain_db_sim(self):
        """
        直流利得(シミュレーション値)を抽出。単位: [dB]

        Returns
        -------
            直流利得。単位: [dB]
        """
        return self.extract(self.spice.GAIN_DB_PATTERN)

    def get_gain_db(self):
        """
        直流利得(補正済)を抽出。単位: [dB]

        Returns
        -------
            直流利得(補正済)。単位: [dB]
        """
        if self.result_gain is None:
            self.get_gain()
        return str(20 * math.log10(Decimal(self.result_gain)))

    def get_gbw(self):
        """
        ゲイン帯域幅を抽出。単位: [Hz]

        Returns
        -------
            ゲイン帯域幅。単位: [Hz]
        """
        if isinstance(self.spice, Ngspice):
            # Ngspice の場合
            return self.extract(self.spice.GBW_PATTERN)
        elif isinstance(self.spice, Hspice):
            # Hspice の場合、GBW GAIN_SIM を求める際に同時に抽出・計算する
            # 利得帯域幅積

            pattern_ugain = "^ unity_gain_freq=.*$"
            pattern_halfdc = "^ half_dcgain_db=.*$"
            pattern_halfdcf = "^ half_dcgain_db_freq=.*$"

            unitygain = self.extract(pattern_ugain)
            halfdc = self.extract(pattern_halfdc)
            halfdc_f = self.extract(pattern_halfdcf)

            gbw = 0.0
            if (float(halfdc) > 0) and (float(halfdc_f) > 0):
                gbw = float(halfdc) * float(halfdc_f)
            if float(unitygain) < gbw and float(unitygain) > 0:
                # gbw をユニティゲイン周波数にする
                gbw = unitygain

            return gbw

    def get_pm(self):
        """
        位相余裕を抽出。単位: [degree]

        Returns
        -------
            位相余裕。単位: [degree]
        """
        return self.extract(self.spice.PM_PATTERN)

    def get_sr(self):
        """
        スルーレートを抽出。単位:[V/μs]

        Returns
        -------
            スルーレート。単位:[V/μs]
        """
        print_dbg = False

        if isinstance(self.spice, Ngspice):
            # Ngspice の場合

            # vnt, vpt, vp 取得
            vnt = float(self.extract("^vnt\s+=\s+.*$"))
            vpt = float(self.extract("^vpt\s+=\s+.*$"))
            vp = float(self.extract("^vp\s+=\s+.*$"))

            if print_dbg:
                print("vnt= {}".format(vnt))
                print("vpt= {}".format(vpt))
                print("vp= {}".format(vp))

            # data = self.sim_result.splitlines()  # なぜかこれだと動かない
            data = self.sim_result_str.split("\n")
            index = 0
            for i, line in enumerate(data):
                if line.find(self.spice.SR_DATA_PATTERN) != -1:
                    index = i
                    break

            # 立ち上がり、立ち下がりで単調増加、単調減少していない場合は
            # メッセージ出力
            # 5行後からデータの記述開始
            data2 = data[index + 4:]
            sr_data = []
            offset = 0
            for i, line in enumerate(data2):
                # 行頭が数値である行が SR のデータとみなす
                if re.match("^\\d", line) is not None:
                    tmp = line.split()

                    # チェックは、経過時間が 100 ns 以降のデータを対象とする
                    if float(tmp[1]) >= 100.0e-9:
                        sr_data.append(tmp)
                        if offset == 0:
                            offset = int(tmp[0])

            # np_data には、100 ns 以降のデータが入っている
            np_data = np.array(sr_data, dtype='float64')

            # 立ち上がりチェック事項
            # ①100ns 後から1回目の定常値vptに到達するまでに、立ち上がりと立ち下がりを繰り返しているかどうか
            # ②1回目の定常値以降、発振していないこと
            #   発振の定義：
            #   (1)データ列の最後の100点の出力電圧の平均値を算出 = Vave
            #   (2)データ列の最後の100点の出力電圧のabs(各点のデータ - Vave)/Vave が全て 0.01 以内にある
            # ③定常値Vave が「abs(2*vp) の 1% 以内」にない場合はメッセージ出力

            if self.SR_msg_flag:
                self.print_msg("SR: Checking for rise....")

            ########## 立ち上がりチェック ###########

            # ①100ns 後から1回目の定常値vptに到達するまでに、立ち上がりと立ち下がりを繰り返しているかどうか
            # vpt を最初に超えた時点のインデックスを取得
            index_list = np.where(np_data[:, 2] > vpt)[0].tolist()
            if index_list:
                # vpt より大きいデータあり
                # 立ち上がり時のチェックなので、傾きがマイナスになったらメッセージ出力
                over_vpt_index = int(index_list[0])
                diff = np.diff(np_data[0:over_vpt_index, 2], axis=0)
                if np.count_nonzero(diff < 0.0) > 0:
                    minus_slope_index = (np.where(diff < 0.0)[0]).tolist()[0]
                    if self.SR_msg_flag:
                        self.print_msg("\tRise: **************** CAUTION ****************")
                        self.print_msg("\tRise: Not monotonically increasing: index={}\n"
                                       .format(offset + 1 + minus_slope_index))
            else:
                # vpt より大きいデータがない => 最大値が vpt と等しければ問題なし
                index_list2 = np.where(np_data[:, 2] == vpt)[0].tolist()
                if index_list2:
                    # 問題なし
                    pass
                else:
                    # すべてのデータが vpt より小さい -> エラー
                    self.print_msg("\tFall: **************** CAUTION ****************")
                    self.print_msg(f"\tFall: all data is less than vpt:{vpt}")

            # ②1回目の定常値以降、発振していないこと
            # (1)データ列の最後の100点の出力電圧の平均値を算出 = Vave
            last_100_data = np_data[-100:, 2]  # diff_out1 のみ抽出
            v_ave = np.average(last_100_data)
            if print_dbg:
                print("v_ave={}".format(v_ave))

            """
            # 最小二乗法で定常値を求める場合
            #
            x = np_data[over_vpt_index:, 1]
            y = np_data[over_vpt_index:, 2]
            v_ave = np.polyfit(x, y, 0)  # 定常値(最小二乗法により求める)
            print("\tRise: base = {}".format(v_ave))
            if (abs(2 * vp) - abs(v_ave)) > (abs(2 * vp) * 0.01):
                self.print_msg("\tRise: **************** CAUTION ****************")
                self.print_msg("\tRise: Steady state values are not within 1% of " \
                      "abs(2*vp).\n")
            """

            # (2)データ列の最後の100点の出力電圧のabs(各点のデータ - Vave)/Vave が全て 0.01 以内にあるかチェック
            tmp_data = np.abs(last_100_data - v_ave)
            if np.where(tmp_data > abs(v_ave) * 0.01)[0].size != 0:
                if self.SR_msg_flag:
                    self.print_msg("\tRise: **************** CAUTION ****************")
                    self.print_msg("\tRise: Oscillations: There is a point that does not fall within 1% error\n")

            # ③定常値Vave が「abs(2*vp) の 1% 以内」にない場合はメッセージ出力
            if abs(abs(2*vp)-abs(v_ave)) > (abs(v_ave)*0.01):
                if self.SR_msg_flag:
                    self.print_msg("\tRise: **************** CAUTION ****************")
                    self.print_msg("\tRise: V_ave are not within 1% of abs(2*vp).\n")

            ########## 立ち下がりチェック ###########
            # 立ち下がりチェック事項
            # ①100ns 後から1回目の定常値vntに到達するまでに、立ち上がりと立ち下がりを繰り返しているかどうか
            # ②1回目の定常値以降、発振していないこと
            #   発振の定義：
            #   (1)データ列の最後の100点の出力電圧の平均値を算出 = Vave
            #   (2)データ列の最後の100点の出力電圧のabs(各点のデータ - Vave)/Vave が全て 0.01 以内にある
            # ③「Vave が Vp の 1% 以内」にない場合、メッセージを出力

            # ①1回目の定常値vntに到達するまでに、立ち上がりと立ち下がりを繰り返しているかどうか
            # vnt を最初に超えた時点のインデックスを取得
            if self.SR_msg_flag:
                self.print_msg("SR: Checking for fall....")

            index_list = np.where(np_data[:, 3] < vnt)[0].tolist()
            if index_list:
                # vnt 未満のデータあり
                # 立下り時のチェックなので、傾きがプラスになったらメッセージ出力
                over_vnt_index = int(index_list[0])
                diff = np.diff(np_data[0:over_vnt_index, 3], axis=0)
                if np.count_nonzero(diff > 0.0) > 0:
                    plus_slope_index = (np.where(diff > 0.0)[0]).tolist()[0]
                    if self.SR_msg_flag:
                        self.print_msg("\tFall: **************** CAUTION ****************")
                        self.print_msg("\tFall: Not monotonically decreasing: index={}\n"
                                       .format(offset + 1 + plus_slope_index))
            else:
                # vnt 未満のデータがない => 最小値が vnt と等しければ問題なし
                index_list2 = np.where(np_data[:, 3] == vnt)[0].tolist()
                if index_list2:
                    # 問題なし
                    pass
                else:
                    # すべてのデータが vnt より大きい -> エラー
                    if self.SR_msg_flag:
                        self.print_msg("\tFall: **************** CAUTION ****************")
                        self.print_msg(f"\tFall: all data is more than vnt:{vnt}")

            # ②1回目の定常値以降、発振していないこと
            # (1)データ列の最後の100点の出力電圧の平均値を算出 = Vave
            last_100_data = np_data[-100:, 3]  # diff_out2 のみ抽出
            v_ave = np.average(last_100_data)
            if print_dbg:
                print("v_ave={}".format(v_ave))

            # (2)データ列の最後の100点の出力電圧のabs(各点のデータ - Vave)/Vave が全て 0.01 以内にあるかチェック
            tmp_data = np.abs(last_100_data - v_ave)
            if np.where(tmp_data > abs(v_ave) * 0.01)[0].size != 0:
                if self.SR_msg_flag:
                    self.print_msg("\tFall: **************** CAUTION ****************")
                    self.print_msg("\tFall: Oscillations: There is a point that does not fall within 1% error\n")

            # ③定常値Vave が「abs(2*vp) の 1% 以内」にない場合はメッセージ出力
            if abs(abs(2*vp)-abs(v_ave)) > (abs(v_ave)*0.01):
                if self.SR_msg_flag:
                    self.print_msg("\tFall: **************** CAUTION ****************")
                    self.print_msg("\tFall: V_ave are not within 1% of abs(2*vp).\n")

            if self.SR_msg_flag:
                self.print_msg("....done\n\n")

            return self.extract(self.spice.SR_PATTERN)

        elif isinstance(self.spice, Hspice):
            # Hspice の場合

            if not Extractor.ACQ_SR_FLAG:
                # １回目の実行時

                # vp 取得
                lines = self.sim_result_str.splitlines()
                index = 0
                for index, line in enumerate(lines):
                    if re.search(self.spice.SR_VP_PATTERN, line) is not None:
                        # 「$sr1」の3行下に 「x」の行があるか？
                        if (lines[index+3] is not None) and (re.match("^x$", lines[index+3]) is not None):
                            break
                # 「$sr1」の7行下からデータ開始
                data = []
                for index, line in enumerate(lines[index+7:]):
                    if re.match("^y$", line) is not None:
                        break
                    data.append(line.split())

                np_data = np.array(data, dtype='float64')
                np_data.reshape(-1, 3)

                # 3, 4列のデータが 0.05 を越えたと時の vin1 のうち、小さい値を vp とする
                # abs(v(out1,os)-v(in1)*gain)/v(in1) > 0.05 を最初に超えた時点の vin1 を取得
                vin_out1 = float(self.psvoltage)/2
                vp_out1_list = np_data[np.where(abs(np_data[:, 1]) > 0.05), 0]
                if vp_out1_list[0].size != 0:
                    vin_out1 = float(vp_out1_list[0][0])

                vin_out2 = float(self.psvoltage)/2
                vp_out2_list = np_data[np.where(abs(np_data[:, 2]) > 0.05), 0]
                if vp_out2_list[0].size != 0:
                    vin_out2 = float(vp_out2_list[0][0])

                # vin1 のうち、小さい値を vp とする
                vp = vin_out1 if vin_out1 < vin_out2 else vin_out2
                Extractor.SR_VP = vp
                # print("(1)vp= {}".format(vp))

                # hsSR2.lib 中の vp の値を書き換え
                replace_str = ".param vp=" + str(vp)
                Extractor.rewrite_file(self.spice.REWRITE_SR_FILENAME, "^\\.param vp=.*", replace_str)

                # Hspice 実行(hspice2.sp を使用)、実行結果から SR の値を抽出
                spfile_index = int(self.spice.sp_filename[-4])
                spfile_index += 1
                new_spfilename = self.spice.sp_filename[:-4] + str(spfile_index) + ".sp"  # hspice2.sp
                print(new_spfilename)
                if not Extractor.ACQ_SR_FLAG:
                    Extractor.ACQ_SR_FLAG = True
                # １回目のシミュレーション結果文字列を退避する
                Extractor.SIM_RESULT_STR_1ST = self.sim_result_str
                sr_result = self.spice.simulate(new_spfilename, 'SR', self.spice.cir_file, 'hspice')
                return sr_result["SR"]

            else:
                # ２回目の実行時

                # vnt, vpt, vp 取得
                vnt = float(self.extract("^ vnt=.*$"))
                vpt = float(self.extract("^ vpt=.*$"))
                vp = Extractor.SR_VP

                if print_dbg:
                    print("vnt= {}".format(vnt))
                    print("vpt= {}".format(vpt))
                    print("(2)vp= {}".format(vp))

                #data = self.sim_result.splitlines()  # なぜかこれだと動かない
                data = self.sim_result_str.split("\n")
                index = 0
                for i, line in enumerate(data):
                    if re.match(self.spice.SR_DATA_PATTERN, line) is not None:
                        index = i
                        break

                # 立ち上がり、立ち下がりで単調増加、単調減少していない場合は
                # メッセージ出力
                # 5行後からデータの記述開始
                # print("index = {}".format(index))
                data2 = data[index + 5:]
                sr_data = []
                offset = 0
                for i, line in enumerate(data2):
                    if re.match("^y$", line) is not None:
                        # データ行の終了
                        break

                    tmp = line.split()

                    # チェックは、経過時間が 100 ns 以降のデータを対象とする
                    if float(tmp[0]) >= 100.0e-9:
                        sr_data.append(tmp)

                # np_data には、100 ns 以降のデータが入っている
                np_data = np.array(sr_data, dtype='float64')

                # 立ち上がりチェック事項
                # ①100ns 後から1回目の定常値vptに到達するまでに、立ち上がりと立ち下がりを繰り返しているかどうか
                # ②1回目の定常値以降、発振していないこと
                #   発振の定義：
                #   (1)データ列の最後の100点の出力電圧の平均値を算出 = Vave
                #   (2)データ列の最後の100点の出力電圧のabs(各点のデータ - Vave)/Vave が全て 0.01 以内にある
                # ③定常値Vave が「abs(2*vp) の 1% 以内」にない場合はメッセージ出力

                if self.SR_msg_flag:
                    self.print_msg("SR: Checking for rise....")

                # ①100ns 後から1回目の定常値vptに到達するまでに、立ち上がりと立ち下がりを繰り返しているかどうか
                # vpt を最初に超えた時点のインデックスを取得
                index_list = np.where(np_data[:, 2] > vpt)[0].tolist()
                if index_list:
                    # vpt より大きいデータあり
                    # 立ち上がり時のチェックなので、傾きがマイナスになったらメッセージ出力
                    over_vpt_index = int(index_list[0])
                    diff = np.diff(np_data[0:over_vpt_index, 2], axis=0)
                    if np.count_nonzero(diff < 0.0) > 0:
                        minus_slope_index = (np.where(diff < 0.0)[0]).tolist()[0]
                        if self.SR_msg_flag:
                            self.print_msg("\tRise: **************** CAUTION ****************")
                            self.print_msg("\tRise: Not monotonically increasing: index={}\n"
                                           .format(offset + 1 + minus_slope_index))
                else:
                    # vpt より大きいデータがない => 最大値が vpt と等しければ問題なし
                    index_list2 = np.where(np_data[:, 2] == vpt)[0].tolist()
                    if index_list2:
                        # 問題なし
                        pass
                    else:
                        # すべてのデータが vpt より小さい -> エラー
                        self.print_msg("\tFall: **************** CAUTION ****************")
                        self.print_msg(f"\tFall: all data is less than vpt:{vpt}")

                # ②1回目の定常値以降、発振していないこと
                # (1)データ列の最後の100点の出力電圧の平均値を算出 = Vave
                last_100_data = np_data[-100:, 2]  # diff_out1 のみ抽出
                v_ave = np.average(last_100_data)
                if print_dbg:
                    print("v_ave={}".format(v_ave))

                """
                # 最小二乗法で定常値を求める場合
                #
                x = np_data[over_vpt_index:, 1]
                y = np_data[over_vpt_index:, 2]
                v_ave = np.polyfit(x, y, 0)  # 定常値(最小二乗法により求める)
                print("\tRise: base = {}".format(v_ave))
                if (abs(2 * vp) - abs(v_ave)) > (abs(2 * vp) * 0.01):
                    self.print_msg("\tRise: **************** CAUTION ****************")
                    self.print_msg("\tRise: Steady state values are not within 1% of " \
                          "abs(2*vp).\n")
                """

                # (2)データ列の最後の100点の出力電圧のabs(各点のデータ - Vave)/Vave が全て 0.01 以内にあるかチェック
                tmp_data = np.abs(last_100_data - v_ave)
                if np.where(tmp_data > abs(v_ave) * 0.01)[0].size != 0:
                    if self.SR_msg_flag:
                        self.print_msg("\tRise: **************** CAUTION ****************")
                        self.print_msg("\tRise: Oscillations: There is a point that does not fall within 1% error\n")

                # ③定常値Vave が「abs(2*vp) の 1% 以内」にない場合はメッセージ出力
                if abs(abs(2 * vp) - abs(v_ave)) > (abs(v_ave) * 0.01):
                    if self.SR_msg_flag:
                        self.print_msg("\tRise: **************** CAUTION ****************")
                        self.print_msg("\tRise: V_ave are not within 1% of abs(2*vp).\n")

                ########## 立ち下がりチェック ###########
                # 立ち下がりチェック事項
                # ①100ns 後から1回目の定常値vntに到達するまでに、立ち上がりと立ち下がりを繰り返しているかどうか
                # ②1回目の定常値以降、発振していないこと
                #   発振の定義：
                #   (1)データ列の最後の100点の出力電圧の平均値を算出 = Vave
                #   (2)データ列の最後の100点の出力電圧のabs(各点のデータ - Vave)/Vave が全て 0.01 以内にある
                # ③「Vave が Vp の 1% 以内」にない場合、メッセージを出力

                # ①1回目の定常値vntに到達するまでに、立ち上がりと立ち下がりを繰り返しているかどうか
                # vnt を最初に超えた時点のインデックスを取得
                if self.SR_msg_flag:
                    self.print_msg("SR: Checking for fall....")
                index_list = np.where(np_data[:, 3] < vnt)[0].tolist()
                if index_list:
                    # vnt 未満のデータあり
                    # 立下り時のチェックなので、傾きがプラスになったらメッセージ出力
                    over_vnt_index = int(index_list[0])
                    diff = np.diff(np_data[0:over_vnt_index, 3], axis=0)
                    if np.count_nonzero(diff > 0.0) > 0:
                        plus_slope_index = (np.where(diff > 0.0)[0]).tolist()[0]
                        if self.SR_msg_flag:
                            self.print_msg("\tFall: **************** CAUTION ****************")
                            self.print_msg("\tFall: Not monotonically decreasing: index={}\n"
                                           .format(offset + 1 + plus_slope_index))
                else:
                    # vnt 未満のデータがない => 最小値が vnt と等しければ問題なし
                    index_list2 = np.where(np_data[:, 3] == vnt)[0].tolist()
                    if index_list2:
                        # 問題なし
                        pass
                    else:
                        # すべてのデータが vnt より大きい -> エラー
                        if self.SR_msg_flag:
                            self.print_msg("\tFall: **************** CAUTION ****************")
                            self.print_msg(f"\tFall: all data is more than vnt:{vnt}")

                # ②1回目の定常値以降、発振していないこと
                # (1)データ列の最後の100点の出力電圧の平均値を算出 = Vave
                last_100_data = np_data[-100:, 3]  # diff_out2 のみ抽出
                v_ave = np.average(last_100_data)
                if print_dbg:
                    print("v_ave={}".format(v_ave))

                # (2)データ列の最後の100点の出力電圧のabs(各点のデータ - Vave)/Vave が全て 0.01 以内にあるかチェック
                tmp_data = np.abs(last_100_data - v_ave)
                if np.where(tmp_data > abs(v_ave) * 0.01)[0].size != 0:
                    if self.SR_msg_flag:
                        self.print_msg("\tFall: **************** CAUTION ****************")
                        self.print_msg("\tFall: Oscillations: There is a point that does not fall within 1% error\n")

                # ③定常値Vave が「abs(2*vp) の 1% 以内」にない場合はメッセージ出力
                if abs(abs(2 * vp) - abs(v_ave)) > (abs(v_ave) * 0.01):
                    if self.SR_msg_flag:
                        self.print_msg("\tFall: **************** CAUTION ****************")
                        self.print_msg("\tFall: V_ave are not within 1% of abs(2*vp).\n")

                if self.SR_msg_flag:
                    self.print_msg("....done\n\n")

                # シミュレーション結果を１回目のものに戻す
                # print("SR={}".format(self.extract(self.spice.SR_PATTERN)))
                ret_str = self.extract(self.spice.SR_PATTERN)
                self.sim_result_str = Extractor.SIM_RESULT_STR_1ST
                Extractor.ACQ_SR_FLAG = False
                return ret_str

    def get_ca(self):
        """
        占有面積を抽出。単位:[m^2]

        Returns
        -------
            占有面積(①MOSトランジスタ、②抵抗、③容量の総面積) 単位:[m^2]
        """

        # ①MOS トランジスタ面積を求める
        # ゲート面積(チャネル幅×チャネル長) + 
        # ドレイン面積(チャネル幅 ×0.6μm) +
        # ソース面積(チャネル幅 ×0.6μm) 

        # config ファイル中のパラメータを取得
        with open(self.cir_file, "r", encoding="utf-8") as f:
            contents = f.read()

        result = re.findall("^M.+$", contents, re.MULTILINE)

        g_area = 0
        d_area = 0
        s_area = 0

        for tmp_str in result:
            result2 = re.search("l=\d+.*$", tmp_str).group()
            index = result2.find(' ')
            if index != -1:
                result2 = result2[:index]
            l_val = Extractor.unit_conv(result2.split("=")[1])
            result2 = re.search("w=\d+.*$", tmp_str).group()
            index = result2.find(' ')
            if index != -1:
                result2 = result2[:index]
            w_val = Extractor.unit_conv(result2.split("=")[1])
            result2 = re.search("m=\d+.*$", tmp_str)
            if result2 != None:
                result2 = result2.group()
                index = result2.find(' ')
                if index != -1:
                    result2 = result2[:index]
                    m_val = Extractor.unit_conv(result2.split("=")[1])
                else:
                    m_val = 1

            g_area += l_val * w_val * m_val
            d_area += w_val * m_val * 0.6e-6
            s_area += w_val * m_val * 0.6e-6

        # print("g_area={}".format(g_area))
        # print("d_area={}".format(d_area))
        # print("s_area={}".format(s_area))

        # ②抵抗面積を求める
        r_area = 0
        result = re.findall("^R.+$", contents, re.MULTILINE)
        for tmp_str in result:
            r_val = Extractor.unit_conv(tmp_str.split()[3])
            if (r_val % 50) == 0:
                # 50Ωの整数倍の場合
                r_area += ((r_val / 50) * 0.4e-6 * 0.4e-6)
            else:
                # 50Ωの整数倍ではない場合  
                quo_100 = r_val // 100
                mod_100 = r_val % 100
                quo_25 = mod_100 // 25
                mod_25 = mod_100 % 25
                quo_10 = mod_25 // 10
                mod_10 = mod_25 % 10
                quo_5 = mod_10 // 5
                mod_5 = mod_10 % 5

                count = 0
                if quo_100 != 0:
                    count += (quo_100 * 2)
                if quo_25 != 0:
                    count += (quo_25 * 2)
                if quo_10 != 0:
                    count += (quo_10 * 5)
                if quo_5 != 0:
                    count += (quo_5 * 10)
                if mod_5 != 0:
                    count += (quo_100 * 50)

                r_area += (count * 0.4e-6 * 0.4e-6)
                # print(count)
        # print("r_area={}".format(r_area))

        # ③容量を求める
        c_area = 0
        result = re.findall("^C.+$", contents, re.MULTILINE)

        for tmp_str in result:
            c_val = Extractor.unit_conv(tmp_str.split()[3])
            c_area += ((c_val / 1e-15) * 1.0e-12)
        # print("c_area={}".format(c_area))

        # 単位を um^2 へ変換
        return "{:e}".format((g_area + d_area + s_area + r_area + c_area) / 1.0e-12)

    def get_psvoltage(self):
        """
        電源電圧を抽出。単位:[V]

        Returns
        -------
            電源電圧。単位:[V]
        """
        if self.psvoltage is None:
            with open(self.cir_file, "r", encoding="utf-8") as f:
                contents = f.read()
            result = re.findall(self.spice.PSVOLTAGE_PATTERN, contents, re.MULTILINE)
            self.psvoltage = result[0].split("=")[1]
        return self.psvoltage

    @classmethod
    def unit_conv(cls, data):
        """
        単位付きの数値を数値へ変換する

        Parameters
        ----------
        data :
           単位付きの数値

        Returns
        -------
            数値
            
        """
        unit_map = {"T": 1.0e+12, "G": 1.0e+9, "MEG": 1.0e+6, "k": 1.0e+3,
                    "m": 1.0e-3, "u": 1.0e-6, "n": 1.0e-9, "p": 1.0e-12,
                    "f": 1.0e-15}

        # 数値
        num_m = re.search("[0-9]+\\.?[0-9]*", data)
        num = num_m.group()

        # 単位
        unit = data.replace(num, "")
        if unit == "":
            return float(num)
        else:
            return float(num) * unit_map[unit]

    @classmethod
    def get_area_magnification(cls, req_unit, my_unit):
        """
        単位変換の際の掛け率を返す(面積)

        Parameters
        ----------
        req_unit :
           変換後の単位
        my_unit :
           現在の単位

        Returns
        -------
            数値

        """
        unit_map = {"m^2": 1.0, "cm^2": 1.0e-4, "mm^2": 1.0e-6, "um^2": 1.0e-12, "nm^2": 1.0e-18}

        # 数値
        return float(unit_map[my_unit]/unit_map[req_unit])

    def print_msg(self, msg):
        """
        結果を標準出力へ表示。出力ファイルパスの指定がある場合は、ファイルへ書き出す

        Parameters
        ----------
        msg :
           出力する文字列
        """

        if self.out_file is None:
            print(msg)
        else:
            with open(self.out_file, 'a') as f:
                print(msg, file=f)

class IllegalArgumentException(Exception):
    """ 引数が不正時のエラー """
    pass


class ItemExtractException(Exception):
    """ 結果抽出時のエラー発生を知らせる例外クラス """
    pass


class IllegalConfFileException(Exception):
    """ config ファイルのフォーマットエラー発生を知らせる例外クラス """
    pass
