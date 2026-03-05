#!/usr/bin/env python3
"""
Linux网络稳定性监控工具
支持Ping、路由追踪、带宽测试，并提供可视化图表
"""

import os
import time
import json
import argparse
import csv
import subprocess
import threading
from datetime import datetime
from statistics import mean, stdev
from ping3 import ping
import matplotlib

matplotlib.use('Agg')  # 无图形界面模式
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# ==================== 默认配置 ====================
DEFAULT_CONFIG = {
    "target": "114.114.114.114",        # 监测目标IP或域名
    "ping_interval": 60,                 # Ping测试间隔（秒）
    "bandwidth_interval": 3600,           # 带宽测试间隔（秒）
    "loss_threshold": 10,                 # 触发路由追踪的丢包率阈值（%）
    "delay_threshold": 100,               # 触发路由追踪的延迟阈值（ms）
    "ping_count": 4,                       # 每次Ping发送的包数量
    "timeout": 2,                          # Ping超时时间（秒）
    "output_dir": "./network_monitor",      # 输出目录
    "duration": 0,                          # 运行时长（0表示无限）
    "plot": False,                          # 仅生成图表并退出
    "plot_last_days": 1,                    # 图表显示最近几天的数据
    "config_file": ""                        # 配置文件路径（JSON）
}


# ==================== 工具函数 ====================
def ensure_dir(path):
    """确保目录存在"""
    os.makedirs(path, exist_ok=True)


def timestamp_str():
    """返回当前时间字符串（精确到秒）"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def parse_time(t_str):
    """将时间字符串解析为datetime对象"""
    return datetime.strptime(t_str, "%Y-%m-%d %H:%M:%S")


def load_config(args):
    """加载配置：先读文件，再用命令行参数覆盖"""
    config = DEFAULT_CONFIG.copy()
    if args.config_file:
        with open(args.config_file, 'r') as f:
            file_config = json.load(f)
            config.update(file_config)
    # 命令行参数覆盖（仅当显式提供时）
    for key in config.keys():
        if hasattr(args, key) and getattr(args, key) is not None:
            config[key] = getattr(args, key)
    return config


# ==================== Ping测试 ====================
def ping_test(target, count=4, timeout=2):
    """
    对目标执行多次Ping，返回统计结果
    返回: (丢包率, 最小RTT, 平均RTT, 最大RTT, 抖动, 各包延迟列表)
    """
    rtts = []
    lost = 0
    for i in range(count):
        try:
            rtt = ping(target, timeout=timeout, unit='ms')
            if rtt is None:
                lost += 1
            else:
                rtts.append(rtt)
        except Exception as e:
            print(f"Ping异常: {e}")
            lost += 1
        time.sleep(0.1)  # 避免包发送过快

    total = count
    loss_rate = (lost / total) * 100
    if rtts:
        min_rtt = min(rtts)
        max_rtt = max(rtts)
        avg_rtt = mean(rtts)
        jitter = stdev(rtts) if len(rtts) > 1 else 0.0
    else:
        min_rtt = max_rtt = avg_rtt = jitter = 0.0
    return loss_rate, min_rtt, avg_rtt, max_rtt, jitter, rtts


# ==================== 路由追踪 ====================
def traceroute(target):
    """
    执行系统traceroute命令，解析结果
    返回: (hop数, 每跳详情列表)
    每跳详情: (序号, IP, 平均延迟(ms)或'*')
    """
    try:
        # 使用 -n 避免DNS解析，-w 2 设置超时2秒，-q 1 每跳发送一个包
        cmd = ["traceroute", "-n", "-w", "2", "-q", "1", target]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        output = result.stdout
    except Exception as e:
        print(f"traceroute执行失败: {e}")
        return 0, []

    hops = []
    lines = output.strip().split('\n')[1:]  # 跳过第一行
    for line in lines:
        parts = line.split()
        if len(parts) < 2:
            continue
        try:
            hop_num = int(parts[0])
            ip = parts[1] if parts[1] != '*' else None
            # 尝试提取延迟
            delay = None
            for p in parts[2:]:
                if p.endswith("ms"):
                    try:
                        delay = float(p[:-2])
                        break
                    except:
                        pass
            hops.append((hop_num, ip, delay))
        except:
            continue
    return len(hops), hops


# ==================== 带宽测试 ====================
def bandwidth_test():
    """
    使用speedtest-cli进行带宽测试
    返回: (下载速度Mbps, 上传速度Mbps, ping_ms)
    """
    try:
        import speedtest
        st = speedtest.Speedtest()
        st.get_best_server()
        ping_ms = st.results.ping
        download = st.download() / 1_000_000  # 转换为Mbps
        upload = st.upload() / 1_000_000
        return download, upload, ping_ms
    except Exception as e:
        print(f"带宽测试失败: {e}")
        return None, None, None


# ==================== 数据记录 ====================
def record_ping(csv_writer, timestamp, target, loss_rate, min_rtt, avg_rtt, max_rtt, jitter, rtts):
    """记录Ping结果到CSV"""
    row = [timestamp, target, loss_rate, min_rtt, avg_rtt, max_rtt, jitter, str(rtts)]
    csv_writer.writerow(row)


def record_traceroute(csv_writer, timestamp, target, hops):
    """记录路由追踪结果到CSV（hops序列化为JSON）"""
    hops_str = json.dumps(hops)
    row = [timestamp, target, hops_str]
    csv_writer.writerow(row)


def record_bandwidth(csv_writer, timestamp, download, upload, ping_ms):
    """记录带宽测试结果到CSV"""
    row = [timestamp, download, upload, ping_ms]
    csv_writer.writerow(row)


# ==================== 可视化 ====================
def generate_plots(config):
    """
    读取最近的数据并生成图表
    图表包含：
        - 延迟趋势（平均RTT）
        - 丢包率
        - 带宽（下载/上传）
    """
    output_dir = config['output_dir']
    ping_file = os.path.join(output_dir, "ping.csv")
    bandwidth_file = os.path.join(output_dir, "bandwidth.csv")
    plot_file = os.path.join(output_dir, f"network_summary_{datetime.now().strftime('%Y%m%d')}.png")

    if not os.path.exists(ping_file):
        print("没有找到ping数据文件，无法生成图表。")
        return

    # 读取Ping数据
    ping_times = []
    ping_avg = []
    ping_loss = []
    with open(ping_file, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)  # 跳过表头
        for row in reader:
            if len(row) < 6:
                continue
            ts = parse_time(row[0])
            ping_times.append(ts)
            ping_avg.append(float(row[4]))   # avg_rtt
            ping_loss.append(float(row[2]))   # loss_rate

    # 读取带宽数据
    bw_times = []
    bw_down = []
    bw_up = []
    if os.path.exists(bandwidth_file):
        with open(bandwidth_file, 'r') as f:
            reader = csv.reader(f)
            header = next(reader)
            for row in reader:
                if len(row) < 4:
                    continue
                ts = parse_time(row[0])
                bw_times.append(ts)
                bw_down.append(float(row[1]) if row[1] else 0)
                bw_up.append(float(row[2]) if row[2] else 0)

    # 创建图表
    fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
    fig.suptitle(f'网络监控报告 - 目标 {config["target"]}', fontsize=14)

    # 延迟图
    ax1 = axes[0]
    ax1.plot(ping_times, ping_avg, 'b-', label='平均延迟 (ms)')
    ax1.set_ylabel('延迟 (ms)')
    ax1.legend(loc='upper left')
    ax1.grid(True)

    # 丢包率图
    ax2 = axes[1]
    ax2.plot(ping_times, ping_loss, 'r-', label='丢包率 (%)')
    ax2.set_ylabel('丢包率 (%)')
    ax2.set_ylim(0, 100)
    ax2.legend(loc='upper left')
    ax2.grid(True)

    # 带宽图
    ax3 = axes[2]
    if bw_times:
        ax3.plot(bw_times, bw_down, 'g-', label='下载 (Mbps)')
        ax3.plot(bw_times, bw_up, 'orange', label='上传 (Mbps)')
        ax3.set_ylabel('带宽 (Mbps)')
        ax3.legend(loc='upper left')
    else:
        ax3.text(0.5, 0.5, '无带宽数据', ha='center', va='center', transform=ax3.transAxes)
    ax3.grid(True)

    # 时间轴格式化
    for ax in axes:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=30)

    plt.tight_layout()
    plt.savefig(plot_file, dpi=150)
    print(f"图表已保存至: {plot_file}")
    plt.close()


# ==================== 主监控循环 ====================
def monitor_loop(config):
    """主监控循环，执行周期性测试"""
    output_dir = config['output_dir']
    ensure_dir(output_dir)

    # 准备CSV文件
    ping_csv = open(os.path.join(output_dir, "ping.csv"), 'a', newline='')
    traceroute_csv = open(os.path.join(output_dir, "traceroute.csv"), 'a', newline='')
    bandwidth_csv = open(os.path.join(output_dir, "bandwidth.csv"), 'a', newline='')

    ping_writer = csv.writer(ping_csv)
    traceroute_writer = csv.writer(traceroute_csv)
    bandwidth_writer = csv.writer(bandwidth_csv)

    # 写入表头（如果文件为空）
    if ping_csv.tell() == 0:
        ping_writer.writerow(["timestamp", "target", "loss_rate", "min_rtt", "avg_rtt", "max_rtt", "jitter", "rtt_list"])
    if traceroute_csv.tell() == 0:
        traceroute_writer.writerow(["timestamp", "target", "hops_json"])
    if bandwidth_csv.tell() == 0:
        bandwidth_writer.writerow(["timestamp", "download_mbps", "upload_mbps", "ping_ms"])

    last_bandwidth_time = 0
    start_time = time.time()
    duration = config['duration']

    print(f"开始监控，目标: {config['target']}")
    print(f"Ping间隔: {config['ping_interval']}秒，带宽测试间隔: {config['bandwidth_interval']}秒")
    print(f"输出目录: {output_dir}")
    print("按 Ctrl+C 停止...\n")

    try:
        while True:
            # 检查运行时长
            if duration > 0 and (time.time() - start_time) > duration:
                print("达到设定运行时长，监控结束。")
                break

            now = time.time()
            ts_str = timestamp_str()

            # 1. 执行Ping测试
            loss_rate, min_rtt, avg_rtt, max_rtt, jitter, rtts = ping_test(
                config['target'], config['ping_count'], config['timeout'])
            record_ping(ping_writer, ts_str, config['target'], loss_rate, min_rtt, avg_rtt, max_rtt, jitter, rtts)
            ping_csv.flush()
            print(f"[{ts_str}] Ping: 丢包率={loss_rate:.1f}%, 平均延迟={avg_rtt:.2f}ms")

            # 2. 判断是否需要路由追踪
            if loss_rate >= config['loss_threshold'] or avg_rtt >= config['delay_threshold']:
                print(f"  触发路由追踪 (丢包率>{config['loss_threshold']}% 或 延迟>{config['delay_threshold']}ms)")
                hop_count, hops = traceroute(config['target'])
                record_traceroute(traceroute_writer, ts_str, config['target'], hops)
                traceroute_csv.flush()
                # 简单打印问题节点
                for hop in hops:
                    if hop[2] is None or hop[2] > 200:
                        print(f"    可能问题节点: 跳数{hop[0]}, IP={hop[1]}, 延迟={hop[2]}ms")

            # 3. 带宽测试（按间隔执行）
            if now - last_bandwidth_time >= config['bandwidth_interval']:
                print(f"[{ts_str}] 开始带宽测试...")
                down, up, ping_ms = bandwidth_test()
                if down is not None:
                    record_bandwidth(bandwidth_writer, ts_str, down, up, ping_ms)
                    bandwidth_csv.flush()
                    print(f"  下载: {down:.2f} Mbps, 上传: {up:.2f} Mbps, Ping: {ping_ms:.2f} ms")
                else:
                    print("  带宽测试失败")
                last_bandwidth_time = now

            # 等待下一个Ping周期
            time.sleep(config['ping_interval'])

    except KeyboardInterrupt:
        print("\n监控被用户中断。")
    finally:
        ping_csv.close()
        traceroute_csv.close()
        bandwidth_csv.close()
        print("所有文件已关闭。")


# ==================== 主入口 ====================
def main():
    parser = argparse.ArgumentParser(description="Linux网络稳定性监控工具")
    parser.add_argument("--target", help="监测目标IP或域名")
    parser.add_argument("--ping-interval", type=int, help="Ping测试间隔（秒）")
    parser.add_argument("--bandwidth-interval", type=int, help="带宽测试间隔（秒）")
    parser.add_argument("--loss-threshold", type=float, help="触发路由追踪的丢包率阈值（%）")
    parser.add_argument("--delay-threshold", type=int, help="触发路由追踪的延迟阈值（ms）")
    parser.add_argument("--ping-count", type=int, help="每次Ping发送的包数量")
    parser.add_argument("--timeout", type=int, help="Ping超时时间（秒）")
    parser.add_argument("--output-dir", help="输出目录")
    parser.add_argument("--duration", type=int, help="运行时长（秒，0为无限）")
    parser.add_argument("--plot", action="store_true", help="仅根据现有数据生成图表并退出")
    parser.add_argument("--plot-last-days", type=int, help="图表显示最近几天的数据")
    parser.add_argument("--config-file", help="配置文件路径（JSON）")

    args = parser.parse_args()
    config = load_config(args)

    if config['plot']:
        generate_plots(config)
    else:
        monitor_loop(config)


if __name__ == "__main__":
    main()
