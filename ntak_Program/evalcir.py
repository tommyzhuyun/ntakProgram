# -*- coding: utf-8 -*-

import re
import numpy as np
import texttable as ttb
from spice import *
from extractor import Extractor, IllegalArgumentException


class EvalCir:
    """
    回路の評価を行うクラス
    """

    def __init__(self, sp_filename, spice_type='ngspice', port=None,
                 cir_file=None, conf_file='ngspice.conf', out_file=None, pid=None):
        """
        回路の評価を行う

        Parameters
        ----------
        sp_filename : str
            ネットリストファイル名

        spice_type : str
            シミュレーションを行うspice を指定する。
            "ngspice", "hspice" のいずれかを指定。
            指定のない場合は、デフォルト値の "ngspice" になる

        port : str
            spice_type で "hspice" 指定時、かつ C/S モードで動作させる場合の
　          ポートを指定。spice_typeで指定なし、もしくは "ngspice" 指定の時は
            無視される

        cir_file : str
            回路ファイル名

        conf_file : str
            config ファイル名

        out_file : str
            結果出力用ファイル名。None の場合は、標準出力へ結果表示

        pid : str
            MLモード動作時のプロセスID

        Returns
        -------
        EvalCir : EvalCir
            対応するシミュレータークラスのインスタンス
        """
        # 回路ファイルパス
        self.cir_file = None

        # シミュレーション結果を保持
        self.sim_result = dict()

        # 目標値のリスト
        self.requirements_list = dict()

        # Failed 時の設定値のリスト
        self.failed_val_list = dict()

        # 評価式のリスト
        self.eval_list = dict()

        # 評価式の結果のリスト
        self.eval_result = dict()

        self.spice = self.get_spice_instance(spice_type)
        if port is not None:
            if spice_type == "hspice":
                self.spice.set_port(port)
            else:
                # hspice 以外の場合は、port が指定されていても無視
                pass

        #print(f"conf_file: {conf_file}")
        tmp_conf_file = conf_file
        #print(f"pid: {pid}")
        if pid is not None:
            # ML モードで動いている場合
            # conf ファイルはコピーしておらす、ディレクトリ移動しているためパスを調整する必要あり
            tmp_conf_file = "../../../" + conf_file
        params = self.get_conf(tmp_conf_file)
        self.spice.set_pid(pid)
        self.spice.set_conf(params)

        # Extractor.print_msg('spice_type: {}'.format(spice_type))
        # Extractor.print_msg("*********************")
        self.spice_type = spice_type
        self.sp_filename = sp_filename
        self.cir_file = cir_file
        self.out_file = out_file

        if self.spice_type == 'ngspice':
            # 「.csparam psvoltage=psvoltage」の行が入っていなかったら追加
            with open(cir_file, "r", encoding="utf-8") as f:
                contents = f.read()
            lines = contents.splitlines()
            check_flag = False
            for tmp_str in lines:
                if tmp_str.lower() == r".csparam psvoltage=psvoltage":
                    check_flag = True
                    break

            if not check_flag:
                print(f"ERROR: {cir_file}: 「.csparam psvoltage=psvoltage」行を追加してください")
                exit(1)

        # 結果出力用ファイル名
        self.out_file = out_file
        self.extractor = Extractor(None, self.spice, self.cir_file, self.out_file, self.failed_val_list)
        self.spice.set_extractor(self.extractor)


    @classmethod
    def get_spice_instance(cls, spice_type):
        """
        実行時のコマンドから判別して、対応する spice のインスタンスを返す

        Parameters
        ----------
        spice_type :
            使用するスパイスの指定
        Returns
        -------
            対応する spiceのインスタンス
        """

        spice_map = {
            'hspice': Hspice,
            'ngspice': Ngspice,
        }

        try:
            return spice_map[spice_type]()
        except KeyError as e:
            raise ValueError('Invalid spice: {}'.format(spice_type))
        finally:
            pass

    def get_conf(self, conf_file):
        """
        実行時のコマンドから判別して、対応する spice のインスタンスを返す

        Parameters
        ----------
        conf_file : str
            config ファイルのパス名

        Returns
        -------
            config ファイル中のパラメータとその値が入った dict
        """

        # config ファイル中のパラメータを取得
        try:
            #print(f"EvalCir: get_conf(): conf_file: {conf_file}")
            conf = dict()
            with open(conf_file, "r", encoding="utf-8") as f:
                tmp_str = f.read()
            result = re.findall(".*:.*$", tmp_str, re.MULTILINE)
            for tmp_str in result:
                if tmp_str.startswith("#"):
                    # コメント行
                    pass
                else:
                    # 指定されたファイル名から、変数の値を取得
                    if tmp_str.startswith("Path:"):
                        path = tmp_str.split(":")[1]
                        # パラメータ名を取得
                        par_str = tmp_str.split(":")[2]
                        param_list = par_str.split(",")

                        for param in param_list:
                            pattern_str = "^.*" + param + "=.*$"
                            with open(path, "r", encoding="utf-8") as f2:
                                str2 = f2.read()
                            result2 = re.findall(pattern_str, str2, re.MULTILINE)
                            val = (result2[0].split("="))[1]
                            val = Extractor.unit_conv(val)
                            conf[param] = val

                    # 目標値を取得
                    if tmp_str.startswith("TargetVal:"):
                        tmp_data = tmp_str.split(":")
                        # パラメータ名を取得
                        par_str = tmp_data[1]
                        # 範囲を取得
                        cond = tmp_data[2]
                        # 数値+単位を取得
                        num_unit = tmp_data[3]
                        # 数値部分を抽出
                        tmp_list = num_unit.split()
                        num = tmp_list[0]
                        # 単位のみ抽出
                        unit = tmp_list[1]
                        # print("param: {}, cond: {}, num: {}, unit: {}".format(param, cond, num, unit))
                        self.requirements_list[par_str] = LimitVal(par_str, cond, num, unit)

                    # 評価式を取得
                    if tmp_str.startswith("EvalForm:"):
                        tmp_data = tmp_str.split(":")
                        # 評価式名を取得
                        tmp_str2 = tmp_data[1]
                        tmp_data = tmp_str2.split("=")
                        self.eval_list[tmp_data[0].strip()] = tmp_data[1].strip()

                    # Failed 時の設定値を取得
                    if tmp_str.startswith("FailedVal:"):
                        tmp_data = tmp_str.split(":")
                        # パラメータ名を取得
                        par_str = tmp_data[1]
                        # 数値を取得
                        num = tmp_data[2]
                        self.failed_val_list[par_str] = float(num)

            # print(conf)
            # print(EvalCir.requirements_list)
            # print(EvalCir.eval_list)
            # print(self.failed_val_list)
            return conf
        except FileNotFoundException as e:
            raise IllegalArgumentException('No such config file: {}'.format(conf_file))
        finally:
            pass

    def calc(self, sp_filename, item=None):
        """
        spiceによるシミュレーション結果を返す

        Parameters
        ----------
        sp_filename: string
            netlistファイル名

        item: 評価項目文字列またはその配列
            抽出する評価項目
            ①抽出する評価項目
            ②同一 LIBファイル内で結果が取得できるものは、各項目の配列
            ③指定がない場合は、すべての項目を抽出

        Returns
        -------
            itemを指定した場合は、その項目の評価。
            指定しない場合はすべての項目の評価（15項目）の連想配列
        """

        tmp_item = item

        # CC : PD 必須
        if tmp_item is not None:
            if ('CC' in tmp_item) and ('PD' not in tmp_item):
                tmp_item.append('PD')
            # GAIN: GAIN_SIM, OR_SIM, OR 必須
            if 'GAIN' in tmp_item:
                if 'GAIN_SIM' not in tmp_item:
                    tmp_item.append('GAIN_SIM')
                if 'OR_SIM' not in tmp_item:
                    tmp_item.append('OR_SIM')
                if 'OR' not in tmp_item:
                    tmp_item.append('OR')
            # OR: OR_SIM, GAIN_SIM 必須
            if 'OR' in tmp_item:
                if 'OR_SIM' not in tmp_item:
                    tmp_item.append('OR_SIM')
                if 'GAIN_SIM' not in tmp_item:
                    tmp_item.append('GAIN_SIM')
            if 'CMIR' in tmp_item:
                if 'PSVOLTAGE' not in tmp_item:
                    tmp_item.append('PSVOLTAGE')

        else:
            # すべてのパラメータ取得
            tmp_item = list(Spice.PARAM_UNIT.keys())
        tmp_result = self.spice.simulate(sp_filename, tmp_item, self.cir_file, self.spice_type)

        # シミュレーション結果文字列をを抽出用クラスへセット
        #self.extractor.sim_result_str = tmp_result

        # results は str もしくは dict
        # シミュレーション結果が条件を満たすか否かチェック
        self.check_requirements(tmp_result)

        self.calc_eval_form()
        return self.sim_result

    def check_requirements(self, result):
        """
        シミュレーション結果が要件を満たすか否かチェック
        sim_result に判定結果をセットする

        Parameters
        ----------
        result: dict
            シミュレーション結果
        """
        for item_name, item_val in result.items():
            # 指定要件あり
            judge = False
            #print(item_name, item_val)
            # 指定されたパラメータに関する結果が無かった場合(空のリスト)
            if isinstance(item_val, list) and len(item_val) == 0:
                item_val = None
                self.sim_result[item_name] = ParamData(item_val, sim_unit, judge)
                continue

            # CC は config ファイル内に指定要件なし
            sim_unit = Spice.PARAM_UNIT[item_name][0]
            if item_name == 'CC':
                # CC の要件が複雑で config 内に記述できないため実装
                # ①消費電流変動率が 50% 以内かチェック
                # item_val は numpy.ndarray
                base_val = float(item_val[1][1])
                tmp_array = np.copy(item_val)
                tmp_array = tmp_array.astype(np.float64)
                if np.all((tmp_array >= (base_val * 0.5)) & (tmp_array <= (base_val * 1.5))):
                    # すべての要素が 50% 以内
                    judge = True
                # CC の場合は、基準の要素[1][1]の値
                item_val = item_val[1][1]

            else:
                # 指定要件があるか？
                req = self.requirements_list.get(item_name, None)

                if (re.search(".+_SIM$", item_name) is not None) or (req is None):
                    # XXX_SIM についてはチェックなし
                    # 指定要件なし
                    # print("{}: pass....".format(item_name))
                    self.sim_result[item_name] = ParamData(item_val, sim_unit, True)
                    continue

                if item_name == 'PD':
                    # PD の場合は、基準の要素[1][1]の値が要件を満たすかチェック
                    item_val = item_val[1][1]

                # CC: 消費電流変動率が 50% 以内のチェックは済んでいるはず. PD のチェックはそちらで行う
                if req is not None:
                    # 指定要件あり
                    req_cond = req.cond
                    req_num = req.num
                    req_unit = req.unit

                    sim_unit = Spice.PARAM_UNIT[item_name][0]
                    if sim_unit != req_unit:
                        # print("Not Same Unit....")
                        # 単位を揃える
                        if re.search("\\^2$", req_unit) is not None:
                            # 面積の場合。単位付きの数値を数値へ変換
                            # print("Area unit")
                            mag = Extractor.get_area_magnification(req_unit, sim_unit)
                            new_item_val = float(item_val) * mag
                            if req_cond == '1':
                                # 以上
                                self.print_check_msg("", req_cond, item_val, sim_unit, req_num, req_unit)
                                self.print_check_msg("---> ", req_cond, new_item_val, req_unit, req_num, req_unit)
                                if float(new_item_val) >= float(req_num):
                                    judge = True
                            elif req_cond == '2':
                                # 以下
                                self.print_check_msg("", req_cond, item_val, sim_unit, req_num, req_unit)
                                self.print_check_msg("---> ", req_cond, new_item_val, req_unit,
                                                        req_num, req_unit)
                                if float(new_item_val) <= float(req_num):
                                    judge = True
                            item_val = new_item_val
                            sim_unit = req_unit
                        else:
                            # 面積以外の単位
                            # print("NOT Area unit")
                            req_num = Extractor.unit_conv(req_num)
                            judge = False
                            if req_cond == '1':
                                # 以上
                                self.print_check_msg("", req_cond, item_val, sim_unit, req_num, req_unit)
                                if float(item_val) >= float(req_num):
                                    judge = True
                            elif req_cond == '2':
                                # 以下
                                self.print_check_msg("", req_cond, item_val, sim_unit, req_num, req_unit)
                                if float(item_val) <= float(req_num):
                                    judge = True

                            item_val = new_item_val
                            sim_unit = req_unit

                    else:
                        # 単位が同じ
                        # print("Same Unit....")
                        req_num = Extractor.unit_conv(req_num)
                        judge = False
                        if req_cond == '1':
                            # 以上
                            self.print_check_msg("", req_cond, item_val, sim_unit, req_num, req_unit)
                            if float(item_val) >= float(req_num):
                                judge = True
                        elif req_cond == '2':
                            # 以下
                            self.print_check_msg("", req_cond, item_val, sim_unit, req_num, req_unit)
                            if float(item_val) <= float(req_num):
                                judge = True
                else:
                    # 指定要件なし
                    pass

            # print("Done:  item_name = {}, judge = {}".format(item_name, judge))
            self.sim_result[item_name] = ParamData(item_val, sim_unit, judge)

        """
        for item_name, item_val in self.sim_result.items():
            print("{} = {}".format(item_name, item_val))
        """

    def calc_eval_form(self):
        """
        シミュレーション結果が要件を満たすか否かチェック
        sim_result に判定結果をセットする

        Parameters
        ----------
        sim_result: dict
            シミュレーション結果
        """
        result = dict()
        for item_name, param_data in self.sim_result.items():
            #print(f"item_name: {item_name}, param_data:{param_data}")
            # 各パラメータの名前を持つ変数を宣言する
            # print("exec: {} = {}".format(item_name, float(param_data.val)))
            if param_data.val is None:
                exec('{} = {}'.format(item_name, None))
            elif param_data.val == np.inf:
                exec('{} = {}'.format(item_name, "float('inf')"))
            elif param_data.val == -np.inf:
                exec('{} = {}'.format(item_name, "float('-inf')"))
            else:
                exec('{} = {}'.format(item_name, float(param_data.val)))

        for eval_name, formula in self.eval_list.items():
            # print(formula)
            try:
                self.eval_result[eval_name] = "{:.6E}".format(eval(str(formula)))
            except ZeroDivisionError as e:
                print(f"ERROR::: {eval_name}: ZeroDivisionError")
        # print(result)

    def get_eval_list(self):
        return self.eval_result

    def get_requirements(self):
        return self.requirements_list

    def print_msg(self, msg):
        self.extractor.print_msg(msg)

    def first_print(self):
        """
        出場部門と目標値の表示
        """
        self.print_msg("*==========================================================================*")
        self.print_msg("                              PROGRAM START                                 ")
        self.print_msg("*==========================================================================*")

    def print_check_msg(self, prefix, req_cond, item_val, sim_unit, req_num, req_unit):
        print_flag = False
        if print_flag:
            ineq = ""
            if req_cond == '1':
                ineq = ">="
            elif req_cond == '2':
                ineq = "<="

            self.print_msg(prefix + "checking {:.6E}[{}] {} {:.6E}[{}]...".format(float(item_val), sim_unit, ineq,
                                                                                       float(req_num), req_unit))
        else:
            pass

    def print_opamp_performance(self):
        """
        性能値の表示

        Parameters:
            result: dict
                key: パラメータ名, value: ParamData　クラス
        """
        self.print_msg("*")
        self.print_msg("**---< Design Result of Opamp >---**")

        table = ttb.Texttable()
        table.set_cols_align(['l', 'r', 'r', 'l'])
        table.set_cols_dtype(['t', 't', 't', 't'])
        # header
        table.add_row(["parameter", "Limit", "Unit", "Judge"])
        for item_name, param_data in self.sim_result.items():
            if item_name == 'CC':
                # print("消費電流変動率 : ==========>\t{}".format("pass  :)" if param_data.judge else "fail"))
                table.add_row(["消費電流変動率", "50", "%", "pass  :)" if param_data.judge else "fail"])
            else:
                param_str = Spice.PARAM_UNIT[item_name][1]
                param_data = self.sim_result[item_name]
                val_str = ""
                if param_data.val is None:
                    val_str = "No Data..."
                else:
                    val_str = "{:.6E}".format(float(param_data.val))

                judge_str = ""
                req = self.requirements_list.get(item_name, None)
                if req is None:
                    judge_str = "not required"
                else:
                    judge_str = "pass  :)" if param_data.judge else "fail"
                table.add_row([param_str, val_str, param_data.unit, judge_str])

        self.print_msg(table.draw())

        """
        # param_data = self.sim_result['CC']
        for item_name, param_data in self.sim_result.items():
            if item_name == 'CC':
                print("消費電流変動率 : ==========>\t{}".format("pass  :)" if param_data.judge else "fail"))
            self.print_sim_results(item_name)
        print("**-----------------------------------------------------------------**")
        print("*")
        """

        self.print_msg("**-----------------------------------------------------------------**")
        for eval_name, val in self.eval_result.items():
            self.print_msg("*-->[{}] 評価値 : {:.6E}".format(eval_name, float(val)))

        self.print_msg("*")
        self.print_msg("**=================================================================**\n")

    def print_sim_results(self, item_name):
        param_str = Spice.PARAM_UNIT[item_name][1]
        param_data = self.sim_result[item_name]
        # 指定要件があるか？
        judge_str = ""
        req = self.requirements_list.get(item_name, None)
        if req is None:
            judge_str = "not required"
        else:
            judge_str = "pass  :)" if param_data.judge else "fail"
        if param_data.val is None:
            self.print_msg("{}\tNo Data... [{}]:\t{}".format(param_str, param_data.unit, judge_str))
        else:
            self.print_msg("{}\t{:.6E} [{}]:\t{}".format(param_str, float(param_data.val), param_data.unit, judge_str))


class LimitVal:
    """
    目標値設定用クラス
    """
    param = None  # パラメータ名
    cond = None  # 範囲(1(以上), 2(以下)のいずれか)
    num = None  # 値(単位なし)
    unit = None  # 単位

    def __init__(self, param, cond, num, unit):
        """
        目標値設定

        Parameters
        ----------
        param : str
            パラメータ名
        cond : str
            範囲
        num : str
            値
        unit : str
            単位
        """
        self.param = param
        self.cond = cond
        self.num = num
        self.unit = unit

    def __str__(self):
        return "param: {}, cond: {}, num: {}, unit: {}".format(self.param, self.cond, self.num, self.unit)


class ParamData:
    """
    各パラメータの値および判定結果を保持するクラス
    """
    val = None
    unit = None
    judge = None

    def __init__(self, val, unit, judge):
        """
        目標値設定

        Parameters
        ----------
        val : str
            値(単位なし)
        unit : str
            単位
        judge : Bool
            条件を満たすか否かの判定
        """
        self.val = val
        self.unit = unit
        self.judge = judge

    def __str__(self):
        return "val: {}, unit: {}, judge: {}".format(self.val, self.unit, self.judge)
