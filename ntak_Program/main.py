#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import os
import shutil
import sys
import time

import numpy as np
from spice import Spice
from evalcir import EvalCir
from extractor import Extractor


class IllegalArgumentError(Exception):
    """実行時引数なしの例外クラス"""


def main():

    start_time = time.perf_counter()

    parser = argparse.ArgumentParser(description='Execute Spice simulation.')
    # ngspice.sp または hspice1.sp へのファイルパスを指定
    parser.add_argument("-i", required=True, help="input sp filename")
    # ngspice または hspice を指定
    parser.add_argument("-spice", default="ngspice", help="spice type")
    # ../Sp_Data/Opamp.sp のシンボリックリンク先を指定。*.lib ファイル中では ../Sp_Data/Opamp.sh で指定
    parser.add_argument("-cir", default="../Sp_Data/OPamp_org.sp",
                        help="Main stage's file path")
    # Hspice C/S モードでの接続先ポートを指定
    parser.add_argument("-cc", default=None, help="hspice: port")
    # ngspice.conf または hspice.conf へのファイルパスを指定
    parser.add_argument("-conf", default="ngspice.conf", help="config filename")
    # 結果をファイルへ出力する際、そのパスを指定
    parser.add_argument("-o", default=None, help="output filename")
    # MOSFET モデルパラメータファイルのディレクトリパス(Hspiceのみ)
    parser.add_argument("-modeldir", default=None, help="MOSFET model file's  directory path")
    # MOSFET モデルパラメータファイルのモデル名(Hspiceのみ)
    parser.add_argument("-model", default=None, help="MOSFET model name")

    args = parser.parse_args()

    if args.o is not None:
        EvalCir.out_file = args.o

    # Hspice 実行時のみ、-cc でポートを指定可能とする
    if args.cc is not None:
        if args.spice is None or args.spice == "ngspice":
            args.cc = None
            args.modeldir = None
            args.model = None
        elif args.spice == 'hspice':
            if args.modeldir is None or args.model is None:
                # どちらかが None の場合は、何もしない
                args.modeldir = None
                args.model = None

    # -cir オプションで指定したファイルが実際に存在するかチェック、しなかったら Exit
    if not os.path.isfile(args.cir):
        print(f"Error: -cir file is not Exist:{args.cir}")
        sys.exit(1)

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

    # ../Sp_Data/Opamp.sp -> (-cir オプションで指定したファイル)へのシンボリックリンクを作成
    # -cir オプションで指定したファイルが "../Sp_Data/Opamp.sp" だったらシンボリックリンクは作成せずにそのまま使用する
    path_args_cirfile = os.path.abspath(args.cir)
    path_base_cirfile = os.path.abspath('../Sp_Data/OPamp.sp')
    if path_args_cirfile != path_base_cirfile:
        os.unlink(path_base_cirfile)
        os.symlink(path_args_cirfile, path_base_cirfile)

    # cir ファイルには ../Sp_Data/OPamp.sp を指定
    ec = EvalCir(args.i, args.spice, args.cc, path_base_cirfile, args.conf, args.o)

    ec.print_msg("args.i = {} ".format(args.i))
    ec.print_msg("args.spice = {} ".format(args.spice))
    ec.print_msg(f"args.cir: ../Sp_Data/OPamp.sp -> {args.cir} (symbolic link)")
    ec.print_msg("args.cc = {} ".format(args.cc))
    ec.print_msg("args.conf = {} ".format(args.conf))
    if args.o is not None:
        ec.print_msg("args.o = {} ".format(args.o))
    else:
        ec.print_msg("args.o = print standard output")

    if args.cc is not None:
        if args.spice is None or args.spice == 'ngspice':
            ec.print_msg("-cc option is not allowed for ngspice: Ignored...")
    if args.modeldir is not None or args.model is not None:
        ec.print_msg("args.modeldir = {} ".format(args.modeldir))
        ec.print_msg("args.model = {} ".format(args.model))

    # args.modeldir, args.model が指定されている場合は、args.i で指定されたファイル内の書き換えを行う
    if args.modeldir or args.model:
        before_str = ".lib '../Lib_Data/tsmc018.lib' model27"
        after_str = ".lib '" + args.modeldir + "' " + args.model
        spfilename = args.i
        for i in range(2):
            # 元のファイルを *.bak として保存
            shutil.copy2(spfilename, spfilename+'.bak')

            with open(spfilename, "r") as f:
                strs = [row.replace(before_str, after_str) for row in f]
            # 書き込み
            with open(spfilename, "w") as f:
                f.writelines(strs)

            # 次のファイル名を求める
            spfile_index = int(spfilename[-4])
            spfile_index += 1
            spfilename = spfilename[:-4] + str(spfile_index) + ".sp"  # hspice2.sp

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
