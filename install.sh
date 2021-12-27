set -ex

NAME=cron_calendar

DEST_DIR=/opt/$NAME
DEST_SERVICES=/etc/systemd/system

function install_python {
    rm -rf $DEST_DIR
    mkdir -p $DEST_DIR
    python3 -m venv $DEST_DIR
    source $DEST_DIR/bin/activate
    pip install .
}

function install_cron {
    cp cron_calendar.cron /etc/cron.d
}

install_python
install_cron
