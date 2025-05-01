# 中国药物临床试验数据提取工具

这个工具集可以帮助您从中国药物临床试验登记与信息公示平台（chinadrugtrials.org.cn）搜索和提取临床试验信息，特别是研究者和参与机构的详细信息。

## 功能特点

- 支持关键词搜索和过滤
- 支持多页结果自动获取
- 提取临床试验的详细信息，特别是研究者和参与机构信息
- 生成结构化的Markdown格式报告
- 支持生成综合汇总报告，包含试验状态和研究机构分布统计
- 支持使用Cookie进行认证，避免访问限制

## 文件说明

1. `chinadrugtrials_extract.py` - 基础版查询脚本，提供基本的搜索和提取功能
2. `chinadrugtrials_detail_extractor_v1.py` - 详细信息提取脚本，专注于提取研究者和参与机构信息
3. `config.json` - 配置文件，用于存储Cookie等配置信息

## 安装依赖

```bash
pip install requests beautifulsoup4
```

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
- `-d, --detail-dir`: 详细信息输出目录，默认为details
- `-l, --local`: 使用本地文件作为响应内容，而不是从网站获取
- `--no-auto-pages`: 不自动获取所有页面，只获取第一页
- `--comprehensive`: 生成综合汇总报告

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

## 输出文件说明

脚本会生成以下文件：

1. `YYYYMMDD_关键词.md` - 基本搜索结果，包含所有匹配的临床试验基本信息
2. `details/登记号_detail.md` - 每个临床试验的详细信息，包含研究者和参与机构信息
3. `YYYYMMDD_关键词_details.md` - 详细信息汇总文件，包含所有详细信息文件的链接
4. `YYYYMMDD_关键词_comprehensive.md` - 综合汇总报告，包含试验状态和研究机构分布统计

## 注意事项

1. 请合理控制访问频率，避免对网站造成过大负担
2. Cookie有效期有限，如果遇到访问问题，请更新Cookie
3. 网站结构可能会变化，如果脚本无法正常工作，可能需要更新解析逻辑
4. 建议使用`--local`参数和保存的响应内容进行测试，以减少对网站的请求

## 示例输出

### 基本信息

```markdown
# KRAS相关临床试验

## IX001 TCR-T注射液治疗晚期胰腺癌患者的I期临床研究

- **试验编号**: CTR20251024
- **药物名称**: IX001 TCR-T注射液
- **试验状态**: 尚未招募
- **试验分期**: I 期
- **适应症**: 基因型为HLA-A*11:01， KRAS G12V突变的晚期胰腺癌
- **研究机构**: 中山大学肿瘤防治中心
- **地区**: 广东省
- **申办方**: 上海镔铁生物科技有限责任公司
- **来源**: chinadrugtrials.org.cn

---
```

### 详细信息

```markdown
# IX001 TCR-T注射液治疗晚期胰腺癌患者的I期临床研究

## 基本信息

- **登记号**: CTR20251024
- **药物名称**: IX001 TCR-T注射液
- **试验状态**: 进行中 尚未招募
- **适应症**: 基因型为HLA-A*11:01， KRAS G12V突变的晚期胰腺癌

## 研究者信息

### 主要研究者

**姓名**: 徐瑞华
**学位**: 医学博士
**职称**: 主任医师
**单位名称**: 中山大学肿瘤防治中心

**联系方式**:
- 电话: 020-87343333
- Email: xurh@sysucc.org.cn
- 邮政地址: 广东省广州市越秀区东风东路651号
- 邮编: 510060

### 参加机构

**1. 中山大学肿瘤防治中心**
- 主要研究者: 徐瑞华
- 地区: 广东省广州市

**2. 中山大学肿瘤防治中心**
- 主要研究者: 李宇红
- 地区: 广东省广州市
```

## 许可证

MIT