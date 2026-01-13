#!/usr/bin/env bash
set -euo pipefail

REPO="Frank1o3/smithpy"
PYTHON=${PYTHON:-python3}
OS="$(uname -s)"

echo "Installing SmithPy..."

# Ensure pip exists
$PYTHON -m ensurepip --upgrade >/dev/null 2>&1 || true
$PYTHON -m pip install --upgrade pip >/dev/null

# Resolve latest wheel URL
WHEEL_URL="$(
  curl -fsSL "https://api.github.com/repos/$REPO/releases/latest" \
  | grep -E '"browser_download_url".*\.whl"' \
  | head -n 1 \
  | cut -d '"' -f 4
)"

if [[ -z "$WHEEL_URL" ]]; then
  echo "Failed to locate SmithPy wheel in latest release."
  exit 1
fi

case "$OS" in
  Linux*)
    echo "Detected Linux — using pipx for global install"

    if ! command -v pipx >/dev/null 2>&1; then
      echo "pipx not found, installing..."
      $PYTHON -m pip install --user pipx
      $PYTHON -m pipx ensurepath
    fi

    pipx install --force "$WHEEL_URL"
    ;;

  Darwin*|MINGW*|MSYS*|CYGWIN*)
    echo "Detected macOS or Windows — using pip"
    $PYTHON -m pip install --upgrade "$WHEEL_URL"
    ;;

  *)
    echo "Unsupported OS: $OS"
    exit 1
    ;;
esac

echo
echo "SmithPy installed successfully."
echo "Run: smithpy --help"
