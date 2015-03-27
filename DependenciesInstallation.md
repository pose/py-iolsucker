# Introduction #
py-iolsucker needs certain dependecies that must be installed for it to work. Instead of installing them at /lib I prefered installing libs in my home dir. Here I explain how I do it.

# Dependecies #
  * PyRSS2Gen
  * Beautiful Soup


# Howto install @ /home/ #

## Download ##
  * [Beautiful Soup](http://www.crummy.com/software/BeautifulSoup/)
  * [PyRSS2Gen](http://www.dalkescientific.com/Python/PyRSS2Gen.html)

## Installation ##
  * Extract files.
  * python setup.py install --home=~

## Usage ##
Open a terminal and type:
```
export PYTHONPATH=$PYTHONPATH:/home/your_user/lib/python/
```
Enjoy!