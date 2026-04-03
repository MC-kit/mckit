#!/bin/bash

#
#  Install prerequisites for python.
#
#  dvp Apr 2026
#
#  Be patient: this script has been changed since the last usage and not tested after that.
#

OS="$(uname)"

install_linux_prerequisites() {
    sudo apt update && sudo apt install -y make build-essential libssl-dev zlib1g-dev \
        libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev \
        libncursesw5-dev xz-utils tk-dev libffi-dev liblzma-dev python-openssl git
}


install_all() {
    if [[ "$OS" == "Linux" ]]; then
        install_linux_prerequisites
    else
        echo "ERROR: Install build tools is not implemented for $OS"
        return 1
    fi
}

install_all "$@"

# vim: set ts=4 sw=0: tw=79 ss=0 ft=sh et ai :
