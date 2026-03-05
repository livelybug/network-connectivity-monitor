import os
import time
import requests

def test_upload_speed(url, size_mb=10):
    """
    url: 接受 POST 上传的接口（如你自己写的 Flask/Django/FastAPI 上传接口）
    size_mb: 要上传的测试数据大小（MB）
    """
    data_size = size_mb * 1024 * 1024
    # 生成指定大小的随机字节
    data = os.urandom(data_size)

    start = time.time()
    r = requests.post(url, data=data, timeout=30)
    r.raise_for_status()
    elapsed = time.time() - start

    mbps = (data_size * 8) / (elapsed * 1_000_000)
    return mbps, elapsed, data_size

if __name__ == "__main__":
    url = "https://你的服务器/upload"  # 换成你自己的上传接口
    mbps, elapsed, uploaded = test_upload_speed(url, size_mb=10)
    print(f"上传耗时: {elapsed:.2f} s")
    print(f"上传数据: {uploaded/1024/1024:.2f} MB")
    print(f"上传速度: {mbps:.2f} Mbps")