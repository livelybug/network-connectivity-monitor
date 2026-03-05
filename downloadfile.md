
import time
import requests

def test_download_speed(url, chunk_size=1024*256, duration=10):
    """
    url: 一个可直接下载的大文件/测试接口（建议放在国内）
    duration: 测试持续秒数，默认 10 秒
    """
    start = time.time()
    downloaded = 0

    with requests.get(url, stream=True, timeout=10) as r:
        r.raise_for_status()
        for chunk in r.iter_content(chunk_size=chunk_size):
            if not chunk:
                break
            downloaded += len(chunk)
            now = time.time()
            if now - start >= duration:
                break

    elapsed = time.time() - start
    # bytes -> Mbps
    mbps = (downloaded * 8) / (elapsed * 1_000_000)
    return mbps, elapsed, downloaded

if __name__ == "__main__":
    url = "https://你的服务器/large_test_file.bin"   # 换成你内外网都能访问的国内地址
    mbps, elapsed, downloaded = test_download_speed(url)
    print(f"下载耗时: {elapsed:.2f} s")
    print(f"下载数据: {downloaded/1024/1024:.2f} MB")
    print(f"下载速度: {mbps:.2f} Mbps")

url = "https://wirelesscdn-download.xuexi.cn/publish/xuexi_android/latest/xuexi_android_10002068.apk"
mbps, elapsed, downloaded = test_download_speed(url, duration=10)
print(f"下载速度: {mbps:.2f} Mbps")  # 结果会很快出来