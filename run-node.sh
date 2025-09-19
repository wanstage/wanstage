#!/usr/bin/env bash
set -eu
export API_KEY=${API_KEY:-changeme-api-key}
node dist/index.js
