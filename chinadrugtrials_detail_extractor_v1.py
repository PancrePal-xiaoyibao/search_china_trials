#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import requests
import datetime
import logging
import argparse
from bs4 import BeautifulSoup
from chinadrugtrials_extract import ChinaDrugTrialsSearcher

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class ChinaDrugTrialsDetailExtractor(ChinaDrugTrialsSearcher):
    """
    增强版中国药物临床试验搜索器，提取详细信息
    """
    def __init__(self):
        super().__init__()  # 调用父类初始化方法
        # 创建输出目录
        self.output_dir = os.path.join(os.getcwd(), "output")
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            logging.info(f"创建输出目录: {self.output_dir}")
        
    def get_trial_detail(self, trial_id, ckm_index="1"):
        """
        获取临床试验详细信息
        """
        detail_url = f"{self.base_url}/clinicaltrials.searchlistdetail.dhtml"

        data = {
            "id": trial_id,
            "ckm_index": ckm_index,
            "sort": "desc",
            "sort2": "",
            "rule": "CTR",
            "secondLevel": "0",
            "currentpage": "1",
            "keywords": "",
            "reg_no": "",
            "indication": "",
            "case_no": "",
            "drugs_name": "",
            "drugs_type": "",
            "appliers": "",
            "communities": "",
            "researchers": "",
            "agencies": "",
            "state": ""
        }

        logging.info(f"获取临床试验详细信息: {trial_id}")

        try:
            response = self.session.post(detail_url, headers=self.headers, data=data)
            status_code = response.status_code
            logging.info(f"请求返回状态码: {status_code}")

            if status_code not in [200, 202]:
                logging.error(f"请求失败，状态码: {status_code}")
                return None

            # 保存详细信息到output子目录
            detail_file = os.path.join(self.output_dir, f"trial_detail_{trial_id}.html")
            with open(detail_file, "w", encoding="utf-8") as f:
                f.write(response.text)
            logging.info(f"已保存详细信息到 {detail_file}")

            return response.text
        except requests.exceptions.RequestException as e:
            logging.error(f"请求异常: {e}")
            return None

    def extract_trial_detail(self, html_content):
        """
        从HTML内容中提取临床试验详细信息，重点提取研究者信息
        """
        if not html_content:
            logging.error("HTML内容为空")
            return {}

        soup = BeautifulSoup(html_content, 'html.parser')
        detail = {}

        # 查找研究者信息部分
        researcher_section = soup.find(lambda tag: tag.name == 'div' and '研究者信息' in tag.text and 'searchDetailPartTit' in tag.get('class', []))
        
        if not researcher_section:
            logging.error("未找到研究者信息部分")
            # 保存HTML用于调试
            debug_file = os.path.join(self.output_dir, f"debug_html_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
            with open(debug_file, "w", encoding="utf-8") as f:
                f.write(html_content)
            logging.info(f"已保存调试HTML到 {debug_file}")
            return {}
        
        researcher_info = {}
        
        # 1. 提取主要研究者信息
        main_researcher_section = soup.find(lambda tag: tag.name == 'div' and '主要研究者信息' in tag.text and 'sDPTit2' in tag.get('class', []))
        if main_researcher_section:
            main_researcher_info = {}
            
            # 查找主要研究者表格
            main_table = main_researcher_section.find_next('table', class_='searchDetailTable')
            if main_table:
                # 提取研究者信息
                rows = main_table.find_all('tr')
                if rows:
                    # 第一行: 姓名、学位、职称
                    first_row = rows[0]
                    cells = first_row.find_all(['th', 'td'])
                    if len(cells) >= 7:  # 跳过第一个th(序号)
                        main_researcher_info['姓名'] = cells[2].text.strip()
                        main_researcher_info['学位'] = cells[4].text.strip()
                        main_researcher_info['职称'] = cells[6].text.strip()
                    
                    # 第二行: 电话、Email、邮政地址
                    if len(rows) > 1:
                        second_row = rows[1]
                        cells = second_row.find_all(['th', 'td'])
                        if len(cells) >= 7:
                            main_researcher_info['电话'] = cells[1].text.strip()
                            main_researcher_info['Email'] = cells[3].text.strip()
                            main_researcher_info['邮政地址'] = cells[5].text.strip()
                    
                    # 第三行: 邮编、单位名称
                    if len(rows) > 2:
                        third_row = rows[2]
                        cells = third_row.find_all(['th', 'td'])
                        if len(cells) >= 5:
                            main_researcher_info['邮编'] = cells[1].text.strip()
                            main_researcher_info['单位名称'] = cells[3].text.strip()
        
            researcher_info['主要研究者信息'] = main_researcher_info
        
        # 2. 提取各参加机构信息
        institutions_section = soup.find(lambda tag: tag.name == 'div' and '各参加机构信息' in tag.text and 'sDPTit2' in tag.get('class', []))
        if institutions_section:
            institutions = []
            
            # 查找机构表格
            inst_table = institutions_section.find_next('table', class_='searchDetailTable')
            if inst_table:
                # 获取表头
                header_row = inst_table.find('tr')
                if header_row:
                    headers = [th.text.strip() for th in header_row.find_all('th')]
                    
                    # 处理数据行
                    data_rows = inst_table.find_all('tr')[1:]  # 跳过表头
                    for row in data_rows:
                        cells = row.find_all('td')
                        if cells:
                            # 创建一个字典，将表头与单元格内容对应
                            inst = {}
                            for i, cell in enumerate(cells):
                                if i < len(headers):  # 确保不超出表头数量
                                    inst[headers[i]] = cell.text.strip()
                            
                            institutions.append(inst)
        
            researcher_info['各参加机构信息'] = institutions
        
        # 将研究者信息添加到详细信息中
        if researcher_info:
            detail['研究者信息'] = researcher_info
        else:
            logging.error("未能提取到研究者信息")
        
        return detail

    def format_detail_markdown(self, trial, detail):
        """
        将临床试验详细信息格式化为Markdown，以更直观的格式展示研究者信息
        """
        markdown = f"# {trial['试验通俗题目']}\n\n"
        
        # 基本信息
        markdown += "## 基本信息\n\n"
        markdown += f"- **登记号**: {trial['登记号']}\n"
        markdown += f"- **药物名称**: {trial['药物名称']}\n"
        markdown += f"- **试验状态**: {trial['试验状态']}\n"
        markdown += f"- **适应症**: {trial['适应症']}\n"
        if trial.get('详情URL'):
            markdown += f"- **详情链接**: [{trial['登记号']}]({trial['详情URL']})\n"
        markdown += "\n"
        
        # 研究者信息
        if '研究者信息' in detail:
            markdown += "## 研究者信息\n\n"
            
            # 主要研究者信息
            if '主要研究者信息' in detail['研究者信息']:
                markdown += "### 主要研究者\n\n"
                main_info = detail['研究者信息']['主要研究者信息']
                
                markdown += f"**姓名**: {main_info.get('姓名', '')}\n"
                markdown += f"**学位**: {main_info.get('学位', '')}\n"
                markdown += f"**职称**: {main_info.get('职称', '')}\n"
                
                if '单位名称' in main_info:
                    markdown += f"**单位名称**: {main_info.get('单位名称', '')}\n"
                
                if '电话' in main_info or 'Email' in main_info or '邮政地址' in main_info or '邮编' in main_info:
                    markdown += "\n**联系方式**:\n"
                    if '电话' in main_info:
                        markdown += f"- 电话: {main_info.get('电话', '')}\n"
                    if 'Email' in main_info:
                        markdown += f"- Email: {main_info.get('Email', '')}\n"
                    if '邮政地址' in main_info:
                        markdown += f"- 邮政地址: {main_info.get('邮政地址', '')}\n"
                    if '邮编' in main_info:
                        markdown += f"- 邮编: {main_info.get('邮编', '')}\n"
                
                markdown += "\n"
            
            # 各参加机构信息
            if '各参加机构信息' in detail['研究者信息'] and detail['研究者信息']['各参加机构信息']:
                markdown += "### 参加机构\n\n"
                
                for inst in detail['研究者信息']['各参加机构信息']:
                    markdown += f"**{inst.get('序号', '')}. {inst.get('机构名称', '')}**\n"
                    markdown += f"- 主要研究者: {inst.get('主要研究者', '')}\n"
                    markdown += f"- 地区: {inst.get('省（州）', '')}{inst.get('城市', '')}\n"
                    markdown += "\n"
        
        # 其他详细信息
        for section, info in detail.items():
            if section != '研究者信息' and section != '标题':
                markdown += f"## {section}\n\n"
                if isinstance(info, dict):
                    for key, value in info.items():
                        markdown += f"- **{key}**: {value}\n"
                else:
                    markdown += f"{info}\n"
                markdown += "\n"
            
        return markdown

    def process_trials_with_details(self, trials, output_dir):
        """
        处理多个临床试验，提取详细信息并保存到文件
        
        Args:
            trials: 临床试验列表
            output_dir: 输出目录
        
        Returns:
            bool: 是否成功处理
        """
        # 确保输出目录存在
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            logging.info(f"创建输出目录: {output_dir}")
        
        # 创建汇总文件
        summary_file = f"{output_dir}/trials_summary.md"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("# 临床试验详细信息汇总\n\n")
            f.write("## 目录\n\n")
        
        # 处理每个试验
        for i, trial in enumerate(trials):
            if not trial.get('试验ID'):
                logging.warning(f"试验 {i+1} 没有ID，跳过")
                continue
                
            logging.info(f"处理第 {i+1}/{len(trials)} 个试验: {trial['登记号']}")
            
            # 获取详细信息
            detail_html = self.get_trial_detail(trial['试验ID'])
            if not detail_html:
                logging.error(f"无法获取试验 {trial['登记号']} 的详细信息")
                continue
                
            # 提取详细信息
            detail = self.extract_trial_detail(detail_html)
            if not detail:
                logging.error(f"无法提取试验 {trial['登记号']} 的详细信息")
                continue
                
            # 格式化为Markdown
            markdown = self.format_detail_markdown(trial, detail)
            
            # 保存到单独文件
            filename = f"{output_dir}/{trial['登记号']}_detail.md"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(markdown)
            logging.info(f"已保存试验 {trial['登记号']} 的详细信息到 {filename}")
            
            # 添加到汇总文件
            with open(summary_file, 'a', encoding='utf-8') as f:
                # 添加到目录
                f.write(f"- [{trial['试验通俗题目']}](#{trial['登记号']})\n")
            
            # 休眠以避免过载服务器
            import time
            time.sleep(1)
        
        # 添加详细内容到汇总文件
        with open(summary_file, 'a', encoding='utf-8') as f:
            f.write("\n---\n\n")
            f.write("# 详细信息\n\n")
        
        # 再次处理每个试验，添加详细内容到汇总文件
        for i, trial in enumerate(trials):
            if not trial.get('试验ID'):
                continue
                
            # 读取单独文件内容
            filename = f"{output_dir}/{trial['登记号']}_detail.md"
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as source:
                    content = source.read()
                    
                    # 添加锚点
                    with open(summary_file, 'a', encoding='utf-8') as target:
                        target.write(f"<a id='{trial['登记号']}'></a>\n\n")
                        target.write(content)
                        target.write("\n---\n\n")
        
        logging.info(f"已生成汇总文件: {summary_file}")
        return True

    def create_comprehensive_summary(self, trials, output_dir, search_keywords, filter_keywords):
        """
        创建一个全面的汇总文件，包含所有试验的基本信息和详细链接
        
        Args:
            trials: 临床试验列表
            output_dir: 输出目录
            search_keywords: 搜索关键词
            filter_keywords: 过滤关键词列表
        
        Returns:
            str: 汇总文件路径
        """
        # 确保输出目录存在
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 创建汇总文件
        today = datetime.datetime.now().strftime('%Y%m%d')
        summary_file = f"{today}_{search_keywords}_comprehensive.md"
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            # 标题和基本信息
            f.write(f"# {search_keywords} 相关临床试验综合报告\n\n")
            f.write(f"**搜索日期**: {datetime.datetime.now().strftime('%Y-%m-%d')}\n")
            f.write(f"**搜索关键词**: {search_keywords}\n")
            if filter_keywords:
                f.write(f"**过滤关键词**: {', '.join(filter_keywords)}\n")
            f.write(f"**试验总数**: {len(trials)}\n\n")
            
            # 目录
            f.write("## 目录\n\n")
            f.write("1. [试验概览](#试验概览)\n")
            f.write("2. [试验状态分布](#试验状态分布)\n")
            f.write("3. [研究机构分布](#研究机构分布)\n")
            f.write("4. [详细试验列表](#详细试验列表)\n\n")
            
            # 试验概览
            f.write("<a id='试验概览'></a>\n")
            f.write("## 试验概览\n\n")
            
            # 按试验状态分组
            status_groups = {}
            for trial in trials:
                status = trial.get('试验状态', '未知')
                if status not in status_groups:
                    status_groups[status] = []
                status_groups[status].append(trial)
            
            # 试验状态分布
            f.write("<a id='试验状态分布'></a>\n")
            f.write("## 试验状态分布\n\n")
            f.write("| 试验状态 | 数量 | 百分比 |\n")
            f.write("|---------|------|--------|\n")
            
            for status, trials_in_status in status_groups.items():
                percentage = len(trials_in_status) / len(trials) * 100
                f.write(f"| {status} | {len(trials_in_status)} | {percentage:.1f}% |\n")
            
            f.write("\n")
            
            # 研究机构分布
            f.write("<a id='研究机构分布'></a>\n")
            f.write("## 研究机构分布\n\n")
            
            # 收集所有机构
            all_institutions = {}
            for trial in trials:
                # 从详细信息文件中读取研究者信息
                detail_file = f"{output_dir}/{trial['登记号']}_detail.md"
                if os.path.exists(detail_file):
                    with open(detail_file, 'r', encoding='utf-8') as detail_f:
                        content = detail_f.read()
                        # 简单解析，查找参加机构部分
                        if "### 参加机构" in content:
                            inst_section = content.split("### 参加机构")[1].split("##")[0]
                            # 提取机构名称
                            import re
                            inst_matches = re.findall(r'\*\*\d+\.\s+(.*?)\*\*', inst_section)
                            for inst in inst_matches:
                                if inst not in all_institutions:
                                    all_institutions[inst] = 0
                                all_institutions[inst] += 1
            
            # 显示机构分布
            if all_institutions:
                # 按参与试验数量排序
                sorted_institutions = sorted(all_institutions.items(), key=lambda x: x[1], reverse=True)
                
                f.write("| 研究机构 | 参与试验数量 |\n")
                f.write("|----------|------------|\n")
                
                for inst, count in sorted_institutions[:20]:  # 显示前20个机构
                    f.write(f"| {inst} | {count} |\n")
                
                if len(sorted_institutions) > 20:
                    f.write("| ... | ... |\n")
                
                f.write("\n")
            else:
                f.write("未找到研究机构分布信息\n\n")
            
            # 详细试验列表
            f.write("<a id='详细试验列表'></a>\n")
            f.write("## 详细试验列表\n\n")
            
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
                f.write(f"### {trial['试验通俗题目']}\n\n")
                f.write(f"- **登记号**: {trial['登记号']}\n")
                f.write(f"- **药物名称**: {trial['药物名称']}\n")
                f.write(f"- **试验状态**: {trial['试验状态']}\n")
                f.write(f"- **适应症**: {trial['适应症']}\n")
                
                # 添加详情链接
                detail_file = f"{output_dir}/{trial['登记号']}_detail.md"
                if os.path.exists(detail_file):
                    f.write(f"- [查看详细信息]({detail_file})\n")
                
                f.write("\n")
        
        logging.info(f"已生成综合汇总文件: {summary_file}")
        return summary_file

def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(description='搜索中国药物临床试验登记与信息公示平台并提取详细信息')
    parser.add_argument('-k', '--keywords', help='搜索关键词')
    parser.add_argument('-f', '--filter', help='过滤关键词，用空格分隔多个关键词')
    parser.add_argument('-i', '--indication', help='适应症')
    parser.add_argument('-r', '--reg_no', help='登记号')
    parser.add_argument('-s', '--state', help='试验状态')
    parser.add_argument('-d', '--drugs-name', help='药物名称')
    parser.add_argument('-c', '--ckm-index', default="1", help='ckm_index参数，默认为1')
    parser.add_argument('-p', '--pages', type=int, help='最大页数，如果不指定则获取所有页面')
    parser.add_argument('-o', '--output', help='输出文件名，默认为日期_关键词_details.md')
    parser.add_argument('--detail-dir', help='详细信息输出目录，默认为output/details')
    parser.add_argument('-l', '--local', action='store_true', help='使用本地文件作为响应内容，而不是从网站获取')
    parser.add_argument('--no-auto-pages', action='store_true', help='不自动获取所有页面，只获取第一页')
    parser.add_argument('--debug', action='store_true', help='调试模式，保存更多中间文件')

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
    detail_extractor = ChinaDrugTrialsDetailExtractor()

    print(f"搜索关键词: {search_keywords}")
    print(f"过滤关键词: {', '.join(filter_keywords)}")

    # 搜索临床试验
    trials = searcher.search_all_pages(
        search_keywords,
        filter_keywords,
        args.pages,
        args.indication or "",
        args.reg_no or "",
        args.state or "",
        args.drugs_name or "",
        args.ckm_index,
        args.local,  # 使用本地文件
        not args.no_auto_pages  # 自动获取所有页面
    )

    if not trials:
        print(f"未找到与过滤关键词相关的临床试验: {', '.join(filter_keywords)}")
        sys.exit(0)

    # 格式化为Markdown并保存基本信息
    # 使用format_trials_markdown函数而不是searcher的方法
    from chinadrugtrials_extract import format_trials_markdown
    markdown = format_trials_markdown(trials)
    
    # 保存基本信息到文件
    today = datetime.datetime.now().strftime('%Y%m%d')
    if args.output:
        output_file = args.output
    else:
        output_file = f"{today}_{search_keywords}_{'_'.join(filter_keywords)}.md"

    # 确保输出文件保存在output目录下
    output_file = os.path.join(detail_extractor.output_dir, output_file)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown)

    print(f"成功提取 {len(trials)} 个临床试验基本信息并保存到 {output_file}")

    # 处理详细信息
    detail_dir = args.detail_dir or os.path.join(detail_extractor.output_dir, "details")
    # 确保详细信息目录存在
    if not os.path.exists(detail_dir):
        os.makedirs(detail_dir)
        logging.info(f"创建详细信息目录: {detail_dir}")
    
    print(f"开始提取详细信息并保存到 {detail_dir} 目录...")
    
    # 处理详细信息
    detail_extractor.process_trials_with_details(trials, detail_dir)
    
    # 生成汇总文件
    summary_file = os.path.join(detail_extractor.output_dir, f"{today}_{search_keywords}_details.md")
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(f"# {search_keywords} 相关临床试验详细信息\n\n")
        f.write(f"搜索关键词: {search_keywords}\n")
        f.write(f"过滤关键词: {', '.join(filter_keywords)}\n\n")
        f.write(f"共找到 {len(trials)} 个相关临床试验\n\n")
        
        # 添加详细信息链接
        f.write("## 详细信息链接\n\n")
        for trial in trials:
            if trial.get('试验ID'):
                detail_file = f"{detail_dir}/{trial['登记号']}_detail.md"
                if os.path.exists(detail_file):
                    # 使用相对路径
                    rel_path = os.path.relpath(detail_file, os.path.dirname(summary_file))
                    f.write(f"- [{trial['试验通俗题目']}]({rel_path})\n")
    
    print(f"成功生成汇总文件: {summary_file}")

if __name__ == "__main__":
    main()
