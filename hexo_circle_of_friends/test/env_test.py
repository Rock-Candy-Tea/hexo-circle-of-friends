# -*- coding:utf-8 -*-
# Author：yyyz
import os
import sys

def restart_program():
    print(os.environ)
    os.execl(sys.executable, sys.executable, *sys.argv)


if __name__ == '__main__':
    restart_program()
