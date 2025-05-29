#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import requests
import datetime
from bs4 import BeautifulSoup
import logging
import argparse
import time
# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class ChinaDrugTrialsSearcher:
    """
    搜索中国药物临床试验登记与信息公示平台
    """
    def __init__(self):
        """
        初始化搜索器
        """
        self.base_url = "http://www.chinadrugtrials.org.cn"
        self.search_url = f"{self.base_url}/clinicaltrials.searchlist.dhtml" # 修正为正确的搜索结果URL
        self.session = requests.Session()
        self.headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "http://www.chinadrugtrials.org.cn",
            "Referer": "http://www.chinadrugtrials.org.cn/clinicaltrials.searchlist.dhtml",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
        }
        
        # 设置Cookie
        self.cookies = {
            "FSSBBIl1UgzbN7N80S": "4NXiRDf8zFgRh0Dwjpupk1CBWco1dQwyo4E.2kcgsHtkpxmIpxj0jM4rOOfnHSCt",
            "token": "we7piDj4EhlmQadtUeVdVpn8W6-QTSrHGXHLfaaHcGcmff3oV98wUulXjuG",
            "FSSBBIl1UgzbN7N80T": "3rhmUE9qYsygSBEBCVmu6_UP.459xWkrwlURuzFQkDtW1E62v14PNegineEq9BOFpoueZXLejZbWfN_gmWMJS4JNFkkEFSGqH1Q7dd4NvO.ye3z9o62_iJ6fZYYewWQ.maPX53Ev52tX9O6RYOPLlUrml0Pd9iErKh8wiBQei1xlNusQyYECWkOXLJ9qBs8gVYy_VtYi7utNUw8rHSIPmqZr.e4akqnIZhcE1K3bBB_WIINd5LfxqxCaeXlpw4Tts5IcPnT.CoW1ZYwiIzMNyLlnUz0UAz889bc9gQvP6p.KIHansaq8Yn.HG9aYGQFj_4x0"
        }
        
        # 将Cookie添加到会话中
        for key, value in self.cookies.items():
            self.session.cookies.set(key, value)
        
        # 初始化会话，访问首页获取Cookie
        logging.info("初始化会话，访问首页获取Cookie")
        try:
            response = self.session.get(self.base_url, headers=self.headers)
            status_code = response.status_code
            logging.info(f"首页访问状态码: {status_code}")
            
            # 接受 200 和 202 状态码
            if status_code not in [200, 202]:
                logging.error(f"访问首页失败，状态码: {status_code}")
            else:
                logging.info("成功访问首页，获取Cookie")
        except requests.exceptions.RequestException as e:
            logging.error(f"访问首页异常: {e}")

    def get_trial_detail(self, trial_id, ckm_index=""):
        """
        获取临床试验详细信息
        """
        detail_url = f"{self.base_url}/clinicaltrials.searchlistdetail.dhtml"

        data = {
            "id": trial_id,
            "ckm_index": ckm_index
        }

        logging.info(f"获取临床试验详细信息: {trial_id}")


        try:
            response = self.session.post(detail_url, headers=self.headers, data=data)
            status_code = response.status_code
            logging.info(f"请求返回状态码: {status_code}")
            logging.info(f"实际请求URL: {response.url}")

            if status_code not in [200, 202]:
                logging.error(f"请求失败，状态码: {status_code}")
                return None

            # 保存详细信息到文件
            with open(f"trial_detail_{trial_id}.html", "w", encoding="utf-8") as f:
                f.write(response.text)
            logging.info(f"已保存详细信息到 trial_detail_{trial_id}.html")

            return response.text
        except requests.exceptions.RequestException as e:
            logging.error(f"请求异常: {e}")
            return None

    def extract_trial_detail(self, html_content):
        """
        从HTML内容中提取临床试验详细信息
        """
        if not html_content:
            return {}

        soup = BeautifulSoup(html_content, 'html.parser')

        # 提取详细信息
        detail = {}

        # 提取标题
        title_elem = soup.find('h3', class_='text-center')
        if title_elem:
            detail['标题'] = title_elem.text.strip()

        # 提取详细信息表格
        tables = soup.find_all('table', class_='table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    key = cells[0].text.strip()
                    value = cells[1].text.strip()
                    if key and value:
                        detail[key] = value

        return detail

    def search(self, keywords, page=1, indication="", reg_no="", state="", drugs_name="", ckm_index=""):
        """
        搜索临床试验
        
        参数:
            keywords: 搜索关键词
            page: 页码
            indication: 适应症（二级搜索参数）
            reg_no: 登记号（二级搜索参数）
            state: 试验状态（二级搜索参数），默认为"进行中"
            drugs_name: 药物名称（二级搜索参数）
            ckm_index: ckm_index参数
        """
        data = {
            "id": "",
            "ckm_index": ckm_index,
            "sort": "desc",
            "sort2": "",
            "rule": "CTR",
            "secondLevel": "0",  # 0表示使用二级搜索
            "currentpage": str(page),
            "keywords": keywords,
            "reg_no": reg_no,
            "indication": indication,
            "case_no": "",
            "drugs_name": drugs_name,
            "drugs_type": "",
            "appliers": "",
            "communities": "",
            "researchers": "",
            "agencies": "",
            "state": state
        }

        logging.info(f"发送请求到 {self.search_url}")
        logging.info(f"搜索参数: 关键词={keywords}, 页码={page}, 适应症={indication}, 登记号={reg_no}, 状态={state}, 药物名称={drugs_name}, ckm_index={ckm_index}")

        try:
            # 使用会话对象发送POST请求，根据用户提供的curl命令
            response = self.session.post(self.search_url, headers=self.headers, data=data)
            status_code = response.status_code
            logging.info(f"请求返回状态码: {status_code}")
            logging.info(f"实际请求URL: {response.url}")

            # 接受 200 和 202 状态码
            if status_code not in [200, 202]:
                logging.error(f"请求失败，状态码: {status_code}")
                return None

            # 如果是 202 状态码，记录一下但继续处理
            if status_code == 202:
                logging.warning("收到 202 Accepted 状态码，继续处理响应内容")

            content_length = len(response.text)
            logging.info(f"返回内容长度: {content_length} 字符")

            # 检查响应内容是否包含关键字
            content_preview = response.text[:200] + "..." if len(response.text) > 200 else response.text
            logging.info(f"响应内容预览: {content_preview}")

            # 检查是否包含常见的HTML标签
            has_html = "<html" in response.text.lower() and "<body" in response.text.lower()
            logging.info(f"响应内容是否包含HTML标签: {has_html}")

            # 检查是否包含可能的临床试验信息
            has_trial_info = "试验" in response.text or "临床" in response.text
            logging.info(f"响应内容是否包含临床试验相关信息: {has_trial_info}")

            # 检查是否包含可能的表格元素
            has_table = "<table" in response.text.lower() and "<tr" in response.text.lower()
            logging.info(f"响应内容是否包含表格元素: {has_table}")

            # 创建输出目录（如果不存在）
            output_dir = os.path.join(os.getcwd(), "output")
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                logging.info(f"创建输出目录: {output_dir}")

            # 添加调试信息检查response内容
            logging.info(f"Response内容长度: {len(response.text)}")
            logging.info(f"Response状态码: {response.status_code}")
            logging.info(f"Response URL: {response.url}")
            logging.info(f"Response headers: {dict(response.headers)}")
            
            # 检查response中是否包含关键的搜索结果标识
            has_search_results = "暂无数据" in response.text or "CTR" in response.text
            logging.info(f"Response是否包含搜索结果标识: {has_search_results}")
            
            # 检查是否包含分页信息
            has_pagination = "当前第" in response.text and "页" in response.text
            logging.info(f"Response是否包含分页信息: {has_pagination}")
            
            # 保存原始响应内容到文件，用于调试
            debug_file = os.path.join(output_dir, f"response_page_{page}.html")
            with open(debug_file, "w", encoding="utf-8") as f:
                f.write(response.text)
            logging.info(f"已保存原始响应内容到 {debug_file}")
            
            # 额外保存一个带时间戳的临时文件用于对比
            import time
            temp_file = os.path.join(output_dir, f"temp_response_page_{page}_{int(time.time())}.html")
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(response.text)
            logging.info(f"已保存临时响应文件到 {temp_file}")

            return response.text
        except requests.exceptions.RequestException as e:
            logging.error(f"请求异常: {e}")
            return None

    def extract_trials_from_table(self, html_content, filter_keywords=None):
        """
        从HTML表格中提取临床试验信息
        """
        if not html_content:
            logging.error("HTML内容为空，无法提取临床试验信息")
            return []

        logging.info("开始解析HTML内容")
        soup = BeautifulSoup(html_content, 'html.parser')

        # 查找表格 - 直接查找searchTable
        table = soup.find('table', class_='searchTable')
        logging.info(f"直接查找searchTable结果: {table is not None}")
        
        if not table:
            # 尝试查找所有table元素进行调试
            all_tables = soup.find_all('table')
            logging.info(f"页面中所有table元素: {[t.get('class') for t in all_tables]}")
            logging.error("未找到临床试验表格")
            return []

        # 查找表格行
        rows = table.find_all('tr')
        if len(rows) <= 1:  # 只有标题行
            logging.error("表格中没有数据行")
            return []

        # 提取表头
        headers = []
        header_row = rows[0]
        for th in header_row.find_all('th'):
            headers.append(th.text.strip())

        logging.info(f"表头: {headers}")

        # 提取数据行
        trials = []
        for row in rows[1:]:  # 跳过标题行
            cells = row.find_all('td')
            if len(cells) < 6:  # 确保至少有6列
                continue

            # 提取ID，用于构建详情URL
            trial_id = ""
            detail_url = ""
            if cells[1].find('a'):
                a_tag = cells[1].find('a')
                if 'id' in a_tag.attrs:
                    trial_id = a_tag['id']
                    detail_url = f"{self.base_url}/clinicaltrials.searchlistdetail.dhtml?id={trial_id}"

            # 提取单元格内容
            trial = {
                '序号': cells[0].text.strip(),
                '登记号': cells[1].find('a').text.strip() if cells[1].find('a') else '',
                '试验状态': cells[2].find('a').text.strip() if cells[2].find('a') else '',
                '药物名称': cells[3].find('a').text.strip() if cells[3].find('a') else '',
                '适应症': cells[4].find('a').text.strip() if cells[4].find('a') else '',
                '试验通俗题目': cells[5].find('a').text.strip() if cells[5].find('a') else '',
                '详情URL': detail_url,
                '试验ID': trial_id
            }

            # 过滤关键词
            if filter_keywords:
                trial_text = ' '.join(trial.values()).lower()
                if not any(keyword.lower() in trial_text for keyword in filter_keywords):
                    continue

            trials.append(trial)

        logging.info(f"从表格中提取到 {len(trials)} 个临床试验")
        return trials

    def get_total_pages(self, html_content):
        """
        从HTML内容中提取总页数
        """
        if not html_content:
            return 1

        soup = BeautifulSoup(html_content, 'html.parser')

        # 查找分页信息 - 新的HTML结构中，分页信息在class为pageInfo的div中
        page_info = soup.select_one('div.pageInfo')
        if page_info:
            text = page_info.get_text().strip()
            # 格式为"当前第 <i>1</i> 页，共 <i>3</i> 页，共 <i>54</i> 条记录"
            match = re.search(r'共\s*<i>(\d+)</i>\s*页', str(page_info))
            if match:
                total_pages = int(match.group(1))
                logging.info(f"找到分页信息，总页数: {total_pages}")
                return total_pages

        # 尝试从分页控件中提取 - 新的HTML结构中，分页控件在class为pagination的ul中
        pagination_controls = soup.select('ul.pagination li a')
        if pagination_controls:
            page_numbers = []
            for a in pagination_controls:
                # 提取数字页码
                if a.text.strip().isdigit():
                    page_numbers.append(int(a.text.strip()))
                # 检查onclick属性中的gotopage函数参数
                elif 'onclick' in a.attrs:
                    onclick = a['onclick']
                    page_match = re.search(r'gotopage\(\s*(\d+)\s*\)', onclick)
                    if page_match:
                        page_numbers.append(int(page_match.group(1)))

            if page_numbers:
                max_page = max(page_numbers)
                logging.info(f"从分页控件中提取到最大页码: {max_page}")
                return max_page

        # 尝试从表格行数估算
        table = soup.find('table', class_='searchTable')
        if table:
            rows = table.find_all('tr')
            if len(rows) > 1:  # 有数据行
                # 假设每页显示20条记录
                estimated_pages = (len(rows) - 1 + 19) // 20
                logging.info(f"根据表格行数估算页数: {estimated_pages}")
                return max(1, estimated_pages)

        logging.warning("无法确定总页数，默认为1页")
        return 1

    def search_all_pages(self, keywords, filter_keywords=None, max_pages=None, indication="", reg_no="", state="进行中", drugs_name="", ckm_index="1", use_local_file=False, auto_all_pages=True):
        """
        搜索所有页面的临床试验

        参数:
            keywords: 搜索关键词
            filter_keywords: 过滤关键词
            max_pages: 最大页数，如果为None则获取所有页面
            indication: 适应症
            reg_no: 登记号
            state: 试验状态，默认为"进行中"
            drugs_name: 药物名称
            ckm_index: ckm_index参数
            use_local_file: 是否使用本地文件
            auto_all_pages: 是否自动获取所有页面
        """
        all_trials = []
        page = 1

        # 获取第一页内容
        html_content = None
        if use_local_file:
            # 尝试从本地文件加载
            local_file = f"response_page_{page}.html"
            if os.path.exists(local_file):
                with open(local_file, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                logging.info(f"使用本地文件 {local_file} 作为响应内容")

        # 如果本地文件不存在或不使用本地文件，则从网站获取
        if not html_content:
            html_content = self.search(keywords, page, indication, reg_no, state, drugs_name, ckm_index)

        if not html_content:
            logging.error("无法获取第一页内容")
            return []

        # 提取第一页的临床试验
        trials = self.extract_trials_from_table(html_content, filter_keywords)
        all_trials.extend(trials)

        # 获取总页数
        total_pages = self.get_total_pages(html_content)

        # 如果指定了最大页数，则使用最大页数
        if max_pages and max_pages < total_pages:
            total_pages = max_pages
            logging.info(f"限制为最大 {max_pages} 页")

        # 如果不自动获取所有页面，则只获取第一页
        if not auto_all_pages:
            total_pages = 1
            logging.info("不自动获取所有页面，只获取第一页")

        logging.info(f"找到 {total_pages} 页结果，将获取所有页面")

        # 搜索剩余页面
        for page in range(2, total_pages + 1):
            logging.info(f"正在搜索第 {page}/{total_pages} 页...")

            # 尝试从本地文件加载
            html_content = None
            if use_local_file:
                local_file = f"response_page_{page}.html"
                if os.path.exists(local_file):
                    with open(local_file, 'r', encoding='utf-8') as f:
                        html_content = f.read()
                    logging.info(f"使用本地文件 {local_file} 作为响应内容")

            # 如果本地文件不存在或不使用本地文件，则从网站获取
            if not html_content:
                html_content = self.search(keywords, page, indication, reg_no, state, drugs_name, ckm_index)

            if not html_content:
                logging.error(f"无法获取第 {page} 页内容")
                break

            # 提取当前页的临床试验
            page_trials = self.extract_trials_from_table(html_content, filter_keywords)
            logging.info(f"第 {page} 页提取到 {len(page_trials)} 个临床试验")

            # 如果当前页没有提取到临床试验，可能是到达了最后一页
            if not page_trials:
                logging.warning(f"第 {page} 页没有提取到临床试验，可能是到达了最后一页")
                break

            all_trials.extend(page_trials)

            # 休眠以避免过载服务器
            import time
            time.sleep(1)

        logging.info(f"总共提取到 {len(all_trials)} 个临床试验")
        return all_trials

def format_trials_markdown(trials):
    """
    将临床试验格式化为Markdown
    """
    if not trials:
        return "# 未找到相关临床试验\n"

    markdown = "# KRAS相关临床试验\n\n"

    # 按试验状态排序
    def get_trial_priority(trial):
        status = trial['试验状态']
        if "尚未招募" in status:
            return 0
        elif "招募中" in status:
            return 1
        else:
            return 2

    sorted_trials = sorted(trials, key=get_trial_priority)

    for trial in sorted_trials:
        # 添加标题和详情链接
        if trial['详情URL']:
            markdown += f"## [{trial['试验通俗题目']}]({trial['详情URL']})\n\n"
        else:
            markdown += f"## {trial['试验通俗题目']}\n\n"

        markdown += f"- **登记号**: {trial['登记号']}\n"
        markdown += f"- **药物名称**: {trial['药物名称']}\n"
        markdown += f"- **试验状态**: {trial['试验状态']}\n"
        markdown += f"- **适应症**: {trial['适应症']}\n"

        # 添加详情链接（作为单独的行）
        if trial['详情URL']:
            markdown += f"- **详情链接**: [{trial['登记号']}]({trial['详情URL']})\n"

        markdown += "\n---\n\n"

    return markdown

def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(description='搜索中国药物临床试验登记与信息公示平台')
    parser.add_argument('-k', '--keywords', help='搜索关键词')
    parser.add_argument('-f', '--filter', help='过滤关键词，用空格分隔多个关键词')
    parser.add_argument('-i', '--indication', help='适应症')
    parser.add_argument('-r', '--reg_no', help='登记号')
    parser.add_argument('-s', '--state', default="进行中", help='试验状态，默认为"进行中"')
    parser.add_argument('-a', '--all-states', action='store_true', help='搜索所有试验状态，覆盖默认的"进行中"状态')
    parser.add_argument('-d', '--drugs-name', help='药物名称')
    parser.add_argument('-p', '--pages', type=int, help='最大页数，如果不指定则获取所有页面')
    parser.add_argument('-o', '--output', help='输出文件名，默认为日期_关键词.md')
    parser.add_argument('-l', '--local', action='store_true', help='使用本地文件作为响应内容，而不是从网站获取')
    parser.add_argument('--debug', action='store_true', help='调试模式，保存更多中间文件')
    parser.add_argument('--detail', action='store_true', help='获取每个临床试验的详细信息')
    parser.add_argument('--no-auto-pages', action='store_true', help='不自动获取所有页面，只获取第一页')

    args = parser.parse_args()

    # 获取搜索关键词
    if args.keywords:
        search_keywords = args.keywords
    else:
        print("请输入搜索关键词（例如：KRAS）：")
        search_keywords = input().strip()
        if not search_keywords:
            print("未输入搜索关键词，将使用默认关键词：KRAS")
            search_keywords = "KRAS"

    # 获取过滤关键词
    if args.filter:
        filter_keywords = args.filter.split()
    else:
        print("请输入过滤关键词（用空格分隔，例如：胰腺癌 实体瘤）：")
        filter_input = input().strip()
        if not filter_input:
            print("未输入过滤关键词，将使用默认过滤关键词：胰腺癌 实体瘤")
            filter_keywords = ["胰腺癌", "实体瘤"]
        else:
            filter_keywords = filter_input.split()

    # 初始化搜索器
    searcher = ChinaDrugTrialsSearcher()

    print(f"搜索关键词: {search_keywords}")
    print(f"过滤关键词: {', '.join(filter_keywords)}")

    # 搜索临床试验
    trials = searcher.search_all_pages(
        search_keywords,
        filter_keywords,
        args.pages, # 最大页数
        args.indication or "", # 适应症
        args.reg_no or "", # 登记号
        args.state or "进行中" if not args.all_states else "", # 试验状态
        args.drugs_name or "", # 药物名称·
        "1",  # ckm_index
        args.local,  # 使用本地文件
        not args.no_auto_pages  # 自动获取所有页面
    )

    if not trials:
        print(f"未找到与过滤关键词相关的临床试验: {', '.join(filter_keywords)}")
        sys.exit(0)

    # 如果需要获取详细信息
    if args.detail:
        print("正在获取详细信息...")
        for i, trial in enumerate(trials):
            if trial['试验ID']:
                print(f"获取第 {i+1}/{len(trials)} 个试验的详细信息: {trial['登记号']}")

                # 尝试从本地文件加载
                detail_html = None
                local_file = f"trial_detail_{trial['试验ID']}.html"
                if args.local and os.path.exists(local_file):
                    with open(local_file, 'r', encoding='utf-8') as f:
                        detail_html = f.read()
                    print(f"使用本地文件 {local_file} 作为详细信息")

                # 如果本地文件不存在或不使用本地文件，则从网站获取
                if not detail_html:
                    detail_html = searcher.get_trial_detail(trial['试验ID'])

                if detail_html:
                    # 提取详细信息
                    detail = searcher.extract_trial_detail(detail_html)

                    # 将详细信息添加到试验信息中
                    for key, value in detail.items():
                        if key not in trial:
                            trial[key] = value

                # 休眠以避免过载服务器
                import time
                time.sleep(1)

    # 格式化为Markdown
    markdown = format_trials_markdown(trials)

    # 保存到文件
    today = datetime.datetime.now().strftime('%Y%m%d')
    if args.output:
        output_file = args.output
    else:
        output_file = f"{today}_{search_keywords}_{'_'.join(filter_keywords)}.md"

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown)

    print(f"成功提取 {len(trials)} 个临床试验并保存到 {output_file}")

if __name__ == "__main__":
    main()
