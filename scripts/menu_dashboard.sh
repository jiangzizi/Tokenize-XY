#!/bin/bash
# Menu Lens Dashboard - 交互式统计面板

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# 激活 conda 环境
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate tokenlized_xy

cd "$PROJECT_DIR"

# 运行 dashboard
python -c "
import sys
sys.path.insert(0, 'src')
from menu_lens.dashboard.app import main
main()
" "$@"
