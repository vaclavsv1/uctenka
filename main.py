import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os

DB_SOUBOR = 'obchod.db'
def priprav_databazi():
   conn = sqlite3.connect(DB_SOUBOR)
   cursor = conn.cursor()
   cursor.execute('''
       CREATE TABLE IF NOT EXISTS produkty (
           kod TEXT PRIMARY KEY,
           nazev TEXT,
           cena REAL
       )
   ''')
   cursor.execute('''
       CREATE TABLE IF NOT EXISTS kosik (
           kod TEXT PRIMARY KEY,
           mnozstvi INTEGER
       )
   ''')
   cursor.execute("SELECT COUNT(*) FROM produkty")
   if cursor.fetchone()[0] == 0:
       testovaci_produkty = [
           ('CPU-01', 'AMD Ryzen 7 7800X3D', 9500.0),
           ('GPU-13', 'MSI GeForce RTX 4070 SUPER', 16200.0),
           ('RAM-05', 'Kingston FURY 32GB DDR5', 3100.0),
           ('MB-09', 'ASUS TUF GAMING B650-PLUS', 4400.0),
           ('SSD-01', 'Samsung 990 Pro 2TB', 4900.0)
       ]
       cursor.executemany('INSERT INTO produkty VALUES (?, ?, ?)', testovaci_produkty)
   conn.commit()
   return conn

class PokladnaApp(tk.Tk):
   def __init__(self, db_conn):
       super().__init__()
       self.db_conn = db_conn
       self.title("Pokladna a Sklad")
       self.geometry("1100x500")
       self.configure(padx=10, pady=10)
       self.kosik = {}  
       self.cena_dopravy = 120.0
       self.sazba_dph = 0.21
       self.vytvor_gui()
       self.nacti_produkty_z_databaze()
       self.nacti_kosik_z_databaze()
   def vytvor_gui(self):
       ramec_sklad = tk.LabelFrame(self, text="Sklad (Databáze)", padx=10, pady=10)
       ramec_sklad.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
       ramec_uctenka = tk.LabelFrame(self, text="Účtenka (Košík)", padx=10, pady=10)
       ramec_uctenka.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
       sloupce_sklad = ('kod', 'nazev', 'cena')
       self.tree_sklad = ttk.Treeview(ramec_sklad, columns=sloupce_sklad, show='headings', height=10)
       self.tree_sklad.heading('kod', text='Kód')
       self.tree_sklad.heading('nazev', text='Název Produktu')
       self.tree_sklad.heading('cena', text='Cena')
       self.tree_sklad.column('kod', width=70)
       self.tree_sklad.column('nazev', width=200)
       self.tree_sklad.column('cena', width=80, anchor='e')
       self.tree_sklad.pack(fill=tk.BOTH, expand=True)
       btn_pridat = tk.Button(ramec_sklad, text="Přidat do účtenky ➔", bg='lightblue', font=('Arial', 10, 'bold'), command=self.pridej_polozku)
       btn_pridat.pack(fill=tk.X, pady=(10, 0))
       sloupce_uctenka = ('kod', 'nazev', 'mnozstvi', 'cena_ks', 'celkem')
       self.tree_uctenka = ttk.Treeview(ramec_uctenka, columns=sloupce_uctenka, show='headings', height=8)
       self.tree_uctenka.heading('kod', text='Kód')
       self.tree_uctenka.heading('nazev', text='Název')
       self.tree_uctenka.heading('mnozstvi', text='Mn.')
       self.tree_uctenka.heading('cena_ks', text='Cena/ks')
       self.tree_uctenka.heading('celkem', text='Celkem')
       self.tree_uctenka.column('kod', width=70)
       self.tree_uctenka.column('nazev', width=180)
       self.tree_uctenka.column('mnozstvi', width=40, anchor='center')
       self.tree_uctenka.column('cena_ks', width=80, anchor='e')
       self.tree_uctenka.column('celkem', width=80, anchor='e')
       self.tree_uctenka.pack(fill=tk.BOTH, expand=True)
       btn_odebrat = tk.Button(ramec_uctenka, text="✖ Odebrat z účtenky", bg='#ff9999', command=self.odeber_polozku)
       btn_odebrat.pack(fill=tk.X, pady=(5, 10))
       ramec_soucty = tk.Frame(ramec_uctenka, bg='#f0f0f0', pady=5)
       ramec_soucty.pack(fill=tk.X)
       self.lbl_mezisoucet = tk.Label(ramec_soucty, text="Mezisoučet: 0 Kč", bg='#f0f0f0', anchor='e')
       self.lbl_mezisoucet.pack(fill=tk.X)
       self.lbl_doprava = tk.Label(ramec_soucty, text=f"Doprava: {self.cena_dopravy} Kč", bg='#f0f0f0', anchor='e')
       self.lbl_doprava.pack(fill=tk.X)
       self.lbl_dph = tk.Label(ramec_soucty, text="DPH (21%): 0 Kč", bg='#f0f0f0', anchor='e')
       self.lbl_dph.pack(fill=tk.X)
       self.lbl_celkem = tk.Label(ramec_soucty, text="Celkem: 0 Kč", bg='#f0f0f0', font=('Arial', 12, 'bold'), anchor='e')
       self.lbl_celkem.pack(fill=tk.X, pady=5)
       self.btn_zaplatit = tk.Button(ramec_uctenka, text="ZAPLATIT A OBJEDNAT = 0 Kč", bg='#28a745', fg='white', font=('Arial', 12, 'bold'), command=self.zaplatit_a_smazat_kosik)
       self.btn_zaplatit.pack(fill=tk.X, ipady=5)
   def nacti_produkty_z_databaze(self):
       for row in self.tree_sklad.get_children():
           self.tree_sklad.delete(row)
       cursor = self.db_conn.cursor()
       cursor.execute("SELECT kod, nazev, cena FROM produkty")
       for kod, nazev, cena in cursor.fetchall():
           self.tree_sklad.insert('', tk.END, values=(kod, nazev, f"{cena:,.0f} Kč".replace(',', ' ')))
   def nacti_kosik_z_databaze(self):
       cursor = self.db_conn.cursor()
       cursor.execute('''
           SELECT k.kod, p.nazev, p.cena, k.mnozstvi
           FROM kosik k
           JOIN produkty p ON k.kod = p.kod
       ''')
       for kod, nazev, cena, mnozstvi in cursor.fetchall():
           self.kosik[kod] = {'nazev': nazev, 'cena': cena, 'mnozstvi': mnozstvi}
       self.prekresli_uctenku()
   def pridej_polozku(self):
       vybrane = self.tree_sklad.focus()
       if not vybrane:
           messagebox.showwarning("Upozornění", "Vyberte nejprve produkt ze skladu nalevo!")
           return
       hodnoty = self.tree_sklad.item(vybrane, 'values')
       kod = hodnoty[0]
       nazev = hodnoty[1]
       cena = float(hodnoty[2].replace(' Kč', '').replace(' ', ''))
       cursor = self.db_conn.cursor()
       if kod in self.kosik:
           self.kosik[kod]['mnozstvi'] += 1
           cursor.execute("UPDATE kosik SET mnozstvi = ? WHERE kod = ?", (self.kosik[kod]['mnozstvi'], kod))
       else:
           self.kosik[kod] = {'nazev': nazev, 'cena': cena, 'mnozstvi': 1}
           cursor.execute("INSERT INTO kosik (kod, mnozstvi) VALUES (?, ?)", (kod, 1))
       self.db_conn.commit()
       self.prekresli_uctenku()
   def odeber_polozku(self):
       vybrane = self.tree_uctenka.focus()
       if not vybrane:
           messagebox.showwarning("Upozornění", "Vyberte produkt na účtence, který chcete odebrat!")
           return
       kod = self.tree_uctenka.item(vybrane, 'values')[0]
       cursor = self.db_conn.cursor()
       if kod in self.kosik:
           if self.kosik[kod]['mnozstvi'] > 1:
               self.kosik[kod]['mnozstvi'] -= 1
               cursor.execute("UPDATE kosik SET mnozstvi = ? WHERE kod = ?", (self.kosik[kod]['mnozstvi'], kod))
           else:
               del self.kosik[kod]
               cursor.execute("DELETE FROM kosik WHERE kod = ?", (kod,))
       self.db_conn.commit()
       self.prekresli_uctenku()
   def zaplatit_a_smazat_kosik(self):
       if not self.kosik:
           messagebox.showinfo("Info", "Košík je prázdný.")
           return
       odpoved = messagebox.askyesno("Zaplatit", "Opravdu chcete zaplatit a dokončit objednávku?")
       if odpoved:
           cursor = self.db_conn.cursor()
           cursor.execute("DELETE FROM kosik")
           self.db_conn.commit()
           self.kosik.clear()
           self.prekresli_uctenku()
           messagebox.showinfo("Úspěch", "Objednávka byla úspěšně zaplacena!")
   def prekresli_uctenku(self):
       for row in self.tree_uctenka.get_children():
           self.tree_uctenka.delete(row)
       mezisoucet = 0
       for kod, data in self.kosik.items():
           celkem_za_polozku = data['cena'] * data['mnozstvi']
           mezisoucet += celkem_za_polozku
           self.tree_uctenka.insert('', tk.END, values=(
               kod,
               data['nazev'],
               f"{data['mnozstvi']}x",
               f"{data['cena']:,.0f} Kč".replace(',', ' '),
               f"{celkem_za_polozku:,.0f} Kč".replace(',', ' ')
           ))
       if mezisoucet > 0:
           celkem = mezisoucet + self.cena_dopravy
       else:
           celkem = 0
       hodnota_dph = celkem - (celkem / (1 + self.sazba_dph))
       self.lbl_mezisoucet.config(text=f"Mezisoučet: {mezisoucet:,.0f} Kč".replace(',', ' '))
       self.lbl_dph.config(text=f"DPH (21%): {hodnota_dph:,.0f} Kč".replace(',', ' '))
       self.lbl_celkem.config(text=f"Celkem: {celkem:,.0f} Kč".replace(',', ' '))
       if celkem > 0:
           self.btn_zaplatit.config(text=f"ZAPLATIT A OBJEDNAT = {celkem:,.0f} Kč".replace(',', ' '))
       else:
           self.btn_zaplatit.config(text="ZAPLATIT A OBJEDNAT = 0 Kč")

if __name__ == "__main__":
   db = priprav_databazi()
   app = PokladnaApp(db)
   app.mainloop()
   db.close()