#!/bin/bash
# Menu Lens 分析脚本
# 对清华大学新雅书院公众号文章目录进行分析

set -e

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# 默认使用完整数据
DATA_FILE="${PROJECT_DIR}/data/official_account_menu.json"
OUTPUT_DIR="${PROJECT_DIR}/reports"

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --lite)
            DATA_FILE="${PROJECT_DIR}/data/official_account_menu_lite.json"
            shift
            ;;
        --full)
            DATA_FILE="${PROJECT_DIR}/data/official_account_menu.json"
            shift
            ;;
        --output|-o)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --lite          使用轻量版数据 (debug用)"
            echo "  --full          使用完整数据 (默认)"
            echo "  -o, --output    指定报告输出目录 (默认: reports/)"
            echo "  -h, --help      显示帮助信息"
            echo ""
            echo "Examples:"
            echo "  $0              # 运行完整数据分析"
            echo "  $0 --lite       # 运行轻量版数据分析"
            echo "  $0 -o ./output  # 指定输出目录"
            exit 0
            ;;
        *)
            echo "未知参数: $1"
            echo "使用 --help 查看帮助"
            exit 1
            ;;
    esac
done

# 检查 conda 环境
if ! conda info --envs | grep -q "tokenlized_xy"; then
    echo "错误: 未找到 conda 环境 'tokenlized_xy'"
    exit 1
fi

# 检查数据文件
if [[ ! -f "$DATA_FILE" ]]; then
    echo "错误: 数据文件不存在: $DATA_FILE"
    exit 1
fi

echo "=============================================="
echo "Menu Lens - 新雅书院公众号文章目录分析"
echo "=============================================="
echo ""
echo "数据文件: $DATA_FILE"
echo "输出目录: $OUTPUT_DIR"
echo ""

# 激活 conda 环境并运行分析
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate tokenlized_xy

cd "$PROJECT_DIR"

python3 << EOF
import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path("$PROJECT_DIR") / "src"))

from menu_lens import MenuStats

data_path = Path("$DATA_FILE")
output_dir = Path("$OUTPUT_DIR")

print(f"加载数据: {data_path}")
print(f"文件大小: {data_path.stat().st_size / 1024 / 1024:.2f} MB")
print("=" * 60)

stats = MenuStats(data_path, output_dir=output_dir)
stats.print_summary()

print()
saved = stats.save_reports()
print(f"\n✓ 报告已保存:")
for fmt, path in saved.items():
    print(f"  [{fmt}] {path}")
EOF

echo ""
echo "=============================================="
echo "分析完成!"
echo "=============================================="
