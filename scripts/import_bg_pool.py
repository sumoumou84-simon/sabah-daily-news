#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
底图库导入与 16:9 居中裁切轻量压缩脚本
将本机桌面底图库扫描、裁切至 1200x675，以 quality=82 压缩为轻量 jpg
"""

import os
import sys
from pathlib import Path
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent.parent
REPO_BG_POOL_DIR = BASE_DIR / "assets" / "bg_pool"

CATEGORIES = ["sabah", "national", "sports", "general"]

def find_source_bg_pool() -> Path:
    """自动扫描本机桌面可能存在的 bg_pool 路径"""
    home = Path.home()
    candidates = [
        home / "OneDrive" / "Desktop" / "bg_pool",
        home / "OneDrive" / "桌面" / "bg_pool",
        home / "Desktop" / "bg_pool",
        home / "桌面" / "bg_pool",
        Path("C:/Users/simon/OneDrive/桌面/bg_pool"),
        Path("C:/Users/simon/OneDrive/Desktop/bg_pool"),
        Path("C:/Users/simon/Desktop/bg_pool"),
    ]
    for c in candidates:
        if c.exists() and c.is_dir():
            print(f"[*] 找到本机底图库源目录: {c}")
            return c
    raise FileNotFoundError("未能在本机桌面找到 bg_pool 目录！请确认路径。")

def crop_and_compress(src_file: Path, dst_file: Path, target_w=1200, target_h=675, quality=82):
    """等比居中裁切并缩放到目标尺寸，保存为 quality=82 的轻量 JPEG"""
    with Image.open(src_file) as img:
        # 转换为 RGB
        if img.mode != "RGB":
            img = img.convert("RGB")

        w, h = img.size
        target_ratio = target_w / target_h
        current_ratio = w / h

        if current_ratio > target_ratio:
            # 原图较宽：居中裁切左右两侧
            crop_w = int(round(h * target_ratio))
            crop_h = h
            left = (w - crop_w) // 2
            top = 0
        else:
            # 原图较高：居中裁切上下两侧
            crop_w = w
            crop_h = int(round(w / target_ratio))
            left = 0
            top = (h - crop_h) // 2

        right = left + crop_w
        bottom = top + crop_h
        cropped = img.crop((left, top, right, bottom))
        resized = cropped.resize((target_w, target_h), Image.Resampling.LANCZOS)

        dst_file.parent.mkdir(parents=True, exist_ok=True)
        resized.save(dst_file, "JPEG", quality=quality, optimize=True)

def import_all_backgrounds():
    src_root = find_source_bg_pool()
    total_count = 0
    total_bytes = 0

    for cat in CATEGORIES:
        src_cat_dir = src_root / cat
        dst_cat_dir = REPO_BG_POOL_DIR / cat
        dst_cat_dir.mkdir(parents=True, exist_ok=True)

        if not src_cat_dir.exists():
            print(f"[-] 警告: 分类目录不存在: {src_cat_dir}")
            continue

        images = [f for f in src_cat_dir.iterdir() if f.is_file() and f.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]]
        print(f"\n[+] 正在处理板块 [{cat}]：共 {len(images)} 张图片...")

        for img_path in images:
            # 统一以 .jpg 后缀保存
            dst_filename = f"{img_path.stem}.jpg"
            dst_file = dst_cat_dir / dst_filename
            crop_and_compress(img_path, dst_file, target_w=1200, target_h=675, quality=82)
            
            size_kb = dst_file.stat().st_size / 1024.0
            total_bytes += dst_file.stat().st_size
            total_count += 1
            print(f"    ✓ {img_path.name} -> {dst_filename} ({size_kb:.1f} KB)")

    avg_size_kb = (total_bytes / total_count / 1024.0) if total_count else 0
    print("\n" + "=" * 60)
    print(f"🎉 底图库导入与压缩完成！")
    print(f"• 总计处理图片: {total_count} 张")
    print(f"• 仓库底图库体积: {total_bytes / 1024.0 / 1024.0:.2f} MB")
    print(f"• 单张平均体积: {avg_size_kb:.1f} KB (目标 ~120KB，轻量秒开)")
    print(f"• 保存目标路径: {REPO_BG_POOL_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    import_all_backgrounds()
