#!/bin/bash
# 构建锁+后验：禁重叠构建（emptyOutDir竞态=js/css互抹根因）
set -e
cd "$(dirname "$0")"
exec 9>/tmp/qgl-app-build.lock
flock -n 9 || { echo "另一构建在跑，拒重叠"; exit 1; }
rm -rf dist
npx vite build
for i in 1 2 3 4 5; do
  if [ -f dist/index.html ] && ls dist/assets/*.js >/dev/null 2>&1 && ls dist/assets/*.css >/dev/null 2>&1 && [ -f dist/dash-beat.json ]; then
    echo "POST-BUILD VERIFY OK (t=${i})"; exit 0
  fi
  sleep 1
done
echo "POST-BUILD VERIFY FAIL"; exit 2
