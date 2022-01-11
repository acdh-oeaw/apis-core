#!/bin/sh
# Shell script to check the apis-core version on pypi and bump it

CURRENTLY_BUILT_VER=$(sed -n '3s/.*= "\(.*\)"/\1/p' pyproject.toml)
LASTVER_PIP=$(lastversion apis-core --at pip -gt ${CURRENTLY_BUILT_VER})
echo $LASTVER_PIP
echo $CURRENTLY_BUILT_VER
LASTVER=$(lastversion ${CURRENTLY_BUILT_VER} -gt ${LASTVER_PIP})
echo $LASTVER
if [ "$CURRENTLY_BUILT_VER" == "$LASTVER" ]; then
    echo "version already newer"; else
    echo "patching version"
    sed -i "3s/\".*$/\"${LASTVER_PIP}\"/" pyproject.toml
    poetry version patch
fi