#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""爬取三国杀官网武将头像(https://www.sanguosha.cn/hero-list.html)

用法:
  python3 scripts/crawl_sanguosha_avatars.py              # 下载 20 将头像 → public/games/sanguo-monopoly/img/ (WebP 84x84)
  python3 scripts/crawl_sanguosha_avatars.py --all        # 下载页面全部 579 名武将头像(仅转换,不入游戏目录)

页面结构(2026-09 实测,可能变动):
  hero-list.html 为服务端渲染 HTML,每个英雄:
    <a href="https://www.sanguosha.cn/pc/hero-detail-{id}.html">
      <div class="general-img"><img src="https://www.sanguosha.cn/storage/uploads/images/pic_index/{n}.jpg" alt="名字"/></div>
      名字
    </a>
  - hero-list 页内头像为 84x84 缩略图(轻量,适合 web 游戏卡片)
  - hero-detail-{id}.html 页内 <img src=".../skins/{n}.jpg"> 为高清原画(~300KB,web 游戏不需要)
  - 每位武将通常 2 个版本(标准/界),取页面中第一个

输出: public/games/sanguo-monopoly/img/{key}.webp (84x84 WebP q80, 1-3KB)
依赖: Pillow
"""
import json, os, re, sys, glob, urllib.request

LIST_URL = 'https://www.sanguosha.cn/hero-list.html'
UA = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0'}
# 武将名 → 游戏内 key(设计文档 20 将;新增武将时在此追加)
GENERAL_KEYS = {
    '曹操': 'caocao', '孙坚': 'sunjian', '司马懿': 'simayi', '董卓': 'dongzhuo',
    '刘备': 'liubei', '孙权': 'sunquan', '刘表': 'liubiao', '袁绍': 'yuanshao',
    '关羽': 'guanyu', '张飞': 'zhangfei', '吕布': 'lbu', '赵云': 'zhaoyun',
    '马超': 'machao', '诸葛亮': 'zhugeliang', '周瑜': 'zhouyu', '陆逊': 'luxun',
    '郭嘉': 'guojia', '荀彧': 'xunyu', '庞统': 'pangtong', '黄月英': 'huangyueying',
}

def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=30).read()

def parse_list(html):
    """返回 {名字: (hero_id, 头像src)}"""
    pat = re.compile(r'hero-detail-(\d+)\.html">\s*<div class="general-img"><img src="([^"]+)" alt="([^"]+)"')
    out = {}
    for m in pat.finditer(html):
        hid, src, name = int(m.group(1)), m.group(2), m.group(3)
        out.setdefault(name, (hid, src))
    return out

def main():
    dst = os.path.expanduser('~/Documents/workspace/ruimakes-web/public/games/sanguo-monopoly/img')
    os.makedirs(dst, exist_ok=True)
    html = fetch(LIST_URL).decode('utf-8', 'ignore')
    heroes = parse_list(html)
    print(f'页面共 {len(heroes)} 名武将')
    all_flag = '--all' in sys.argv
    wanted = list(GENERAL_KEYS.items()) if not all_flag else [(n, n) for n in heroes]
    for name, key in wanted:
        if name not in heroes:
            print(f'跳过(未找到): {name}')
            continue
        hid, src = heroes[name]
        try:
            data = fetch(src)
        except Exception as e:
            print(f'下载失败 {name}: {e}')
            continue
        # 转 WebP 84x84(与原缩略图等大;PIL 依赖)
        from PIL import Image
        import io
        im = Image.open(io.BytesIO(data)).convert('RGB').resize((84, 84), Image.LANCZOS)
        out = os.path.join(dst, key + '.webp')
        im.save(out, 'WEBP', quality=80, method=6)
        print(f'{name}(id {hid}) -> {os.path.basename(out)} {os.path.getsize(out)}B')

if __name__ == '__main__':
    main()
