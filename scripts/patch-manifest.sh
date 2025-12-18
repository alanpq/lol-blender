#!/usr/bin/env bash

cd addon
WHEELS=$(printf '"./%s",' wheels/* | sed 's/,$//')
echo "Wheels: $WHEELS"
perl -0777 -i -pe '
  BEGIN { $wheels = shift }
  s/wheels\s*=\s*\[.*?\]/wheels = [$wheels]/sg
' "$WHEELS" blender_manifest.toml
cat blender_manifest.toml