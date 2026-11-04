#!/bin/sh
set -eu
VERSION=1.30.3
SHA256=b512bf24945503a33fc10738ecffc1f2dccaaf8593a448e94ee9ac86a9559a59
BASE_URL=https://software.verapdf.org/rel/1.30
PREFIX=${1:-"$PWD/.tools/verapdf-$VERSION"}
ARCHIVE=${TMPDIR:-/tmp}/verapdf-greenfield-$VERSION-installer.zip
mkdir -p "$(dirname "$PREFIX")"
if [ ! -f "$ARCHIVE" ]; then curl --fail --location --retry 3 --output "$ARCHIVE" "$BASE_URL/verapdf-greenfield-$VERSION-installer.zip"; fi
actual=$(sha256sum "$ARCHIVE" | awk '{print $1}')
test "$actual" = "$SHA256" || { echo "veraPDF checksum mismatch: $actual" >&2; exit 1; }
if [ ! -x "$PREFIX/verapdf" ]; then
  rm -rf "$PREFIX.tmp"; mkdir -p "$PREFIX.tmp"; unzip -q "$ARCHIVE" -d "$PREFIX.tmp"
  cat > "$PREFIX.tmp/auto-install.xml" <<EOF
<AutomatedInstallation langpack="eng">
  <com.izforge.izpack.panels.htmlhello.HTMLHelloPanel id="welcome"/>
  <com.izforge.izpack.panels.target.TargetPanel id="install_dir"><installpath>$PREFIX</installpath></com.izforge.izpack.panels.target.TargetPanel>
  <com.izforge.izpack.panels.packs.PacksPanel id="sdk_pack_select"><pack index="0" name="veraPDF GUI" selected="true"/><pack index="1" name="veraPDF CLI" selected="true"/><pack index="2" name="veraPDF Documentation" selected="true"/><pack index="3" name="veraPDF Sample Plugins" selected="false"/></com.izforge.izpack.panels.packs.PacksPanel>
  <com.izforge.izpack.panels.install.InstallPanel id="install"/>
  <com.izforge.izpack.panels.finish.FinishPanel id="finish"/>
</AutomatedInstallation>
EOF
  (cd "$PREFIX.tmp/verapdf-greenfield-$VERSION" && sh ./verapdf-install "$PREFIX.tmp/auto-install.xml")
  rm -rf "$PREFIX.tmp"
fi
test -x "$PREFIX/verapdf"; "$PREFIX/verapdf" --version
