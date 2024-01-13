#!/usr/bin/env bash
set -e

if test ! -e "rbinstall/main.py"; then
    echo "Run this in the root of the rbinstall tree."
    exit 1
fi

rm -rf dist

python3 -m build .

RBINSTALL_FILENAME=$(basename "$(find dist -name 'rbinstall*.whl')")
INSTALLER_PAYLOAD=$(base64 < "dist/$RBINSTALL_FILENAME")

cat scripts/templates/bootstrap.py > dist/rbinstall.py

echo "
rbinstall_whl_filename = '${RBINSTALL_FILENAME}'

def get_installer_data():
    return b'''${INSTALLER_PAYLOAD}'''


if __name__ == '__main__':
    main()
" >> dist/rbinstall.py
