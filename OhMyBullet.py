import calendar
from collections import defaultdict
from datetime import datetime, timedelta
import os
import re
import sys
from matplotlib import pyplot as plt
import numpy as np
import seaborn as sns
import toml


def extract_pie_data(file_path):
    # 从文件读取Markdown文本
    with open(file_path, 'r', encoding='utf-8') as file:
        markdown_text = file.read()

    # 匹配 pie 代码块的正则表达式
    pie_block_pattern = re.compile(
        r'```mermaid\s+pie\s+showData\s+(.*?)```', 
        re.DOTALL
    )

    # 匹配数据行的正则表达式
    data_line_pattern = re.compile(
    r'^\s*"(.+?)"\s*:\s*(\d+)\s*$',
    re.MULTILINE
    )

    pie_blocks = pie_block_pattern.findall(markdown_text)
    pie_data = {}

    for block in pie_blocks:
        # 提取标题
        title_match = re.search(r'title\s+(.*)', block)
        title = title_match.group(1).strip() if title_match else "Unknown"

        # 提取数据行
        data_lines = data_line_pattern.findall(block)
        data_dict = {key.strip(): int(value) for key, value in data_lines}

        pie_data[title] = data_dict

    return pie_data


def qeury(file_path, assets_path, schedule):
    print(f"Querying the file path: {file_path}")
    print(f"Querying for schedule: {schedule}")
    
    if schedule == "week":
        # 处理 "week" 参数
        today = datetime.today()
        start_of_week = today - timedelta(days=today.weekday())
        weeks = [start_of_week + timedelta(days=i) for i in range(0, 7)]
        weeks = [day.strftime('%m-%d') for day in weeks]
        
        print(f"today is: {today.strftime('%m-%d')}")
        print(f"the week begin from {weeks[0]} to {weeks[-1]}")
        pie_date = extract_pie_data(file_path)
        merged_dic = defaultdict(int)
        
        for day in weeks:
            if day not in pie_date:
                if day == today.strftime('%m-%d'):
                    print(f">> WARNING: {day} is today, but have not created date.")
                else:
                     print(f"{day} have not comed, so not load data.")
                continue
            else:
                today_dic = pie_date[day]
                if len(today_dic) == 0:
                    print(f">> WARNING: {day} data is empty.")
            for k, d in today_dic.items():
                 merged_dic[k] += d
        
        print(">> Result: the merged data for the week is:")
        merged_dic = dict(merged_dic) 
        print(merged_dic)
        return merged_dic
    
    elif schedule == "month":
        # 处理 "month" 参数
        today = datetime.today()
        _, days_in_month = calendar.monthrange(today.year, today.month)        
        month = [datetime(today.year, today.month, day).strftime("%m-%d") for day in range(1, days_in_month+1)]
        everyday_total_times = {day: 0 for day in month}
        
        print(f"today is: {today.strftime('%m-%d')}")
        print(f"the month begin from {month[0]} to {month[-1]}")
        pie_date = extract_pie_data(file_path)
        merged_dic = defaultdict(int)
        
        for day in month:
            if day not in pie_date:
                if day == today.strftime('%m-%d'):
                    print(f">> WARNING: {day} is today, but have not created date.")
                continue
            else:
                today_dic = pie_date[day]
                if len(today_dic) == 0:
                    print(f">> WARNING: {day} data is empty.")
                everyday_total_times[day] += sum(today_dic.values())
                for k, d in today_dic.items():
                    merged_dic[k] += d
        
        print(">> Result: the merged data for the week is:")
        merged_dic = dict(merged_dic) 
        print(merged_dic)
        image_path = generate_hotmap(assets_path, everyday_total_times)
        return merged_dic
        
    elif schedule == "all":
        pie_date = extract_pie_data(file_path)
        all_date = list(pie_date.keys())
        print(f"the date from {all_date[0]} to {all_date[-1]}")
        
        merged_dic = defaultdict(int)

        for _, data_value in pie_date.items():
            for k, d in data_value.items():
                 merged_dic[k] += d
        
        merged_dic = dict(merged_dic) 
        print(merged_dic)
        return merged_dic
        
    elif schedule == "today":
        # 处理 "today" 参数
        today = datetime.today()
        today = today.strftime('%m-%d')
        print(f"Today is: {today}")
        
        pie_date = extract_pie_data(file_path)
        try:
            today_dic = pie_date[today]
        except KeyError as e:
            print(f"There is no data for {today}.")
            sys.exit((1))
        print(today_dic)
        return today_dic
        
    else:
        try:
            date_param = datetime.strptime(schedule, "%m-%d")
            date_param = date_param.strftime('%m-%d')
            
            pie_date = extract_pie_data(file_path)
            try:
                date_dic = pie_date[date_param]
            except KeyError as e:
                print(f"There is no data for {date_param}.")
                sys.exit((1))
            print(date_dic)
            return date_dic
        except ValueError:
            print("Incorrect parameter, please specify date in 'week', 'all', 'today' or MM-DD format.")



def write_markdown(input_dict, title, filename, assets_path):
    image_path = get_assets_path(assets_path)
    with open(filename, 'w', encoding='utf-8') as file:
        file.write("# Query And Statistics\n\n")
        file.write("Statistical results\n\n")
        file.write(f"Total Time is: {round(sum([value for _, value in input_dict.items()]) / 60.0, 2)} hours\n\n")
        file.write("Pie: \n")
        file.write("```mermaid\n")
        file.write("pie showData\n")
        file.write(f'    title query {title}\n')
        
        for key, value in input_dict.items():
            file.write(f'    "{key}" : {value}\n')
        
        file.write("```\n\n")
        file.write("HotMap:\n")
        embeded_hotmap = f'<img src="{image_path}" alt="HopMap Image" style="zoom: 75%;" /> \n'
        file.write(f'{embeded_hotmap}')


def read_toml():
    with open("config.toml", "r") as f:
        config = toml.load(f)
    return config


def get_assets_path(assets_path):
    today = datetime.today()
    dir_path = assets_path
    img_file = f"month_{today.month}_heatmap.png"
    image_path = os.path.join(dir_path, img_file)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    return image_path


def generate_hotmap(assets_path, input_dict):
    # 获取当前日期
    today = datetime.today()

    # 获取当前月份的第一天是星期几
    first_weekday, _ = calendar.monthrange(today.year, today.month)
    first_weekday = int(first_weekday)
    hot_value = [value for _, value in input_dict.items()]
    hot_index = 0
    hot_max_index = len(hot_value) - 1
    data = np.zeros((6, 7))
    for i in range(7):
        if i == 0:
            for j in range(first_weekday, 7):
                data[i, j] = hot_value[hot_index]
                hot_index += 1
        else:
            for j in range(0, 7):
                if hot_index > hot_max_index:
                    break
                data[i, j] = hot_value[hot_index]
                hot_index += 1
    
    data_min = data.min()
    data_max = data.max()
    normalized_data = (data - data_min) / (data_max - data_min)
    
    plt.figure(figsize=(10, 8))
    ax = sns.heatmap(normalized_data, annot=False, cmap="YlGnBu", linewidths=0.1, linecolor='gray')
    for line in ax.get_lines():
        line.set_alpha(0.3)  # 设置透明度，0.0 完全透明，1.0 完全不透明
    
    image_path = get_assets_path(assets_path)
    plt.savefig(f"{image_path}")


def main():
    config = read_toml()
    file_path = config.get("file_path")
    schedule = config.get("schedule")
    assets_path = config.get("assets_path")
    qeury_dic = qeury(file_path, assets_path, schedule)
    write_markdown(qeury_dic, schedule, f'{schedule}.md', assets_path)
    


if __name__ == '__main__':
    main()
    print("The program has completed execution.")
    input("Press Enter to exit...")
