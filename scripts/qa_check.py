#!/usr/bin/env python3
"""
QA 检查工具 - 本地页面、图片资源和 CI 构建检查

用法：
    python3 qa_check.py local <页面路径>          # 检查单页（如 workbench/105x52）
    python3 qa_check.py local --all               # 检查所有页面
    python3 qa_check.py images                    # 检查图片资源目录
    python3 qa_check.py ci <构建目录>             # CI 构建后检查

检查项目：
    - 图片引用路径是否正确（文件存在性）
    - 图片格式是否符合规范（WebP）
    - 大体积文件报告（及时发现需压缩的文件）
    - 页面引用缺失图片
"""

import os
import sys
from pathlib import Path
from PIL import Image

# 告警阈值
LARGE_FILE_THRESHOLD_MB = 1.0    # WebP > 1MB → 告警
FORBIDDEN_EXTENSIONS = {".bmp", ".tiff", ".tif", ".gif", ".tga"}
BASE_DIR = Path("/Users/myclaw/Documents/workspace/ruimakes-web")
PUBLIC_IMAGES = BASE_DIR / "public" / "images"
SRC_PAGES = BASE_DIR / "src" / "pages"


def check_image_file(file_path: Path) -> list:
    """
    检查单张图片，返回问题列表
    """
    issues = []
    size_mb = file_path.stat().st_size / 1024 / 1024

    # 1. 格式检查
    ext = file_path.suffix.lower()
    if ext in FORBIDDEN_EXTENSIONS:
        issues.append(f"禁止格式: {ext}")

    # 2. 大文件检查
    if ext == ".webp" and size_mb > LARGE_FILE_THRESHOLD_MB:
        issues.append(f"WebP 过大: {size_mb:.1f}MB (建议压缩)")

    # 3. 尺寸检查（可选，用 --check-size 开启）
    # if '--check-size' in sys.argv:
    #     with Image.open(file_path) as im:
    #         if im.width > 1920:
    #             issues.append(f"宽度超限: {im.width}px")

    return issues


def check_images_dir() -> dict:
    """
    检查 public/images/ 目录
    - 报告所有大体积文件
    - 标记禁止格式
    - 统计各格式数量和总体积
    """
    print("\n=== 图片资源检查 ===\n")

    exts = {".webp", ".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".gif", ".tga"}
    images = [f for f in PUBLIC_IMAGES.rglob("*") if f.suffix in exts and f.is_file()]

    if not images:
        print("未找到图片文件")
        return {}

    # 分类统计
    format_stats = {}
    total_size = 0
    large_files = []
    forbidden_files = []

    for img in images:
        size_mb = img.stat().st_size / 1024 / 1024
        ext = img.suffix.lower()
        total_size += size_mb

        if ext not in format_stats:
            format_stats[ext] = {"count": 0, "size": 0}
        format_stats[ext]["count"] += 1
        format_stats[ext]["size"] += size_mb

        issues = check_image_file(img)
        if issues:
            if "禁止格式" in issues[0]:
                forbidden_files.append((img, issues, size_mb))
            else:
                large_files.append((img, issues, size_mb))

    # 打印统计
    print(f"总文件数: {len(images)}")
    print(f"总大小: {total_size:.1f}MB\n")

    print("格式分布:")
    for ext, stat in sorted(format_stats.items(), key=lambda x: -x[1]["size"]):
        print(f"  {ext:<8} {stat['count']:>4} 个  {stat['size']:>7.1f}MB")

    # 禁止格式
    if forbidden_files:
        print(f"\n⛔ 禁止格式 ({len(forbidden_files)} 个):")
        for f, issues, size in forbidden_files:
            rel = f.relative_to(PUBLIC_IMAGES)
            print(f"  {rel} ({size:.1f}MB) — {', '.join(issues)}")

    # 大文件
    if large_files:
        print(f"\n⚠️  大体积文件 ({len(large_files)} 个，应 < {LARGE_FILE_THRESHOLD_MB}MB):")
        for f, issues, size in sorted(large_files, key=lambda x: -x[2]):
            rel = f.relative_to(PUBLIC_IMAGES)
            print(f"  {rel} ({size:.1f}MB) — {', '.join(issues)}")
    else:
        print(f"\n✅ 无大体积文件（全部 < {LARGE_FILE_THRESHOLD_MB}MB）")

    return {"large": large_files, "forbidden": forbidden_files, "total": total_size}


def find_referenced_images(page_path: Path) -> set:
    """
    从页面源码中提取所有引用的图片路径
    """
    if not page_path.exists():
        return set()

    content = page_path.read_text(encoding="utf-8")
    refs = set()

    # 匹配 src="/images/..." 或 src="images/..."
    import re
    for m in re.finditer(r'src=["\'](/?images/[^"\']+)["\']', content):
        refs.add(m.group(1).lstrip("/"))

    return refs


def check_local_page(page_identifier: str):
    """
    检查本地页面（相对于 src/pages/）
    page_identifier: 如 "workbench/105x52" 或 "toolstorage/joker"
    """
    page_path = SRC_PAGES / f"{page_identifier}.astro"
    if not page_path.exists():
        page_path = SRC_PAGES / page_identifier
        if not page_path.exists():
            print(f"页面不存在: {page_identifier}")
            return False

    print(f"\n=== 检查页面: {page_identifier} ===\n")

    refs = find_referenced_images(page_path)
    if not refs:
        print("未找到图片引用")
        return True

    print(f"找到 {len(refs)} 个图片引用\n")

    missing = []
    large_refs = []
    wrong_format = []

    for ref in sorted(refs):
        # ref 格式: /images/storage/xxx.webp 或 images/storage/xxx.webp
        # 去掉前导 /，去掉重复的 images/ 前缀
        clean_ref = ref.lstrip("/")
        if clean_ref.startswith("images/"):
            clean_ref = clean_ref[len("images/"):]

        file_path = PUBLIC_IMAGES / clean_ref
        if not file_path.exists():
            # 尝试找同名的 webp
            webp_path = PUBLIC_IMAGES / (clean_ref.rsplit(".", 1)[0] + ".webp")
            if webp_path.exists():
                continue  # 正常，已转换为 webp
            missing.append((ref, file_path))
        else:
            # 文件存在，检查体积
            size_mb = file_path.stat().st_size / 1024 / 1024
            ext = file_path.suffix.lower()

            if ext not in (".webp",):
                wrong_format.append((ref, ext, size_mb))
            elif size_mb > LARGE_FILE_THRESHOLD_MB:
                large_refs.append((ref, size_mb))

    has_issue = False

    if missing:
        print(f"⛔ 缺失文件 ({len(missing)} 个):")
        for ref, path in missing:
            print(f"  /{ref}")
        has_issue = True

    if wrong_format:
        print(f"⛔ 非 WebP 格式 ({len(wrong_format)} 个，应转 WebP):")
        for ref, ext, size in wrong_format:
            print(f"  /{ref} ({ext}, {size:.1f}MB)")
        has_issue = True

    if large_refs:
        print(f"⚠️  引用了大文件 ({len(large_refs)} 个):")
        for ref, size in large_refs:
            print(f"  /{ref} ({size:.1f}MB)")
        has_issue = True

    if not has_issue:
        print("✅ 全部通过")

    return not has_issue


def check_local_all():
    """
    检查所有页面
    """
    print("\n=== 检查所有页面 ===\n")

    pages = []
    for pattern in ["workbench/*.astro", "toolstorage/*.astro"]:
        pages.extend(SRC_PAGES.glob(pattern))

    results = {}
    for page in sorted(pages):
        identifier = str(page.relative_to(SRC_PAGES)).replace(".astro", "")
        ok = check_local_page(identifier)
        results[identifier] = ok

    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed

    print(f"\n=== 汇总 ===")
    print(f"总页面: {total}")
    print(f"通过: {passed}")
    print(f"失败: {failed}")

    if failed > 0:
        print("\n失败页面:")
        for page, ok in results.items():
            if not ok:
                print(f"  - {page}")


def check_ci(dist_dir: Path):
    """
    CI 构建后检查 dist/ 目录
    - 检查 index.html 是否存在
    - 检查 CNAME 是否存在
    - 检查图片资源
    """
    print("\n=== CI 构建检查 ===\n")

    dist_dir = Path(dist_dir)
    issues = []

    # 1. index.html
    index = dist_dir / "index.html"
    if not index.exists():
        issues.append("index.html 不存在")
    else:
        print("✅ index.html 存在")

    # 2. CNAME（用于 GitHub Pages 自定义域名）
    cname = dist_dir / "CNAME"
    if not cname.exists():
        issues.append("CNAME 缺失（GitHub Pages 自定义域名需要）")
    else:
        print("✅ CNAME 存在")

    # 3. 图片大小
    if PUBLIC_IMAGES.exists():
        print("\n图片目录大小:")
        import subprocess
        result = subprocess.run(["du", "-sh", str(PUBLIC_IMAGES)], capture_output=True, text=True)
        print(f"  {result.stdout.strip()}")

        # 大文件检查
        result = check_images_dir()
        if result.get("large") or result.get("forbidden"):
            issues.append("图片目录存在需要处理的文件")

    if issues:
        print("\n⛔ CI 检查失败:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("\n✅ CI 检查全部通过")
        return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "local":
        if len(sys.argv) < 3:
            print("用法: python3 qa_check.py local <页面> 或 python3 qa_check.py local --all")
            sys.exit(1)
        page = sys.argv[2]
        if page == "--all":
            check_local_all()
        else:
            check_local_page(page)

    elif cmd == "images":
        check_images_dir()

    elif cmd == "ci":
        if len(sys.argv) < 3:
            print("用法: python3 qa_check.py ci <dist目录>")
            sys.exit(1)
        ok = check_ci(sys.argv[2])
        sys.exit(0 if ok else 1)

    else:
        print(f"未知命令: {cmd}")
        print(__doc__)
        sys.exit(1)
