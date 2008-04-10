# -*- coding: utf-8 -*-

from iolsucker import *
import getpass

def main():

    #TODO Verify if dni is correct.
    dni = raw_input('Enter your DNI: ')
    pwd = getpass.getpass("Enter password for DNI %s: " %dni)

    sucker = PyIOLSucker()
    if not sucker.isLogged():
        sucker.doLogin(dni, pwd)
    subs = getSubjects()

    for subject in subs:
        files = files + acidRain(subject.folder)


main()