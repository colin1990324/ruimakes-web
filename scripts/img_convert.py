#!/usr/bin/env python3
"""
图片格式转换工具 - 将图片转换为 WebP 格式

用法：
    python3 img_convert.py check <目录>          # 检查目录中的图片是否符合规范
    python3 img_convert.py batch <源目录> <目标目录>  # 批量转换
    python3 img_convert.py convert <源文件> <目标目录>  # 单张转换

规范：
    - 格式：WebP（优先）
    - 尺寸：宽度上限 1920px（保持宽高比）
    - WebP 质量：80%，method=6
    - 有透明通道的图：保留 RGBA 模式
    - 照片（无透明）：白色背景合成后转 RGB WebP
"""

import os
import sys
from PIL import Image
from pathlib import Path

MAX_W = 1920
QUALITY = 80


def get_image_mode(path):
    """获取图片模式"""
    with Image.open(path) as im:
        return im.mode


def convert_to_webp(src_path, dst_dir, max_w=MAX_W, quality=QUALITY):
    """
    将单张图片转换为 WebP 格式

    Args:
        src_path: 源文件路径
        dst_dir: 目标目录
        max_w: 宽度上限
        quality: WebP 质量
    """
    src_path = Path(src_path)
    if not src_path.exists():
        print(f"  SKIP: 文件不存在 {src_path}")
        return False

    dst_name = src_path.stem + ".webp"
    dst_path = Path(dst_dir) / dst_name

    os.makedirs(dst_dir, exist_ok=True)

    orig_size = src_path.stat().st_size / 1024 / 1024
    print(f"  转换: {src_path.name} ({orig_size:.1f}MB)")

    with Image.open(src_path) as im:
        has_transparency = im.mode in ("RGBA", "LA", "P")
        is_photo = src_path.suffix.lower() in (".jpg", ".jpeg")

        if not has_transparency and is_photo:
            # 照片模式：RGB，直接缩放
            if im.mode != "RGB":
                im = im.convert("RGB")
        elif has_transparency:
            # 透明模式：保留通道（RGBA 或转 RGB）
            if im.mode == "P":
                im = im.convert("RGBA")
            elif im.mode == "LA":
                im = im.convert("RGBA")
        else:
            # 其他无透明图：RGB
            if im.mode != "RGB":
                im = im.convert("RGB")

        # 缩放
        if im.width > max_w:
            ratio = max_w / im.width
            new_h = int(im.height * ratio)
            im = im.resize((max_w, new_h), Image.LANCZOS)

        # 保存为 WebP
        im.save(dst_path, "WEBP", quality=quality, method=6)

    new_size = dst_path.stat().st_size / 1024 / 1024
    saved = orig_size - new_size
    print(f"  ✓ -> {dst_name} ({new_size:.1f}MB, 节省 {saved:.1f}MB)")
    return True


def batch_convert(src_dir, dst_dir, max_w=MAX_W, quality=QUALITY):
    """
    批量转换目录下所有图片

    Args:
        src_dir: 源目录
        dst_dir: 目标目录
        max_w: 宽度上限
        quality: WebP 质量
    """
    src_dir = Path(src_dir)
    if not src_dir.exists():
        print(f"错误: 源目录不存在 {src_dir}")
        return

    os.makedirs(dst_dir, exist_ok=True)

    exts = (".png", ".jpg", ".jpeg", ".PNG", ".JPG", ".JPEG")
    images = [f for f in src_dir.rglob("*") if f.suffix in exts and f.is_file()]

    if not images:
        print(f"未找到图片文件 in {src_dir}")
        return

    print(f"\n批量转换: {len(images)} 个文件\n")

    success = 0
    failed = 0
    for img_path in images:
        rel = img_path.relative_to(src_dir)
        sub_dst = Path(dst_dir) / rel.parent
        try:
            convert_to_webp(img_path, sub_dst, max_w, quality)
            success += 1
        except Exception as e:
            print(f"  错误: {e}")
            failed += 1

    print(f"\n完成: 成功 {success}, 失败 {failed}")
    print(f"输出目录: {dst_dir}")


def check_directory(dir_path, max_w=MAX_W):
    """
    检查目录中的图片是否符合规范

    报告：
    - 非 WebP/PNG/JPG 文件
    - 宽度超过 max_w 的文件
    - 建议转换的大文件
    """
    dir_path = Path(dir_path)
    if not dir_path.exists():
        print(f"错误: 目录不存在 {dir_path}")
        return

    exts = (".png", ".jpg", ".jpeg", ".PNG", ".JPG", ".JPEG", ".webp", ".WEBP")
    images = [f for f in dir_path.rglob("*") if f.suffix in exts and f.is_file()]

    if not images:
        print(f"未找到图片 in {dir_path}")
        return

    print(f"\n检查目录: {dir_path}")
    print(f"找到 {len(images)} 个图片文件\n")
    print(f"{'文件':<50} {'当前大小':<10} {'宽度':<8} {'建议'}")
    print("-" * 80)

    for img_path in sorted(images):
        try:
            with Image.open(img_path) as im:
                w, h = im.size
                size_mb = img_path.stat().st_size / 1024 / 1024
                issues = []

                if img_path.suffix.lower() not in (".webp",):
                    issues.append("转WebP")

                if w > max_w:
                    issues.append(f"缩放({w}→{max_w})")

                if size_mb > 1:
                    issues.append(f"压缩({size_mb:.0f}MB)")

                status = "✓" if not issues else "✗ " + ", ".join(issues)
                print(f"{str(img_path.name):<50} {size_mb:>6.1f}MB   {w:>5}px   {status}")
        except Exception as e:
            print(f"{img_path.name:<50} 错误: {e}")

    print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "check":
        if len(sys.argv) < 3:
            print("用法: python3 img_convert.py check <目录>")
            sys.exit(1)
        check_directory(sys.argv[2])

    elif cmd == "batch":
        if len(sys.argv) < 4:
            print("用法: python3 img_convert.py batch <源目录> <目标目录>")
            sys.exit(1)
        batch_convert(sys.argv[2], sys.argv[3])

    elif cmd == "convert":
        if len(sys.argv) < 4:
            print("用法: python3 img_convert.py convert <源文件> <目标目录>")
            sys.exit(1)
        convert_to_webp(sys.argv[2], sys.argv[3])

    else:
        print(f"未知命令: {cmd}")
        print(__doc__)
        sys.exit(1)
