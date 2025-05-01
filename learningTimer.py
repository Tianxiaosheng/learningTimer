import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import time
import json
from datetime import datetime, date, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
from matplotlib.font_manager import FontProperties
import matplotlib
import platform
from pathlib import Path
import numpy as np

class LearningTimer:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Learning Timer")
        
        # 添加标志位，用于区分是否正在进行程序控制的窗口调整
        self.is_programmatic_resize = False
        self.is_shutting_down = False
        
        # 设置初始尺寸
        self.window_sizes = {
            'timer': {
                'width': 280,
                'height': 280
            },
            'stats': {
                'width': 800,
                'height': 600
            }
        }
        
        # 设置初始窗口大小和模式
        self.current_mode = 'timer'
        # 强制设置初始窗口大小为计时器尺寸
        self.root.geometry(f"{self.window_sizes['timer']['width']}x{self.window_sizes['timer']['height']}")
        
        # 绑定窗口大小变化事件
        self.root.bind('<Configure>', self.on_window_resize)
        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 设置DPI缩放以提高文字清晰度
        plt.rcParams['figure.dpi'] = 120
        plt.rcParams['savefig.dpi'] = 120
        
        # 设置主题颜色 - 更新为科技感配色
        self.colors = {
            'bg': '#FFFFFF',           # 白色背景
            'primary': '#007AFF',      # Apple 蓝
            'secondary': '#34C759',    # Apple 绿
            'text': '#000000',         # 黑色文字
            'text_secondary': '#666666', # 次要文字颜色
            'accent': '#FF3B30',       # Apple 红
            'chart_bg': '#F5F5F7',     # 浅灰色图表背景
            'grid': '#E5E5EA',         # 网格线颜色
            'chart_main': '#5856D6',   # 科技紫
            'chart_fill': '#5856D6',   # 科技紫（透明）
            'session_time': '#2C2C2E', # 深灰色（本次学习时间）
            'chart_bar': '#5856D6',    # 柱状图颜色
            'chart_bar_highlight': '#7A79E5'  # 柱状图高亮色
        }
        
        # 配置按钮样式以修复 macOS 警告
        self.style = ttk.Style()
        if platform.system() == 'Darwin':  # 仅在 macOS 上应用特殊样式
            self.style.configure('MacOS.TButton',
                               padding=(2, 0),  # 水平内边距2，垂直内边距0
                               height=0,        # 让按钮高度自适应
                               borderwidth=4)   # 减小边框宽度
            
            self.style.configure('Compact.TButton',
                               padding=(1, 0),  # 更小的水平内边距
                               height=0,        # 让按钮高度自适应
                               borderwidth=3)   # 更小的边框宽度
            
        # 设置窗口样式
        self.root.configure(bg=self.colors['bg'])
        self.root.option_add('*TButton*background', self.colors['bg'])
        self.root.option_add('*TButton*foreground', self.colors['text'])
        
        # 设置全局样式
        self.style = ttk.Style()
        
        # 设置中文字体
        self.setup_chinese_font()
        
        # 初始化变量
        self.is_timing = False
        self.start_time = 0
        self.accumulated_time = 0
        self.current_session_start = 0  # 当前学习段的开始时间
        self.current_session_time = 0   # 当前学习段的持续时间
        self.today = date.today().strftime("%Y-%m-%d")
        self.today_sessions = []        # 记录今天的学习时间段 [(start_timestamp, end_timestamp), ...]
        
        # 初始化数据文件路径
        self.data_file = 'learning_data.json'
        
        # 创建菜单栏
        self.create_menu()
        
        # 设置matplotlib中文字体
        self.setup_matplotlib_font()
        
        # 创建并设置主Notebook
        self.create_notebook()
        
        # 加载今日数据
        self.load_data()
        
        # 更新时间显示
        self.update_time()
        
    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="选择数据保存位置", command=self.choose_save_location)
        file_menu.add_command(label="导入历史数据", command=self.import_data)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)
        
    def choose_save_location(self):
        new_file = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            initialfile="learning_data.json",
            title="选择数据保存位置"
        )
        if new_file:
            # 如果原数据文件存在，复制数据到新位置
            if os.path.exists(self.data_file):
                try:
                    with open(self.data_file, 'r') as f:
                        data = json.load(f)
                    with open(new_file, 'w') as f:
                        json.dump(data, f)
                except Exception as e:
                    messagebox.showerror("错误", f"复制数据失败: {str(e)}")
                    return
            
            self.data_file = new_file
            messagebox.showinfo("成功", "数据保存位置已更改")
            
    def import_data(self):
        import_file = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json")],
            title="选择要导入的数据文件"
        )
        if import_file:
            try:
                with open(import_file, 'r') as f:
                    import_data = json.load(f)
                
                # 合并数据
                current_data = {}
                if os.path.exists(self.data_file):
                    with open(self.data_file, 'r') as f:
                        current_data = json.load(f)
                
                # 更新现有数据
                current_data.update(import_data)
                
                # 保存合并后的数据
                with open(self.data_file, 'w') as f:
                    json.dump(current_data, f)
                
                messagebox.showinfo("成功", "数据导入成功")
                self.update_stats()
            except Exception as e:
                messagebox.showerror("错误", f"导入数据失败: {str(e)}")

    def setup_timer_page(self):
        # 主框架
        main_frame = ttk.Frame(self.timer_frame, style='Custom.TFrame')
        main_frame.pack(expand=True, fill='both', padx=10, pady=10)
        
        # 标题标签
        title_label = tk.Label(main_frame, 
                             text="今日累计学习时间", 
                             font=(self.font_family, 12, 'bold'),
                             fg=self.colors['primary'],
                             bg=self.colors['bg'])
        title_label.pack(pady=(0, 5))
        
        # 累计时间显示容器
        time_container = ttk.Frame(main_frame, style='Custom.TFrame')
        time_container.pack(expand=True, fill='both', pady=5)
        time_container.grid_columnconfigure(0, weight=1)  # 使列可以居中
        
        # 累计时间显示标签
        self.time_label = tk.Label(time_container, 
                                 text="00:00:00", 
                                 font=('Consolas', 32, 'bold'),
                                 fg=self.colors['secondary'],
                                 bg=self.colors['bg'],
                                 width=8)  # 设置固定字符宽度
        self.time_label.grid(row=0, column=0)
        
        # 当前学习时间容器
        current_session_container = ttk.Frame(main_frame, style='Custom.TFrame')
        current_session_container.pack(fill='both', pady=(0, 5))
        current_session_container.grid_columnconfigure(0, weight=1)  # 使列可以居中
        
        # 当前学习时间标题 - 更新样式
        current_session_title = tk.Label(current_session_container,
                                       text="本次学习时间",
                                       font=(self.font_family, 10),
                                       fg=self.colors['session_time'],
                                       bg=self.colors['bg'])
        current_session_title.grid(row=0, column=0)
        
        # 当前学习时间显示 - 更新样式
        self.current_session_label = tk.Label(current_session_container,
                                            text="00:00:00",
                                            font=('Consolas', 16),
                                            fg=self.colors['session_time'],
                                            bg=self.colors['bg'],
                                            width=8)
        self.current_session_label.grid(row=1, column=0)
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame, style='Custom.TFrame')
        button_frame.pack(pady=(5, 0))
        
        # 配置按钮样式
        button_style = 'MacOS.TButton' if platform.system() == 'Darwin' else 'TButton'
        
        # 开始/暂停按钮
        self.start_button = ttk.Button(button_frame, 
                                     text="开始",
                                     command=self.toggle_timing,
                                     style=button_style)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        # 重置按钮
        self.reset_button = ttk.Button(button_frame, 
                                     text="重置",
                                     command=self.reset_timer,
                                     style=button_style)
        self.reset_button.pack(side=tk.LEFT, padx=5)
        
    def setup_stats_page(self):
        # 统计页面主框架
        self.stats_main_frame = ttk.Frame(self.stats_frame, style='Custom.TFrame')
        self.stats_main_frame.pack(expand=True, fill='both', padx=20, pady=20)
        
        # 创建Notebook用于切换不同统计视图
        self.stats_notebook = ttk.Notebook(self.stats_main_frame)
        self.stats_notebook.pack(expand=True, fill='both')
        
        # 创建图表框架
        self.weekly_frame = ttk.Frame(self.stats_notebook)
        self.daily_frame = ttk.Frame(self.stats_notebook)
        
        # 预先创建图表对象
        self.setup_weekly_chart()
        self.setup_daily_chart()
        
        # 添加标签页
        self.stats_notebook.add(self.weekly_frame, text='周统计')
        self.stats_notebook.add(self.daily_frame, text='日统计')
        
        # 绑定切换事件
        self.stats_notebook.bind('<<NotebookTabChanged>>', self.on_stats_tab_changed)
        
        # 创建日期导航框架
        self.nav_frame = ttk.Frame(self.daily_frame)
        self.nav_frame.pack(fill='x', pady=5)
        
        # 使用紧凑按钮样式
        button_style = 'Compact.TButton' if platform.system() == 'Darwin' else 'TButton'
        
        # 导航按钮
        self.prev_day_btn = ttk.Button(self.nav_frame, 
                                     text="◀", 
                                     command=lambda: self.change_date(-1),
                                     style=button_style)
        self.prev_day_btn.pack(side=tk.LEFT, padx=5)
        
        self.date_label = ttk.Label(self.nav_frame, text=self.today)
        self.date_label.pack(side=tk.LEFT, padx=10)
        
        self.next_day_btn = ttk.Button(self.nav_frame, 
                                     text="▶", 
                                     command=lambda: self.change_date(1),
                                     style=button_style)
        self.next_day_btn.pack(side=tk.LEFT, padx=5)

    def setup_weekly_chart(self):
        """预先设置周统计图表"""
        weekly_chart_frame = ttk.Frame(self.weekly_frame)
        weekly_chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.figure_weekly = plt.Figure(figsize=(8, 5))
        self.ax_weekly = self.figure_weekly.add_subplot(111)
        self.setup_plot_style(self.ax_weekly)
        self.canvas_weekly = FigureCanvasTkAgg(self.figure_weekly, weekly_chart_frame)
        self.canvas_weekly.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def setup_daily_chart(self):
        """预先设置日统计图表"""
        daily_chart_frame = ttk.Frame(self.daily_frame)
        daily_chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.figure_daily = plt.Figure(figsize=(8, 7))
        gs = self.figure_daily.add_gridspec(2, 1, height_ratios=[2, 1], hspace=0.3)
        self.ax_daily = self.figure_daily.add_subplot(gs[0])
        self.ax_info = self.figure_daily.add_subplot(gs[1])
        self.setup_plot_style(self.ax_daily)
        self.setup_plot_style(self.ax_info)
        self.canvas_daily = FigureCanvasTkAgg(self.figure_daily, daily_chart_frame)
        self.canvas_daily.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def setup_plot_style(self, ax):
        ax.set_facecolor(self.colors['chart_bg'])
        ax.grid(True, linestyle='--', alpha=0.3, color=self.colors['grid'])
        ax.tick_params(colors=self.colors['text'])
        for spine in ax.spines.values():
            spine.set_color(self.colors['grid'])

    def toggle_timing(self):
        if not self.is_timing:
            self.start_time = time.time()
            self.current_session_start = time.time()
            self.current_session_time = 0
            self.is_timing = True
            self.start_button.configure(text="暂停")
            self.style.configure('Primary.TButton', background=self.colors['accent'])
        else:
            end_time = time.time()
            self.accumulated_time += end_time - self.start_time
            self.current_session_time = end_time - self.current_session_start
            self.is_timing = False
            self.start_button.configure(text="继续")
            self.style.configure('Primary.TButton', background=self.colors['primary'])
            # 记录本次学习时间段
            self.today_sessions.append((self.current_session_start, end_time))
            self.save_data()
            
    def reset_timer(self):
        """重置当天的所有学习记录"""
        if messagebox.askyesno("确认重置", "确定要重置今天的所有学习记录吗？\n这将清除今天的所有学习数据。"):
            # 停止计时（如果正在计时）
            self.is_timing = False
            self.start_time = 0
            self.accumulated_time = 0
            self.current_session_time = 0
            self.current_session_start = 0
            
            # 清除今天的学习记录
            self.today_sessions = []
            
            # 更新按钮状态
            self.start_button.configure(text="开始")
            self.style.configure('Primary.TButton', background=self.colors['primary'])
            
            # 从数据文件中删除今天的记录
            try:
                if os.path.exists(self.data_file):
                    with open(self.data_file, 'r') as f:
                        data = json.load(f)
                    
                    # 删除今天的数据
                    if self.today in data:
                        del data[self.today]
                    
                    # 保存更新后的数据
                    with open(self.data_file, 'w') as f:
                        json.dump(data, f)
                
                # 强制更新时间显示
                self.time_label.config(text="00:00:00")
                self.current_session_label.config(text="00:00:00")
                
                # 强制更新统计图表
                self.update_daily_stats(self.today)  # 更新日统计
                self.update_weekly_stats(data)       # 更新周统计
                
            except Exception as e:
                messagebox.showerror("错误", f"重置数据失败: {str(e)}")
        
    def update_time(self):
        if self.is_timing:
            current_time = time.time()
            total_time = current_time - self.start_time + self.accumulated_time
            session_time = current_time - self.current_session_start
        else:
            total_time = self.accumulated_time
            session_time = self.current_session_time
            
        # 更新总计时间显示
        hours = int(total_time // 3600)
        minutes = int((total_time % 3600) // 60)
        seconds = int(total_time % 60)
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        self.time_label.config(text=time_str)
        
        # 更新本次学习时间显示
        session_hours = int(session_time // 3600)
        session_minutes = int((session_time % 3600) // 60)
        session_seconds = int(session_time % 60)
        session_str = f"{session_hours:02d}:{session_minutes:02d}:{session_seconds:02d}"
        self.current_session_label.config(text=session_str)
        
        self.root.after(1000, self.update_time)
        
    def load_data(self):
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    if self.today in data:
                        today_data = data[self.today]
                        self.accumulated_time = today_data['total_time']
                        self.today_sessions = today_data.get('sessions', [])
            self.update_stats()
        except Exception as e:
            messagebox.showerror("错误", f"加载数据失败: {str(e)}")
            
    def save_data(self):
        data = {}
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                data = json.load(f)
        
        # 保存当日数据，包括总时间和学习时间段
        data[self.today] = {
            'total_time': self.accumulated_time,
            'sessions': self.today_sessions
        }
        
        try:
            with open(self.data_file, 'w') as f:
                json.dump(data, f)
            self.update_stats()
        except Exception as e:
            messagebox.showerror("错误", f"保存数据失败: {str(e)}")
        
    def update_stats(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                data = json.load(f)
            
            # 更新周统计
            self.update_weekly_stats(data)
            
            # 更新日统计（默认显示今天）
            self.update_daily_stats(self.today)
            
    def update_weekly_stats(self, data):
        dates = list(data.keys())[-7:]
        times = [data[d]['total_time']/3600 for d in dates]  # 转换为小时
        
        self.ax_weekly.clear()
        self.setup_plot_style(self.ax_weekly)
        
        # 绘制渐变柱状图
        bars = self.ax_weekly.bar(dates, times, color=self.colors['chart_bar'], alpha=0.8)
        
        # 添加高光效果
        for bar in bars:
            x = bar.get_x()
            y = bar.get_height()
            width = bar.get_width()
            
            # 在柱子上显示具体时间
            self.ax_weekly.text(x + width/2., y + 0.1,  # 稍微上移文字位置
                              f'{y:.1f}h',
                              ha='center', va='bottom',
                              fontsize=10, color=self.colors['text'],
                              weight='bold')  # 加粗文字
        
        self.ax_weekly.set_xlabel('日期', fontsize=12, color=self.colors['text'], labelpad=10)
        self.ax_weekly.set_ylabel('学习时间 (小时)', fontsize=12, color=self.colors['text'], labelpad=10)
        self.ax_weekly.set_title('最近7天学习时间统计', pad=20, fontsize=14, color=self.colors['text'])
        
        # 调整刻度标签
        plt.setp(self.ax_weekly.xaxis.get_majorticklabels(), rotation=45, ha='right', fontsize=10)
        plt.setp(self.ax_weekly.yaxis.get_majorticklabels(), fontsize=10)
        
        # 调整图表边距
        self.figure_weekly.subplots_adjust(bottom=0.2, left=0.12, right=0.95, top=0.9)
        self.canvas_weekly.draw()

    def change_date(self, delta):
        """切换到前一天或后一天"""
        try:
            current_date = datetime.strptime(self.date_label.cget("text"), "%Y-%m-%d")
            new_date = current_date + timedelta(days=delta)
            self.date_label.config(text=new_date.strftime("%Y-%m-%d"))
            self.update_daily_stats(new_date.strftime("%Y-%m-%d"))
        except ValueError:
            messagebox.showerror("错误", "日期格式无效")

    def on_stats_tab_changed(self, event):
        """当切换统计子页面时的处理"""
        try:
            current_tab = self.stats_notebook.select()
            tab_name = self.stats_notebook.tab(current_tab, "text")
            
            # 使用after方法延迟更新图表，避免界面卡顿
            if tab_name == '周统计':
                self.root.after(10, self.update_weekly_stats_if_needed)
            else:
                self.root.after(10, lambda: self.update_daily_stats(self.today))
                
        except Exception as e:
            print(f"切换统计子页面失败: {str(e)}")

    def update_weekly_stats_if_needed(self):
        """仅在需要时更新周统计"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                self.update_weekly_stats(data)
        except Exception as e:
            print(f"更新周统计失败: {str(e)}")

    def on_main_tab_changed(self, event):
        """当切换主页面时调整窗口大小"""
        try:
            current_tab = self.notebook.select()
            tab_name = self.notebook.tab(current_tab, "text")
            
            # 更新当前模式并调整窗口大小
            new_mode = 'stats' if tab_name == '统计' else 'timer'
            if new_mode != self.current_mode:
                # 切换到新模式
                self.current_mode = new_mode
                # 使用新模式的尺寸
                size = self.window_sizes[new_mode]
                self.set_window_size(size['width'], size['height'])
        except Exception as e:
            print(f"切换主页面失败: {str(e)}")

    def update_daily_stats(self, target_date):
        if not os.path.exists(self.data_file):
            return
            
        with open(self.data_file, 'r') as f:
            data = json.load(f)
            
        if target_date not in data:
            messagebox.showinfo("提示", "该日期没有学习记录")
            return
            
        day_data = data[target_date]
        sessions = day_data.get('sessions', [])
        
        # 更新日期导航标签
        self.date_label.config(text=target_date)
        
        # 清除现有图表
        self.ax_daily.clear()
        self.ax_info.clear()
        self.setup_plot_style(self.ax_daily)
        self.setup_plot_style(self.ax_info)
        
        # 创建时间轴（以分钟为单位）
        minutes_in_day = 24 * 60
        time_points = list(range(minutes_in_day + 1))  # 包含最后一个点以使图形完整
        activity = [0] * (minutes_in_day + 1)  # 0表示未学习，1表示学习中
        
        # 统计每个时间点是否有学习活动
        for start, end in sessions:
            start_dt = datetime.fromtimestamp(start)
            end_dt = datetime.fromtimestamp(end)
            
            # 确保只统计当天的时间
            target_date_obj = datetime.strptime(target_date, "%Y-%m-%d").date()
            if start_dt.date() < target_date_obj:
                start_dt = datetime.combine(target_date_obj, datetime.min.time())
            if end_dt.date() > target_date_obj:
                end_dt = datetime.combine(target_date_obj, datetime.max.time())
            
            # 转换为分钟
            start_minute = start_dt.hour * 60 + start_dt.minute
            end_minute = end_dt.hour * 60 + end_dt.minute
            
            # 标记学习时间段
            for i in range(start_minute, end_minute + 1):
                if i <= minutes_in_day:
                    activity[i] = 1
        
        # 绘制时间分布图
        self.ax_daily.step(
            [x/60 for x in time_points],  # 转换回小时以便显示
            activity,
            where='post',
            color=self.colors['chart_main'],
            linewidth=2,
            alpha=0.8
        )
        
        # 填充颜色
        self.ax_daily.fill_between(
            [x/60 for x in time_points],
            activity,
            step='post',
            alpha=0.2,
            color=self.colors['chart_fill']
        )
        
        # 设置坐标轴
        self.ax_daily.set_xlim(0, 24)
        self.ax_daily.set_ylim(-0.1, 1.1)
        
        # 设置x轴刻度（每小时一个刻度）
        hours = range(0, 25)
        self.ax_daily.set_xticks(hours)
        self.ax_daily.set_xticklabels([f'{h:02d}:00' for h in hours])
        plt.setp(self.ax_daily.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # 设置y轴刻度
        self.ax_daily.set_yticks([0, 1])
        self.ax_daily.set_yticklabels(['未学习', '学习中'])
        
        # 设置标签
        self.ax_daily.set_xlabel('时间', fontsize=10)
        self.ax_daily.set_ylabel('学习状态', fontsize=10)
        
        # 添加网格
        self.ax_daily.grid(True, linestyle='--', alpha=0.3, color=self.colors['grid'])
        
        # 设置标题
        title = f'{target_date} 学习时间分布'
        self.ax_daily.set_title(title, pad=15, fontsize=12)
        
        # 计算统计信息
        total_time = day_data['total_time'] / 3600  # 转换为小时
        session_durations = [(end - start) / 3600 for start, end in sessions]  # 转换为小时
        avg_session = sum(session_durations) / len(session_durations) if session_durations else 0
        
        # 更新统计信息显示
        stats_text = f'总学习时间: {total_time:.1f}小时\n'
        stats_text += f'学习次数: {len(sessions)}次\n'
        stats_text += f'平均每次时长: {avg_session:.1f}小时'
        
        self.ax_info.text(0.5, 0.5, stats_text,
                         horizontalalignment='center',
                         verticalalignment='center',
                         transform=self.ax_info.transAxes,
                         fontsize=12,
                         weight='bold')
        self.ax_info.set_axis_off()
        
        # 调整图表边距
        self.figure_daily.subplots_adjust(bottom=0.2, left=0.12, right=0.95, top=0.9)
        self.canvas_daily.draw()
        
    def setup_matplotlib_font(self):
        """设置matplotlib的中文字体"""
        system = platform.system()
        
        # 常见中文字体列表
        font_list = {
            'Windows': [
                'Microsoft YaHei',
                'SimHei',
                'KaiTi',
                'SimSun',
                'NSimSun',
                'FangSong'
            ],
            'Darwin': [  # macOS
                'Arial Unicode MS',
                'Heiti TC',
                'Hiragino Sans GB',
                'STHeiti'
            ],
            'Linux': [
                'Noto Sans CJK SC',
                'Noto Sans CJK TC',
                'Noto Sans CJK JP',
                'WenQuanYi Micro Hei',
                'WenQuanYi Zen Hei',
                'Droid Sans Fallback'
            ]
        }
        
        # 获取当前系统的字体列表
        available_fonts = [f.name for f in matplotlib.font_manager.fontManager.ttflist]
        
        # 查找可用的中文字体
        found_font = None
        for font in font_list.get(system, []):
            if font in available_fonts:
                found_font = font
                break
        
        if found_font:
            matplotlib.rc('font', family=found_font)
            plt.rcParams['axes.unicode_minus'] = False
        else:
            # 如果找不到系统字体，尝试使用自带的文泉驿字体
            try:
                # 获取当前脚本所在目录
                current_dir = Path(__file__).parent
                font_path = current_dir / 'fonts' / 'wqy-microhei.ttc'
                
                if not font_path.exists():
                    # 如果字体文件不存在，显示警告并给出安装建议
                    warning_msg = """未找到合适的中文字体，图表中文可能无法正确显示。

建议安装以下字体之一：
Windows: 微软雅黑(Microsoft YaHei)
macOS: Heiti TC 或 Hiragino Sans GB
Linux: 执行 sudo apt-get install fonts-wqy-microhei"""
                    messagebox.showwarning("警告", warning_msg)
                else:
                    # 使用自带的文泉驿字体
                    font_prop = FontProperties(fname=str(font_path))
                    plt.rcParams['font.family'] = font_prop.get_name()
            except Exception as e:
                messagebox.showerror("错误", f"设置字体失败: {str(e)}")

    def setup_chinese_font(self):
        """设置中文字体"""
        system = platform.system()
        
        if system == 'Linux':
            # Linux系统字体优先级
            fonts = [
                'Droid Sans Fallback',   # Android 后备字体，通常支持中文
                'Noto Sans CJK JP',
                'Ubuntu',
                'DejaVu Sans'
            ]
            
            # 尝试安装额外的中文字体
            try:
                os.system('sudo apt-get install -y fonts-droid-fallback > /dev/null 2>&1')
                os.system('fc-cache -fv > /dev/null 2>&1')
            except:
                pass
        else:
            if system == 'Windows':
                fonts = ['Microsoft YaHei', 'SimHei', 'SimSun', 'NSimSun', 'FangSong', 'KaiTi']
            elif system == 'Darwin':  # macOS
                fonts = ['PingFang SC', 'Heiti TC', 'Hiragino Sans GB', 'STHeiti', 'Apple LiGothic']
            else:  # Linux
                fonts = [
                    'Noto Sans CJK JP',
                    'Droid Sans Fallback',
                    'Ubuntu',
                    'DejaVu Sans'
                ]
        
        # 测试字体是否可用
        test_text = "测试文字"
        found_font = None
        
        # 首先尝试使用 Droid Sans Fallback
        if 'Droid Sans Fallback' in [f.name for f in matplotlib.font_manager.fontManager.ttflist]:
            try:
                test_label = tk.Label(self.root, text=test_text, font=('Droid Sans Fallback', 12))
                test_label.pack()
                test_label.update()
                found_font = 'Droid Sans Fallback'
                test_label.destroy()
            except:
                pass
        
        # 如果 Droid Sans Fallback 不可用，尝试其他字体
        if not found_font:
            for font in fonts:
                try:
                    test_label = tk.Label(self.root, text=test_text, font=(font, 12))
                    test_label.pack()
                    test_label.update()
                    found_font = font
                    test_label.destroy()
                    break
                except Exception as e:
                    try:
                        test_label.destroy()
                    except:
                        pass
        
        if not found_font:
            self.font_family = 'TkDefaultFont'
        else:
            self.font_family = found_font
        
        # 配置按钮样式
        button_font = (self.font_family, 10)
        self.style.configure('Primary.TButton',
                          font=button_font,
                          padding=5)
        
        self.style.configure('Secondary.TButton',
                          font=button_font,
                          padding=5)
        
        # 配置框架样式
        self.style.configure('Custom.TFrame',
                          background=self.colors['bg'])

    def on_window_resize(self, event):
        """记录窗口大小变化"""
        try:
            # 如果是程序控制的调整，不记录尺寸
            if self.is_programmatic_resize:
                return
                
            # 仅在用户手动调整窗口大小时记录
            if event.widget == self.root and (event.width != self.root.winfo_width() or event.height != self.root.winfo_height()):
                # 确保窗口大小不会小于最小值
                width = max(event.width, 280)  # 最小宽度
                height = max(event.height, 280)  # 最小高度
                
                # 更新当前模式的尺寸
                self.window_sizes[self.current_mode]['width'] = width
                self.window_sizes[self.current_mode]['height'] = height
                
                # 如果尺寸被调整，强制应用新尺寸
                if width != event.width or height != event.height:
                    self.set_window_size(width, height)
        except Exception as e:
            print(f"处理窗口大小变化失败: {str(e)}")

    def set_window_size(self, width, height):
        """以程序控制方式设置窗口大小"""
        try:
            self.is_programmatic_resize = True
            # 确保窗口大小不会小于最小值
            width = max(width, 280)  # 最小宽度
            height = max(height, 280)  # 最小高度
            self.root.geometry(f"{width}x{height}")
            # 使用after方法在下一个事件循环中重置标志
            self.root.after(100, self.reset_resize_flag)
        except Exception as e:
            print(f"设置窗口大小失败: {str(e)}")

    def reset_resize_flag(self):
        """重置窗口调整标志"""
        self.is_programmatic_resize = False

    def on_closing(self):
        """处理窗口关闭事件"""
        try:
            self.is_shutting_down = True
            self.root.destroy()
        except Exception as e:
            print(f"关闭窗口失败: {str(e)}")

    def create_notebook(self):
        """创建并设置主Notebook"""
        # 创建notebook用于切换界面
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both')
        
        # 创建计时器页面
        self.timer_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.timer_frame, text='计时器')
        
        # 创建统计页面
        self.stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.stats_frame, text='统计')
        
        # 绑定切换事件
        self.notebook.bind('<<NotebookTabChanged>>', self.on_main_tab_changed)
        
        # 设置计时器和统计页面
        self.setup_timer_page()
        self.setup_stats_page()

    def run(self):
        """运行应用程序"""
        try:
            self.root.mainloop()
        except Exception as e:
            print(f"运行应用程序失败: {str(e)}")

if __name__ == "__main__":
    app = LearningTimer()
    app.run()
