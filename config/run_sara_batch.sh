#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

python "$SCRIPT_DIR/sms/scripts/run_sara_batch.py"
