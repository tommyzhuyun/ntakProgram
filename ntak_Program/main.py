#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import time

import numpy as np
from evalcir import EvalCir
from spice import Spice
from extractor import Extractor


class IllegalArgumentError(Exception):
    """実行時引数なしの例外クラス"""


def main():
    start_time = time.perf_counter()

    parser = argparse.ArgumentParser(description='Execute Spice simulation.')
    parser.add_argument("-i", required=True, help="input sp filename")
    parser.add_argument("-spice", default="ngspice", help="spice type")
    parser.add_argument("-cir", default="../Sp_Data/OPamp.sp",
                        help="Main stage's file path")
    parser.add_argument("-cc", default=None, help="hspice: port")
    parser.add_argument("-conf", default="ngspice.conf", help="config filename")
    parser.add_argument("-o", default=None, help="output filename")
    args = parser.parse_args()

    if args.o is not None:
        EvalCir.out_file = args.o

    # Hspice 実行時のみ、-cc でポートを指定可能とする
    if args.cc is not None:
        if args.spice is None or args.spice == "ngspice":
            args.cc = None

    """
    # -cir オプションで指定した netlist ファイルに書き換え ⇒ OPamp.sp へのシンボリックリンクを変更する方針へ変更
    # Ngspice の場合 ⇒ ../Lib_Data/ng*.lib ファイル中の "OPamp.sp" を -cir で指定したファイル名へ書き換え
    if args.spice is None or args.spice == "ngspice":
        files = glob.glob("../Lib_Data/ng*.lib")
        for file in files:
            Extractor.rewrite_file(file, r"../Sp_Data/OPamp.sp", args.cir)

    # Hspice の場合 ⇒ ../Sp_Data/hspice*.sp ファイル中の "OPamp.sp" を -cir で指定したファイル名へ書き換え
    if args.spice == "hspice":
        files = glob.glob("../Sp_Data/hspice*.sp")
        for file in files:
            Extractor.rewrite_file(file, r"../Sp_Data/OPamp.sp", args.cir)
    """

    ec = EvalCir(args.i, args.spice, args.cc, args.cir, args.conf, args.o)

    ec.print_msg("args.i = {} ".format(args.i))
    ec.print_msg("args.spice = {} ".format(args.spice))
    ec.print_msg("args.cir = {} ".format(args.cir))
    ec.print_msg("args.cc = {} ".format(args.cc))
    ec.print_msg("args.conf = {} ".format(args.conf))
    if args.o is not None:
        ec.print_msg("args.o = {} ".format(args.o))
    else:
        ec.print_msg("args.o = print standard output")
    if args.cc is not None:
        if args.spice is None or args.spice == 'ngspice':
            ec.print_msg("-cc option is not allowed for ngspice: Ignored...")


    # ①同一 LIBファイル内で結果が取得できるものは、項目を配列で指定
    #results = ec.calc(args.i, \
    #          ["CC", "PD", "IRN", "OR", "THD", "OVR", "CMRR", "PSRR", "CMIR"])

    # ②指定がない場合は、すべての項目を抽出
    results = ec.calc(args.i)

    # ③１つだけ結果を抽出する場合
    # results = ec.calc(args.i, Extractor.IRN)
    # print("IRN: {}[{}]".format(results, Extractor.PARAM_UNIT['IRN'][0]))

    print_dbg = False
    if print_dbg:
        print("抽出データ")
        if isinstance(results, str):
            print("{}".format(results))
        elif isinstance(results, dict):
            for tmp in results.keys():
                if isinstance(results[tmp], list) and len(results[tmp]) == 0:
                    print("{}: No Data... [{}]".format(tmp, Spice.PARAM_UNIT[tmp][0]))
                else:
                    if isinstance(results[tmp], np.ndarray):
                        print("{}: {}[{}]".format(tmp, results[tmp], Spice.PARAM_UNIT[tmp][0]))
                    else:
                        print("{}: {}[{}]".format(tmp, results[tmp], Spice.PARAM_UNIT[tmp][0]))

    ec.first_print()
    ec.print_opamp_performance()

    """
    pattern_str = "^\\+ vp='half\\*[0-9]+.?[0-9]*' \\$ pulse amplitude"
    replace_str = "+ vp = 'half*" + "100.00" + "' $ pulse amplitude"
    EvalCir.rewrite_file("hsSR.lib", pattern_str, replace_str)
    """
    stop_time = time.perf_counter()
    ec.print_msg("*-->Execution Time : {:6E} [sec]".format(stop_time - start_time))


if __name__ == '__main__':
    main()
