#!/usr/bin/env bash
set -euo pipefail

SRC=services/frontend/admin-ui
DEST=../tattoo-admin-ui

if [ -d "$DEST" ]; then
  echo "$DEST already exists; aborting"
  exit 1
fi

mkdir -p "$DEST"
rsync -av --exclude node_modules "$SRC/" "$DEST/"
cat > "$DEST/README_PUSH.md" <<'EOF'
Repository prepared for push. To initialize remote repo:

cd tattoo-admin-ui
git init
git add .
git commit -m "Import admin UI from monorepo"
# create remote repo on GitHub and add as origin
# git remote add origin git@github.com:yourorg/tattoo-admin-ui.git
# git push -u origin main
EOF

echo "Admin UI exported to $DEST"
