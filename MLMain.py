#!/usr/bin/env python
# -*- coding: utf-8 -*-
# coded by Xu Yunfeng


import os
import traceback

from ntak_Program.LoopManager import *

if __name__ == '__main__':
    os.chdir('./ntak_Program')
    lm = LoopManager()
    #lm.HspiceStart()
    try:
        lm.HspiceCalling()
        for item_name, param_data in lm.Result.items():
            print(str(item_name) + str(param_data))
    except Exception as e:
        traceback.print_exc()
    finally:
        #lm.HspiceStop()
        os.chdir('..')
