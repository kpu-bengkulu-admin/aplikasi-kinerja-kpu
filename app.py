import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, date

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="E-Kinerja KPU Kota Bengkulu", layout="wide")

# --- KONEKSI GOOGLE SHEETS ---
# Link Sheets Anda: https://google.com
url = "https://google.com"
conn = st.connection("gsheets", type=GSheetsConnection)

# --- FUNGSI AMBIL DATA REKAP ---
def get_rekap(start_date, end_date):
    df = conn.read(spreadsheet=url, usecols=list(range(9))) # Mengambil 9 kolom utama
    df = df.dropna(how="all") # Hapus baris kosong
    
    if not df.empty:
        df['Tanggal'] = pd.to_datetime(df['Tanggal']).dt.date
        # Filter Rentang Tanggal
        mask = (df['Tanggal'] >= start_date) & (df['Tanggal'] <= end_date)
        df_filtered = df.loc[mask].copy()
        # Filter Hari Kerja (Senin-Jumat)
        df_filtered['Hari'] = pd.to_datetime(df_filtered['Tanggal']).dt.weekday
        df_final = df_filtered[df_filtered['Hari'] <= 4].drop(columns=['Hari'])
        return df_final.sort_values(by="Tanggal")
    return df

# --- TAMPILAN ANTARMUKA ---
st.title("📋 Form Laporan Kinerja Harian")
st.subheader("KPU Kota Bengkulu")

# Fitur Login Sederhana (Opsional)
password = st.sidebar.text_input("Password Akses", type="password")
if password == "KPUKOTA2026": # Anda bisa ganti password ini
    with st.form("form_kinerja", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            nama = st.text_input("Nama Lengkap")
            nip = st.text_input("NIP")
            jabatan = st.text_input("Jabatan")
        with col2:
            tgl = st.date_input("Tanggal Kegiatan", date.today())
            jam_masuk = st.time_input("Jam Masuk", datetime.strptime("08:00", "%H:%M"))
            jam_keluar = st.time_input("Jam Keluar", datetime.strptime("16:00", "%H:%M"))
        
        uraian = st.text_area("Uraian Pekerjaan")
        output = st.text_input("Output Pekerjaan")
        lokasi = st.selectbox("Lokasi Bekerja", ["Kantor", "Rumah (WFH)", "Dinas Luar"])
        
        submit = st.form_submit_button("Simpan Laporan")
        
        if submit:
            # Data baru dalam bentuk DataFrame
            new_data = pd.DataFrame([{
                "Nama": nama, "NIP": nip, "Jabatan": jabatan,
                "Tanggal": tgl.strftime('%Y-%m-%d'), 
                "Jam Masuk": jam_masuk.strftime('%H:%M'), 
                "Jam Keluar": jam_keluar.strftime('%H:%M'),
                "Uraian Pekerjaan": uraian, "Output Pekerjaan": output, "Lokasi": lokasi
            }])
            
            # Ambil data lama, gabung dengan baru, lalu update ke Sheets
            existing_data = conn.read(spreadsheet=url)
            updated_df = pd.concat([existing_data, new_data], ignore_index=True)
            conn.update(spreadsheet=url, data=updated_df)
            st.success("Laporan berhasil terkirim ke database pusat!")

    # --- BAGIAN REKAP & DOWNLOAD ---
    st.divider()
    st.sidebar.header("Unduh Rekap Bulanan")
    s_date = st.sidebar.date_input("Dari Tanggal", date(2026, 3, 21))
    e_date = st.sidebar.date_input("Sampai Tanggal", date(2026, 4, 20))

    if st.sidebar.button("Generate Rekap Excel"):
        rekap_df = get_rekap(s_date, e_date)
        if not rekap_df.empty:
            file_name = f"Rekap_Kinerja_{s_date}_to_{e_date}.xlsx"
            rekap_df.to_excel(file_name, index=False)
            with open(file_name, "rb") as f:
                st.sidebar.download_button("📥 Download Excel Siap Print", f, file_name=file_name)
        else:
            st.sidebar.warning("Tidak ada data hari kerja ditemukan.")
else:
    st.info("Masukkan password di sidebar untuk mulai mengisi laporan.")
