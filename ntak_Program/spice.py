# -*- coding: utf-8 -*-

import subprocess
import os


class Spice:

    """ 直流利得、出力抵抗計算用パラメータ(configファイルから取得) """
    conf_param = None

    """ 抽出用パラメータ """
    CC_PATTERN = ""  # 抽出用パターン文字列(消費電流)
    PD_PATTERN = ""  # 抽出用パターン文字列(消費電力)
    IRN_PATTERN = ""  # 抽出用パターン文字列(入力換算雑音)
    OR_SIM_PATTERN = ""  # 抽出用パターン文字列(出力抵抗:シミュレーション値)
    OR_PATTERN = ""  # 抽出用パターン文字列(出力抵抗)
    CMIR_PATTERN = ""  # 抽出用パターン文字列(同相入力範囲)
    CMRR_PATTERN = ""  # 抽出用パターン文字列(同相除去比)
    GAIN_SIM_PATTERN = ""  # 抽出用パターン文字列(利得:シミュレーション値)
    GAIN_PATTERN = ""  # 抽出用パターン文字列(利得)
    PM_PATTERN = ""  # 抽出用パターン文字列(位相余裕)
    GBW_PATTERN = ""  # 抽出用パターン文字列(利得帯域幅積)
    OVR_PATTERN = ""  # 抽出用パターン文字列(出力電圧範囲)
    PSRR_PATTERN = ""  # 抽出用パターン文字列(電源電圧変動除去比)
    SR_PATTERN = ""  # 抽出用パターン文字列(スルーレート)
    THD_PATTERN = ""  # 抽出用パターン文字列(全高調波歪)
    CA_PATTERN = ""  # 抽出用パターン文字列(チップ面積)
    SR_DATA_PATTERN = ""  # 抽出用パターン文字列(SRのデータチェック用)
    PSVOLTAGE_PATTERN = ""  # 抽出用パターン文字列(電源電圧)

    PARAM_UNIT = {'PSVOLTAGE': ['V', '電源電圧'],
                  'CC': ['A', '消費電流'], 'PD': ['W', '消費電力'], 'CMIR': ['%', '同相入力範囲'],
                  'CMRR': ['times', '同相除去比'], 'CMRR_DB': ['dB', '同相除去比 dB'],
                  'GAIN_SIM': ['', '直流利得(sim)'], 'GAIN': ['times', '直流利得(補正後)'],
                  'GAIN_DB_SIM': ['dB', '直流利得 dB(sim)'], 'GAIN_DB': ['dB', '直流利得 dB(補正後)'],
                  'GBW': ['Hz', 'ゲイン帯域幅'], 'PM': ['degree', '位相余裕'], 'IRN': ['Hz', '入力換算雑音'],
                  'OR_SIM': ['', '出力抵抗(sim)'], 'OR': ['ohm', '出力抵抗(補正後)'], 'OVR': ['%', '出力電圧範囲'],
                  'PSRR': ['times', '電源電圧変動除去比'], 'PSRR_DB': ['dB', '電源電圧変動除去比 dB'],
                  'SR': ['V/us', 'スルーレート'], 'THD': ['%', '全高調波歪'], 'CA': ['um^2', '占有面積'],
                  }

    LIB_PREFIX = ""  # 各 lib ファイルにつく接頭文字列。Hspice="hs", Ngspice="ng"

    def __init__(self):
        self.cmd = []  # 実行時のコマンド配列
        self.port = None  # Hspice 実行時の -port 引数の値
        self.cmd = None  # input sp filename
        self.cir_file = None  # Main stage's file path
        self.extractor = None  # Extractor 結果抽出用クラス
        self.hpspice_outfile = None  # Hspice 実行結果を保存するファイル名

    def set_port(self, port):
        """
        ポートをセット

        Parameters
        ----------
        port : str
            ポート
        """
        self.port = port

    def set_conf(self, conf):
        """
        configファイルから取得したパラメータが格納されている
        dict をセット

        Parameters
        ----------
        conf : dict
            configファイルから取得したパラメータ
        """
        self.conf = conf

    def set_extractor(self, extractor):
        """
        結果抽出用クラスのインスタンスをセット

        Parameters
        ----------
        extractor : Extractor
            結果抽出用クラスのインスタンス
        """
        self.extractor = extractor

    def execSpice(self, cmd, sp_filename, spice_type):
        """
        Spiceによるシミュレーションを行う

        Parameters
        ----------
        cmd :
            OS に渡すコマンド配列
        sp_filename :
            Spiceに渡すネットリストファイル名
        spice_type : str
            実行する spice ('hspice' または 'ngspice')

        Returns
        -------
            item == None の場合、全要素の結果値を dict に入れて返す。
            何らかの要素を指定された場合は、その値を返す。
        """

        self.sp_filename = sp_filename

        if not os.path.exists(sp_filename):
            raise FileNotFoundException("Spice.simulate(): "+sp_filename)

        result = ""
        try:
            if spice_type == 'ngspice':
                """
                o = subprocess.run(cmd, shell=False, check=False, \
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                """
                o = subprocess.run(cmd, shell=False, check=False, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
                # check=Trueにすると、CalledProcessErrorが発生してしまう
                # print(o.stdout)
                result = o.stdout.decode('utf_8')
                # print(result)
            elif spice_type == 'hspice':
                with open(self.hpspice_outfile, 'w') as fp:
                    # Hspice 実行結果をファイルに保存
                    cp = subprocess.run(cmd, stdout=fp)
                with open(self.hpspice_outfile, "r", encoding="utf-8") as f:
                    # ファイルに保存された Hspice 実行結果を読み込み
                    result = f.read()

            else:
                pass

        except subprocess.CalledProcessError as e:
            raise ExecSpiceException("Spice.simulate(): Failed Execute Spice: cmd = "+str(cmd))

        # print(result)
        return result

    def simulate(self, cmd, sp_filename, item=None, cir_file=None, spice_type=None):
        """
        Spiceによるシミュレーションを行う

        Parameters
        ----------
        cmd :
            Spice 実行コマンド
        sp_filename :
            Spiceに渡すネットリストファイル名
        item :
            抽出する要素名
        cir_file : str
            回路ファイルパス
        spice_type : str
            実行する spice ('hspice' または 'ngspice')

        Returns
        -------
            指定された要素の結果値を dict に入れて返す。
            item == None の場合は、全要素が対象となる。
        """
        tmp_result = None
        try:
            tmp_result = self.execSpice(cmd, sp_filename, spice_type)
        except ExecSpiceException as e:
            print(e)

        self.extractor.set_sim_result_str(tmp_result)

        result = dict()  # dict 型で返す
        if item:
            if isinstance(item, list):
                # 配列
                for tmp in item:
                    result[tmp] = self.extractor.get_each_elem(tmp)
            elif isinstance(item, str):
                # 文字列
                result[item] = self.extractor.get_each_elem(item)

        # print("Spice: simulate: ".format(result))
        return result

    def get_cc_pattern(self):
        return self.CC_PATTERN

    def get_pd_pattern(self):
        return self.PD_PATTERN

    def get_irn_pattern(self):
        return self.IRN_PATTERN

    def get_or_sim_pattern(self):
        return self.OR_SIM_PATTERN

    def get_or_pattern(self):
        return self.OR_PATTERN

    def get_cmir_pattern(self):
        return self.CMIR_PATTERN

    def get_cmrr_pattern(self):
        return self.CMRR_PATTERN

    def get_gain_sim_pattern(self):
        return self.GAIN_SIM_PATTERN

    def get_gain_pattern(self):
        return self.GAIN_PATTERN

    def get_pm_pattern(self):
        return self.PM_PATTERN

    def get_gbw_pattern(self):
        return self.GBW_PATTERN

    def get_ovr_pattern(self):
        return self.OVR_PATTERN

    def get_psrr_pattern(self):
        return self.PSRR_PATTERN

    def get_sr_pattern(self):
        return self.SR_PATTERN

    def get_thd_pattern(self):
        return self.THD_PATTERN

    def get_ca_pattern(self):
        return self.CA_PATTERN

    def get_sr_data_pattern(self):
        return self.SR_DATA_PATTERN

    def get_psvoltage_data_pattern(self):
        return self.PSVOLTAGE_PATTERN


class Hspice(Spice):
    """
    hspice:
        (client) hspice64 [-CC] -i input_file [-port hostname:port_num]
                [-o output_file]
    """
    CC_PATTERN = "^ ib= .*$"
    PD_PATTERN = "^ pdis= .*$"
    # IRN: Hspice は結果中の最後の要素。
    IRN_PATTERN = "total equivalent input noise += +.*$"
    OR_SIM_PATTERN = "output resistance at v\\(out\\) += +.*$"
    OR_PATTERN = ""
    THD_PATTERN = "total harmonic distortion += .* +percent$"
    OVR_PATTERN = "^ ovr= .*$"
    CMRR_PATTERN = "^ cmrr=\s+.*at"
    PSRR_PATTERN = "^ psrr= .*$"  # 抽出用パターン文字列(電源電圧変動除去比)
    CMIR_PATTERN = "^ \\$cmir$"  # 抽出用パターン文字列(同相入力範囲)
    GAIN_SIM_PATTERN = "^ dcgain=.*$"  # 抽出用パターン文字列(利得)
    GAIN_PATTERN = ""  # 抽出用パターン文字列(利得)
    GAIN_DB_PATTERN = "^ dcgain_db=.*$"  # 抽出用パターン文字列(利得[dB])
    PM_PATTERN = "^ phase_margin=.*$"  # 抽出用パターン文字列(位相余裕)
    GBW_PATTERN = ""  # 抽出用パターン文字列(利得帯域幅積)
    SR_PATTERN = "^ sr=\\s+.*"  # 抽出用パターン文字列(スルーレート)
    SR_DATA_PATTERN = "^x$"  # 抽出用パターン文字列(SR詳細データ)
    CA_PATTERN = ""  # 抽出用パターン文字列(チップ面積)
    PSVOLTAGE_PATTERN = "^\\.param\\s+psvoltage=.*$"  # 抽出用パターン文字列(電源電圧)

    LIB_PREFIX = "hs"
    SR_VP_PATTERN = "^ \\$sr1$"  # 抽出用パターン文字列(スルーレート)
    REWRITE_SR_FILENAME = "../Lib_Data/" + LIB_PREFIX + "SR2.lib"
    OUTPUT_DIR = "../Lis_Data/"

    sr_exec_flag = False  # SR取得中(Hspiceの場合、2回シミュレーションを行ってSRを求める)のフラグ

    def set_port(self, port):
        """
        Hspice を C/Sモードで動作させる際の port をセットする

        Parameters
        ----------
        port : str
            Hspice 実行時の -port オプションで指定するポート
        """
        self.port = port

    def simulate(self, sp_filename, item, cir_file=None, spice_type=None):
        cmd = ['hspice64']
        if self.port is not None:
            cmd.extend(['-CC'])
        cmd.extend(['-i', sp_filename])
        if self.port is not None:
            cmd.extend(['-port', self.port])
        # Hspice 結果出力ファイル: ../Lis_Data/[spファイル名].lis へ保存
        os.makedirs('../Lis_Data', exist_ok=True)
        basename_without_ext = os.path.splitext(os.path.basename(sp_filename))[0]
        self.hpspice_outfile = self.OUTPUT_DIR + basename_without_ext + '.lis'
        cmd.extend(['-o', self.hpspice_outfile])
        # print(cmd)
        return super().simulate(cmd, sp_filename, item, cir_file, spice_type)


class Ngspice(Spice):
    """
    ngspice:
        ngspice -b input_file [-o output_file]
    """

    CC_PATTERN = "^max\\(abs\\(i\\(vdd\\)\\),"\
                 "abs\\(i\\(vss\\)\\)\\)\s+=\s+.*$"
    PD_PATTERN = "^max\\(abs\\(i\\(vdd\\)\\),"\
                 "abs\\(i\\(vss\\)\\)\\)\\*2.*\s+=\s+.*$"
    IRN_PATTERN = "^inoise_total\s+=\s+.*$"
    OR_SIM_PATTERN = "^output_impedance_at_v\\(out\\)\s+=\s+.*$"
    OR_PATTERN = ""
    # THD_PATTERN = "THD:\s+\d+\.\d+\s+%"
    THD_PATTERN = "THD:\\s+.+\\s+%"
    OVR_PATTERN = "^ovr\s+=\s+.*$"
    CMRR_PATTERN = "^cmrr\s+=.*at"
    PSRR_PATTERN = "^PSRR\s+=\s+.*$"
    CMIR_PATTERN = "^CMIR\s+=\s+.*$"
    PM_PATTERN = "Phase Margin\s+=\s+.*$"
    GBW_PATTERN = "Gain Bandwidth Product\s+=\s+.*$"
    SR_PATTERN = "^SR\s+=\s+.*$"
    GAIN_SIM_PATTERN = "^dcgain\s+=\s+.*$"
    GAIN_PATTERN = ""
    GAIN_DB_PATTERN = "^dcgain_db\s+=\s+.*$"
    PM_PATTERN = "Phase Margin\s+=\s+.*$"
    # GBW_PATTERN = "Gain Bandwidth Product\s+=\s+.*$"
    # SR_PATTERN = "^SR\s+=\s+.*$"
    SR_DATA_PATTERN = "Transient Analysis"
    CA_PATTERN = ""
    PSVOLTAGE_PATTERN = "^\\.param\\s+psvoltage=.*$"

    LIB_PREFIX = "ng"

    def simulate(self, sp_filename, item=None, cir_file=None, spice_type=None):
        """
        Ngspiceによるシミュレーションを行う

        Parameters
        ----------
        sp_filename :
            Spiceに渡すネットリストファイル名
        item :
            抽出する要素名
        cir_file :
            netlist ファイル名
        spice_type : str
            シミュレーションを行うspice を指定する。
            "ngspice", "hspice" のいずれかを指定。
            指定のない場合は、デフォルト値の "ngspice" になる

        Returns
        -------
            item == None の場合、全要素の結果値を dict に入れて返す。
            何らかの要素を指定された場合は、その値を返す。
        """

        # print("Ngspice: simulate: sp_filename {}".format(sp_filename))
        cmd = ['ngspice', '-b', sp_filename]
        return super().simulate(cmd, sp_filename, item, cir_file, spice_type)


class ExecSpiceException(Exception):
    """ Spice 実行エラーが発生したことを知らせる例外クラス """
    pass


class FileNotFoundException(Exception):
    """ ファイルが存在しないことを知らせる例外クラス """
    pass