#!/usr/bin/env sh
# Add kicad-cursor scripts/bin to PATH via your shell profile.
# Usage: ./scripts/install-path-commands.sh [--uninstall]
set -e

repoRoot=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
binDir="$repoRoot/scripts/bin"
marker="# kicad-cursor scripts/bin"

if [ ! -d "$binDir" ]; then
    echo "Bin directory not found: $binDir" >&2
    exit 1
fi

case "${SHELL##*/}" in
    zsh)  profile="$HOME/.zshrc" ;;
    bash) if [ -f "$HOME/.bash_profile" ]; then profile="$HOME/.bash_profile"; else profile="$HOME/.bashrc"; fi ;;
    fish) profile="$HOME/.config/fish/config.fish" ;;
    *)    profile="$HOME/.profile" ;;
esac

if [ "$1" = "--uninstall" ]; then
    if [ -f "$profile" ] && grep -qF "$marker" "$profile"; then
        tmp=$(mktemp)
        grep -vF -e "$marker" -e "$binDir" "$profile" > "$tmp"
        mv "$tmp" "$profile"
        echo "Removed from $profile"
    else
        echo "Nothing to remove in $profile"
    fi
    exit 0
fi

chmod +x "$binDir/fetch-part" "$binDir/extract-datasheet"

if [ -f "$profile" ] && grep -qF "$binDir" "$profile"; then
    echo "Already on PATH via $profile"
else
    if [ "${SHELL##*/}" = "fish" ]; then
        mkdir -p "$(dirname "$profile")"
        printf '\n%s\nfish_add_path %s\n' "$marker" "$binDir" >> "$profile"
    else
        printf '\n%s\nexport PATH="%s:$PATH"\n' "$marker" "$binDir" >> "$profile"
    fi
    echo "Added to $profile"
fi

echo ""
echo "Available commands (open a new terminal or source $profile):"
echo "  fetch-part C702003"
echo "  fetch-part C702003 --symbol"
echo "  extract-datasheet --pdf datasheets/bq25619.pdf"
echo "  extract-datasheet --all"
