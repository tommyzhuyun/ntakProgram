# -*- coding: utf-8 -*-
import re
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
        self.hspice_outfile = None  # Hspice 実行結果を保存するファイル名
        self.pid = None  # 機械学習実行モードの PID

    def set_port(self, port):
        """
        ポートをセット

        Parameters
        ----------
        port : str
            ポート
        """
        self.port = port

    def set_pid(self, pid):
        """
        機械学習実行モードをセット

        Parameters
        ----------
        pid : str
            機械学習時の pid
        """
        self.pid = pid

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

        #print(f"execSpice: cmd: {cmd}")
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

            elif spice_type == 'hspice':
                with open(self.hspice_outfile, 'w') as fp:
                    # Hspice 実行結果をファイルに保存
                    #print(f"spice: call subprocess.run: cmd:{cmd}")

                    try:
                        cp = subprocess.run(cmd, shell=True, stdout=fp, timeout=30)
                        #cp = subprocess.run(cmd, stdout=fp)
                        #cp = subprocess.run(cmd, shell=False, check=False, stdout=fp, stderr=subprocess.DEVNULL)  #上行と同じ動きになる
                        #print(f"cmd:{cmd} done.-----------------------------")
                        #cp = subprocess.run(cmd, shell=False, stdout=fp)

                    except subprocess.TimeoutExpired as e:
                        print(f"Spice.simulate(): Timeout: Spice: cmd = {str(cmd)}")
                        return ""

                with open(self.hspice_outfile, "r", encoding="utf-8") as f:
                    # ファイルに保存された Hspice 実行結果を読み込み
                    result = f.read()

            else:
                pass

        except subprocess.CalledProcessError as e:
            raise ExecSpiceException("Spice.simulate(): Failed Execute Spice: cmd = "+str(cmd))

        #print(result)
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
        #print(tmp_result)
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
    #CC_PATTERN = "^ ib= .*$"  # 2021-07-16
    CC_PATTERN = "^ *ib=.*$"
    #PD_PATTERN = "^ pdis= .*$"  # 2021-07-16
    PD_PATTERN = "^ *pdis=.*$"
    # IRN: Hspice は結果中の最後の要素。
    # IRN_PATTERN = "total equivalent input noise += +.* +V +$"  # 新Hspice
    IRN_PATTERN = "total equivalent input noise += +.*$"
    OR_SIM_PATTERN = "output resistance at v\\(out\\) += +.*$"
    OR_PATTERN = ""
    THD_PATTERN = "total harmonic distortion += .* +percent$"
    #OVR_PATTERN = "^ ovr= .*$"  # 2021-07-16
    OVR_PATTERN = "^ *ovr=.*$"
    #CMRR_PATTERN = "^ cmrr=\s+.*at"  # 2021-07-16
    CMRR_PATTERN = "^ *cmrr=.*at"
    #PSRR_PATTERN = "^ psrr= .*$"  # 抽出用パターン文字列(電源電圧変動除去比)  # 2021-07-16
    PSRR_PATTERN = "^ *psrr=.*$"  # 抽出用パターン文字列(電源電圧変動除去比)
    #CMIR_PATTERN = "^ \\$cmir$"  # 抽出用パターン文字列(同相入力範囲)  # 2021-07-16
    CMIR_PATTERN = "^ *\\$cmir$"  # 抽出用パターン文字列(同相入力範囲)
    #GAIN_SIM_PATTERN = "^ dcgain=.*$"  # 抽出用パターン文字列(利得)  # 2021-07-16
    GAIN_SIM_PATTERN = "^ *dcgain=.*$"  # 抽出用パターン文字列(利得)
    GAIN_PATTERN = ""  # 抽出用パターン文字列(利得)
    #GAIN_DB_PATTERN = "^ dcgain_db=.*$"  # 抽出用パターン文字列(利得[dB])  # 2021-07-16
    GAIN_DB_PATTERN = "^ *dcgain_db=.*$"  # 抽出用パターン文字列(利得[dB])
    #PM_PATTERN = "^ phase_margin=.*$"  # 抽出用パターン文字列(位相余裕)   # 2021-07-16
    PM_PATTERN = "^ *phase_margin=.*$"  # 抽出用パターン文字列(位相余裕)
    GBW_PATTERN = ""  # 抽出用パターン文字列(利得帯域幅積)
    #SR_PATTERN = "^ sr=\\s+.*"  # 抽出用パターン文字列(スルーレート)
    SR_PATTERN = "^ *sr=\\s+.*"  # 抽出用パターン文字列(スルーレート)
    SR_DATA_PATTERN = "^x$"  # 抽出用パターン文字列(SR詳細データ)
    CA_PATTERN = ""  # 抽出用パターン文字列(チップ面積)
    PSVOLTAGE_PATTERN = "^\\.param\\s+psvoltage=.*$"  # 抽出用パターン文字列(電源電圧)

    LIB_PREFIX = "hs"
    SR_VP_PATTERN = "^ \\$sr1$"  # 抽出用パターン文字列(スルーレート)
    REWRITE_SR_FILENAME = "../Lib_Data/" + LIB_PREFIX + "SR2.lib"  # 回路評価用モードの場合。ML学習モードの際は、動作中に書き換える
    # OUTPUT_DIR = "../Lis_Data/"  # 回路評価用モードの場合。ML学習モードの際は、動作中に書き換える

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
        cmd2 = "exec hspice64"
        if self.port is not None:
            cmd.extend(['-CC'])
            cmd2 += " -CC"

        basename_without_ext = os.path.splitext(os.path.basename(sp_filename))[0]  # hspice
        #
        self.hspice_outfile = "../Lis_Data/" + basename_without_ext + '.lis'
        if self.pid is not None:
            # 機械学習モードの時、一時出力用ディレクトリは ElemParamEnv:step で作成
            """
            pattern_list = re.findall("/ML/(.*)/Sp_Data/", os.path.abspath(sp_filename))
            pid = str(pattern_list[0])

            # Hspice 結果出力ファイル: ./ML/<pid>/Lis_Data/[spファイル名].lis へ保存
            os.makedirs('./ML/' + pid + '/Lis_Data', exist_ok=True)

            # 【注意！！】回路評価プログラム実行モードとは、出力先が異なる
            Hspice.REWRITE_SR_FILENAME = './ML/' + pid + '/Lib_Data/' + Hspice.LIB_PREFIX + 'SR2.lib'
            Hspice.OUTPUT_DIR = './ML/' + pid + '/Lis_Data/'
            self.hspice_outfile = Hspice.OUTPUT_DIR + basename_without_ext + '.lis'
            #print("111111111")
            """

        else:
            # 回路評価プログラム実行モード。Hspice 実行結果は ../Lis_Data/hspice1.lis および hspice2.lis へ保存
            # Hspice 結果出力ファイル: ../Lis_Data/[spファイル名].lis へ保存
            os.makedirs('../Lis_Data', exist_ok=True)
            #print("222222")

        #print(self.hspice_outfile)
        cmd.extend(['-i', sp_filename])
        cmd2 += " -i "
        cmd2 += sp_filename
        if self.port is not None:
            cmd.extend(['-port', self.port])
            cmd2 += " -port "
            cmd2 += self.port
        cmd.extend(['-o', self.hspice_outfile])
        cmd2 += " -o "
        cmd2 += self.hspice_outfile
        #print(cmd)
        return super().simulate(cmd2, sp_filename, item, cir_file, spice_type)


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
        # print(cmd)
        return super().simulate(cmd, sp_filename, item, cir_file, spice_type)


class ExecSpiceException(Exception):
    """ Spice 実行エラーが発生したことを知らせる例外クラス """
    pass


class FileNotFoundException(Exception):
    """ ファイルが存在しないことを知らせる例外クラス """
    pass
