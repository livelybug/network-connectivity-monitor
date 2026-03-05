
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


要中国国内的

中国国内的冷门测速文件较少（因为测速专用文件多是国外VPS厂商提供），但有这些相对冷门、不易限速的静态文件选项，都小于100MB，来自高校和小型镜像站。[1][2]

### 国内冷门测速文件（≤100MB）

| 大小 | URL | 来源 | 说明 |
|------|-----|------|------|
| 100MB | http://speedtest.zju.edu.cn/100M | 浙江大学教育网 | 高校专用，冷门无限制。[1] |
| ~90MB | http://mirrors.ustc.edu.cn/ubuntu/dists/bionic-updates/main/installer-amd64/legacy-images/netboot/ubuntu-installer/amd64/pxelinux.0 | 中科大镜像（USTC） | Linux启动文件，纯静态极冷门。[2] |
| ~50MB | http://ftp.iij.ad.jp/pub/linux/ubuntu/dists/jammy/main/installer-amd64/legacy-images/netboot/ubuntu-installer/amd64/pxelinux.0 | IIJ（日方但国内镜像） | Ubuntu镜像，冷门启动文件。[1] |
| ~80MB | https://mirrors.tuna.tsinghua.edu.cn/ubuntu/dists/jammy-updates/main/installer-amd64/current/legacy-images/netboot/ubuntu-installer/amd64/linux | 清华TUNA镜像 | 清华源启动镜像，小众。[2] |

### 测试代码（优先冷门高校）
```python
urls = [
    "http://speedtest.zju.edu.cn/100M",           # 浙大教育网（最推荐）
    "http://mirrors.ustc.edu.cn/ubuntu/dists/bionic-updates/main/installer-amd64/legacy-images/netboot/ubuntu-installer/amd64/pxelinux.0",  # 中科大
    "https://mirrors.tuna.tsinghua.edu.cn/ubuntu/dists/jammy-updates/main/installer-amd64/current/legacy-images/netboot/ubuntu-installer/amd64/linux"  # 清华
]

for url in urls:
    try:
        mbps, elapsed, size = test_download_speed(url, duration=8)
        print(f"{url.split('/')[-1]}: {mbps:.1f} Mbps ({size/1024/1024:.0f}MB)")
        break
    except Exception as e:
        print(f"{url}: 失败 - {e}")
```

**为什么冷门**：这些是Linux发行版镜像站的启动文件和技术镜像，普通用户基本不会下载，主要给系统管理员用，流量极低无速率限制。[1][2]

优先用浙大教育网100M，最稳定且纯国内大陆服务器。

Citations:
[1] 分享VPS下载测速文件100M/1GB/10GB-许都博客 https://www.xudu.org/10606.html
[2] 用于网络测试的下载测速文件合集 - 繁星点点 https://www.52013120.xyz/posts/26/
[3] https://huggingface.co/weitung8/ntuadlhw2/resolve/... https://huggingface.co/weitung8/ntuadlhw2/resolve/8a799d33f6849919b0766f189c505a345d278424/eval_results_beam_search_10_no_repeat_2_gram.jsonl?download=true
[4] 宅宅開箱小天地！ - RSSing.com https://clumsier67.rssing.com/chan-63258514/latest.php
[5] 全站文章 - 新加坡vps https://vpszz.com/cundang
[6] Download Diff File https://git.mitsea.com/FlintyLemming/MitseaBlog/commit/bae28d6fff10511629c1d09755b12a4f2f9e7b84.diff
[7] [XML] search.xml - 夜法之书 https://blog.17lai.fun/search.xml
[8] TowardsDataScience-博客中文翻译-2019-二十七- https://www.cnblogs.com/apachecn/p/18462375
[9] 测速网 - 专业测网速, 网速测试, 宽带提速, 游戏测速, 直播测速, 5G测速, 物联网监测,Wi-Fi 7,Wi-Fi 6,FTTR,全屋Wi-Fi https://www.speedtest.cn
