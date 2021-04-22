# -*- coding: utf-8 -*-

from engineering_notation import EngNumber
from extractor import *


class Element:

    OUT_FILE = None  # 出力用ファイルパス(default=None, 標準出力)

    def __init__(self, num='1', node=None, param=None):
        """
        初期化を行う

        Parameters
        ----------
        num: str
            素子番号。必須。数値を指定した場合は、文字列へ変換される。デフォルト値: '1'
            ノード名は、<各素子を示すアルファベット1文字>+<num>になる。
            <例> Vsource の場合: vsource.num = 'dd' ⇒ 'vdd'
        node: dict
            素子のノード情報を管理(dict,　key および値は str)。必須。デフォルト値: 空の dict
        param: str
            素子のパラメータ。任意。デフォルト値: None
        """
        self.num = str(num)

        if node is not None:
            if isinstance(node, dict):
                for key, value in node.items():
                    if not isinstance(key, str):
                        raise IllegalArgumentException("node's key must be str")
                    if not isinstance(value, str):
                        raise IllegalArgumentException("node's value must be str")
                self.node = node
            else:
                raise IllegalArgumentException("node must be dict")
        else:
            self.node = dict()

        # param は任意
        self.param = param

    def check_param(self):
        # Checking num
        if self.num is None:
            raise IllegalArgumentException("num must be str")
        if not isinstance(self.num, str):
            self.num = str(self.num)

        # Checking node
        if self.node is None:
            raise IllegalArgumentException("node must be dict")
        if not isinstance(self.node, dict):
            raise IllegalArgumentException("node must be dict")
        for key, value in self.node.items():
            if not isinstance(key, str):
                raise IllegalArgumentException("node's key must be str")
            if not isinstance(value, str):
                raise IllegalArgumentException("node's value must be str")

        # paramは必ずしも必須ではないため、渡された時だけチェックを行う。子クラスで必須パラメータの場合は、子クラスでチェックを行う
        if (self.param is not None) and (not isinstance(self.param, str)):
            raise IllegalArgumentException("param must be str")

    def print_msg(self, msg):
        if Element.OUT_FILE is None:
            print(msg)
        else:
            with open(Element.OUT_FILE, 'a') as f:
                print(msg, file=f)

    @classmethod
    def to_eng_str(cls, num):
        """
        数値を工学表記に変換する。その後、'M'があったら、'MEG'に変換する

        Parameters
        ----------
        num: float
            数値

        Returns
        ----------
        数値を工学表記に変換した文字列
        """

        tmp_str = str(EngNumber(num))
        tmp_str = tmp_str.replace('M', 'MEG')
        return tmp_str


class Resistor(Element):
    """
    抵抗

    [Usage]
    res = Resistor.new()
    res.num = 1
    res.node[:r_top] = 2
    res.node[:r_bottom] = 3
    res.param = 1k
    res.printElement => R1 2 3 1k
    """

    PREFIX = 'R'  # 抵抗を示す接頭語
    R_TOP = 'r_top'
    R_BOTTOM = 'r_bottom'

    def __init__(self, num='1', node=None, param=None):
        """
        初期化を行う

        Parameters
        ----------
        num: str
            素子番号
        node: dict
            素子のノード情報を管理(dict,　各要素は str)
        param: str
            素子のパラメータ
        """
        super().__init__(num, node, param)

    @classmethod
    def create_element(cls, *args):
        """
        文字列からインスタンスを生成

        Parameters:
        ----------
        args: list
            引数の配列
        """

        try:
            # R1 2 3 1k　の形式
            num = str(args[0][0][1:])
            node = {Resistor.R_TOP: str(args[0][1]), Resistor.R_BOTTOM: str(args[0][2])}
            param = str(args[0][3])
            ret = Resistor(num, node, param)
            return ret
        except ValueError:
            raise IllegalArgumentException(f"Invalid Parameter: {args}")

    def valid_check(self):
        """
        各メンバに関するチェックを行う
        """
        super().check_param()
        # param は必須
        if self.param is None:
            raise IllegalArgumentException("Resistor: param is mandatory parameter")
        if not isinstance(self.param, str):
            raise IllegalArgumentException("Resistor: param must be str")
        if self.param == '':
            raise IllegalArgumentException("Resistor: param is mandatory parameter")

    def print_element(self):
        """
        spice ネットリスト形式で出力

        [Usage]
        res.printElement => R1 2 3 1k
        """
        self.valid_check()
        self.print_msg(f"{Resistor.PREFIX}{self.num} {self.node[Resistor.R_TOP]} "
                       f"{self.node[Resistor.R_BOTTOM]} {self.param}")

    def get_element_str(self):
        """
        spice ネットリスト形式で文字列を返す

        Returns:
            ネットリスト形式の文字列
        """
        self.valid_check()
        ret = f"{Resistor.PREFIX}{self.num} {self.node[Resistor.R_TOP]} {self.node[Resistor.R_BOTTOM]} {self.param}"
        return ret

    def print_node(self):
        """
        spice ネットリスト形式でノード情報のみ出力

        [Usage]
        res.printNode => R1 2 3
        """
        self.valid_check()
        self.print_msg(f"{Resistor.PREFIX}{self.num} {self.node[Resistor.R_TOP]} {self.node[Resistor.R_BOTTOM]}")

    def get_node_str(self):
        """
        spice ネットリスト形式でノード情報の文字列を返す

        Returns:
            ネットリスト形式のノード情報のみの文字列
        """
        self.valid_check()
        ret = f"{Resistor.PREFIX}{self.num} {self.node[Resistor.R_TOP]} {self.node[Resistor.R_BOTTOM]}"
        return ret


class Capacitor(Element):

    """
    キャパシタ

    [Usage]
    cap.node[:c_top]
    cap.node[:c_bottom]
    """

    PREFIX = 'C'  # キャパシタを示す接頭語
    C_TOP = 'c_top'
    C_BOTTOM = 'c_bottom'

    def __init__(self, num='1', node=None, param=None):
        """
        初期化を行う

        Parameters
        ----------
        num: str
            素子番号
        node: dict
            素子のノード情報を管理(dict,　各要素は str)
        param: str
            素子のパラメータ
        """
        super().__init__(num, node, param)

    @classmethod
    def create_element(cls, *args):
        """
        文字列からインスタンスを生成

        Parameters:
        ----------
        args: list
            引数の配列
        """

        try:
            # C1 2 3 1k　の形式
            num = str(args[0][0][1:])
            node = {Capacitor.C_TOP: str(args[0][1]), Capacitor.C_BOTTOM: str(args[0][2])}
            param = str(args[0][3])
            ret = Capacitor(num, node, param)
            return ret
        except ValueError:
            raise IllegalArgumentException(f"Invalid Parameter: {args}")

    def valid_check(self):
        """
        各メンバに関するチェックを行う
        """
        super().check_param()
        # param は必須
        if self.param is None:
            raise IllegalArgumentException("Capacitor: param is mandatory parameter")
        if not isinstance(self.param, str):
            raise IllegalArgumentException("Capacitor: param must be str")
        if self.param == '':
            raise IllegalArgumentException("Capacitor: param is mandatory parameter")

    def print_element(self):
        """
        spice ネットリスト形式で出力

        [Usage]
        cap.node[:c_top]
        cap.node[:c_bottom]
        """
        self.valid_check()
        self.print_msg(f"{Capacitor.PREFIX}{self.num} {self.node[Capacitor.C_TOP]} " +
                       f"{self.node[Capacitor.C_BOTTOM]} {self.param}")

    def get_element_str(self):
        """
        spice ネットリスト形式で文字列を返す

        Returns:
            ネットリスト形式の文字列
        """
        self.valid_check()
        ret = f"{Capacitor.PREFIX}{self.num} {self.node[Capacitor.C_TOP]} {self.node[Capacitor.C_BOTTOM]} {self.param}"
        return ret

    def print_node(self):
        """
        spice ネットリスト形式でノード情報のみ出力

        [Usage]
        cap.printNode => C1 2 3
        """
        self.valid_check()
        self.print_msg(f"{Capacitor.PREFIX}{self.num} {self.node[Capacitor.C_TOP]} {self.node[Capacitor.C_BOTTOM]}")

    def get_node_str(self):
        """
        spice ネットリスト形式でノード情報の文字列を返す

        Returns:
            ネットリスト形式のノード情報のみの文字列
        """
        self.valid_check()
        ret = f"{Capacitor.PREFIX}{self.num} {self.node[Capacitor.C_TOP]} {self.node[Capacitor.C_BOTTOM]}"
        return ret


class Inductor(Element):

    """
    インダクタ

    [Usage]
    ind.node[:l_top]
    ind.node[:l_bottom]
    """

    PREFIX = 'L'  # インダクタを示す接頭語
    L_TOP = 'l_top'
    L_BOTTOM = 'l_bottom'

    def __init__(self, num='1', node=None, param=None):
        """
        初期化を行う

        Parameters
        ----------
        num: str
            素子番号
        node: dict
            素子のノード情報を管理(dict,　各要素は str)
        param: str
            素子のパラメータ
        """
        super().__init__(num, node, param)

    @classmethod
    def create_element(cls, *args):
        """
        文字列からインスタンスを生成

        Parameters:
        ----------
        args: list
            引数の配列
        """

        try:
            # L1 2 3 1k　の形式
            num = str(args[0][0][1:])
            node = {Inductor.L_TOP: str(args[0][1]), Inductor.L_BOTTOM: str(args[0][2])}
            param = str(args[0][3])
            ret = Inductor(num, node, param)
            return ret
        except ValueError:
            raise IllegalArgumentException(f"Invalid Parameter: {args}")

    def valid_check(self):
        """
        各メンバに関するチェックを行う
        """
        super().check_param()
        # param は必須
        if self.param is None:
            raise IllegalArgumentException("Inductor: param is mandatory parameter")
        if not isinstance(self.param, str):
            raise IllegalArgumentException("Inductor: param must be str")
        if self.param == '':
            raise IllegalArgumentException("Inductor: param is mandatory parameter")

    def print_element(self):
        """
        spice ネットリスト形式で出力

        [Usage]
        ind.node[:i_top]
        ind.node[:i_bottom]
        """
        self.valid_check()
        self.print_msg(f"{Inductor.PREFIX}{self.num} {self.node[Inductor.L_TOP]} {self.node[Inductor.L_BOTTOM]}" +
                       f" {self.param}")

    def get_element_str(self):
        """
        spice ネットリスト形式で文字列を返す

        Returns:
            ネットリスト形式の文字列
        """
        self.valid_check()
        ret = f"{Inductor.PREFIX}{self.num} {self.node[Inductor.L_TOP]} {self.node[Inductor.L_BOTTOM]} {self.param}"
        return ret

    def print_node(self):
        """
        spice ネットリスト形式でノード情報のみ出力

        [Usage]
        ind.printNode => I1 2 3
        """
        self.valid_check()
        self.print_msg(f"{Inductor.PREFIX}{self.num} {self.node[Inductor.L_TOP]} {self.node[Inductor.L_BOTTOM]}")

    def get_node_str(self):
        """
        spice ネットリスト形式でノード情報の文字列を返す

        Returns:
            ネットリスト形式のノード情報のみの文字列
        """
        self.valid_check()
        ret = f"{Inductor.PREFIX}{self.num} {self.node[Inductor.L_TOP]} {self.node[Inductor.L_BOTTOM]}"
        return ret


class Vsource(Element):

    """
    Vsource

    [Usage]
    vs = Vsource()
    vs.num = 1
    vs.node[:v_top] = 2
    vs.node[:v_bottom] = 3
    vs.param = 1.5
    vs.printElement => V1 2 3 1.5

    vs.param = "dc 1.5 ac 1"
    vs.printElement => V1 2 3 dc 1.5 ac 1

    vs.param = "sin(0 1 1k 0 0 45.0)"
    vs.printElement => V1 2 3 sin(0 1 1k 0 0 45.0)

    vs.param = "pulse(-1 1 0 1e-5 1e-5 5e-4 1e-3 45.0)"
    vs.printElement => V1 2 3 pulse(-1 1 0 1e-5 1e-5 5e-4 1e-3 45.0)
    """

    PREFIX = 'V'  # Vsource を示す接頭語
    V_TOP = 'v_top'
    V_BOTTOM = 'v_bottom'

    def __init__(self, num='1', node=None, param=None):
        """
        初期化を行う

        Parameters
        ----------
        num: str
            素子番号
        node: dict
            素子のノード情報を管理(dict,　各要素は str)
        param: str
            素子のパラメータ
        """
        super().__init__(num, node, param)

    @classmethod
    def create_element(cls, *args):
        """
        文字列からインスタンスを生成

        Parameters:
        ----------
        args: list
            引数の配列
        """

        try:
            # 例1: V1 2 3 1k
            # 例2: V2 2 3 pulse(-1 1 0 1e-5 1e-5 5e-4 1e-3 45.0)
            num = str(args[0][0][1:])
            node = {Vsource.V_TOP: str(args[0][1]), Vsource.V_BOTTOM: str(args[0][2])}
            param = ' '.join(args[0][3:])
            ret = Vsource(num, node, param)
            return ret
        except ValueError:
            raise IllegalArgumentException(f"Invalid Parameter: {args}")

    def valid_check(self):
        """
        各メンバに関するチェックを行う
        """
        super().check_param()
        # param は必須
        if self.param is None:
            raise IllegalArgumentException("Vsource: param is mandatory parameter")
        if not isinstance(self.param, str):
            raise IllegalArgumentException("Vsource: param must be str")
        if self.param == '':
            raise IllegalArgumentException("Vsource: param is mandatory parameter")

    def print_element(self):
        """
        spice ネットリスト形式で出力

        [Usage]
        vs.printElement => V1 2 3 pulse(-1 1 0 1e-5 1e-5 5e-4 1e-3 45.0)
        """
        self.valid_check()
        self.print_msg(f"{Vsource.PREFIX}{self.num} {self.node[Vsource.V_TOP]} {self.node[Vsource.V_BOTTOM]}" +
                       f" {self.param}")

    def get_element_str(self):
        """
        spice ネットリスト形式で文字列を返す

        Returns:
            ネットリスト形式の文字列
        """
        self.valid_check()
        ret = f"{Vsource.PREFIX}{self.num} {self.node[Vsource.V_TOP]} {self.node[Vsource.V_BOTTOM]} {self.param}"
        return ret

    def print_node(self):
        """
        spice ネットリスト形式でノード情報のみ出力

        [Usage]
        vs.printNode => V1 2 3
        """
        self.valid_check()
        self.print_msg(f"{Vsource.PREFIX}{self.num} {self.node[Vsource.V_TOP]} {self.node[Vsource.V_BOTTOM]}")

    def get_node_str(self):
        """
        spice ネットリスト形式でノード情報の文字列を返す

        Returns:
            ネットリスト形式のノード情報のみの文字列
        """
        self.valid_check()
        ret = f"{Vsource.PREFIX}{self.num} {self.node[Vsource.V_TOP]} {self.node[Vsource.V_BOTTOM]}"
        return ret


class Isource(Element):

    """
    Isource

    [Usage]
    is = Isource()
    is.num = 1
    is.node[:i_top] = 2
    is.node[:i_bottom] = 3
    is.param = 0.5
    is.printElement => I1 2 3 0.5
    """

    PREFIX = 'I'  # Isource を示す接頭語
    I_TOP = 'i_top'
    I_BOTTOM = 'i_bottom'

    def __init__(self, num='1', node=None, param=None):
        """
        初期化を行う

        Parameters
        ----------
        num: str
            素子番号
        node: dict
            素子のノード情報を管理(dict,　各要素は str)
        param: str
            素子のパラメータ
        """
        super().__init__(num, node, param)

    @classmethod
    def create_element(cls, *args):
        """
        文字列からインスタンスを生成

        Parameters:
        ----------
        args: list
            引数の配列
        """

        try:
            # 例1: I1 2 3 1k
            # 例2: I2 2 3 pulse(-1 1 0 1e-5 1e-5 5e-4 1e-3 45.0)
            num = str(args[0][0][1:])
            node = {Isource.I_TOP: str(args[0][1]), Isource.I_BOTTOM: str(args[0][2])}
            param = ' '.join(args[0][3:])
            ret = Isource(num, node, param)
            return ret
        except ValueError:
            raise IllegalArgumentException(f"Invalid Parameter: {args}")

    def valid_check(self):
        """
        各メンバに関するチェックを行う
        """
        super().check_param()
        # param は必須
        if self.param is None:
            raise IllegalArgumentException("Isource: param is mandatory parameter")
        if not isinstance(self.param, str):
            raise IllegalArgumentException("Isource: param must be str")
        if self.param == '':
            raise IllegalArgumentException("Isource: param is mandatory parameter")

    def print_element(self):
        """
        spice ネットリスト形式で出力

        [Usage]
        is.printElement => I1 2 3 0.5
        """
        self.valid_check()
        self.print_msg(f"{Isource.PREFIX}{self.num} {self.node[Isource.I_TOP]} {self.node[Isource.I_BOTTOM]}" +
                       f" {self.param}")

    def get_element_str(self):
        """
        spice ネットリスト形式で文字列を返す

        Returns:
            ネットリスト形式の文字列
        """
        self.valid_check()
        ret = f"{Isource.PREFIX}{self.num} {self.node[Isource.I_TOP]} {self.node[Isource.I_BOTTOM]} {self.param}"
        return ret

    def print_node(self):
        """
        spice ネットリスト形式でノード情報のみ出力

        [Usage]
        is.printNode => I1 2 3
        """
        self.valid_check()
        self.print_msg(f"{Isource.PREFIX}{self.num} {self.node[Isource.I_TOP]} {self.node[Isource.I_BOTTOM]}")

    def get_node_str(self):
        """
        spice ネットリスト形式でノード情報の文字列を返す

        Returns:
            ネットリスト形式のノード情報のみの文字列
        """
        self.valid_check()
        ret = f"{Isource.PREFIX}{self.num} {self.node[Isource.I_TOP]} {self.node[Isource.I_BOTTOM]}"
        return ret


class Mosfet(Element):

    """
    Mosfet

    [Usage]
    内部に model、length、width、multiple の変数を持つ。いずれもメソッドとして利用できる
    model、length、width は必須。multiple は任意
    model: string
    length、width: float
    multiple: Decimal

    mosfet = Mosfet()
    mosfet.num = 1
    mosfet.node[:drain] = nd
    mosfet.node[:gate] = ng
    mosfet.node[:source] = ns
    mosfet.node[:bulk] = nb
    mosfet.model = cmosn
    mosfet.length = 1.2e-6
    mosfet.width = 10e-6
    mosfet.multiple = 2.0
    mosfet.printElement => M1 nd ng ns nb cmosn l=1.2u w=10u m=2.0
    length, width は print するときに単位を付加する
    1.0e-6 と入力すると自動で 1.0u と変換する
    """

    PREFIX = 'M'  # Mosfetを示す接頭語
    M_DRAIN = 'drain'
    M_GATE = 'gate'
    M_SOURCE = 'source'
    M_BULK = 'bulk'

    def __init__(self, num='1', node=None, param=None, model=None, length=None, width=None, multiple=None):
        """
        初期化を行う

        Parameters
        ----------
        num: str
            素子番号
        node: dict
            素子のノード情報を管理(dict,　各要素は str)
        param: str
            素子のパラメータ
        model: str
            model(必須)
        length: float
            length(必須)
        width: float
            width(必須)
        multiple: 数値
            multiple(任意)。数値を指定した場合、Decimal型に変換される。
        """
        super().__init__(num, node, param)

        if (model is not None) and ((not isinstance(model, str)) or (str == '')):
            raise IllegalArgumentException(f"Mosfet: model is mandatory parameters(str): {model}")
        if (length is not None) and (not isinstance(length, float)):
            raise IllegalArgumentException(f"Mosfet: length is mandatory parameters(float): {length}")
        if (width is not None) and (not isinstance(width, float)):
            raise IllegalArgumentException(f"Mosfet: width is mandatory parameters(float): {width}")
        if multiple is not None:
            # multiple は任意
            try:
                tmp = Decimal(str(multiple))
            except InvalidOperation as e:
                raise IllegalArgumentException(f"Mosfet: multiple must be digit: {multiple}")
        self.model = model
        self.length = length
        self.width = width
        self.multiple = Decimal(str(multiple)) if multiple is not None else None

    def check_mosfet_param(self):
        super().check_param()
        # model(str), length(float), width(float), multiple(Decimal) は必須
        if (self.model is None) or (self.length is None) or (self.width is None):
            raise IllegalArgumentException("Mosfet: model, length, width are mandatory parameters")
        if (self.model is not None) and ((not isinstance(self.model, str)) or (str == '')):
            raise IllegalArgumentException(f"Mosfet: model is mandatory parameters(str): {self.model}")
        if (self.length is not None) and (not isinstance(self.length, float)):
            raise IllegalArgumentException(f"Mosfet: length is mandatory parameters(float): {self.length}")
        if (self.width is not None) and (not isinstance(self.width, float)):
            raise IllegalArgumentException(f"Mosfet: width is mandatory parameters(float): {self.width}")
        if self.multiple is not None:
            if not isinstance(self.multiple, Decimal):
                try:
                    tmp = Decimal(str(self.multiple))
                except InvalidOperation as e:
                    raise IllegalArgumentException(f"Mosfet: multiple must be digit: {self.multiple}")

    @classmethod
    def create_element(cls, *args):
        """
        文字列からインスタンスを生成

        Parameters:
        ----------
        args: list
            引数の配列
        """

        try:
            # 例1: M1 N001 inm  N003 N003 cmosn l=2u w=3.8u
            num = str(args[0][0][1:])
            node = {Mosfet.M_DRAIN: str(args[0][1]), Mosfet.M_GATE: str(args[0][2]), Mosfet.M_SOURCE: str(args[0][3]),
                    Mosfet.M_BULK: str(args[0][4])}
            model = args[0][5]
            length = Extractor.unit_conv(args[0][6].replace('l=', ''))
            width = Extractor.unit_conv(args[0][7].replace('w=', ''))
            multiple = args[0][8].replace('m=', '') if len(args[0]) == 9 else None
            ret = Mosfet(num, node, None, model, length, width, multiple)
            return ret
        except ValueError:
            raise IllegalArgumentException(f"Invalid Parameter: {args}")

    def valid_check(self):
        """
        各メンバに関するチェックを行う
        """
        super().check_param()
        self.check_mosfet_param()

    def print_element(self):
        """
        spice ネットリスト形式で出力

        [Usage]
        mosfet.printElement => M1 nd ng ns nb cmosn l=1.2u w=10u m=2.0
        length, width は print するときに単位を付加する
        1.0e-6 と入力すると自動で 1.0u と変換する
        """
        self.valid_check()

        length_str = Element.to_eng_str(self.length)
        width_str = Element.to_eng_str(self.width)
        multiple_str = " m="+str(self.multiple) if self.multiple is not None else ""
        # param は不要？
        self.print_msg(f"{Mosfet.PREFIX}{self.num} {self.node[Mosfet.M_DRAIN]} {self.node[Mosfet.M_GATE]} " +
                       f"{self.node[Mosfet.M_SOURCE]} {self.node[Mosfet.M_BULK]} {self.model} l={length_str} " +
                       f"w={width_str}{multiple_str}")

    def get_element_str(self):
        """
        spice ネットリスト形式で文字列を返す

        Returns:
            ネットリスト形式の文字列
        """
        self.valid_check()
        length_str = Element.to_eng_str(self.length)
        width_str = Element.to_eng_str(self.width)
        multiple_str = " m="+str(self.multiple) if self.multiple is not None else ""
        # param は不要？
        ret = f"{Mosfet.PREFIX}{self.num} {self.node[Mosfet.M_DRAIN]} {self.node[Mosfet.M_GATE]} " \
              f"{self.node[Mosfet.M_SOURCE]} {self.node[Mosfet.M_BULK]} {self.model} l={length_str}" \
              f" w={width_str}{multiple_str}"
        return ret

    def print_node(self):
        """
        spice ネットリスト形式でノード情報のみ出力

        [Usage]
        mosfet.printNode => M1 nd ng ns nb
        """
        self.valid_check()

        self.print_msg(f"{Mosfet.PREFIX}{self.num} {self.node[Mosfet.M_DRAIN]} {self.node[Mosfet.M_GATE]} " +
                       f"{self.node[Mosfet.M_SOURCE]} {self.node[Mosfet.M_BULK]}")

    def get_node_str(self):
        """
        spice ネットリスト形式でノード情報の文字列を返す

        Returns:
            ネットリスト形式のノード情報のみの文字列
        """
        self.valid_check()
        ret = f"{Mosfet.PREFIX}{self.num} {self.node[Mosfet.M_DRAIN]} {self.node[Mosfet.M_GATE]} " \
              f"{self.node[Mosfet.M_SOURCE]} {self.node[Mosfet.M_BULK]}"
        return ret


class Diode(Element):

    """
    ダイオード

    [Usage]
    内部に model、area、multiple の変数を持つ。いずれもメソッドとして利用できる
    model は必須。area、multiple は任意
    model: string
    area, multiple: decimal

    diode = Diode()
    diode.num = 1
    diode.node[:d_top] = 2
    diode.node[:d_bottom] = 3
    diode.model = diode1
    diode.area = 1.0
    diode.multiple = 2.0
    """

    PREFIX = 'D'  # ダイオードを示す接頭語
    D_TOP = 'd_top'
    D_BOTTOM = 'd_bottom'

    def __init__(self, num='1', node=None, param=None, model=None, area=None, multiple=None):
        """
        初期化を行う

        Parameters
        ----------
        num: str
            素子番号
        node: dict
            素子のノード情報を管理(dict,　各要素は str)
        param: str
            素子のパラメータ
        model: str
            model(必須)
        area: 数値
            area(任意)。数値を指定した場合、Decimal型に変換される
        multiple: 数値
            multiple(任意)。数値を指定した場合、Decimal型に変換される
        """
        super().__init__(num, node, param)
        # model は必須
        if (model is not None) and ((not isinstance(model, str)) or (str == '')):
            raise IllegalArgumentException(f"Diode: model is mandatory parameters(str): {model}")

        # area, multiple は任意
        if area is not None:
            try:
                tmp = Decimal(str(area))
            except InvalidOperation as e:
                raise IllegalArgumentException(f"Diode: area must be digit: {area}")
        if multiple is not None:
            try:
                tmp = Decimal(str(multiple))
            except InvalidOperation as e:
                raise IllegalArgumentException(f"Diode: multiple must be digit: {multiple}")

        self.model = model
        self.area = Decimal(str(area)) if area is not None else None
        self.multiple = Decimal(str(multiple)) if multiple is not None else None

    def check_diode_param(self):
        super().check_param()
        # model(str)は必須, area(Decimal), multiple(Decimal) は任意
        if self.model is None:
            raise IllegalArgumentException("Diode: model is mandatory parameters")
        if self.model == "":
            raise IllegalArgumentException("Diode: model is mandatory parameters")
        if not isinstance(self.model, str):
            raise IllegalArgumentException("Diode: model must be str")

        # area, multiple は任意
        if self.area is not None:
            try:
                tmp = Decimal(str(self.area))
            except InvalidOperation as e:
                raise IllegalArgumentException(f"Diode: area must be digit: {self.area}")
        if self.multiple is not None:
            try:
                tmp = Decimal(str(self.multiple))
            except InvalidOperation as e:
                raise IllegalArgumentException(f"Diode: multiple must be digit: {self.multiple}")

    @classmethod
    def create_element(cls, *args):
        """
        文字列からインスタンスを生成

        Parameters:
        ----------
        args: list
            引数の配列
        """

        try:
            # 例: D1 2 3 diode1 area=1.0 m=2.0
            num = str(args[0][0][1:])
            node = {Diode.D_TOP: str(args[0][1]), Diode.D_BOTTOM: str(args[0][2])}
            # model(str)は必須, area(Decimal), multiple(Decimal) は任意
            model = str(args[0][3])
            area = None
            multiple = None
            index = 4
            while len(args[0]) > index:
                # area もしくは multiple の指定あり
                if re.search('^area=', args[0][index]) is not None:
                    area = Decimal(str(args[0][index].replace('area=', '')))
                if re.search('^m=', args[0][index]) is not None:
                    multiple = Decimal(str(args[0][index].replace('m=', '')))
                index += 1

            # param は None
            ret = Diode(num, node, None, model, area, multiple)
            return ret
        except ValueError:
            raise IllegalArgumentException(f"Invalid Parameter: {args}")

    def valid_check(self):
        """
        各メンバに関するチェックを行う
        """
        super().check_param()
        self.check_diode_param()

    def print_element(self):
        """
        spice ネットリスト形式で出力

        [Usage]
        diode.printElement => D1 2 3 diode1 area=1.0 m=2.0
        """
        self.valid_check()

        model_str = " " + self.model if self.model is not None else ""
        area_str = " area=" + str(self.area) if self.area is not None else ""
        multiple_str = " m=" + str(self.multiple) if self.multiple is not None else ""
        # param は不要？
        self.print_msg(f"{Diode.PREFIX}{self.num} {self.node[Diode.D_TOP]} {self.node[Diode.D_BOTTOM]}" +
                       f"{model_str}{area_str}{multiple_str}")

    def get_element_str(self):
        """
        spice ネットリスト形式で文字列を返す

        Returns:
            ネットリスト形式の文字列
        """
        self.valid_check()

        model_str = " " + self.model if self.model is not None else ""
        area_str = " area=" + str(self.area) if self.area is not None else ""
        multiple_str = " m=" + str(self.multiple) if self.multiple is not None else ""
        # param は不要？
        ret = f"{Diode.PREFIX}{self.num} {self.node[Diode.D_TOP]} {self.node[Diode.D_BOTTOM]}" \
              f"{model_str}{area_str}{multiple_str}"
        return ret

    def print_node(self):
        """
        spice ネットリスト形式でノード情報のみ出力

        [Usage]
        diode.printNode => D1 2 3
        """
        self.valid_check()
        self.print_msg(f"{Diode.PREFIX}{self.num} {self.node[Diode.D_TOP]} {self.node[Diode.D_BOTTOM]}")

    def get_node_str(self):
        """
        spice ネットリスト形式でノード情報の文字列を返す

        Returns:
            ネットリスト形式のノード情報のみの文字列
        """
        self.valid_check()
        ret = f"{Diode.PREFIX}{self.num} {self.node[Diode.D_TOP]} {self.node[Diode.D_BOTTOM]}"
        return ret


class Cccs(Element):
    """
    内部に vs_name, c_gain, multiple の変数を持つ
    vs_name, c_gain は必須
    multipleは任意
    vs_name, c_gain: string
    multiple: decimal

    [Usage]
    cccs = Cccs()
    cccs.num = 1
    cccs.node[:out_p] = cc2
    cccs.node[:out_m] = cc3
    cccs.vs_name = "vsens""
    cccs.c_gain = 5.0
    cccs.multiple = 2.0
    cccs.printElement => F1 cc2 cc3 vsens 5.0 m=2.0

    """

    PREFIX = 'F'  # Cccsを示す接頭語
    F_OUT_P = 'out_p'
    F_OUT_M = 'out_m'

    def __init__(self, num='1', node=None, param=None, vs_name=None, c_gain=None, multiple=None):
        """
        初期化を行う

        Parameters
        ----------
        num: str
            素子番号
        node: dict
            素子のノード情報を管理(dict,　各要素は str)
        param: str
            素子のパラメータ
        vs_name: str
            vs_name(必須)
        c_gain: str
            c_gain(必須)
        multiple: 数値
            multiple(任意)。数値を指定した場合、Decimal型に変換される
        """
        super().__init__(num, node, param)

        # vs_name(str), c_gain(str) は必須、multiple(数値)は任意。
        if (vs_name is not None) and ((not isinstance(vs_name, str)) or (str == '')):
            raise IllegalArgumentException(f"Cccs: vs_name is mandatory parameters(str): {vs_name}")
        if (c_gain is not None) and ((not isinstance(c_gain, str)) or (str == '')):
            raise IllegalArgumentException(f"Cccs: c_gain is mandatory parameters(str): {c_gain}")
        if multiple is not None:
            try:
                tmp = Decimal(str(multiple))
            except InvalidOperation as e:
                raise IllegalArgumentException(f"Cccs: multiple must be digit: {multiple}")

        self.vs_name = vs_name
        self.c_gain = c_gain
        self.multiple = Decimal(str(multiple)) if multiple is not None else None

    def check_cccs_param(self):
        # vs_name(str), c_gain(str) は必須、multiple(Decimal)は任意。
        super().check_param()
        if self.vs_name is None:
            raise IllegalArgumentException("Cccs: vs_name is mandatory parameters")
        if self.vs_name == "":
            raise IllegalArgumentException("Cccs: vs_name is mandatory parameters")
        if not isinstance(self.vs_name, str):
            raise IllegalArgumentException("Cccs: vs_name must be str")

        if self.c_gain is None:
            raise IllegalArgumentException("Cccs: c_gain is mandatory parameters")
        if self.c_gain == "":
            raise IllegalArgumentException("Cccs: c_gain is mandatory parameters")
        if not isinstance(self.c_gain, str):
            raise IllegalArgumentException("Cccs: c_gain must be str")

        # multiple は任意
        if self.multiple is not None:
            try:
                tmp = Decimal(str(self.multiple))
            except InvalidOperation as e:
                raise IllegalArgumentException(f"Cccs: multiple must be digit: {self.multiple}")

    @classmethod
    def create_element(cls, *args):
        """
        文字列からインスタンスを生成

        Parameters:
        ----------
        args: list
            引数の配列
        """

        try:
            # 例: F1 cc2 cc3 vsens 5.0 m=2.0
            num = str(args[0][0][1:])
            node = {Cccs.F_OUT_P: str(args[0][1]), Cccs.F_OUT_M: str(args[0][2])}
            # vs_name(str), c_gain(str) は必須、multiple(数値)は任意。
            vs_name = str(args[0][3])
            c_gain = str(args[0][4])
            multiple = Decimal(str(args[0][5].replace('m=', ''))) if len(args[0]) == 6 else None

            # param は None
            ret = Cccs(num, node, None, vs_name, c_gain, multiple)
            return ret
        except ValueError:
            raise IllegalArgumentException(f"Invalid Parameter: {args}")

    def valid_check(self):
        """
        各メンバに関するチェックを行う
        """
        super().check_param()
        self.check_cccs_param()

    def print_element(self):
        """
        spice ネットリスト形式で出力

        [Usage]
        cccs.printElement => F1 cc2 cc3 vsens 5.0 m=2.0
        """
        self.valid_check()

        multiple_str = " m=" + str(self.multiple) if self.multiple is not None else ""
        # param は不要？
        self.print_msg(f"{Cccs.PREFIX}{self.num} {self.node[Cccs.F_OUT_P]} {self.node[Cccs.F_OUT_M]} " +
                       f"{self.vs_name} {self.c_gain}{multiple_str}")

    def get_element_str(self):
        """
        spice ネットリスト形式で文字列を返す

        Returns:
            ネットリスト形式の文字列
        """
        self.valid_check()
        multiple_str = " m=" + str(self.multiple) if self.multiple is not None else ""
        # param は不要？
        ret = f"{Cccs.PREFIX}{self.num} {self.node[Cccs.F_OUT_P]} {self.node[Cccs.F_OUT_M]} " \
              f"{self.vs_name} {self.c_gain}{multiple_str}"
        return ret

    def print_node(self):
        """
        spice ネットリスト形式でノード情報のみ出力

        [Usage]
        cccs.printNode => F1 cc2 cc3
        """
        self.valid_check()
        self.print_msg(f"{Cccs.PREFIX}{self.num} {self.node[Cccs.F_OUT_P]} {self.node[Cccs.F_OUT_M]}")

    def get_node_str(self):
        """
        spice ネットリスト形式でノード情報の文字列を返す

        Returns:
            ネットリスト形式のノード情報のみの文字列
        """
        self.valid_check()
        ret = f"{Cccs.PREFIX}{self.num} {self.node[Cccs.F_OUT_P]} {self.node[Cccs.F_OUT_M]}"
        return ret


class Ccvs(Element):
    """
    内部に vs_name, transresistance の変数を持つ
    vs_name, ccvs.transresistance: string、必須
    """
    PREFIX = 'H'  # Ccvsを示す接頭語
    H_OUT_P = 'out_p'
    H_OUT_M = 'out_m'

    def __init__(self, num='1', node=None, param=None, vs_name=None, transresistance=None):
        """
        初期化を行う

        Parameters
        ----------
        num: str
            素子番号
        node: dict
            素子のノード情報を管理(dict,　各要素は str)
        param: str
            素子のパラメータ
        vs_name: str
            vs_name(必須)
        transresistance: str
            transresistance(必須)
        """
        super().__init__(num, node, param)
        # vs_name(str), transresistance(str) は必須
        if (vs_name is not None) and ((not isinstance(vs_name, str)) or (str == '')):
            raise IllegalArgumentException(f"Ccvs: vs_name is mandatory parameters(str): {vs_name}")
        if (transresistance is not None) and ((not isinstance(transresistance, str)) or (str == '')):
            raise IllegalArgumentException(f"Ccvs: c_gain is mandatory parameters(str): {transresistance}")

        self.vs_name = vs_name
        self.transresistance = transresistance

    def check_ccvs_param(self):
        # vs_name(str), transresistance(str) は必須
        super().check_param()
        if self.vs_name is None:
            raise IllegalArgumentException("Ccvs: vs_name is mandatory parameters")
        if self.vs_name == "":
            raise IllegalArgumentException("Ccvs: vs_name is mandatory parameters")
        if not isinstance(self.vs_name, str):
            raise IllegalArgumentException("Ccvs: vs_name must be str")

        if self.transresistance is None:
            raise IllegalArgumentException("Ccvs: transresistance is mandatory parameters")
        if self.transresistance == "":
            raise IllegalArgumentException("Ccvs: transresistance is mandatory parameters")
        if not isinstance(self.transresistance, str):
            raise IllegalArgumentException("Ccvs: transresistance must be str")

    @classmethod
    def create_element(cls, *args):
        """
        文字列からインスタンスを生成

        Parameters:
        ----------
        args: list
            引数の配列
        """

        try:
            # 例: F1 cc2 cc3 vsens 5.0 m=2.0
            num = str(args[0][0][1:])
            node = {Ccvs.H_OUT_P: str(args[0][1]), Ccvs.H_OUT_M: str(args[0][2])}
            # vs_name(str), transresistance(str) は必須
            vs_name = str(args[0][3])
            transresistance = str(args[0][4])

            # param は None
            ret = Ccvs(num, node, None, vs_name, transresistance)
            return ret
        except ValueError:
            raise IllegalArgumentException(f"Invalid Parameter: {args}")

    def valid_check(self):
        """
        各メンバに関するチェックを行う
        """
        super().check_param()
        self.check_ccvs_param()

    def print_element(self):
        """
        spice ネットリスト形式で出力

        [Usage]
        ccvs = Ccvs.new()
        ccvs.num = 1
        ccvs.node[:out_p] = 2
        ccvs.node[:out_m] = 3
        ccvs.vs_name = "vsens"
        ccvs.transresistance = "0.5k"
        ccvs.printElement => H1 2 3 vsens 0.5k
        """
        self.valid_check()

        # param は不要？
        self.print_msg(f"{Ccvs.PREFIX}{self.num} {self.node[Ccvs.H_OUT_P]} {self.node[Ccvs.H_OUT_M]} " +
                       f"{self.vs_name} {self.transresistance}")

    def get_element_str(self):
        """
        spice ネットリスト形式で文字列を返す

        Returns:
            ネットリスト形式の文字列
        """
        self.valid_check()
        # param は不要？
        ret = f"{Ccvs.PREFIX}{self.num} {self.node[Ccvs.H_OUT_P]} {self.node[Ccvs.H_OUT_M]} " \
              f"{self.vs_name} {self.transresistance}"
        return ret

    def print_node(self):
        """
        spice ネットリスト形式でノード情報のみ出力

        [Usage]
        ccvs.printNode => H1 2 3
        """
        self.valid_check()
        self.print_msg(f"{Ccvs.PREFIX}{self.num} {self.node[Ccvs.H_OUT_P]} {self.node[Ccvs.H_OUT_M]}")

    def get_node_str(self):
        """
        spice ネットリスト形式でノード情報の文字列を返す

        Returns:
            ネットリスト形式のノード情報のみの文字列
        """
        self.valid_check()
        ret = f"{Ccvs.PREFIX}{self.num} {self.node[Ccvs.H_OUT_P]} {self.node[Ccvs.H_OUT_M]}"
        return ret


class Vccs(Element):
    """
    内部にtransconductance, multiple の変数を持つ
    transconductance: decimal、必須
    multiple: decimal、任意
    """
    PREFIX = 'G'  # Vccsを示す接頭語
    G_OUT_P = 'out_p'
    G_OUT_M = 'out_m'
    G_IN_P = 'in_p'
    G_IN_M = 'in_m'

    def __init__(self, num='1', node=None, param=None, transconductance=None, multiple=None):
        """
        初期化を行う

        Parameters
        ----------
        num: str
            素子番号
        node: dict
            素子のノード情報を管理(dict,　各要素は str)
        param: str
            素子のパラメータ
        transconductance: 数値
            transconductance(必須)。数値を指定した場合、Decimal型に変換される
        multiple: 数値
            multiple(任意)。数値を指定した場合、Decimal型に変換される
        """
        super().__init__(num, node, param)

        # transconductance(数値) は必須
        if transconductance is not None:
            try:
                tmp = Decimal(str(transconductance))
            except InvalidOperation as e:
                raise IllegalArgumentException(f"Vccs: transconductance must be digit: {transconductance}")

        # multiple(数値) は任意
        if multiple is not None:
            try:
                tmp = Decimal(str(multiple))
            except InvalidOperation as e:
                raise IllegalArgumentException(f"Vccs: multiple must be digit: {multiple}")

        self.transconductance = transconductance
        self.multiple = Decimal(str(multiple)) if multiple is not None else None

    def check_vccs_param(self):
        # transconductance(数値) は必須
        if self.transconductance is None:
            raise IllegalArgumentException("Vccs: transconductance is mandatory parameters")
        else:
            try:
                tmp = Decimal(str(self.transconductance))
            except InvalidOperation as e:
                raise IllegalArgumentException(f"Vccs: multiple must be digit: {self.transconductance}")

        # multiple は任意
        if self.multiple is not None:
            try:
                tmp = Decimal(str(self.multiple))
            except InvalidOperation as e:
                raise IllegalArgumentException(f"Vccs: multiple must be digit: {self.multiple}")

    @classmethod
    def create_element(cls, *args):
        """
        文字列からインスタンスを生成

        Parameters:
        ----------
        args: list
            引数の配列
        """

        try:
            # 例: F1 cc2 cc3 vsens 5.0 m=2.0
            num = str(args[0][0][1:])
            node = {Vccs.G_OUT_P: str(args[0][1]), Vccs.G_OUT_M: str(args[0][2]), Vccs.G_IN_P: str(args[0][3]),
                    Vccs.G_IN_M: str(args[0][4])}
            # transconductance(数値) は必須
            transconductance = Decimal(str(args[0][5]))
            multiple = Decimal(str(args[0][6].replace('m=', ''))) if len(args[0]) == 7 else None

            # param は None
            ret = Vccs(num, node, None, transconductance, multiple)
            return ret
        except ValueError:
            raise IllegalArgumentException(f"Invalid Parameter: {args}")

    def valid_check(self):
        """
        各メンバに関するチェックを行う
        """
        super().check_param()
        self.check_vccs_param()

    def print_element(self):
        """
        spice ネットリスト形式で出力

        [Usage]
        vccs = Vccs.new()
        vccs.num = 1
        vccs.node[:out_p] = 2
        vccs.node[:out_m] = 3
        vccs.node[:in_p] = 4
        vccs.node[:in_m] = 5
        vccs.transconductance = 0.1
        vccs.multiple = 3.0
        vccs.printElement => G1 2 3 4 5 0.1 m=3.0
        """
        self.valid_check()

        # param は不要？
        multiple_str = " m=" + str(self.multiple) if self.multiple is not None else ""
        self.print_msg(f"{Vccs.PREFIX}{self.num} {self.node[Vccs.G_OUT_P]} {self.node[Vccs.G_OUT_M]} " +
                       f"{self.node[Vccs.G_IN_P]} {self.node[Vccs.G_IN_M]} " +
                       f"{str(self.transconductance)}{multiple_str}")

    def get_element_str(self):
        """
        spice ネットリスト形式で文字列を返す

        Returns:
            ネットリスト形式の文字列
        """
        self.valid_check()

        # param は不要？
        multiple_str = " m=" + str(self.multiple) if self.multiple is not None else ""
        ret = f"{Vccs.PREFIX}{self.num} {self.node[Vccs.G_OUT_P]} {self.node[Vccs.G_OUT_M]} " \
              f"{self.node[Vccs.G_IN_P]} {self.node[Vccs.G_IN_M]} " \
              f"{str(self.transconductance)}{multiple_str}"
        return ret

    def print_node(self):
        """
        spice ネットリスト形式でノード情報のみ出力

        [Usage]
        vccs.printNode => G1 2 3 4 5
        """
        self.valid_check()

        # param は不要？
        multiple_str = " m=" + str(self.multiple) if self.multiple is not None else ""
        self.print_msg(f"{Vccs.PREFIX}{self.num} {self.node[Vccs.G_OUT_P]} {self.node[Vccs.G_OUT_M]} " +
                       f"{self.node[Vccs.G_IN_P]} {self.node[Vccs.G_IN_M]}")

    def get_node_str(self):
        """
        spice ネットリスト形式でノード情報の文字列を返す

        Returns:
            ネットリスト形式のノード情報のみの文字列
        """
        self.valid_check()

        # param は不要？
        multiple_str = " m=" + str(self.multiple) if self.multiple is not None else ""
        ret = f"{Vccs.PREFIX}{self.num} {self.node[Vccs.G_OUT_P]} {self.node[Vccs.G_OUT_M]} " \
              f"{self.node[Vccs.G_IN_P]} {self.node[Vccs.G_IN_M]}"
        return ret


class Vcvs(Element):
    """
    内部に v_gain の変数を持つ
    v_gain: decimal、必須
    """
    PREFIX = 'E'  # Vcvs を示す接頭語
    E_OUT_P = 'out_p'
    E_OUT_M = 'out_m'
    E_IN_P = 'in_p'
    E_IN_M = 'in_m'

    def __init__(self, num='1', node=None, param=None, v_gain=None):
        """
        初期化を行う

        Parameters
        ----------
        num: str
            素子番号
        node: dict
            素子のノード情報を管理(dict,　各要素は str)
        param: str
            素子のパラメータ
        v_gain: 数値
            v_gain(必須)。数値を指定した場合、Decimal型に変換される
        """
        super().__init__(num, node, param)
        # v_gain(数値) は必須
        if v_gain is not None:
            try:
                tmp = Decimal(str(v_gain))
            except InvalidOperation as e:
                raise IllegalArgumentException(f"Vcvs: v_gain must be digit: {v_gain}")

        self.v_gain = Decimal(str(v_gain)) if v_gain is not None else None

    def check_vcvs_param(self):
        # v_gain(数値) は必須
        if self.v_gain is None:
            raise IllegalArgumentException("Vcvs: v_gain is mandatory parameters")
        try:
            tmp = Decimal(str(self.v_gain))
        except InvalidOperation as e:
            raise IllegalArgumentException(f"Vcvs: v_gain must be digit: {self.v_gain}")

    @classmethod
    def create_element(cls, *args):
        """
        文字列からインスタンスを生成

        Parameters:
        ----------
        args: list
            引数の配列
        """

        try:
            # 例: E1 2 3 4 5 -1.0
            num = str(args[0][0][1:])
            node = {Vcvs.E_OUT_P: str(args[0][1]), Vcvs.E_OUT_M: str(args[0][2]), Vcvs.E_IN_P: str(args[0][3]),
                    Vcvs.E_IN_M: str(args[0][4])}
            # v_gain(数値) は必須
            v_gain = Decimal(str(args[0][5]))

            # param は None
            ret = Vcvs(num, node, None, v_gain)
            return ret
        except ValueError:
            raise IllegalArgumentException(f"Invalid Parameter: {args}")

    def valid_check(self):
        """
        各メンバに関するチェックを行う
        """
        super().check_param()
        self.check_vcvs_param()

    def print_element(self):
        """
        spice ネットリスト形式で出力

        [Usage]
        vcvs = Vcvs.new()
        vcvs.num = 1
        vcvs.node[:out_p] = 2
        vcvs.node[:out_m] = 3
        vcvs.node[:in_p] = 4
        vcvs.node[:in_m] = 5
        vcvs.v_gain = -1.0
        vcvs.printElement => E1 2 3 4 5 -1.0
        """
        self.valid_check()

        # param は不要？
        self.print_msg(f"{Vcvs.PREFIX}{self.num} {self.node[Vcvs.E_OUT_P]} {self.node[Vcvs.E_OUT_M]} " +
                       f"{self.node[Vcvs.E_IN_P]} {self.node[Vcvs.E_IN_M]} {str(self.v_gain)}")

    def get_element_str(self):
        """
        spice ネットリスト形式で文字列を返す

        Returns:
            ネットリスト形式の文字列
        """
        self.valid_check()

        # param は不要？
        ret = f"{Vcvs.PREFIX}{self.num} {self.node[Vcvs.E_OUT_P]} {self.node[Vcvs.E_OUT_M]} " \
              f"{self.node[Vcvs.E_IN_P]} {self.node[Vcvs.E_IN_M]} {str(self.v_gain)}"
        return ret

    def print_node(self):
        """
        spice ネットリスト形式でノード情報のみ出力

        [Usage]
        vcvs.printNode => E1 2 3 4 5
        """
        self.valid_check()

        # param は不要？
        self.print_msg(f"{Vcvs.PREFIX}{self.num} {self.node[Vcvs.E_OUT_P]} {self.node[Vcvs.E_OUT_M]} " +
                       f"{self.node[Vcvs.E_IN_P]} {self.node[Vcvs.E_IN_P]}")

    def get_node_str(self):
        """
        spice ネットリスト形式でノード情報の文字列を返す

        Returns:
            ネットリスト形式のノード情報のみの文字列
        """
        self.valid_check()

        # param は不要？
        ret = f"{Vcvs.PREFIX}{self.num} {self.node[Vcvs.E_OUT_P]} {self.node[Vcvs.E_OUT_M]} " \
              f"{self.node[Vcvs.E_IN_P]} {self.node[Vcvs.E_IN_P]}"
        return ret


class Circuit:
    """
    以下で構成される
    resistor, capacitor, inductor, vsource, isource, mosfet, diode, cccs, ccvs, vccs, vcvs class
    node_info: Array、回路のノード（節点）情報を格納、各要素は string
    power_supply: Hash、回路の電源を格納、power_supply[:TOP]、power_supply[:BOTTOM]、power_supply[:GND]で構成される
    _elements: Array　回路を構成する素子クラスを格納
    count: Hash、各素子の数を格納、例：count[:MOSFET] は mosfet の数を格納
    """

    OUT_FILE = None  # 出力用ファイルパス(default=None, 標準出力)

    def __init__(self):
        """
        初期化を行う

        Parameters
        ----------
        num: str
            素子番号
        node: dict
            素子のノード情報を管理(dict,　各要素は str)
        param: str
            素子のパラメータ
        """

        # 回路のノード（節点）情報を格納、各要素は str
        self.node_list = []

        # 回路の電源を格納、power_supply[:TOP]、power_supply[:BOTTOM]、power_supply[:GND]で構成される
        self.power_supply = dict()

        # 回路を構成する素子クラスを格納
        # resistor, capacitor, inductor, vsource, isource, mosfet, diode, cccs, ccvs, vccs, vcvs　で構成される
        self._elements = []

        # Hash、各素子の数を格納、例：count[:MOSFET] は mosfet の数を格納
        self.count = dict()

    def size(self):
        """
        circuit class を構成する素子の数を返す

        Returns
        -------
            circuit class を構成する素子の数
        """
        return len(self._elements)

    def print_elements(self):
        """
        circuit class を構成する全ての素子を spice netlist 形式で出力
        """
        self.print_element_list(self._elements)

    def print_element_list(self, element_list):
        """
        引数 element のみの spice netlist 形式で出力

        Parameters
        ----------
        element_list: list
            素子のリスト 各要素は Element のインスタンス

        [Usage]
          res = []
          res[0] = Resistor.new()
          res[0].num = 1
          res[0].node[:r_top] = 2
          res[0].node[:r_bottom] = 3
          res[0].param = 1k
          res[1] = Resistor.new()
          res[1].num = 2
          res[1].node[:r_top] = 3
          res[1].node[:r_bottom] = 0
          res[1].param = 2k

          printElement(res) => res[0].printElement, res[1].printElement を実行
        """
        if isinstance(element_list, list):
            for elem in element_list:
                if isinstance(elem, Element):
                    elem.print_element()
                else:
                    raise IllegalArgumentException("Circuit: print_element: element_list must be list of Element")
        else:
            raise IllegalArgumentException("Circuit: print_element: element_list must be list of Element")

    def set_cir(self):
        """
        保持している _elements[] のリストから
        node_list, power_supply, count を求める
        """
        # 回路のノード（節点）情報を格納、各要素は str
        self.node_list = []
        for elem in self._elements:
            tmp_node = elem.node
            self.node_list.extend(list(tmp_node.values()))
        self.node_list = set(self.node_list)
        # print(self.node_list)

        # 回路の電源を格納、power_supply[:TOP]、power_supply[:BOTTOM]、power_supply[:GND]で構成される
        self.power_supply = dict()
        # ノード名に VDD と VSS あり ⇒ power_supply[:TOP] = "VDD", power_supply[:BOTTOM] = "VSS"
        # VSS がなく、VDD あり ⇒ power_supply[:TOP] = "VDD", power_supply[:BOTTOM] = "GND"
        # VDD がなく VSS あり ⇒ power_supply[:TOP] = "GND", power_supply[:BOTTOM] = "VSS"
        vdd_flag = False
        vss_flag = False
        if 'VDD' in self.node_list:
            vdd_flag = True
        if 'VSS' in self.node_list:
            vss_flag = True

        if vdd_flag and vss_flag:
            self.power_supply['TOP'] = 'VDD'
            self.power_supply['BOTTOM'] = 'VSS'
        if not vss_flag and vdd_flag:
            self.power_supply['TOP'] = 'VDD'
            self.power_supply['BOTTOM'] = 'GND'
        if not vdd_flag and vss_flag:
            self.power_supply['TOP'] = 'GND'
            self.power_supply['BOTTOM'] = 'VSS'

        # Hash、各素子の数を格納、例：count[:MOSFET] は mosfet の数を格納
        self.count = dict()
        for elem in self._elements:
            cls_name = elem.__class__.__name__.upper()
            if cls_name in self.count:
                self.count[cls_name] += 1
            else:
                self.count[cls_name] = 1

    def get_elements(self):
        return self._elements

    def make_circuit(self, elem_list):
        """
        array は各素子のクラスのインスタンスで構成
        例：array = [mosfet1, mosfet2, resistor, vsource]
        これを引数にして circuit class を作成

        Parameters:
            elem_list: elementからなる配列
        """
        if (elem_list is None) or (len(elem_list) == 0):
            # elem_listが None、または空の場合は何もしない
            return

        if not isinstance(elem_list, list):
            raise IllegalArgumentException("Circuit: make_circuit: elem_list must be list of Element")
        for elem in elem_list:
            if not isinstance(elem, Element):
                raise IllegalArgumentException("Circuit: make_circuit: elem_list must be list of Element")

        self._elements = elem_list
        self.set_cir()

    def read_circuit(self, filename):
        """
        spice netlist 形式のファイルを読み込み circuit クラスを作成

        Parameters:
            filename: 入力ファイル名
        """
        with open(filename, "r", encoding="utf-8") as f:
            contents = f.read()

        lines = contents.splitlines()
        for tmp_str in lines:
            # '*', '.' から始まる行はコメント
            if (re.match('^\\*.*$', tmp_str) is not None) or (re.match('^\\..*$', tmp_str) is not None) \
                    or (tmp_str.strip() == ""):
                continue
            else:
                self._elements.append(Circuit.get_element_instance(tmp_str))

        self.set_cir()
        #self.print_elements()

    def write_circuit(self, filename):
        """
        spice netlist 形式で回路を出力

        Parameters:
            filename: 出力ファイル名。既存ファイルの場合は、append モードで書き出しを行う。
        """

        pre_out_file = Element.OUT_FILE
        Element.OUT_FILE = filename
        self.print_elements()
        Element.OUT_FILE = pre_out_file

    def node_info(self):
        """
        circuit class のノード（節点）一覧を表示

        Returns:
            circuit class のノード（節点）一覧
        """
        return self.node_list

    @classmethod
    def get_element_instance(cls, line):
        """
        実行時のコマンドから判別して、対応する Element のインスタンスを返す

        Parameters
        ----------
        line :
            netlist 中の文字列

        Returns
        -------
            対応する Element のインスタンス
        """

        element_map = {
            'R': Resistor,
            'C': Capacitor,
            'L': Inductor,
            'V': Vsource,
            'I': Isource,
            'M': Mosfet,
            'D': Diode,
            'F': Cccs,
            'H': Ccvs,
            'G': Vccs,
            'E': Vcvs,
        }

        try:
            return element_map[line[0]].create_element(line.split())
        except KeyError as e:
            raise IllegalArgumentException(f"Invalid element's data: {line}")
        finally:
            pass

    def print_msg(self, msg):
        if Circuit.OUT_FILE is None:
            print(msg)
        else:
            with open(Element.OUT_FILE, 'a') as f:
                print(msg, file=f)

