from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView  # 新增：滚动视图
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.core.text import LabelBase  # 新增：字体管理
from kivy.clock import Clock
from kivy.config import Config
from datetime import datetime
import json
import os
from kivy.utils import platform # 新增：判断平台

# --- 字体配置 ---
# 请确保你的项目文件夹里有一个名为 font.ttf 的中文字体文件
# 如果没有，打包后中文会显示成方块
try:
    LabelBase.register(name='Roboto', fn_regular='font.ttf', fn_bold='font.ttf')
except:
    print("未找到 font.ttf，如果在电脑上运行可忽略，打包APK必须有！")

# 全局变量
sales_count = 0
total_expense = 0.0
total_received_quantity = 0.0
handled_six_count = 0
entries = []
result_labels = []

# 基础配置
Config.set('graphics', 'resizable', True)
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
Window.clearcolor = (1, 1, 1, 1)
Window.softinput_mode = "below_target"

class TradeCalcLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = 10
        self.spacing = 8
        self.calc_grid = None
        self.create_base_ui()
        
        # --- 核心修改：添加滚动视图容器 ---
        self.scroll_view = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        self.add_widget(self.scroll_view)
        
        self.refresh_calc_layout()
        
        Window.bind(on_key_down=self.on_key_handler)
        Window.bind(on_resize=self.on_screen_resize)

    def create_base_ui(self):
        """顶部固定区域（不随下面滚动）"""
        # 顶部容器
        top_container = BoxLayout(orientation='vertical', size_hint_y=None, height=280, spacing=5)
        
        self.date_label = Label(text=datetime.now().strftime('%Y-%m-%d'), font_size=18, size_hint_y=None, height=30, color=(0, 0, 0, 1))
        top_container.add_widget(self.date_label)

        self.success_label = Label(text="", font_size=16, size_hint_y=None, height=30, color=(0, 1, 0, 1), bold=True)
        top_container.add_widget(self.success_label)

        self.clear_btn = Button(text="一键清零", font_size=24, size_hint_y=None, height=60, background_color=(0, 0.8, 0, 1), color=(1,1,1,1), bold=True)
        self.clear_btn.bind(on_press=lambda _: self.clear_all())
        top_container.add_widget(self.clear_btn)

        self.total_sum_label = Label(text="总计: --", font_size=32, size_hint_y=None, height=60, color=(1, 0, 0, 1), bold=True)
        top_container.add_widget(self.total_sum_label)

        # 统计区域
        self.stat_grid = GridLayout(cols=2, spacing=5, size_hint_y=None, height=100)
        self.stat_grid.add_widget(Label(text="卖货人数:", font_size=18, halign="right", color=(0,0,0,1)))
        self.sales_count_label = Label(text="0", font_size=18, halign="left", color=(0,0,0,1))
        self.stat_grid.add_widget(Label(text="总支出:", font_size=18, halign="right", color=(0,0,0,1)))
        self.total_expense_label = Label(text="0.0", font_size=18, halign="left", color=(0,0,0,1))
        self.stat_grid.add_widget(Label(text="今日收货:", font_size=18, halign="right", color=(0,0,0,1)))
        self.received_quantity_label = Label(text="0.0 公斤", font_size=18, halign="left", color=(0,0,0,1))
        
        top_container.add_widget(self.stat_grid)
        self.add_widget(top_container)

    def refresh_calc_layout(self):
        """刷新计算区域，放入滚动视图中"""
        global entries, result_labels
        entries = []
        result_labels = []
        
        # 清除旧的 Grid
        if self.calc_grid:
            self.scroll_view.clear_widgets()

        # 手机端强制单列，平板可双列
        col_num = 2 if Window.width >= 800 else 1
        
        self.calc_grid = GridLayout(cols=col_num, spacing=5, size_hint_y=None, padding=[0, 10, 0, 50])
        # 关键：高度绑定，让滚动条知道有多长
        self.calc_grid.bind(minimum_height=self.calc_grid.setter('height'))

        for row in range(26):
            row_layout = BoxLayout(orientation="horizontal", spacing=2, size_hint_y=None, height=60)
            
            # 序号/左括号
            row_layout.add_widget(Label(text=f"{row+1}.(", font_size=16, size_hint_x=None, width=40, color=(0,0,0,1)))
            
            # 输入框优化：input_type='number' 会调出数字键盘
            e1 = TextInput(multiline=False, font_size=18, input_filter="float", input_type='number', size_hint_x=0.3, halign="center", background_color=(0.95, 0.95, 0.95, 1))
            e1.bind(text=lambda _, r=row: self.calculate_result(r))
            
            e2 = TextInput(multiline=False, font_size=18, input_filter="float", input_type='number', size_hint_x=0.3, halign="center", background_color=(0.95, 0.95, 0.95, 1))
            e2.bind(text=lambda _, r=row: self.calculate_result(r))
            
            e3 = TextInput(multiline=False, font_size=18, input_filter="float", input_type='number', size_hint_x=0.3, halign="center", background_color=(0.95, 0.95, 0.95, 1))
            e3.bind(text=lambda _, r=row: self.calculate_result(r))

            entries.append([e1, e2, e3])
            
            row_layout.add_widget(e1)
            row_layout.add_widget(Label(text="-", font_size=20, size_hint_x=None, width=15, color=(0,0,0,1)))
            row_layout.add_widget(e2)
            row_layout.add_widget(Label(text=")*", font_size=20, size_hint_x=None, width=20, color=(0,0,0,1)))
            row_layout.add_widget(e3)
            row_layout.add_widget(Label(text="=", font_size=20, size_hint_x=None, width=15, color=(0,0,0,1)))
            
            res_label = Label(text="...", font_size=18, size_hint_x=0.25, halign="center", color=(0, 0, 1, 1))
            result_labels.append(res_label)
            row_layout.add_widget(res_label)
            
            self.calc_grid.add_widget(row_layout)
            
        self.scroll_view.add_widget(self.calc_grid)

    def on_screen_resize(self, window, width, height):
        self.refresh_calc_layout()

    def calculate_result(self, row):
        global handled_six_count
        try:
            v1 = float(entries[row][0].text) if entries[row][0].text.strip() else 0.0
            v2 = float(entries[row][1].text) if entries[row][1].text.strip() else 0.0
            v3 = float(entries[row][2].text) if entries[row][2].text.strip() else 0.0
            
            # 避免无数据时计算
            if v1 == 0 and v2 == 0 and v3 == 0:
                result_labels[row].text = "..."
                self.update_total_sum()
                return

            raw_result = (v1 - v2) * v3
            fractional_part = raw_result % 1
            integer_part = int(raw_result)

            if fractional_part >= 0.7:
                result = integer_part + 1
            elif fractional_part < 0.599999:
                result = integer_part
            elif 0.599999 <= fractional_part < 0.7:
                handled_six_count += 1
                result = integer_part + 1 if handled_six_count % 2 == 0 else integer_part
            else:
                result = raw_result

            result_labels[row].text = f"{result:.1f}"
            self.update_total_sum()
        except:
            result_labels[row].text = "Err"

    def update_total_sum(self):
        total = 0.0
        for row in range(26):
            try:
                res_text = result_labels[row].text
                if res_text not in ["...", "Err", "等待输入"]:
                    total += float(res_text)
            except:
                continue
        self.total_sum_label.text = f"总计: {total:.1f}"

    def clear_all(self):
        global sales_count, total_expense, total_received_quantity, handled_six_count
        handled_six_count = 0

        # 计算并保存这一单的数据
        current_bill_received = 0.0
        for row in range(26):
            try:
                v1 = float(entries[row][0].text) if entries[row][0].text.strip() else 0.0
                v2 = float(entries[row][1].text) if entries[row][1].text.strip() else 0.0
                current_bill_received += (v1 - v2)
            except:
                continue
        
        # 只有当总计有数据时才记录
        total_text = self.total_sum_label.text
        if "总计: --" not in total_text and "总计: 0.0" not in total_text:
            current_expense = float(total_text.split(":")[1].strip())
            sales_count += 1
            total_expense += current_expense
            total_received_quantity += current_bill_received
            
            # 更新UI
            self.sales_count_label.text = f"{sales_count}"
            self.total_expense_label.text = f"{total_expense:.1f}"
            self.received_quantity_label.text = f"{total_received_quantity:.1f}"
            
            # 保存到JSON
            self.export_to_json()
            
            self.success_label.text = "✅ 保存成功！财源广进！"
        else:
            self.success_label.text = "🗑️ 已重置"

        # 清空输入
        for row in range(26):
            for col in range(3):
                entries[row][col].text = ""
            result_labels[row].text = "..."
        
        self.total_sum_label.text = "总计: --"
        Clock.schedule_once(lambda _: setattr(self.success_label, 'text', ''), 2)

    def on_key_handler(self, window, key, scancode, codepoint, modifier):
        # 保持原有的键盘逻辑
        focused = Window.focus
        if not isinstance(focused, TextInput): return False
        
        # 简单查找当前焦点位置
        row, col = -1, -1
        found = False
        for r in range(len(entries)):
            for c in range(3):
                if entries[r][c] == focused:
                    row, col = r, c
                    found = True
                    break
            if found: break
        
        if not found: return False

        if modifier == ['ctrl'] and codepoint == 'r':
            self.clear_all()
            return True
            
        # 回车逻辑
        if key == 13 or key == 40: # Enter
            if col < 2:
                entries[row][col+1].focus = True
            elif row < 25:
                entries[row+1][0].focus = True
            return True
        return False

    def export_to_json(self):
        """适配安卓路径的保存逻辑"""
        data = {
            "date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "daily_sales_count": sales_count,
            "daily_total_expense": total_expense,
            "daily_total_received": total_received_quantity
        }
        
        # Android 路径适配
        if platform == 'android':
            from android.storage import app_storage_path
            # 使用 App 专属数据目录
            user_data_dir = App.get_running_app().user_data_dir
            file_name = os.path.join(user_data_dir, "daily_report.json")
        else:
            file_name = "daily_report.json"

        # 读取旧数据
        existing_data = []
        if os.path.exists(file_name):
            try:
                with open(file_name, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
            except: pass
            
        existing_data.append(data)
        
        try:
            with open(file_name, "w", encoding="utf-8") as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            self.success_label.text = "保存失败: " + str(e)

class TradeCalcApp(App):
    def build(self):
        self.title = "业忠贸易计算器"
        return TradeCalcLayout()

if __name__ == '__main__':
    TradeCalcApp().run()