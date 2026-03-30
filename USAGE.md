# 店铺数据采集 Skill 使用说明

## 先看这里

请直接拉取这个仓库：

`https://github.com/jackro123438-crypto/openclaw-look-dianpu.git`

把这个仓库地址发给你的小龙虾，让小龙虾先学习这个 skill 的结构和用法，再按下面的步骤配置自己的 key 并运行即可。

## 这个项目是做什么的

这个项目是一个可分享的 OpenClaw skill，用来采集江阴市门店 POI 数据，并完成以下流程：

- 从高德地图和百度地图采集门店数据
- 将原始数据写入本地 SQLite 数据库
- 对门店名称、电话、地址和类型做清洗
- 对疑似重复门店做标记
- 导出可分享的 Excel 文件

## 这个项目最大的优势

这个项目最大的优势有 4 个：

- 可以直接作为 skill 分享给同事使用，不是一次性的脚本仓库
- 已经去掉了原作者自己的 API key 和私有数据，适合公开或内部流转
- 使用者只需要填写自己的 key，不需要改业务代码
- 采集、清洗、统计、导出都已经拆成明确命令，便于重复执行和排查问题
- 仓库默认不带任何已采集数据，分享出去更干净、更安全

## 项目简介

这个仓库原本是一个独立的 Python 采集项目，后来已经整理成了适合 OpenClaw 使用和分享的 skill 结构。

当前仓库的核心组成如下：

- `SKILL.md`
  - skill 的说明入口，告诉 OpenClaw 这个 skill 是做什么的、什么时候该用
- `scripts/run_shop_data_skill.py`
  - 命令行入口，所有常用操作都从这里启动
- `shop_data_skill/config.py`
  - 统一配置文件，改成从环境变量读取 key，不再写死私人信息
- `shop_data_skill/collectors/`
  - 采集器目录，分别处理高德地图和百度地图的数据抓取
- `shop_data_skill/cleaner.py`
  - 数据清洗逻辑
- `shop_data_skill/exporter.py`
  - Excel 导出逻辑
- `shop_data_skill/models.py`
  - SQLite 数据库结构和数据写入逻辑

另外要特别说明：

- 当前仓库不附带任何你已经采集过的数据
- 不包含数据库文件
- 不包含 Excel 结果文件
- 不包含 GeoJSON、缓存和中间产物
- 同事拉取后拿到的是一个“空模板 skill”，不是你的历史数据包

## 项目具体细节

### 1. 获取代码

直接拉取仓库：

```bash
git clone https://github.com/jackro123438-crypto/openclaw-look-dianpu.git
cd openclaw-look-dianpu
```

### 2. 安装依赖

建议使用 Python 3.11 或更高版本。

安装依赖：

```bash
pip install -r requirements.txt
```

当前依赖主要包括：

- `requests`
- `pandas`
- `openpyxl`

### 3. 配置你自己的 key

这个项目已经删除了原作者自己的 key。

使用前必须填写你自己的地图 key：

- `DIANPU_AMAP_KEY`
- `DIANPU_BMAP_AK`

可以用两种方式配置。

方式一：直接设置环境变量

```bash
set DIANPU_AMAP_KEY=你的高德Key
set DIANPU_BMAP_AK=你的百度AK
```

如果你在 PowerShell 中运行：

```powershell
$env:DIANPU_AMAP_KEY="你的高德Key"
$env:DIANPU_BMAP_AK="你的百度AK"
```

方式二：参考仓库里的 `.env.example` 自己建立环境配置

示例内容如下：

```env
DIANPU_AMAP_KEY=replace-with-your-amap-key
DIANPU_BMAP_AK=replace-with-your-baidu-ak
DIANPU_DATA_DIR=./data
DIANPU_EXPORT_FILENAME=jiangyin_shops.xlsx
```

注意：

- 不要把自己的 key 提交回仓库
- 不要把生成的数据库、Excel 和缓存文件提交回仓库

### 4. 常用命令

所有命令都从这个入口运行：

```bash
python scripts/run_shop_data_skill.py
```

#### 测试采集

先测高德：

```bash
python scripts/run_shop_data_skill.py test amap
```

再测百度：

```bash
python scripts/run_shop_data_skill.py test bmap
```

这两个命令适合先验证 key 是否可用、接口是否正常。

#### 正式采集

只采高德：

```bash
python scripts/run_shop_data_skill.py collect amap
```

只采百度：

```bash
python scripts/run_shop_data_skill.py collect bmap
```

同时采集两个来源：

```bash
python scripts/run_shop_data_skill.py collect all
```

#### 数据清洗

```bash
python scripts/run_shop_data_skill.py clean
```

#### 导出 Excel

```bash
python scripts/run_shop_data_skill.py export
```

#### 查看统计信息

```bash
python scripts/run_shop_data_skill.py stats
```

#### 一键跑完整流程

```bash
python scripts/run_shop_data_skill.py all
```

### 5. 运行结果会输出到哪里

默认情况下，运行产物会放到：

- `./data/jiangyin_shops.db`
- `./data/jiangyin_shops.xlsx`

你也可以通过环境变量修改：

- `DIANPU_DATA_DIR`
- `DIANPU_EXPORT_FILENAME`

### 6. 这个 skill 的实际工作流

建议同事按下面顺序使用：

1. 拉取仓库
2. 安装依赖
3. 配置自己的高德和百度 key
4. 先执行 `test amap` 和 `test bmap`
5. 确认测试通过后执行 `collect all`
6. 执行 `clean`
7. 执行 `export`
8. 用 `stats` 检查结果

如果想省事，也可以在确认 key 正常后直接执行：

```bash
python scripts/run_shop_data_skill.py all
```

### 7. 报错时怎么判断

如果运行时报错，优先看这几类问题：

- 没有配置 key
  - 项目会明确提示你填写 `DIANPU_AMAP_KEY` 或 `DIANPU_BMAP_AK`
- key 不可用
  - 可能是 key 填错、权限不够、额度不足
- 网络问题
  - 请求地图接口失败时，通常和网络或接口限制有关
- 导出失败
  - 通常是依赖没装完整，重点检查 `pandas` 和 `openpyxl`

### 8. 适合分享时怎么说

你可以直接把下面这段话发给同事：

> 直接拉这个仓库：`https://github.com/jackro123438-crypto/openclaw-look-dianpu.git`  
> 这是一个适合 OpenClaw 使用的门店数据采集 skill。  
> 仓库里默认不带任何历史采集数据。  
> 你先让小龙虾学习这个 skill 的结构和命令，再把你自己的高德 key 和百度 key 配上，就可以执行采集、清洗、导出完整流程。

## 总结

这个项目本质上是一个“可复用、可分享、去私有化”的江阴市门店数据采集 skill。

它不是原始脚本堆，而是已经整理成适合同事直接拉取、学习、配置自己 key、重复运行的标准化仓库。
