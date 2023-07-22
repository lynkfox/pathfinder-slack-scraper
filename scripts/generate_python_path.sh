
ROOT_PATH="$(find . -maxdepth 2 -type d -not -path "./cdk.out" -not -path "./__pycache__" -not -path "./venv" -not -path "./.git" -not -path "./.vscode" -not -path "./common" | sed '/\/\./d' | tr '\n' ':' | sed 's/:$//')"
# parse the root directory and add all top level folders to the python path
export PYTHONPATH="${PYTHONPATH}:${ROOT_PATH}"

unset ROOT_PATH
