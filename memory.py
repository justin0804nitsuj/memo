import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import tkinter.simpledialog as simpledialog  # 用於彈出簡單的文字輸入對話框
import sqlite3
import os
from PIL import Image, ImageTk

DB_NAME = 'my_files.db'

class FileManager:
    def __init__(self, db_name=DB_NAME):
        self.conn = sqlite3.connect(db_name)
        self.create_table()

    def create_table(self):
        """建立（若不存在）檔案資料表"""
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_type TEXT,
                description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def add_file(self, file_name, file_path, file_type, description):
        """新增檔案資訊"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO files (file_name, file_path, file_type, description)
            VALUES (?, ?, ?, ?)
        ''', (file_name, file_path, file_type, description))
        self.conn.commit()

    def delete_file(self, file_id):
        """刪除檔案資訊"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM files WHERE id = ?', (file_id,))
        self.conn.commit()

    def get_all_files(self):
        """取得所有檔案資訊"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, file_name, file_path, file_type, description FROM files')
        return cursor.fetchall()

    def get_file_by_id(self, file_id):
        """依檔案ID查詢單筆檔案資訊"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM files WHERE id = ?', (file_id,))
        return cursor.fetchone()

    def search_files(self, keyword):
        """搜尋檔案（依名稱或描述）"""
        cursor = self.conn.cursor()
        like_kw = f'%{keyword}%'
        cursor.execute('''
            SELECT id, file_name, file_path, file_type, description
            FROM files
            WHERE file_name LIKE ? OR description LIKE ?
        ''', (like_kw, like_kw))
        return cursor.fetchall()
    
    def update_description(self, file_id, new_desc):
        """更新檔案的描述欄位"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE files
            SET description = ?
            WHERE id = ?
        ''', (new_desc, file_id))
        self.conn.commit()


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("我的檔案管理系統")

        self.file_manager = FileManager()

        # -- 上方功能區 --
        top_frame = tk.Frame(root)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        self.search_entry = tk.Entry(top_frame)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        
        search_btn = tk.Button(top_frame, text="搜尋", command=self.search_files)
        search_btn.pack(side=tk.LEFT, padx=5)

        add_btn = tk.Button(top_frame, text="新增檔案", command=self.add_file_dialog)
        add_btn.pack(side=tk.LEFT, padx=5)

        delete_btn = tk.Button(top_frame, text="刪除選擇", command=self.delete_selected)
        delete_btn.pack(side=tk.LEFT, padx=5)

        # ★ 新增「編輯描述」按鈕
        edit_desc_btn = tk.Button(top_frame, text="編輯描述", command=self.edit_description)
        edit_desc_btn.pack(side=tk.LEFT, padx=5)

        # -- 左側: 檔案列表 (Treeview) --
        left_frame = tk.Frame(root)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        columns = ("ID", "名稱", "類型", "描述")
        self.file_tree = ttk.Treeview(left_frame, columns=columns, show='headings', height=20)
        for col in columns:
            self.file_tree.heading(col, text=col)
            self.file_tree.column(col, width=100, anchor=tk.W)
        self.file_tree.pack(side=tk.LEFT, fill=tk.Y)

        # 點選事件
        self.file_tree.bind("<<TreeviewSelect>>", self.on_file_select)

        # -- 右側: 預覽區 --
        right_frame = tk.Frame(root)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.preview_label = tk.Label(right_frame, text="預覽區", bg="white", justify=tk.LEFT)
        self.preview_label.pack(fill=tk.BOTH, expand=True)

        # 載入所有檔案
        self.load_files()

    def load_files(self, files=None):
        """讀取檔案清單，顯示在列表中"""
        # 清空 Treeview
        for row in self.file_tree.get_children():
            self.file_tree.delete(row)

        if files is None:
            files = self.file_manager.get_all_files()

        for f in files:
            file_id, file_name, file_path, file_type, description = f
            self.file_tree.insert('', tk.END, values=(file_id, file_name, file_type, description))

    def add_file_dialog(self):
        """選擇檔案並新增到資料庫"""
        file_path = filedialog.askopenfilename()
        if not file_path:
            return

        file_name = os.path.basename(file_path)
        ext = os.path.splitext(file_name)[1].lower()

        # 簡易判斷檔案類型
        if ext in ['.png', '.jpg', '.jpeg', '.gif']:
            file_type = "image"
        elif ext in ['.mp4', '.avi', '.mov']:
            file_type = "video"
        elif ext in ['.txt']:
            file_type = "text"
        else:
            file_type = "others"

        # ★ 讓使用者輸入描述
        description = simpledialog.askstring("新增描述", f"為「{file_name}」輸入描述 (可留空)：", initialvalue="")
        if description is None:
            description = ""  # 若取消或關閉，視為空字串

        # 新增到資料庫
        self.file_manager.add_file(file_name, file_path, file_type, description)
        messagebox.showinfo("訊息", f"已新增：{file_name}")
        self.load_files()

    def delete_selected(self):
        """刪除選擇的檔案資訊"""
        selected = self.file_tree.selection()
        if not selected:
            return

        for sel in selected:
            item = self.file_tree.item(sel)
            file_id = item['values'][0]
            self.file_manager.delete_file(file_id)
        
        self.load_files()

    def on_file_select(self, event):
        """當使用者點選列表中的檔案時，顯示預覽"""
        selected = self.file_tree.selection()
        if not selected:
            return

        item = self.file_tree.item(selected[0])
        file_id = item['values'][0]
        file_info = self.file_manager.get_file_by_id(file_id)

        if file_info:
            # file_info 結構: (id, file_name, file_path, file_type, description, created_at)
            _, file_name, file_path, file_type, description, _ = file_info

            # 顯示預覽 (圖片或文字檔)
            self.show_preview(file_path, file_type)
            
            # 如果需要在預覽區顯示檔案的描述，可以加上：
            # (但若是圖片，label 會用 image=... 取代文字；因此示範放在下方)
            current_text = self.preview_label.cget("text")
            # 若是圖片預覽完後，就會把text清空；因此我們先把它記錄下來
            self.preview_label.config(text=f"{current_text}\n\n描述：{description}")

    def show_preview(self, file_path, file_type):
        """根據檔案類型做預覽"""
        # 先清空圖像與文字 (避免上一次的殘留)
        self.preview_label.config(image="", text="")

        if file_type == "image":
            self.preview_image(file_path)
        elif file_type == "video":
            # 簡易做法：以外部播放器開啟
            self.preview_label.config(text="影片檔案，已嘗試用外部程式開啟。")
            try:
                os.startfile(file_path)  # Windows
            except AttributeError:
                # macOS 或 Linux 可換成 subprocess 呼叫對應的open / xdg-open
                import subprocess
                subprocess.call(["open", file_path])  # macOS: 'open', Linux: 'xdg-open'
        elif file_type == "text":
            self.preview_text(file_path)
        else:
            self.preview_label.config(text="不支援的檔案類型，已嘗試用外部程式開啟。")
            try:
                os.startfile(file_path)
            except AttributeError:
                import subprocess
                subprocess.call(["open", file_path])

    def preview_image(self, file_path):
        """顯示圖片"""
        img = Image.open(file_path)
        img.thumbnail((400, 400))  # 縮小一點
        self.tk_img = ImageTk.PhotoImage(img)
        self.preview_label.config(image=self.tk_img)

    def preview_text(self, file_path):
        """顯示文字檔內容"""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        self.preview_label.config(text=content)

    def search_files(self):
        """搜尋檔案(依名稱或描述)"""
        keyword = self.search_entry.get()
        if keyword:
            files = self.file_manager.search_files(keyword)
            self.load_files(files)
        else:
            self.load_files()

    def edit_description(self):
        """編輯所選檔案的描述"""
        selected = self.file_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "請先選擇要編輯描述的檔案")
            return
        
        # 取得第一個選擇的檔案ID
        item = self.file_tree.item(selected[0])
        file_id = item['values'][0]
        file_info = self.file_manager.get_file_by_id(file_id)
        
        if not file_info:
            messagebox.showwarning("警告", "無法取得檔案資訊")
            return
        
        # file_info 結構: (id, file_name, file_path, file_type, description, created_at)
        current_desc = file_info[4]  # 第五個欄位就是 description

        # 彈出輸入對話框，預設文字為目前描述
        new_desc = simpledialog.askstring("編輯描述", "請輸入描述：", initialvalue=current_desc)
        
        # 如果使用者按下「取消」或關閉，new_desc 會是 None
        if new_desc is None:
            return

        # 更新至資料庫
        self.file_manager.update_description(file_id, new_desc)
        
        # 更新 Treeview
        self.load_files()
        
        # 如果你想即時更新右側預覽，也可以再執行一次 on_file_select(None)，
        # 或手動更新 self.preview_label 的內容。


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
