
[comment]: # (-*-coding: utf-8-*-)
# CheckMeIn
[![License](https://img.shields.io/badge/license-MIT-green)](https://en.wikipedia.org/wiki/MIT_License)
[![Build Status](https://github.com/cnobile2012/CheckMeIn/actions/workflows/main.yml/badge.svg?branch=development)](https://github.com/cnobile2012/CheckMeIn/actions/workflows/main.yml)
[![Coverage](https://coveralls.io/repos/github/cnobile2012/CheckMeIn/badge.svg?branch=development&dummy=987654321)](https://coveralls.io/github/cnobile2012/CheckMeIn?branch=development)

A system for checking into and out of a building

# Setup
You will need to install some basic packages on Linux, these are the packages
for Ubuntu. This updated version of `CheckMeIn` can work with Python 3.10 -
3.14 only. I'm assuming python 3.14 throughout this document. `sqlitebrowswer`
is only needed in development environments.
```bash
$ sudo apt install build-essential python3.14 python3-setuptools git virtualenvwrapper
$ sudo apt install sqlitebrowswer
```

Now we clone the repository.

The first command is used if you have a GitHub account and are logged in and
the second command is if you do not have a GitHub account.
```bash
$ git clone git@github.com:theforgeinitiative/CheckMeIn.git

$ git clone https://github.com/theforgeinitiative/CheckMeIn.git
```

Setup the VE (Virtual Environment). The virtualenvwrapper package is a wrapper
around virtualenv that provides easy to use tools for virtualenv and will
install virtualenv for you. I use the `nano` editor but you can use the editor
of your choice.
```bash
$ nano .bashrc
```

Then add the following lines to the bottom of the .bashrc file.
```
# Setup the Python virtual environment.
VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3
source /etc/profile.d/virtualenvwrapper.sh
```

Create a VE for your project. The VE name can be whatever you want and does not
need to match the actual project's name, but it might be a good idea to keep it
short so that you can remember it. Use whichever Python version you have in the
commands below.
```bash
$ cd /path/to/your_project
$ mkvirtualenv -p python3.14 CMI3.14
```

After the initial creation of the VE you can use these commands to activate and
deactivate a VE.
```bash
$ workon CMI3.14
$ deactivate
```

If all the correct system packages have been installed you can now setup the
virtual environment that `CheckMeIn` requires. Use the first command for a
development environment and the second command for a production environment.
```bash
$ pip install -r requirements/development.txt

$ pip install -r requirements/production.txt
```

There is a `Makefile` in the repository. The targets in the `Makefile` should
be used for working in the development environment. This is the current listing
of make targets. Look in the `Makefile` for additional information on what the
targets do.
```bash
$ make help
all
clean
clobber
flake8
install-dev
install-prod
run
setup
tar
tests
test_setup
```

Running the server is as simple as typing `make run`, it sets up the
`checkmein.key` file and starts CherryPi.

## Running tests
To make sure you haven't broken anything where the app will crash, run the
tests. See the `Makefile` for instructions on how to run tests individually,
just classes, or just modules.
```bash
$ make tests
```

If a test fails and you want to eliminate it temporarily, uncomment the skip
that is before each test. This can also be done for an entire test class.
```
#@unittest.skip("Temporarily skipped")
```

## Launching the server on your test platform
Before the first start of the server create an admin account with the provided
script, following the instruction. *** TODO  This script is not written yet.***
```bash
$ ./scripts/create_admin.py
```

Once you are satisfied that you have the dependencies met, and the unit tests
are passing, then to run the server, you will execute:
```bash
$ make run
```

You can connect to your server using a local browser at "http://localhost:8089"

## Temporary notes for trouble shooting
* On recent releases of Raspberry Pi OS, it may be necessary to
`sudo apt install libatlas-base-dev` to get numpy to work in python3.

## Credits
Original repo: https://github.com/alan412/CheckMeIn<br>
Second repo: https://github.com/theforgeinitiative/CheckMeIn<br>
Third repo: https://github.com/cnobile2012/CheckMeIn<br>
