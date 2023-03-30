#!/bin/sh

${PYTHON_BIN} main.py --address=0.0.0.0 --port=30000 gameserver > /tmp/gameserver.log && ${PYTHON_BIN} user_server/main.py userserver > /tmp/userserver.log

echo "start server finished" > /tmp/start.log