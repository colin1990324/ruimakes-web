#!/usr/bin/env python3
"""质数表生成器(埃拉托斯特尼筛法)
输出(public/games/prime-viz/data/):
  primes_1e4.txt  1万以内,逗号分隔文本(游戏可直接嵌入)
  primes_1e5.bin  10万以内,uint32 小端二进制
  primes_1e6.bin  100万以内,uint32 小端二进制
  primes_1e7.bin  1000万以内,uint32 小端二进制
二进制文件游戏侧统一 fetch+DataView(小端)读取,按索引访问任意质数。
"""
import array, os, sys, time

def sieve(n):
    """返回 n 以内所有质数列表"""
    is_prime = bytearray(b'\x01') * (n + 1)
    is_prime[0] = is_prime[1] = 0
    i = 2
    while i * i <= n:
        if is_prime[i]:
            is_prime[i*i : n+1 : i] = b'\x00' * (((n - i*i) // i) + 1)
        i += 1
    return [i for i in range(2, n + 1) if is_prime[i]]

def write_bin(primes, path):
    a = array.array('I', primes)  # unsigned int,本机小端
    if sys.byteorder != 'little':
        a.byteswap()
    with open(path, 'wb') as f:
        a.tofile(f)

def main():
    base = os.path.join(os.path.dirname(__file__), '..', 'public', 'games', 'prime-viz', 'data')
    os.makedirs(base, exist_ok=True)

    # 1万以内(文本,逗号分隔,可嵌入游戏)
    t0 = time.time()
    p1e4 = sieve(10_000)
    txt_path = os.path.join(base, 'primes_1e4.txt')
    with open(txt_path, 'w') as f:
        f.write(','.join(map(str, p1e4)))
    print(f'1e4: {len(p1e4)} 个, 最大 {p1e4[-1]}, 文本 {os.path.getsize(txt_path)}B, {time.time()-t0:.2f}s')

    # 10万 / 100万 / 1000万(二进制 uint32 小端)
    for n, tag in [(100_000,'1e5'), (1_000_000,'1e6'), (10_000_000,'1e7')]:
        t1 = time.time()
        p = sieve(n)
        bin_path = os.path.join(base, f'primes_{tag}.bin')
        write_bin(p, bin_path)
        print(f'{tag}: {len(p)} 个, 最大 {p[-1]}, 二进制 {os.path.getsize(bin_path)/1e6:.2f}MB, {time.time()-t1:.2f}s')

    # 抽查
    assert p1e4[:6] == [2,3,5,7,11,13], p1e4[:6]
    assert p1e4[-1] == 9973, p1e4[-1]
    print('抽查通过: 开头 2,3,5,7,11,13 / 1万内最大 9973 / 总数 1229,9592,78498,664579')

if __name__ == '__main__':
    main()
