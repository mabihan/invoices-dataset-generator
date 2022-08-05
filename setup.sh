#!/usr/bin/env bash

do_linux_install() {

    echo -e "linux installation"

    # install dependencies
    sudo apt install -y wkhtmltopdf

    # create virtual environment
    python3 -m venv .venv

    source .venv/bin/activate
    pip install -r requirements.txt
}

do_macOs_install() {

    echo -e "macOs installation"

    # check brew is installed
    [ ! -f "`which brew`" ] && echo "Brew is not installed. Please see https://brew.sh/" && exit 1

    # install dependencies
    brew install wkhtmltopdf

    # create virtual environment
    python3 -m venv .venv

    source .venv/bin/activate
    pip install -r requirements.txt
}

if [ "$(uname)" == "Darwin" ]; then
    do_macOs_install       
elif [ "$(expr substr $(uname -s) 1 5)" == "Linux" ]; then
    do_linux_install
fi
