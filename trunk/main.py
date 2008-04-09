# -*- coding: utf-8 -*-

from iolsucker import *
import getpass

def main():

    #TODO
    #dni should be gotten from stdin not from os.
    dni = getpass.getuser()
    pwd = getpass.getpass("enter password for user %s: " %dni)

    suck = PyIOLSucker()
    suck.doLogin( dni, pwd )

    print suck.isLogged()

main()