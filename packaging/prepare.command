#!/bin/bash
set -euo pipefail

if [ "$(uname -s)" != Darwin ]; then
    echo "Resource preparation requires macOS and JDK 25." >&2
    exit 1
fi
here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
support="$HOME/Library/Application Support/Herspers Minecraft"
resources="$support/resources/26.3"

# Prefer an installed JDK 25. Never silently use an older system Java.
if selected_java=$(/usr/libexec/java_home -F -v 25 2>/dev/null); then
    export JAVA_HOME="$selected_java"
fi
if [ -z "${JAVA_HOME:-}" ] || [ ! -x "$JAVA_HOME/bin/java" ] || [ ! -x "$JAVA_HOME/bin/javac" ]; then
    echo "Install JDK 25, then run this script again. A JRE alone is insufficient." >&2
    exit 1
fi
java_major=$("$JAVA_HOME/bin/java" -version 2>&1 | /usr/bin/awk 'NR == 1 { gsub(/"/, "", $3); split($3, v, "."); print v[1] }')
javac_version=$("$JAVA_HOME/bin/javac" -version 2>&1)
javac_major=${javac_version#javac }
javac_major=${javac_major%%.*}
if [ "$java_major" != 25 ] || [ "$javac_major" != 25 ]; then
    echo "JDK 25 is required; JAVA_HOME must provide both java 25 and javac 25." >&2
    exit 1
fi
export PATH="$JAVA_HOME/bin:$PATH"

server_jar=${1:-}
if [ -z "$server_jar" ]; then
    server_jar=$(/usr/bin/osascript -e 'POSIX path of (choose file with prompt "Choose your Minecraft Java Edition 26.3 server.jar")')
fi
if [ ! -f "$server_jar" ]; then
    echo "Server JAR not found: $server_jar" >&2
    exit 1
fi
minecraft_dir=${2:-"$HOME/Library/Application Support/minecraft"}
if [ ! -d "$minecraft_dir" ]; then
    echo "Minecraft folder not found: $minecraft_dir. Play Java Edition 26.3 once in the official launcher first." >&2
    exit 1
fi

# Preparers create caches and compile exporters. Keep those writes outside the signed app.
preparation_id=$(cat "$here/preparation-id.txt")
case "$preparation_id" in
    ''|*[!0-9a-f]*) echo "Invalid bundled preparation identity." >&2; exit 1 ;;
esac
if [ "${#preparation_id}" != 64 ]; then
    echo "Invalid bundled preparation identity length." >&2
    exit 1
fi
mkdir -p "$support/preparation" "$support/resources"
working_root="$support/preparation/$preparation_id"
if [ ! -d "$working_root" ]; then
    staging=$(mktemp -d "$support/preparation/.inputs.XXXXXX")
    trap 'if [ -n "${staging:-}" ]; then rm -rf -- "$staging"; fi' EXIT
    /usr/bin/ditto "$here/preparation" "$staging"
    mv -- "$staging" "$working_root"
    staging=
fi
export HORIZON_HOME="$support"
export HORIZON_LAUNCHER_NO_SELF_UPDATE=1
"$here/../MacOS/horizon-prepare" --root "$working_root" --output "$resources" \
    --prepare --complete --server-jar "$server_jar" --minecraft-dir "$minecraft_dir"
"$here/../MacOS/horizon-prepare" --root "$working_root" --output "$resources" --check
echo "Resources are ready. You can now open Herspers Minecraft.app."
