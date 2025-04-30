import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import time
import json
from datetime import datetime, date
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
from matplotlib.font_manager import FontProperties
import matplotlib
import platform
from pathlib import Path

class LearningTimer:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Learning Timer")
        self.root.geometry("300x200")  # 减小窗口尺寸
        
        # 设置主题颜色
        self.colors = {
            'bg': '#1E1E1E',       # 深色背景
            'primary': '#00FF9C',   # 科技绿
            'secondary': '#0066FF', # 明亮蓝
            'text': '#FFFFFF',      # 白色文字
            'accent': '#FF0066'     # 霓虹粉
        }
        
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
        self.today = date.today().strftime("%Y-%m-%d")
        
        # 初始化数据文件路径
        self.data_file = 'learning_data.json'
        
        # 创建菜单栏
        self.create_menu()
        
        # 设置matplotlib中文字体
        self.setup_matplotlib_font()
        
        # 创建notebook用于切换界面
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both')
        
        # 创建计时器页面
        self.timer_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.timer_frame, text='计时器')
        
        # 创建统计页面
        self.stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.stats_frame, text='统计')
        
        self.setup_timer_page()
        self.setup_stats_page()
        
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
                             text="Study Time", 
                             font=(self.font_family, 12, 'bold'),
                             fg=self.colors['primary'],
                             bg=self.colors['bg'])
        title_label.pack(pady=(0, 5))
        
        # 时间显示框架
        time_frame = ttk.Frame(main_frame, style='Custom.TFrame')
        time_frame.pack(expand=True, fill='both', pady=5)
        
        # 时间显示标签
        self.time_label = tk.Label(time_frame, 
                                 text="00:00:00", 
                                 font=('Consolas', 32, 'bold'),  # 使用等宽字体
                                 fg=self.colors['secondary'],
                                 bg=self.colors['bg'])
        self.time_label.pack(expand=True)
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame, style='Custom.TFrame')
        button_frame.pack(pady=(5, 0))
        
        # 配置按钮样式
        self.style.configure('Primary.TButton',
                          font=(self.font_family, 10),
                          padding=5,
                          background=self.colors['bg'],
                          foreground=self.colors['primary'])
        
        self.style.configure('Secondary.TButton',
                          font=(self.font_family, 10),
                          padding=5,
                          background=self.colors['bg'],
                          foreground=self.colors['accent'])
        
        # 开始/暂停按钮
        self.start_button = ttk.Button(button_frame, 
                                    text="Start",
                                    command=self.toggle_timing,
                                    style='Primary.TButton',
                                    width=8)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        # 重置按钮
        self.reset_button = ttk.Button(button_frame, 
                                    text="Reset",
                                    command=self.reset_timer,
                                    style='Secondary.TButton',
                                    width=8)
        self.reset_button.pack(side=tk.LEFT, padx=5)
        
    def setup_stats_page(self):
        # 统计页面主框架
        stats_main_frame = ttk.Frame(self.stats_frame, style='Custom.TFrame')
        stats_main_frame.pack(expand=True, fill='both', padx=20, pady=20)
        
        # 标题标签
        stats_title = tk.Label(stats_main_frame,
                             text="Study Time Statistics",
                             font=(self.font_family, 16, 'bold'),
                             fg=self.colors['text'],
                             bg=self.colors['bg'])
        stats_title.pack(pady=(0, 10))
        
        self.figure, self.ax = plt.subplots(figsize=(3, 2))  # 减小图表尺寸
        self.figure.patch.set_facecolor(self.colors['bg'])
        self.ax.set_facecolor(self.colors['bg'])
        self.ax.tick_params(colors=self.colors['text'])
        self.ax.spines['bottom'].set_color(self.colors['text'])
        self.ax.spines['top'].set_color(self.colors['text'])
        self.ax.spines['left'].set_color(self.colors['text'])
        self.ax.spines['right'].set_color(self.colors['text'])
        self.ax.xaxis.label.set_color(self.colors['text'])
        self.ax.yaxis.label.set_color(self.colors['text'])
        self.ax.title.set_color(self.colors['text'])
        self.canvas = FigureCanvasTkAgg(self.figure, self.stats_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
    def toggle_timing(self):
        if not self.is_timing:
            self.start_time = time.time()
            self.is_timing = True
            self.start_button.configure(text="Pause")
            self.style.configure('Primary.TButton', background=self.colors['accent'])
        else:
            self.accumulated_time += time.time() - self.start_time
            self.is_timing = False
            self.start_button.configure(text="Continue")
            self.style.configure('Primary.TButton', background=self.colors['primary'])
            self.save_data()
            
    def reset_timer(self):
        self.is_timing = False
        self.start_time = 0
        self.accumulated_time = 0
        self.start_button.configure(text="Start")
        self.style.configure('Primary.TButton', background=self.colors['primary'])
        self.save_data()
        
    def update_time(self):
        if self.is_timing:
            current_time = time.time() - self.start_time + self.accumulated_time
        else:
            current_time = self.accumulated_time
            
        hours = int(current_time // 3600)
        minutes = int((current_time % 3600) // 60)
        seconds = int(current_time % 60)
        
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        self.time_label.config(text=time_str)
        
        self.root.after(1000, self.update_time)
        
    def load_data(self):
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    if self.today in data:
                        self.accumulated_time = data[self.today]
            self.update_stats()
        except Exception as e:
            messagebox.showerror("错误", f"加载数据失败: {str(e)}")
            
    def save_data(self):
        data = {}
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                data = json.load(f)
        
        data[self.today] = self.accumulated_time
        
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
            
            dates = list(data.keys())[-7:]  # 最近7天
            times = [data[d]/3600 for d in dates]  # 转换为小时
            
            self.ax.clear()
            self.ax.plot(dates, times, marker='o')
            self.ax.set_xlabel('Date')
            self.ax.set_ylabel('Study Time (Hours)')
            self.ax.set_title('Last 7 Days Study Time')
            plt.xticks(rotation=45, fontsize=8)  # 减小字体大小以避免重叠
            self.figure.tight_layout(pad=2.0)  # 增加边距，避免文字显示不完整
            self.canvas.draw()
            
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

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = LearningTimer()
    app.run()
