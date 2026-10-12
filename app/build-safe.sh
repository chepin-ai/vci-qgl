#!/bin/bash
# 构建锁+后验：禁重叠构建；vite直写dist在本挂载面静默丢件（实证3.159：assets空/index.html缺但报✓built）
# → staging模式：/tmp构建 → cp落盘 → 五件后验
set -e
cd "$(dirname "$0")"
exec 9>/tmp/qgl-app-build.lock
flock -n 9 || { echo "另一构建在跑，拒重叠"; exit 1; }
STAGE=/tmp/qgl-dist-stage
rm -rf "$STAGE"
npx vite build --outDir "$STAGE" --emptyOutDir
rm -rf dist
cp -r "$STAGE" dist
for i in 1 2 3 4 5; do
  if [ -f dist/index.html ] && ls dist/assets/*.js >/dev/null 2>&1 && ls dist/assets/*.css >/dev/null 2>&1 && [ -f dist/dash-beat.json ] && [ -f dist/dash-beats.json ]; then
    echo "POST-BUILD VERIFY OK (t=${i})"; exit 0
  fi
  sleep 1
done
echo "POST-BUILD VERIFY FAIL"; exit 2
