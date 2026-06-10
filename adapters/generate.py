#!/usr/bin/env python3
"""
Super Harness 适配器生成器

从单一模板生成所有平台的适配器文件。
维护成本：只改 template.md，一键生成所有适配器。
"""

import os
import shutil
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 平台配置：平台名 -> (目标路径, 是否需要特殊处理)
PLATFORMS = {
    "opencode": {
        "path": "AGENTS.md",
        "description": "OpenCode / Codex 统一入口"
    },
    "claude": {
        "path": ".claude/CLAUDE.md",
        "description": "Claude Code 适配器"
    },
    "cursor": {
        "path": ".cursorrules",
        "description": "Cursor 适配器"
    },
    "windsurf": {
        "path": ".windsurfrules",
        "description": "Windsurf 适配器"
    },
    "copilot": {
        "path": ".github/copilot-instructions.md",
        "description": "GitHub Copilot 适配器"
    },
    "gemini": {
        "path": "GEMINI.md",
        "description": "Gemini CLI 适配器"
    },
    "kilo_cline": {
        "path": ".clinerules",
        "description": "Kilo Code (Cline) 规则文件"
    },
    "kilo_roo": {
        "path": ".roomodes",
        "description": "Kilo Code (Roo) 模式定义"
    }
}

def read_template():
    """读取模板文件"""
    template_path = Path(__file__).parent / "template.md"
    if not template_path.exists():
        raise FileNotFoundError(f"模板文件不存在: {template_path}")
    
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()

def generate_adapters():
    """生成所有适配器文件"""
    print("🚀 开始生成适配器文件...\n")
    
    # 读取模板
    template_content = read_template()
    print(f"✓ 读取模板: adapters/template.md ({len(template_content)} 字符)\n")
    
    # 生成每个平台的适配器
    generated = []
    for platform, config in PLATFORMS.items():
        target_path = PROJECT_ROOT / config["path"]
        
        # 确保目录存在
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 写入文件
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(template_content)
        
        generated.append((platform, config["path"], config["description"]))
        print(f"✓ {platform:15} → {config['path']:40} ({config['description']})")
    
    print(f"\n✅ 生成完成！共生成 {len(generated)} 个适配器文件")
    print(f"\n📝 维护说明:")
    print(f"   - 只修改 adapters/template.md")
    print(f"   - 运行 python adapters/generate.py 重新生成所有适配器")
    print(f"   - 所有平台内容自动同步")

def clean_adapters():
    """清理所有适配器文件（可选）"""
    print("🧹 清理适配器文件...\n")
    
    removed = []
    for platform, config in PLATFORMS.items():
        target_path = PROJECT_ROOT / config["path"]
        if target_path.exists():
            target_path.unlink()
            removed.append(config["path"])
            print(f"✓ 删除: {config['path']}")
    
    print(f"\n✅ 清理完成！共删除 {len(removed)} 个文件")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "clean":
        clean_adapters()
    else:
        generate_adapters()
