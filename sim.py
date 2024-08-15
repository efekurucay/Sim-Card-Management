import tkinter as tk
from tkinter import messagebox
from tkcalendar import Calendar, DateEntry
from datetime import datetime
import sqlite3

# Veritabanı Bağlantısı
conn = sqlite3.connect('sim_kart_takip.db')
c = conn.cursor()

# Veritabanı Tablosu Oluşturma
c.execute('''CREATE TABLE IF NOT EXISTS numaralar
             (numara TEXT PRIMARY KEY,
              hat_sahibi TEXT,
              mevcut_sebeke TEXT,
              son_kullanim_baslangic TEXT,
              son_kullanim_bitis TEXT,
              durum TEXT,
              son_gecis_tarihi TEXT,
              gecmis_sebeke TEXT)''')

# Fonksiyonlar

def numara_sorgula():
    # Giriş alanlarını sıfırlama (temizleme)
    entry_hat_sahibi.delete(0, tk.END)
    entry_mevcut_sebeke.delete(0, tk.END)
    entry_son_kullanim.delete(0, tk.END)
    entry_son_kullanim2.delete(0, tk.END)
    entry_durum.delete(0, tk.END)
    entry_fiziki_durum.delete(0, tk.END)
    entry_son_gecis.delete(0, tk.END)
    entry_gecmis_sebeke.delete(0, tk.END)

    # Numara sorgulama
    numara = entry_numara.get()
    c.execute("SELECT * FROM numaralar WHERE numara=?", (numara,))
    result = c.fetchone()
    
    if result:
        entry_hat_sahibi.insert(0, result[1])
        entry_mevcut_sebeke.insert(0, result[2])
        entry_son_kullanim.insert(0, result[3])
        entry_son_kullanim2.insert(0, result[4])

        # Son Kullanım Dönemine Göre Durum Güncelleme
        if result[4]:  # Bitiş tarihi varsa kontrol et
            bitis_tarihi = datetime.strptime(result[4], "%Y-%m-%d")
            if bitis_tarihi < datetime.now():
                durum = "Satılabilir"
            else:
                durum = "Müşteride"
        else:
            durum = result[5]  # Önceki durumu koru
        
        entry_durum.insert(0, durum)
        entry_fiziki_durum.insert(0, result[5])  # Fiziki durum için yeni alan

        entry_son_gecis.insert(0, result[6])
        entry_gecmis_sebeke.insert(0, result[7])

        # Durum veritabanında da güncellenir
        c.execute("UPDATE numaralar SET durum=? WHERE numara=?", (durum, numara))
        conn.commit()
    else:
        messagebox.showinfo("Sonuç", "Numara kayıtlı değil!")


def yeni_numara_ekle():
    def ekle():
        numara = entry_new_numara.get()
        hat_sahibi = entry_new_hat_sahibi.get()
        sebeke = entry_new_sebeke.get()

        # Boş alanları kontrol etme
        if not numara or not hat_sahibi or not sebeke:
            messagebox.showwarning("Uyarı", "Tüm alanları doldurmak zorunludur!")
            return
        
        # Yeni numara veritabanına ekleme
        try:
            c.execute("INSERT INTO numaralar (numara, hat_sahibi, mevcut_sebeke, durum) VALUES (?, ?, ?, ?)", 
                      (numara, hat_sahibi, sebeke, 'Satılabilir'))
            conn.commit()
            messagebox.showinfo("Başarılı", "Numara başarıyla eklendi.")
            new_window.destroy()  # Pencereyi kapat
        except sqlite3.IntegrityError:
            messagebox.showerror("Hata", "Bu numara zaten kayıtlı!")

    # Yeni bir pencere oluşturma
    new_window = tk.Toplevel(root)
    new_window.title("Yeni Numara Ekle")
    new_window.geometry("300x200")

    # Giriş alanları
    tk.Label(new_window, text="Numara:").place(x=20, y=20)
    entry_new_numara = tk.Entry(new_window, width=25)
    entry_new_numara.place(x=100, y=20)

    tk.Label(new_window, text="Hat Sahibi:").place(x=20, y=60)
    entry_new_hat_sahibi = tk.Entry(new_window, width=25)
    entry_new_hat_sahibi.place(x=100, y=60)

    tk.Label(new_window, text="Şebeke:").place(x=20, y=100)
    entry_new_sebeke = tk.Entry(new_window, width=25)
    entry_new_sebeke.place(x=100, y=100)

    # Ekle Butonu
    btn_ekle = tk.Button(new_window, text="Ekle", command=ekle)
    btn_ekle.place(x=120, y=140)

def mevcut_tum_hatlar():
    # Yeni bir pencere oluşturma
    all_numbers_window = tk.Toplevel(root)
    all_numbers_window.title("Mevcut Tüm Hatlar")
    all_numbers_window.geometry("400x400")
    
    c.execute("SELECT numara FROM numaralar")
    numaralar = c.fetchall()

    if numaralar:
        y_position = 20
        for numara in numaralar:
            numara_btn = tk.Button(all_numbers_window, text=numara[0], width=20, command=lambda n=numara[0]: numara_bilgileri_goster(n))
            numara_btn.place(x=20, y=y_position)
            
            sil_btn = tk.Button(all_numbers_window, text="Sil", width=10, command=lambda n=numara[0]: numara_sil(n))
            sil_btn.place(x=250, y=y_position)
            
            y_position += 40
    else:
        messagebox.showinfo("Bilgi", "Veritabanında kayıtlı numara yok.")

def numara_bilgileri_goster(numara):
    entry_numara.delete(0, tk.END)
    entry_numara.insert(0, numara)
    numara_sorgula()

def numara_sil(numara):
    response = messagebox.askyesno("Onay", f"{numara} numarasını silmek istediğinize emin misiniz?")
    if response:
        c.execute("DELETE FROM numaralar WHERE numara=?", (numara,))
        conn.commit()
        messagebox.showinfo("Başarılı", f"{numara} numarası silindi.")
        mevcut_tum_hatlar()  # Listeyi güncellemek için pencereyi yeniden yükleyin

def kullanim_donemi_tanimla():
    def gecis_yap():
        baslangic_tarihi = cal_baslangic.get_date()
        bitis_tarihi = cal_bitis.get_date() 

        # Kullanım dönemi güncellenmesi
        c.execute("UPDATE numaralar SET son_kullanim_baslangic=?, son_kullanim_bitis=? WHERE numara=?", 
                  (baslangic_tarihi, bitis_tarihi, numara))
        conn.commit()
        messagebox.showinfo("Başarılı", f"{numara} numarası için kullanım dönemi güncellendi.")
        new_window.destroy()

    # Seçili numarayı al
    numara = entry_numara.get()
    if not numara:
        messagebox.showwarning("Uyarı", "Lütfen bir numara seçin!")
        return
    
    # Yeni bir pencere oluşturma
    new_window = tk.Toplevel(root)
    new_window.title("Kullanım Dönemi Tanımla")
    new_window.geometry("400x300")

    tk.Label(new_window, text=f"Numara: {numara}").pack(pady=10)

    # Takvimler
    tk.Label(new_window, text="Başlangıç Tarihi").pack()
    cal_baslangic = DateEntry(new_window, width=12, background='darkblue', foreground='white', borderwidth=2)
    cal_baslangic.pack(pady=10)

    tk.Label(new_window, text="Bitiş Tarihi").pack()
    cal_bitis = DateEntry(new_window, width=12, background='darkblue', foreground='white', borderwidth=2)
    cal_bitis.pack(pady=10)

    # Geçiş yap Butonu
    btn_gecis_yap = tk.Button(new_window, text="Geçiş yap.", command=gecis_yap)
    btn_gecis_yap.pack(pady=20)

def sebeke_degistir():
    def gecis_yap():
        yeni_sebeke = selected_sebeke.get()
        eski_sebeke = entry_mevcut_sebeke.get()
        bugunun_tarihi = datetime.now().strftime("%d.%m.%Y")

        # Şebeke güncellenmesi
        c.execute("UPDATE numaralar SET mevcut_sebeke=?, gecmis_sebeke=?, son_gecis_tarihi=? WHERE numara=?", 
                  (yeni_sebeke, eski_sebeke, bugunun_tarihi, numara))
        conn.commit()
        messagebox.showinfo("Başarılı", f"{numara} numarası için şebeke değiştirildi.")
        new_window.destroy()
        numara_sorgula()  # Ana ekranda güncellenen bilgileri göster

    # Seçili numarayı al
    numara = entry_numara.get()
    mevcut_sebeke = entry_mevcut_sebeke.get()
    if not numara:
        messagebox.showwarning("Uyarı", "Lütfen bir numara seçin!")
        return

    # Yeni bir pencere oluşturma
    new_window = tk.Toplevel(root)
    new_window.title("Şebeke Değiştir")
    new_window.geometry("400x300")

    tk.Label(new_window, text=f"Numara: {numara}").pack(pady=10)

    # Şebeke Seçenekleri
    tk.Label(new_window, text="Geçilecek Şebeke:").pack()

    # Mevcut şebeke dışındaki şebekeleri etkinleştirme
    selected_sebeke = tk.StringVar(value="")

    radio_buttons = {
        "Turkcell": tk.Radiobutton(new_window, text="Turkcell", variable=selected_sebeke, value="Turkcell"),
        "Türk Telekom": tk.Radiobutton(new_window, text="Türk Telekom", variable=selected_sebeke, value="Türk Telekom"),
        "Vodafone": tk.Radiobutton(new_window, text="Vodafone", variable=selected_sebeke, value="Vodafone")
    }

    for sebeke, btn in radio_buttons.items():
        btn.pack(anchor="w")
        if sebeke == mevcut_sebeke:
            btn.config(state=tk.DISABLED)

    # Geçiş yap Butonu
    btn_gecis_yap = tk.Button(new_window, text="Geçiş yap.", command=gecis_yap)
    btn_gecis_yap.pack(pady=20)

def fiziki_durum_tanimla():
    def durumu_guncelle():
        secilen_durum = selected_durum.get()

        # Fiziki durum güncellenmesi
        c.execute("UPDATE numaralar SET durum=? WHERE numara=?", (secilen_durum, numara))
        conn.commit()
        messagebox.showinfo("Başarılı", f"{numara} numarası için fiziki durum güncellendi.")
        new_window.destroy()
        numara_sorgula()  # Ana ekranda güncellenen bilgileri göster

    # Seçili numarayı al
    numara = entry_numara.get()
    if not numara:
        messagebox.showwarning("Uyarı", "Lütfen bir numara seçin!")
        return
    
    # Yeni bir pencere oluşturma
    new_window = tk.Toplevel(root)
    new_window.title("Fiziki Durum Tanımla")
    new_window.geometry("400x300")

    tk.Label(new_window, text=f"Numara: {numara}").pack(pady=10)

    # Fiziki Durum Seçenekleri
    tk.Label(new_window, text="Durum:").pack()

    selected_durum = tk.StringVar(value="Dükkanda")

    durum_buttons = {
        "Müşteride": tk.Radiobutton(new_window, text="Müşteride", variable=selected_durum, value="Müşteride"),
        "Dükkanda": tk.Radiobutton(new_window, text="Dükkanda", variable=selected_durum, value="Dükkanda"),
        "Geçiş Yapılacak": tk.Radiobutton(new_window, text="Geçiş Yapılacak", variable=selected_durum, value="Geçiş Yapılacak")
    }

    for durum, btn in durum_buttons.items():
        btn.pack(anchor="w")

    # Durum Güncelle Butonu
    btn_durumu_guncelle = tk.Button(new_window, text="Durumu Güncelle", command=durumu_guncelle)
    btn_durumu_guncelle.pack(pady=20)

def satilabilir_hatlar():
    # Yeni bir pencere oluşturma
    all_numbers_window = tk.Toplevel(root)
    all_numbers_window.title("Satılabilir Hatlar")
    all_numbers_window.geometry("400x400")
    
    c.execute("SELECT numara FROM numaralar WHERE durum='Satılabilir'")
    numaralar = c.fetchall()

    if numaralar:
        y_position = 20
        for numara in numaralar:
            numara_btn = tk.Button(all_numbers_window, text=numara[0], width=20, command=lambda n=numara[0]: numara_bilgileri_goster(n))
            numara_btn.place(x=20, y=y_position)
            y_position += 40
    else:
        messagebox.showinfo("Bilgi", "Satılabilir durumda hat bulunmuyor.")

# Ana Pencere ve Arayüz
root = tk.Tk()
root.title("Sim Kart Takip Uygulaması")
root.geometry("700x600")
root.configure(bg="#d3d3d3")

# Üst Düğmeler
btn_sat_listesi = tk.Button(root, text="Satılabilir Hat Listesi", width=20, height=2, bg="#e0e0e0", command=satilabilir_hatlar)
btn_sat_listesi.place(x=50, y=10)

btn_mevcut_hatlar = tk.Button(root, text="Mevcut Tüm Hatlar", width=20, height=2, bg="#e0e0e0", command=mevcut_tum_hatlar)
btn_mevcut_hatlar.place(x=230, y=10)

btn_yeni_numara_ekle = tk.Button(root, text="Yeni Numara Ekle", width=20, height=2, bg="#e0e0e0", command=yeni_numara_ekle)
btn_yeni_numara_ekle.place(x=410, y=10)

# Numara Sorgulama Bölümü
label_numara = tk.Label(root, text="Numara giriniz:", bg="#d3d3d3", font=('Arial', 12))
label_numara.place(x=50, y=80)

entry_numara = tk.Entry(root, width=30, font=('Arial', 14))
entry_numara.place(x=180, y=75)

btn_sorgula = tk.Button(root, text="Sorgula", width=10, height=1, bg="#e0e0e0", font=('Arial', 12), command=numara_sorgula)
btn_sorgula.place(x=550, y=70)

# Bilgi Bölümü
frame_info = tk.Frame(root, relief=tk.RIDGE, borderwidth=2, bg="white")
frame_info.place(x=50, y=120, width=600, height=250)

label_hat_sahibi = tk.Label(frame_info, text="Hat Sahibi:", bg="white", font=('Arial', 12))
label_hat_sahibi.place(x=10, y=10)
entry_hat_sahibi = tk.Entry(frame_info, width=40, font=('Arial', 12))
entry_hat_sahibi.place(x=150, y=10)

label_mevcut_sebeke = tk.Label(frame_info, text="Mevcut Şebeke:", bg="white", font=('Arial', 12))
label_mevcut_sebeke.place(x=10, y=50)
entry_mevcut_sebeke = tk.Entry(frame_info, width=40, font=('Arial', 12))
entry_mevcut_sebeke.place(x=150, y=50)

label_son_kullanim = tk.Label(frame_info, text="Son Kullanım Dönemi:", bg="white", font=('Arial', 12))
label_son_kullanim.place(x=10, y=90)
entry_son_kullanim = tk.Entry(frame_info, width=18, font=('Arial', 12))
entry_son_kullanim.place(x=150, y=90)
entry_son_kullanim2 = tk.Entry(frame_info, width=18, font=('Arial', 12))
entry_son_kullanim2.place(x=340, y=90)

label_durum = tk.Label(frame_info, text="Durum:", bg="white", font=('Arial', 12))
label_durum.place(x=10, y=130)
entry_durum = tk.Entry(frame_info, width=18, font=('Arial', 12))
entry_durum.place(x=150, y=130)
entry_fiziki_durum = tk.Entry(frame_info, width=18, font=('Arial', 12))  # Yeni fiziki durum kutusu
entry_fiziki_durum.place(x=340, y=130)

label_son_gecis = tk.Label(frame_info, text="Son Geçiş Tarihi:", bg="white", font=('Arial', 12))
label_son_gecis.place(x=10, y=170)
entry_son_gecis = tk.Entry(frame_info, width=40, font=('Arial', 12))
entry_son_gecis.place(x=150, y=170)

label_gecmis_sebeke = tk.Label(frame_info, text="Geçmiş Şebeke:", bg="white", font=('Arial', 12))
label_gecmis_sebeke.place(x=10, y=210)
entry_gecmis_sebeke = tk.Entry(frame_info, width=40, font=('Arial', 12))
entry_gecmis_sebeke.place(x=150, y=210)

# Alt Düğmeler
btn_sebeke_degistir = tk.Button(root, text="Şebeke Değiştir", width=20, height=2, bg="#e0e0e0", font=('Arial', 10), command=sebeke_degistir)
btn_sebeke_degistir.place(x=50, y=480)

btn_kullanim_donemi = tk.Button(root, text="Kullanım Dönemi Tanımla", width=20, height=2, bg="#e0e0e0", font=('Arial', 10), command=kullanim_donemi_tanimla)
btn_kullanim_donemi.place(x=230, y=480)

btn_fiziki_durum = tk.Button(root, text="Fiziki Durum Tanımla", width=20, height=2, bg="#e0e0e0", font=('Arial', 10), command=fiziki_durum_tanimla)
btn_fiziki_durum.place(x=410, y=480)

# Pencereyi sürekli açık tutma
root.mainloop()

# Veritabanı bağlantısını kapatma
conn.close()
