import json
import os
import csv
from tkinter import *
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from fpdf import FPDF
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

DATA_FILE = 'firearms.json'

# ----- Data Persistence -----
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return []

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# ----- GUI -----
class FirearmApp(Tk):
    def __init__(self):
        super().__init__()
        self.title('Firearm Inventory Tracker')
        self.geometry('1000x700')
        self.resizable(False, False)

        self.data = load_data()

        self.create_widgets()
        self.refresh_ui()

    def create_widgets(self):
        # Stats frame
        stats_frame = Frame(self)
        stats_frame.pack(pady=10)

        self.stat_count = StringVar()
        self.stat_cost = StringVar()
        self.stat_value = StringVar()
        self.stat_profit = StringVar()

        labels = [
            ('Total Firearms', self.stat_count),
            ('Total Purchase Cost', self.stat_cost),
            ('Total Value', self.stat_value),
            ('Profit / Loss', self.stat_profit)
        ]
        for i, (text, var) in enumerate(labels):
            frame = LabelFrame(stats_frame, text=text, padx=10, pady=10)
            frame.grid(row=0, column=i, padx=5)
            Label(frame, textvariable=var, width=12).pack()

        # Chart
        chart_frame = Frame(self)
        chart_frame.pack(fill=BOTH, padx=10, pady=10)
        self.fig, self.ax = plt.subplots(figsize=(8,3))
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.canvas.get_tk_widget().pack(fill=BOTH)

        # Form
        form_frame = LabelFrame(self, text='Add Firearm', padx=10, pady=10)
        form_frame.pack(fill=X, padx=10, pady=10)
        self.entries = {}
        fields = [
            ('name', 'Firearm Name'),
            ('serial_number', 'Serial Number'),
            ('purchase_price', 'Purchase Price'),
            ('current_value', 'Current Value'),
            ('purchase_date', 'Purchase Date (YYYY-MM-DD)'),
            ('notes', 'Notes')
        ]
        for i, (key, label) in enumerate(fields):
            Label(form_frame, text=label).grid(row=0, column=i, padx=5, sticky=W)
            entry = Entry(form_frame, width=15)
            entry.grid(row=1, column=i, padx=5)
            self.entries[key] = entry
        Button(form_frame, text='Add Firearm', command=self.add_firearm).grid(row=1, column=len(fields), padx=5)

        # Table
        table_frame = Frame(self)
        table_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        cols = ('name','serial_number','purchase_price','current_value','purchase_date','notes')
        self.tree = ttk.Treeview(table_frame, columns=cols, show='headings', selectmode='browse')
        for col in cols:
            self.tree.heading(col, text=col.replace('_',' ').title())
            self.tree.column(col, width=100)
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar = Scrollbar(table_frame, orient=VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=RIGHT, fill=Y)

        # Actions
        action_frame = Frame(self)
        action_frame.pack(pady=5)
        Button(action_frame, text='Edit', command=self.edit_selected).grid(row=0, column=0, padx=5)
        Button(action_frame, text='Delete', command=self.delete_selected).grid(row=0, column=1, padx=5)
        Button(action_frame, text='Export CSV', command=self.export_csv).grid(row=0, column=2, padx=5)
        Button(action_frame, text='Export PDF', command=self.export_pdf).grid(row=0, column=3, padx=5)

    # ----- Functional Methods -----
    def refresh_ui(self):
        self.refresh_table()
        self.refresh_stats()
        self.refresh_chart()

    def refresh_table(self):
        self.tree.delete(*self.tree.get_children())
        for firearm in self.data:
            self.tree.insert('', END, values=(
                firearm.get('name',''),
                firearm.get('serial_number',''),
                firearm.get('purchase_price',''),
                firearm.get('current_value',''),
                firearm.get('purchase_date',''),
                firearm.get('notes','')
            ))

    def refresh_stats(self):
        total_count = len(self.data)
        total_cost = sum(float(f.get('purchase_price',0) or 0) for f in self.data)
        total_value = sum(float(f.get('current_value',0) or 0) for f in self.data)
        self.stat_count.set(str(total_count))
        self.stat_cost.set(f'$ {total_cost:.2f}')
        self.stat_value.set(f'$ {total_value:.2f}')
        self.stat_profit.set(f'$ {(total_value - total_cost):.2f}')

    def refresh_chart(self):
        names = [f['name'] for f in self.data]
        values = [float(f.get('current_value',0) or 0) for f in self.data]
        self.ax.clear()
        self.ax.bar(names, values, color='skyblue')
        self.ax.set_ylabel('Current Value ($)')
        self.ax.tick_params(axis='x', rotation=45)
        self.fig.tight_layout()
        self.canvas.draw()

    def add_firearm(self):
        firearm = {k: self.entries[k].get() for k in self.entries}
        # Convert numbers
        try:
            firearm['purchase_price'] = float(firearm['purchase_price'])
        except ValueError:
            firearm['purchase_price'] = 0
        try:
            firearm['current_value'] = float(firearm['current_value']) if firearm['current_value'] else 0
        except ValueError:
            firearm['current_value'] = 0
        if firearm['purchase_date']:
            try:
                datetime.strptime(firearm['purchase_date'], '%Y-%m-%d')
            except ValueError:
                messagebox.showerror('Invalid Date', 'Purchase date must be YYYY-MM-DD')
                return
        self.data.append(firearm)
        save_data(self.data)
        for e in self.entries.values():
            e.delete(0, END)
        self.refresh_ui()

    def delete_selected(self):
        item = self.tree.selection()
        if not item:
            return
        idx = self.tree.index(item)
        del self.data[idx]
        save_data(self.data)
        self.refresh_ui()

    def edit_selected(self):
        item = self.tree.selection()
        if not item:
            return
        idx = self.tree.index(item)
        firearm = self.data[idx]
        EditWindow(self, firearm, lambda updated: self.save_edit(idx, updated))

    def save_edit(self, idx, firearm):
        self.data[idx] = firearm
        save_data(self.data)
        self.refresh_ui()

    def export_csv(self):
        file = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV','*.csv')])
        if not file:
            return
        with open(file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Name','Serial Number','Purchase Price','Current Value','Purchase Date','Notes'])
            for firearm in self.data:
                writer.writerow([
                    firearm.get('name',''),
                    firearm.get('serial_number',''),
                    firearm.get('purchase_price',''),
                    firearm.get('current_value',''),
                    firearm.get('purchase_date',''),
                    firearm.get('notes','')
                ])
        messagebox.showinfo('Export CSV', f'Saved to {file}')

    def export_pdf(self):
        file = filedialog.asksaveasfilename(defaultextension='.pdf', filetypes=[('PDF','*.pdf')])
        if not file:
            return
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0,10,'Firearm Inventory',0,1,'C')
        pdf.set_font('Arial', '', 12)
        col_width = pdf.w / 6
        headers = ['Name','Serial Number','Purchase Price','Current Value','Purchase Date','Notes']
        for h in headers:
            pdf.cell(col_width,10,h,1,0,'C')
        pdf.ln()
        for firearm in self.data:
            pdf.cell(col_width,10,str(firearm.get('name','')),1)
            pdf.cell(col_width,10,str(firearm.get('serial_number','')),1)
            pdf.cell(col_width,10,str(firearm.get('purchase_price','')),1)
            pdf.cell(col_width,10,str(firearm.get('current_value','')),1)
            pdf.cell(col_width,10,str(firearm.get('purchase_date','')),1)
            pdf.cell(col_width,10,str(firearm.get('notes','')),1)
            pdf.ln()
        pdf.output(file)
        messagebox.showinfo('Export PDF', f'Saved to {file}')

class EditWindow(Toplevel):
    def __init__(self, master, firearm, callback):
        super().__init__(master)
        self.title('Edit Firearm')
        self.callback = callback
        self.firearm = firearm.copy()
        fields = [
            ('name','Name'),
            ('serial_number','Serial Number'),
            ('purchase_price','Purchase Price'),
            ('current_value','Current Value'),
            ('purchase_date','Purchase Date (YYYY-MM-DD)'),
            ('notes','Notes')
        ]
        self.entries = {}
        for i,(k,label) in enumerate(fields):
            Label(self, text=label).grid(row=i, column=0, sticky=W, padx=5, pady=5)
            e = Entry(self)
            e.grid(row=i, column=1, padx=5, pady=5)
            e.insert(0, str(firearm.get(k,'')))
            self.entries[k] = e
        Button(self, text='Save', command=self.save).grid(row=len(fields), column=0, columnspan=2, pady=5)

    def save(self):
        for k,e in self.entries.items():
            self.firearm[k] = e.get()
        try:
            self.firearm['purchase_price'] = float(self.firearm['purchase_price'])
        except ValueError:
            self.firearm['purchase_price'] = 0
        try:
            self.firearm['current_value'] = float(self.firearm['current_value']) if self.firearm['current_value'] else 0
        except ValueError:
            self.firearm['current_value'] = 0
        self.callback(self.firearm)
        self.destroy()

if __name__ == '__main__':
    app = FirearmApp()
    app.mainloop()
