#!/usr/bin/env python
# -*- coding: utf-8 -*-
# coded by Xu Yunfeng
import argparse
import random
import os
import shutil
import subprocess
import sys
import time

import numpy as np
from .spice import Spice
from .evalcir import EvalCir


def ReWriteLib():
    pattern_str = "^\\+ vp='half\\*[0-9]+.?[0-9]*' \\$ pulse amplitude"
    replace_str = "+ vp = 'half*" + "100.00" + "' $ pulse amplitude"
    EvalCir.rewrite_file("hsSR.lib", pattern_str, replace_str)


class LoopManager:
    @property
    def Commander(self):
        return self.__Commander

    @Commander.setter
    def Commander(self, value):
        if type(value) is argparse.Namespace:
            self.__Commander = value
        else:
            raise TypeError("class should be 'argparse.Namespace'")

    @property
    def Port(self):
        return self.__Port

    @Port.setter
    def Port(self,value):
        if value is not None:
            if type(value) is int:
                self.__Port = value
            elif type(value) is str:
                self.__Port = int(value)
            else:
                raise TypeError("Unknown Type of port:"+ str(type(value)))

    @property
    def Result(self):
        return self.__Result

    @Result.setter
    def Result(self,value):
        if type(value) is dict:
            self.__Result = value

    def __init__(self):
        # サーバー状態チェック
        self.HspiceCheck = False
        self.Result = dict()
        args = argparse.Namespace()
        self.Port = random.randint(25000, 60000)
        args.cc = str(self.Port)
        args.source_cir ='../Sp_Data/OPamp_new.sp'
        args.base_cir = '../Sp_Data/OPamp.sp'
        args.conf='./hspice.conf'
        args.i='../Sp_Data/hspice1.sp'
        args.before_model = "../Lib_Data/tsmc018.lib"
        args.before_modeldir = "model27"
        args.after_model=None
        args.after_modeldir=None
        args.o=None
        args.spice='hspice'

        # Hspice 実行時のみ、-cc でポートを指定可能とする
        if args.cc is not None:
            if args.spice is None or args.spice == "ngspice":
                args.cc = None
                args.after_modeldir = None
                args.after_model = None
            elif args.spice == 'hspice':
                if args.after_modeldir is None or args.after_model is None:
                    # どちらかが None の場合は、何もしない
                    args.after_modeldir = None
                    args.after_model = None
                else:
                    # args.after_modeldir, args.after_model が指定されている場合は、args.i で指定されたファイル内の書き換えを行う
                    before_str = ".lib '" + args.before_modeldir + "' " + args.before_model
                    after_str = ".lib '" + args.after_modeldir + "' " + args.after_model
                    spfilename = args.i
                    for i in range(2):
                        # 元のファイルを *.bak として保存
                        shutil.copy2(spfilename, spfilename + '.bak')

                        with open(spfilename, "r") as f:
                            strs = [row.replace(before_str, after_str) for row in f]
                        # 書き込み
                        with open(spfilename, "w") as f:
                            f.writelines(strs)
                        # 次のファイル名を求める
                        spfile_index = int(spfilename[-4])
                        spfile_index += 1
                        spfilename = spfilename[:-4] + str(spfile_index) + ".sp"  # hspice2.sp
        """
        # -cir オプションで指定した netlist ファイルに書き換え ⇒ OPamp.sp へのシンボリックリンクを変更する方針へ変更
        # Ngspice の場合 ⇒ ../Lib_Data/ng*.lib ファイル中の "OPamp.sp" を -cir で指定したファイル名へ書き換え
        if args.spice is None or args.spice == "ngspice":
            files = glob.glob("../Lib_Data/ng*.lib")
            for file in files:
                Extractor.rewrite_file(file, r"../Sp_Data/OPamp.sp", args.source_cir)

        # Hspice の場合 ⇒ ../Sp_Data/hspice*.sp ファイル中の "OPamp.sp" を -cir で指定したファイル名へ書き換え
        if args.spice == "hspice":
            files = glob.glob("../Sp_Data/hspice*.sp")
            for file in files:
                Extractor.rewrite_file(file, r"../Sp_Data/OPamp.sp", args.source_cir)
        """
        # -cir オプションで指定したファイルが実際に存在するかチェック、しなかったら Exit
        if not os.path.isfile(args.source_cir):
            print(f"Error: -cir file is not Exist:{args.source_cir}")
            sys.exit(1)

        self.Commander = args

    def __str__(self):
        self.print_msg("args.i = {} ".format(self.Commander.i))
        self.print_msg("args.spice = {} ".format(self.Commander.spice))
        self.print_msg(f"args.source_cir: ../Sp_Data/OPamp.sp -> {self.Commander.source_cir} (symbolic link)")
        self.print_msg("args.cc = {} ".format(self.Commander.cc))
        self.print_msg("args.conf = {} ".format(self.Commander.conf))
        if self.Commander.o is not None:
            self.print_msg("args.o = {} ".format(self.Commander.o))
        else:
            self.print_msg("args.o = print standard output")

        if self.Commander.cc is not None:
            if self.Commander.spice is None or self.Commander.spice == 'ngspice':
                self.print_msg("-cc option is not allowed for ngspice: Ignored...")
        if self.Commander.modeldir is not None or self.Commander.model is not None:
            self.print_msg("args.modeldir = {} ".format(self.Commander.after_modeldir))
            self.print_msg("args.model = {} ".format(self.Commander.after_model))

    def print_msg(self, msg):
        """
        結果を標準出力へ表示。出力ファイルパスの指定がある場合は、ファイルへ書き出す

        Parameters
        ----------
        msg :
           出力する文字列
        """

        if self.Commander.o is None:
            print(msg)
        else:
            with open(self.Commander.o, 'a') as f:
                print(msg, file=f)

    def HspiceStart(self,port=None):
        """
            サーバーを立ち上がる

            Parameters
            ----------
            port :
               ポート番号指定、未指定の場合はランダム
        """
        if self.HspiceCheck:
            self.HspiceStop()

        self.Port = port
        self.Commander.cc = str(self.Port)
        subprocess.run(['hspice64', '-CC', '-port', self.Commander.cc], shell=False, check=False)
        self.HspiceCheck = True

    def HspiceStop(self):
        """
            サーバーを終了させる
        """
        subprocess.run(['hspice64', '-CC', '-K', '-port', self.Commander.cc], shell=False, check=False)
        self.HspiceCheck = False

    def HspiceCalling(self,pid = None):
        args = self.Commander

        # ../Sp_Data/Opamp.sp -> (-cir オプションで指定したファイル)へのシンボリックリンクを作成
        # -cir オプションで指定したファイルが "../Sp_Data/Opamp.sp" だったらシンボリックリンクは作成せずにそのまま使用する
        path_args_cirfile = os.path.abspath(args.source_cir)
        path_base_cirfile = os.path.abspath(args.base_cir)
        """if path_args_cirfile != path_base_cirfile:
            if os.path.exists(path_base_cirfile):
                os.unlink(path_base_cirfile)
            os.symlink(path_args_cirfile, path_base_cirfile)
"""
        # cir ファイルには ../Sp_Data/OPamp.sp を指定
        ec = EvalCir(args.i, args.spice, args.cc, path_base_cirfile, args.conf, args.o, pid)

        # ①同一 LIBファイル内で結果が取得できるものは、項目を配列で指定
        # self.Result = ec.calc(args.i, \
        #          ["CC", "PD", "IRN", "OR", "THD", "OVR", "CMRR", "PSRR", "CMIR"])

        # ②指定がない場合は、すべての項目を抽出
        self.Result = ec.calc(args.i,None,True)

        # ③１つだけ結果を抽出する場合
        # self.Result = ec.calc(args.i, Extractor.IRN)
        # print("IRN: {}[{}]".format(self.Result , Extractor.PARAM_UNIT['IRN'][0]))

        #ec.first_print()
        #ec.print_opamp_performance()

        print_dbg = False
        if print_dbg:
            print("抽出データ")
            if isinstance(self.Result, str):
                print("{}".format(self.Result))
            elif isinstance(self.Result, dict):
                for tmp in self.Result.keys():
                    if isinstance(self.Result[tmp], list) and len(self.Result[tmp]) == 0:
                        print("{}: No Data... [{}]".format(tmp, Spice.PARAM_UNIT[tmp][0]))
                    else:
                        if isinstance(self.Result[tmp], np.ndarray):
                            print("{}: {}[{}]".format(tmp, self.Result[tmp], Spice.PARAM_UNIT[tmp][0]))
                        else:
                            print("{}: {}[{}]".format(tmp, self.Result[tmp], Spice.PARAM_UNIT[tmp][0]))



if __name__ == '__main__':
    lm = LoopManager()
    lm.HspiceStart()
    try:
        lm.HspiceCalling()
        for item_name, param_data in lm.Result.items():
            print(str(item_name) + str(param_data))
    except:
        pass
    finally:
        lm.HspiceStop()


"""HSPICE Options:
  -i           Specifies the input netlist file name
  -o           Specifies the output file name
  -hpp         High performance parallel for transient analysis
  -mt #num     Invokes multithreading and specifies the number of processors
  -mp [#num]   Invokes distributed-processing mode
  -gz          Generate compression output on analysis results
  -n #num      Specifies the starting number for numbering output data file revisions
  -d           Displays the content of .st0 files on screen
  -html        Specifies an HTML output file
  -top         Specifies the sub-circuit name to effectively eliminate .subckt subcktname and corresponding .ends statements
  -case        Enable case-sensitive simulation 
  -hdl         Specifies a Verilog-A module
  -hdlpath     Specifies the search path to Verilog-A files
  -vamodel     Specifies cell name for Verilog-A definitions
  -datamining  Invokes standalone data mining
  -dp [#num]   Invokes distributed-processing mode
  -dpconfig    Specifies a configuration file for distributed-processing mode
  -dplocation  Specifies if dp worker output to NFS directly, or output to /tmp
  -merge       Merge the output files in distributed-processing mode
  -dpincremental Specifies the sub_dpdir of original run for dp incremental run
  -meas        Re-invokes to calculate new measurements from a previous simulation
  -CC          Advanced Client/Server Mode
  -share       Used with -CC to specify a common file name shared by different circuits
  -port        Used with -CC to start or specify server on the designated port
  -K           Shuts down the client server
  -I           Interactive mode
  -L           Used with -I to run commands in a command file
  -h           Outputs this command line help message
  -doc         Provides access to the PDF documentation set user manuals
  -help        Opens the searchable Commands and Options browser-based help system
  -v           Outputs HSPICE version information
"""