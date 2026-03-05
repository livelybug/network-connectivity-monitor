     以下是一个功能完善的Python网络监控脚本，专为Linux系统设计，具备高度可配置性，能够记录详细的网络状态并提供可视化图表。代码集成了Ping测试、路由追踪（定位故障点）、带宽测试，并将结果保存为CSV文件，同时生成趋势图供电信技术人员分析。

### 主要功能
- **Ping测试**：周期性检测目标IP的延迟、丢包率、抖动。
- **自动路由追踪**：当丢包率或延迟超过阈值时，自动执行traceroute，记录路径中各节点的响应情况，帮助定位故障位置。
- **带宽测试**：定时运行速度测试（使用speedtest-cli），记录下载/上传速度及延迟。
- **数据存储**：按类型分别保存为CSV文件（ping、traceroute、带宽），便于后续分析。
- **可视化**：生成包含延迟趋势、丢包率、带宽变化的组合图表，直观展示网络稳定性。
- **可配置性**：通过命令行参数或修改脚本开头的配置字典，可灵活调整监测目标、时间间隔、阈值等。

---

### 环境准备
在Linux系统上运行前，请确保安装以下依赖：
```bash
# 安装系统工具
sudo apt update && sudo apt install traceroute  # Debian/Ubuntu
# 或 sudo yum install traceroute               # CentOS/RHEL
```

这个错误是因为你的Linux系统（通常是Debian/Ubuntu系列）启用了**PEP 668**保护机制，旨在防止`pip`命令破坏系统自带的Python环境。系统建议你使用虚拟环境或系统包管理器来安装Python包。

针对你写网络监控脚本的需求，有以下三种推荐的解决方案，按推荐程度排序：

---

### 使用Python虚拟环境（推荐，最灵活）

1.  **安装`venv`模块**（如果尚未安装）：
    ```bash
    sudo apt update
    sudo apt install python3-venv python3-full
    ```
    *参考：*

2.  **创建虚拟环境**（在你的监控脚本目录下）：
    ```bash
    cd /path/to/your/script  # 进入你的脚本目录
    python3 -m venv .venv
    ```
    这会在当前目录生成一个名为 `.venv` 的隐藏文件夹，包含独立的Python解释器和包管理工具。

3.  **激活虚拟环境**：
    ```bash
    source .venv/bin/activate
    ```
    激活后，终端提示符前会出现 `(.venv)` 标记，表示已进入虚拟环境。

4.  **安装所需的包**（现在可以正常使用`pip`）：
    ```bash
    pip install ping3 speedtest-cli matplotlib
    ```

---


> **注意**：ping3需要发送ICMP包，Linux普通用户可能权限不足。建议使用`sudo`运行脚本，或为Python解释器赋予`cap_net_raw`能力：
> ```bash
> sudo setcap cap_net_raw+ep $(which python3)
> ```

---

---

### 使用方法

#### 1. 直接运行（默认配置）
```bash
sudo python3 network_monitor.py
```
> 默认监测 `114.114.114.114`，每分钟Ping一次，每小时测速一次，输出到 `./network_monitor/` 目录。

#### 2. 自定义参数
例如：监测 `8.8.8.8`，Ping间隔30秒，带宽测试间隔2小时，丢包率超过5%即触发路由追踪：
```bash
sudo python3 network_monitor.py --target 8.8.8.8 --ping-interval 30 --bandwidth-interval 7200 --loss-threshold 5
```

#### 3. 使用配置文件
创建 `config.json`：
```json
{
    "target": "114.114.114.114",        # 监测目标（电信DNS）
    "ping_interval": 60,                 # 每分钟一次
    "bandwidth_interval": 3600,           # 每小时测速一次
    "loss_threshold": 8,                  # 丢包率>8%触发路由追踪
    "delay_threshold": 80,                # 延迟>80ms触发路由追踪
    "ping_count": 4,                       # 每次发送4个包
    "timeout": 2,                          # 超时2秒
    "output_dir": "./network_monitor",
    "duration": 0
}
```
运行：
```bash
sudo python3 network_monitor.py --config-file config.json
```

#### 4. 生成可视化图表
基于已采集的数据生成图表（无需持续监控）：
```bash
python3 network_monitor.py --plot --output-dir ./network_monitor
```
图表将保存为 `network_summary_YYYYMMDD.png`。

#### 5. 查看实时输出
脚本运行时会持续打印状态，包括Ping结果、触发路由追踪时的提示以及带宽测试结果。

#### 6.  **退出虚拟环境**（当不再需要时）：
    ```bash
    deactivate
    ```

---

### 输出文件说明
在输出目录下生成三个CSV文件：
- **ping.csv**：包含每次Ping的时间戳、丢包率、延迟统计等。
- **traceroute.csv**：记录触发时的路由追踪结果，`hops_json`字段存储每跳的详情（序号、IP、延迟）。
- **bandwidth.csv**：带宽测试记录（下载/上传速度、测速时的Ping值）。

### 故障定位
当丢包率或延迟超过阈值时，脚本会自动运行traceroute，并在控制台打印可能的问题节点（延迟>200ms或超时的跳）。您可以通过查看traceroute.csv中的历史数据，分析路径中哪个节点经常出现异常。

---

### 注意事项
1. **权限**：Ping需要root或`cap_net_raw`，带宽测试不需要特殊权限。
2. **traceroute命令**：确保系统已安装traceroute（如未安装，脚本会报错）。
3. **带宽测试依赖**：首次运行speedtest-cli时会下载服务器列表，可能需要几秒钟。
4. **长时间运行**：建议在tmux或screen中运行，避免终端关闭导致脚本终止。
5. **磁盘空间**：CSV文件每天约几十KB，可放心长期运行。
