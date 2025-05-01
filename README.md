# 中国药物临床试验数据提取工具

这个工具集可以帮助您从中国药物临床试验登记与信息公示平台（chinadrugtrials.org.cn）搜索和提取临床试验信息，特别是研究者和参与机构的详细信息。

## 功能特点

- 支持关键词搜索和过滤
- 支持多页结果自动获取
- 提取临床试验的详细信息，特别是研究者和参与机构信息
- 生成结构化的Markdown格式报告
- 支持生成综合汇总报告，包含试验状态和研究机构分布统计
- 支持使用Cookie进行认证，避免访问限制
- 自动创建output目录，所有输出文件统一管理

## 环境要求

- Python 3.6+
- 网络连接（用于访问chinadrugtrials.org.cn）

## 安装步骤

1. 克隆仓库到本地：

```bash
git clone https://github.com/PancrePal-xiaoyibao/search_china_trials.git
cd search_china_trials
```

2. 安装依赖：

```bash
pip install requests beautifulsoup4
```

3. 配置Cookie（可选，但推荐）：
   - 按照下方"使用Cookie进行认证"部分的说明获取Cookie
   - 创建或编辑`config.json`文件

## 文件说明

1. `chinadrugtrials_extract.py` - 基础版查询脚本，提供基本的搜索和提取功能
2. `chinadrugtrials_detail_extractor_v1.py` - 详细信息提取脚本，专注于提取研究者和参与机构信息
3. `config.json` - 配置文件，用于存储Cookie等配置信息

## 使用方法

### 基础搜索

```bash
python chinadrugtrials_extract.py -k KRAS -f "胰腺癌 实体瘤"
```

参数说明：
- `-k, --keywords`: 搜索关键词
- `-f, --filter`: 过滤关键词，用空格分隔多个关键词
- `-p, --pages`: 最大页数，如果不指定则获取所有页面
- `-o, --output`: 输出文件名，默认为日期_关键词.md
- `-l, --local`: 使用本地文件作为响应内容，而不是从网站获取

### 提取详细信息

```bash
python chinadrugtrials_detail_extractor_v1.py -k KRAS -f "胰腺癌 实体瘤" --comprehensive
```

参数说明：
- `-k, --keywords`: 搜索关键词
- `-f, --filter`: 过滤关键词，用空格分隔多个关键词
- `-p, --pages`: 最大页数，如果不指定则获取所有页面
- `-o, --output`: 输出文件名，默认为日期_关键词.md
- `-d, --detail-dir`: 详细信息输出目录，默认为output/details
- `-l, --local`: 使用本地文件作为响应内容，而不是从网站获取
- `--no-auto-pages`: 不自动获取所有页面，只获取第一页
- `--comprehensive`: 生成综合汇总报告

## 输出目录结构

所有生成的文件都会保存在`output`目录下，结构如下：

```
output/
├── YYYYMMDD_关键词.md                 # 基本搜索结果
├── YYYYMMDD_关键词_details.md         # 详细信息汇总文件
├── YYYYMMDD_关键词_comprehensive.md   # 综合汇总报告（如果使用--comprehensive参数）
├── trial_detail_*.html               # 原始HTML响应（用于调试）
└── details/
    └── 登记号_detail.md               # 每个临床试验的详细信息
```

## 使用Cookie进行认证

为了避免访问限制和提高稳定性，您可以使用Cookie进行认证。以下是获取和使用Cookie的方法：

### 获取Cookie

#### 使用Charles抓包工具获取Cookie

1. 安装并配置Charles（https://www.charlesproxy.com/）
2. 配置浏览器使用Charles作为代理
3. 在浏览器中访问 http://www.chinadrugtrials.org.cn/
4. 在Charles中找到对应的请求，查看请求头中的Cookie字段
5. 复制完整的Cookie字符串

![Charles抓包示例](https://i.imgur.com/example1.png)

#### 使用浏览器开发者工具获取Cookie

1. 打开浏览器（Chrome、Firefox等）
2. 访问 http://www.chinadrugtrials.org.cn/
3. 打开开发者工具（F12或右键 -> 检查）
4. 切换到"网络"(Network)选项卡
5. 刷新页面，选择任意一个请求
6. 在请求头(Headers)中找到Cookie字段
7. 复制完整的Cookie字符串

![浏览器开发者工具示例](https://i.imgur.com/example2.png)

Cookie示例：
```
JSESSIONID=1A2B3C4D5E6F7G8H9I0J; eap_language=zh_CN; eap_uid=123456789
```

### 使用Cookie

#### 方法1：通过配置文件使用Cookie

1. 创建或编辑`config.json`文件：

```json
{
  "cookies": "这里粘贴您的完整Cookie字符串",
  "last_updated": "2023-10-01"
}
```

2. 运行脚本时会自动读取配置文件中的Cookie

#### 方法2：通过命令行参数使用Cookie

```bash
python chinadrugtrials_detail_extractor_v1.py -k KRAS -f "胰腺癌" --cookie "这里粘贴您的完整Cookie字符串"
```

## 常见问题解答

### Q: 为什么我无法获取任何结果？
A: 可能是网站访问限制或Cookie过期。尝试更新Cookie或减少请求频率。

### Q: 如何处理大量数据？
A: 使用`-p`参数限制页数，或使用`--local`参数结合已保存的响应内容进行测试。

### Q: 如何解决编码问题？
A: 确保您的终端支持UTF-8编码。在Windows上，可能需要设置`chcp 65001`。

## 项目结构

```
search_china_trials/
├── chinadrugtrials_extract.py              # 基础搜索脚本
├── chinadrugtrials_detail_extractor_v1.py  # 详细信息提取脚本
├── config.json                             # 配置文件
├── README.md                               # 项目说明文档
└── output/                                 # 输出目录（自动创建）
    └── details/                            # 详细信息目录（自动创建）
```

## 贡献指南

欢迎贡献代码或提出建议！请遵循以下步骤：

1. Fork本仓库
2. 创建您的特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交您的更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建一个Pull Request

## 注意事项

1. 请合理控制访问频率，避免对网站造成过大负担
2. Cookie有效期有限，如果遇到访问问题，请更新Cookie
3. 网站结构可能会变化，如果脚本无法正常工作，可能需要更新解析逻辑
4. 建议使用`--local`参数和保存的响应内容进行测试，以减少对网站的请求

## 许可证

MIT
