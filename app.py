import streamlit as st
import pandas as pd
import json
import csv
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import time
import os

# Konfigurasi halaman
st.set_page_config(
    page_title="Part Monitoring System",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

class PartMonitoringSystem:
    def __init__(self):
        self.data_file = "parts_data.json"
        self.parts_data = self.load_data()
        
    def load_data(self):
        """Load data dari file JSON"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except Exception as e:
            st.error(f"Error loading data: {e}")
            return []
    
    def save_data(self):
        """Simpan data ke file JSON"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.parts_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            st.error(f"Error saving data: {e}")
            return False
    
    def calculate_remaining_hours(self, part):
        """Hitung sisa usia pakai dalam jam"""
        try:
            install_date = datetime.strptime(part['install_date'], "%Y-%m-%d")
            current_date = datetime.now()
            days_passed = (current_date - install_date).days
            hours_used = days_passed * 8  # Asumsi 8 jam operasi per hari
            remaining_hours = part['recommended_usage'] - hours_used
            return max(0, remaining_hours)
        except Exception as e:
            st.error(f"Error calculating remaining hours: {e}")
            return 0
    
    def calculate_replacement_date(self, part):
        """Hitung tanggal penggantian"""
        try:
            install_date = datetime.strptime(part['install_date'], "%Y-%m-%d")
            recommended_days = part['recommended_usage'] / 8
            replacement_date = install_date + timedelta(days=recommended_days)
            return replacement_date
        except Exception as e:
            st.error(f"Error calculating replacement date: {e}")
            return datetime.now()
    
    def get_status(self, remaining_hours):
        """Tentukan status berdasarkan sisa usia pakai"""
        if remaining_hours > 500:
            return "Normal", "🟢", "green"
        elif remaining_hours > 0:
            return "Warning", "🟡", "orange"
        else:
            return "Harus Ganti", "🔴", "red"
    
    def show_sidebar_filters(self):
        """Tampilkan filter di sidebar"""
        st.sidebar.title("🔧 Part Monitoring System")
        st.sidebar.markdown("---")
        
        # Status filter
        st.sidebar.subheader("📊 Filter Status")
        status_filter = st.sidebar.multiselect(
            "Pilih Status:",
            ["Normal", "Warning", "Harus Ganti"],
            default=["Normal", "Warning", "Harus Ganti"]
        )
        
        # Data filters
        st.sidebar.subheader("🔍 Filter Data")
        
        # Get unique values for filters
        if self.parts_data:
            machines = ["All"] + sorted(list(set(p['machine_name'] for p in self.parts_data)))
            materials = ["All"] + sorted(list(set(p['material'] for p in self.parts_data)))
            categories = ["All"] + sorted(list(set(p['category'] for p in self.parts_data)))
        else:
            machines = materials = categories = ["All"]
        
        selected_machine = st.sidebar.selectbox("Nama Mesin", machines)
        selected_material = st.sidebar.selectbox("Material Part", materials)
        selected_category = st.sidebar.selectbox("Kategori Part", categories)
        
        return status_filter, selected_machine, selected_material, selected_category
    
    def apply_filters(self, status_filter, selected_machine, selected_material, selected_category):
        """Terapkan filter pada data"""
        filtered_data = []
        
        for part in self.parts_data:
            # Calculate status for each part
            remaining_hours = self.calculate_remaining_hours(part)
            status, _, _ = self.get_status(remaining_hours)
            
            # Apply filters
            status_match = status in status_filter
            machine_match = selected_machine == "All" or part['machine_name'] == selected_machine
            material_match = selected_material == "All" or part['material'] == selected_material
            category_match = selected_category == "All" or part['category'] == selected_category
            
            if status_match and machine_match and material_match and category_match:
                filtered_data.append(part)
                
        return filtered_data
    
    def show_dashboard(self):
        """Tampilkan dashboard utama"""
        st.title("🔧 Dashboard Monitoring Part Mesin")
        
        # Sidebar filters
        status_filter, selected_machine, selected_material, selected_category = self.show_sidebar_filters()
        
        # Apply filters
        filtered_data = self.apply_filters(status_filter, selected_machine, selected_material, selected_category)
        
        # KPI Cards
        st.subheader("📈 Key Performance Indicators")
        col1, col2, col3, col4 = st.columns(4)
        
        total_parts = len(filtered_data)
        
        # Calculate status counts
        status_counts = {"Normal": 0, "Warning": 0, "Harus Ganti": 0}
        for part in filtered_data:
            remaining_hours = self.calculate_remaining_hours(part)
            status, _, _ = self.get_status(remaining_hours)
            status_counts[status] += 1
        
        with col1:
            st.metric(
                "Total Parts", 
                total_parts,
                help="Jumlah total part yang terfilter"
            )
        
        with col2:
            st.metric(
                "Normal", 
                status_counts["Normal"],
                delta=f"{(status_counts['Normal']/total_parts*100):.1f}%" if total_parts > 0 else "0%",
                help="Part dengan sisa usia > 500 jam"
            )
        
        with col3:
            st.metric(
                "Warning", 
                status_counts["Warning"],
                delta=f"{(status_counts['Warning']/total_parts*100):.1f}%" if total_parts > 0 else "0%",
                delta_color="inverse",
                help="Part dengan sisa usia < 500 jam"
            )
        
        with col4:
            st.metric(
                "Harus Ganti", 
                status_counts["Harus Ganti"],
                delta=f"{(status_counts['Harus Ganti']/total_parts*100):.1f}%" if total_parts > 0 else "0%",
                delta_color="off",
                help="Part dengan sisa usia = 0 jam"
            )
        
        # Visualizations
        if filtered_data:
            col1, col2 = st.columns(2)
            
            with col1:
                # Status Distribution Pie Chart
                fig_pie = px.pie(
                    values=list(status_counts.values()),
                    names=list(status_counts.keys()),
                    title="Distribusi Status Part",
                    color=list(status_counts.keys()),
                    color_discrete_map={
                        "Normal": "#00FF00",
                        "Warning": "#FFA500", 
                        "Harus Ganti": "#FF0000"
                    }
                )
                fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                # Category Distribution
                category_data = {}
                for part in filtered_data:
                    category = part['category']
                    category_data[category] = category_data.get(category, 0) + 1
                
                if category_data:
                    fig_bar = px.bar(
                        x=list(category_data.keys()),
                        y=list(category_data.values()),
                        title="Distribusi Part per Kategori",
                        labels={'x': 'Kategori', 'y': 'Jumlah Part'},
                        color=list(category_data.keys())
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)
        
        # Data Table dengan Status Visual
        st.subheader("📋 Data Monitoring Part")
        
        if filtered_data:
            # Prepare data for display dengan status
            display_data = []
            for part in filtered_data:
                remaining_hours = self.calculate_remaining_hours(part)
                replacement_date = self.calculate_replacement_date(part)
                status, emoji, color = self.get_status(remaining_hours)
                
                display_data.append({
                    'No Part': part['part_number'],
                    'Kode Part': part['part_code'],
                    'Nama Mesin': part['machine_name'],
                    'Material': part['material'],
                    'Tanggal Pasang': part['install_date'],
                    'Rekomendasi (jam)': part['recommended_usage'],
                    'Kategori': part['category'],
                    'Tanggal Ganti': replacement_date.strftime("%Y-%m-%d"),
                    'Sisa Usia (jam)': remaining_hours,
                    'Status': status,
                    'Status Icon': emoji,
                    'Color': color
                })
            
            df = pd.DataFrame(display_data)
            
            # Tampilkan tabel dengan styling
            st.dataframe(
                df[[
                    'No Part', 'Kode Part', 'Nama Mesin', 'Material', 
                    'Tanggal Pasang', 'Rekomendasi (jam)', 'Kategori',
                    'Tanggal Ganti', 'Sisa Usia (jam)', 'Status Icon'
                ]],
                use_container_width=True,
                height=400
            )
            
            # Download button
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download Data sebagai CSV",
                data=csv,
                file_name="part_monitoring_data.csv",
                mime="text/csv",
                help="Download data monitoring dalam format CSV"
            )
            
            # Blinking alert untuk part yang harus diganti
            if status_counts["Harus Ganti"] > 0:
                with st.container():
                    st.markdown("---")
                    # Blinking effect
                    if int(time.time()) % 2 == 0:
                        st.error(f"🚨 **PERINGATAN**: {status_counts['Harus Ganti']} part harus segera diganti!")
                    else:
                        st.warning(f"⚠️ **PERINGATAN**: {status_counts['Harus Ganti']} part harus segera diganti!")
                    
        else:
            st.info("📝 Tidak ada data yang sesuai dengan filter yang dipilih.")
    
    def show_input_form(self):
        """Tampilkan form input data part baru"""
        st.title("➕ Input Data Part Baru")
        
        with st.form("input_part_form", clear_on_submit=True):
            st.subheader("📝 Form Input Data Part")
            
            col1, col2 = st.columns(2)
            
            with col1:
                part_number = st.text_input("Nomor Part*", help="Nomor unik identifikasi part")
                part_code = st.text_input("Kode Part*", help="Kode khusus part")
                machine_name = st.text_input("Nama Mesin*", help="Nama mesin tempat part terpasang")
                material = st.text_input("Material Part*", help="Material pembuat part")
            
            with col2:
                install_date = st.date_input("Tanggal Pemasangan*", datetime.now(), help="Tanggal part dipasang")
                recommended_usage = st.number_input(
                    "Rekomendasi Penggunaan (jam)*", 
                    min_value=1, 
                    value=1000,
                    help="Usia pakai recommended dalam jam"
                )
                category = st.selectbox(
                    "Kategori Part*", 
                    ["Mechanical", "Electrical", "Pneumatic"],
                    help="Pilih kategori part"
                )
            
            submitted = st.form_submit_button("💾 Simpan Data Part")
            
            if submitted:
                if all([part_number, part_code, machine_name, material]):
                    # Check for duplicate part number
                    if any(p['part_number'] == part_number for p in self.parts_data):
                        st.error("❌ Nomor Part sudah ada dalam database!")
                    else:
                        new_part = {
                            'part_number': part_number,
                            'part_code': part_code,
                            'machine_name': machine_name,
                            'material': material,
                            'install_date': install_date.strftime("%Y-%m-%d"),
                            'recommended_usage': int(recommended_usage),
                            'category': category
                        }
                        
                        self.parts_data.append(new_part)
                        if self.save_data():
                            st.success("✅ Data part berhasil disimpan!")
                            st.balloons()
                        else:
                            st.error("❌ Gagal menyimpan data!")
                else:
                    st.error("❌ Semua field bertanda * harus diisi!")
    
    def show_edit_data(self):
        """Tampilkan form edit data part"""
        st.title("✏️ Edit Data Part")
        
        if not self.parts_data:
            st.info("📝 Tidak ada data part untuk diedit.")
            return
        
        # Pilih part untuk diedit
        part_options = {f"{p['part_number']} - {p['machine_name']}": p for p in self.parts_data}
        selected_part_key = st.selectbox(
            "Pilih Part untuk Diedit:",
            options=list(part_options.keys())
        )
        
        if selected_part_key:
            selected_part = part_options[selected_part_key]
            
            with st.form("edit_part_form"):
                st.subheader(f"Edit Data: {selected_part['part_number']}")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    new_part_number = st.text_input("Nomor Part*", value=selected_part['part_number'])
                    new_part_code = st.text_input("Kode Part*", value=selected_part['part_code'])
                    new_machine_name = st.text_input("Nama Mesin*", value=selected_part['machine_name'])
                    new_material = st.text_input("Material Part*", value=selected_part['material'])
                
                with col2:
                    new_install_date = st.date_input(
                        "Tanggal Pemasangan*", 
                        datetime.strptime(selected_part['install_date'], "%Y-%m-%d")
                    )
                    new_recommended_usage = st.number_input(
                        "Rekomendasi Penggunaan (jam)*", 
                        min_value=1, 
                        value=selected_part['recommended_usage']
                    )
                    new_category = st.selectbox(
                        "Kategori Part*", 
                        ["Mechanical", "Electrical", "Pneumatic"],
                        index=["Mechanical", "Electrical", "Pneumatic"].index(selected_part['category'])
                    )
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    update_submitted = st.form_submit_button("💾 Update Data")
                with col2:
                    delete_submitted = st.form_submit_button("🗑️ Hapus Part")
                with col3:
                    mark_replaced = st.form_submit_button("🔧 Tandai Sudah Diganti")
                
                if update_submitted:
                    if all([new_part_number, new_part_code, new_machine_name, new_material]):
                        # Update data
                        selected_part.update({
                            'part_number': new_part_number,
                            'part_code': new_part_code,
                            'machine_name': new_machine_name,
                            'material': new_material,
                            'install_date': new_install_date.strftime("%Y-%m-%d"),
                            'recommended_usage': int(new_recommended_usage),
                            'category': new_category
                        })
                        
                        if self.save_data():
                            st.success("✅ Data part berhasil diupdate!")
                            st.rerun()
                        else:
                            st.error("❌ Gagal mengupdate data!")
                    else:
                        st.error("❌ Semua field bertanda * harus diisi!")
                
                if delete_submitted:
                    # Konfirmasi penghapusan
                    if st.checkbox("✅ Konfirmasi penghapusan part"):
                        self.parts_data.remove(selected_part)
                        if self.save_data():
                            st.success("✅ Part berhasil dihapus!")
                            st.rerun()
                        else:
                            st.error("❌ Gagal menghapus part!")
                
                if mark_replaced:
                    # Tandai part sudah diganti (reset tanggal pemasangan)
                    selected_part['install_date'] = datetime.now().strftime("%Y-%m-%d")
                    if self.save_data():
                        st.success("✅ Part berhasil ditandai sebagai sudah diganti!")
                        st.rerun()
                    else:
                        st.error("❌ Gagal menandai part!")
    
    def show_upload_data(self):
        """Tampilkan form upload data CSV"""
        st.title("📤 Upload Data dari CSV")
        
        st.info("""
        **📋 Format CSV yang Didukung:**
        - Kolom wajib: `part_number`, `part_code`, `machine_name`, `material`, `install_date`, `recommended_usage`, `category`
        - Format tanggal: YYYY-MM-DD
        - File harus berformat CSV dengan encoding UTF-8
        """)
        
        # Template download
        template_data = {
            'part_number': ['PART001', 'PART002'],
            'part_code': ['CODE001', 'CODE002'],
            'machine_name': ['Mesin A', 'Mesin B'],
            'material': ['Steel', 'Aluminum'],
            'install_date': ['2024-01-01', '2024-01-15'],
            'recommended_usage': [2000, 1500],
            'category': ['Mechanical', 'Electrical']
        }
        
        template_df = pd.DataFrame(template_data)
        csv_template = template_df.to_csv(index=False)
        
        st.download_button(
            label="📥 Download Template CSV",
            data=csv_template,
            file_name="template_part_data.csv",
            mime="text/csv",
            help="Download template CSV untuk input data"
        )
        
        uploaded_file = st.file_uploader("Pilih file CSV", type=['csv'])
        
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                required_columns = ['part_number', 'part_code', 'machine_name', 'material', 
                                  'install_date', 'recommended_usage', 'category']
                
                if all(col in df.columns for col in required_columns):
                    st.success(f"✅ File berhasil dibaca. {len(df)} data ditemukan.")
                    
                    # Display preview
                    st.subheader("Preview Data")
                    st.dataframe(df.head())
                    
                    # Pilihan import mode
                    import_mode = st.radio(
                        "Mode Import:",
                        ["Tambah Data Baru", "Replace Semua Data"],
                        help="Pilih cara import data"
                    )
                    
                    if st.button("🚀 Import Data ke Sistem"):
                        with st.spinner("Mengimport data..."):
                            if import_mode == "Tambah Data Baru":
                                new_data = df.to_dict('records')
                                # Check for duplicates
                                existing_numbers = [p['part_number'] for p in self.parts_data]
                                duplicates = [p for p in new_data if p['part_number'] in existing_numbers]
                                
                                if duplicates:
                                    st.warning(f"⚠️ {len(duplicates)} data duplicate akan diabaikan.")
                                    new_data = [p for p in new_data if p['part_number'] not in existing_numbers]
                                
                                self.parts_data.extend(new_data)
                                success_msg = f"✅ Berhasil menambahkan {len(new_data)} data part baru!"
                                
                            else:  # Replace semua data
                                self.parts_data = df.to_dict('records')
                                success_msg = f"✅ Berhasil mengganti semua data dengan {len(df)} data part!"
                            
                            if self.save_data():
                                st.success(success_msg)
                                st.balloons()
                            else:
                                st.error("❌ Gagal menyimpan data!")
                                
                else:
                    st.error("❌ Format CSV tidak sesuai. Pastikan semua kolom wajib ada.")
                    st.write("**Kolom yang dibutuhkan:**", required_columns)
                    st.write("**Kolom yang ada dalam file:**", list(df.columns))
                    
            except Exception as e:
                st.error(f"❌ Error membaca file: {str(e)}")
    
    def show_manual_book(self):
        """Tampilkan manual book"""
        st.title("📖 Manual Book")
        
        # Language selection
        col1, col2 = st.columns([1, 4])
        with col1:
            language = st.radio("Bahasa / Language:", ["Indonesia", "English"])
        
        st.markdown("---")
        
        if language == "Indonesia":
            self.show_manual_indonesia()
        else:
            self.show_manual_english()
    
    def show_manual_indonesia(self):
        """Tampilkan manual book bahasa Indonesia"""
        
        st.header("Panduan Penggunaan Sistem Monitoring Part Mesin")
        
        # Overview
        with st.expander("📋 **Overview Sistem**", expanded=True):
            st.markdown("""
            Sistem ini dirancang untuk memantau dan mengelola penggantian part mesin secara efisien.
            
            **Fitur Utama:**
            - 📊 **Dashboard Monitoring**: Pantau status semua part secara real-time
            - ➕ **Input Data**: Tambah data part baru
            - ✏️ **Edit Data**: Update atau hapus data part yang sudah ada
            - 📤 **Upload CSV**: Import data dalam jumlah besar
            - 📖 **Manual Book**: Panduan penggunaan sistem
            """)
        
        # Dashboard Guide
        with st.expander("📊 **Panduan Dashboard**"):
            st.markdown("""
            **1. Filter Data:**
            - **Filter Status**: Pilih status part yang ingin ditampilkan
            - **Filter Mesin**: Filter berdasarkan nama mesin
            - **Filter Material**: Filter berdasarkan material part
            - **Filter Kategori**: Filter berdasarkan kategori part
            
            **2. Key Performance Indicators (KPI):**
            - **Total Parts**: Jumlah total part yang terfilter
            - **Normal**: Part dengan sisa usia > 500 jam
            - **Warning**: Part dengan sisa usia < 500 jam
            - **Harus Ganti**: Part dengan sisa usia = 0 jam
            
            **3. Visualisasi Data:**
            - **Pie Chart**: Distribusi status part
            - **Bar Chart**: Distribusi part per kategori
            
            **4. Tabel Data:**
            - Menampilkan detail semua part
            - Status ditampilkan dengan icon dan warna
            - Download data dalam format CSV
            """)
        
        # Status Guide
        with st.expander("🚦 **Panduan Status Part**"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.success("**🟢 NORMAL**")
                st.write("Sisa usia pakai > 500 jam")
                st.write("**Tindakan**: Lanjutkan pemantauan rutin")
            
            with col2:
                st.warning("**🟡 WARNING**")
                st.write("Sisa usia pakai < 500 jam")
                st.write("**Tindakan**: Persiapkan part pengganti")
            
            with col3:
                st.error("**🔴 HARUS GANTI**")
                st.write("Sisa usia pakai = 0 jam")
                st.write("**Tindakan**: Ganti segera! (Blinking alert)")
        
        # Input Data Guide
        with st.expander("➕ **Panduan Input Data**"):
            st.markdown("""
            **Field Wajib (*):**
            - **Nomor Part**: Identifier unik untuk setiap part
            - **Kode Part**: Kode internal part
            - **Nama Mesin**: Mesin tempat part terpasang
            - **Material Part**: Material pembuat part
            - **Tanggal Pemasangan**: Tanggal part dipasang
            - **Rekomendasi Penggunaan**: Usia pakai dalam jam
            - **Kategori Part**: Mechanical, Electrical, atau Pneumatic
            
            **Tips:**
            - Pastikan Nomor Part unik untuk setiap part
            - Gunakan format tanggal YYYY-MM-DD
            - Rekomendasi penggunaan dalam jam operasi
            """)
        
        # Edit Data Guide
        with st.expander("✏️ **Panduan Edit Data**"):
            st.markdown("""
            **Fitur Edit:**
            - **Update Data**: Ubah informasi part yang sudah ada
            - **Hapus Part**: Hapus part dari sistem
            - **Tandai Sudah Diganti**: Reset tanggal pemasangan ke hari ini
            
            **Penggunaan:**
            1. Pilih part dari dropdown
            2. Ubah data yang diperlukan
            3. Klik tombol aksi yang diinginkan
            4. Konfirmasi perubahan
            """)
    
    def show_manual_english(self):
        """Tampilkan manual book bahasa Inggris"""
        
        st.header("User Manual - Machine Part Monitoring System")
        
        # Overview
        with st.expander("📋 **System Overview**", expanded=True):
            st.markdown("""
            This system is designed to efficiently monitor and manage machine part replacements.
            
            **Main Features:**
            - 📊 **Monitoring Dashboard**: Real-time status monitoring of all parts
            - ➕ **Input Data**: Add new part data
            - ✏️ **Edit Data**: Update or delete existing part data
            - 📤 **Upload CSV**: Bulk import data
            - 📖 **Manual Book**: System usage guide
            """)
        
        # Dashboard Guide
        with st.expander("📊 **Dashboard Guide**"):
            st.markdown("""
            **1. Data Filters:**
            - **Status Filter**: Select part status to display
            - **Machine Filter**: Filter by machine name
            - **Material Filter**: Filter by part material
            - **Category Filter**: Filter by part category
            
            **2. Key Performance Indicators (KPI):**
            - **Total Parts**: Total number of filtered parts
            - **Normal**: Parts with remaining lifespan > 500 hours
            - **Warning**: Parts with remaining lifespan < 500 hours
            - **Must Replace**: Parts with remaining lifespan = 0 hours
            
            **3. Data Visualization:**
            - **Pie Chart**: Part status distribution
            - **Bar Chart**: Part distribution by category
            
            **4. Data Table:**
            - Display detailed part information
            - Status shown with icons and colors
            - Download data in CSV format
            """)
        
        # Status Guide
        with st.expander("🚦 **Part Status Guide**"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.success("**🟢 NORMAL**")
                st.write("Remaining lifespan > 500 hours")
                st.write("**Action**: Continue routine monitoring")
            
            with col2:
                st.warning("**🟡 WARNING**")
                st.write("Remaining lifespan < 500 hours")
                st.write("**Action**: Prepare replacement part")
            
            with col3:
                st.error("**🔴 MUST REPLACE**")
                st.write("Remaining lifespan = 0 hours")
                st.write("**Action**: Replace immediately! (Blinking alert)")
        
        # Input Data Guide
        with st.expander("➕ **Input Data Guide**"):
            st.markdown("""
            **Required Fields (*):**
            - **Part Number**: Unique identifier for each part
            - **Part Code**: Internal part code
            - **Machine Name**: Machine where part is installed
            - **Part Material**: Part construction material
            - **Installation Date**: Date when part was installed
            - **Recommended Usage**: Lifespan in operating hours
            - **Part Category**: Mechanical, Electrical, or Pneumatic
            
            **Tips:**
            - Ensure Part Number is unique for each part
            - Use date format YYYY-MM-DD
            - Recommended usage in operating hours
            """)
        
        # Edit Data Guide
        with st.expander("✏️ **Edit Data Guide**"):
            st.markdown("""
            **Edit Features:**
            - **Update Data**: Modify existing part information
            - **Delete Part**: Remove part from system
            - **Mark as Replaced**: Reset installation date to today
            
            **Usage:**
            1. Select part from dropdown
            2. Modify required data
            3. Click desired action button
            4. Confirm changes
            """)

def main():
    # Initialize the app
    app = PartMonitoringSystem()
    
    # Sidebar navigation
    st.sidebar.markdown("---")
    st.sidebar.subheader("🗂️ Navigation")
    
    menu_options = {
        "📊 Dashboard": app.show_dashboard,
        "➕ Input Data": app.show_input_form,
        "✏️ Edit Data": app.show_edit_data,
        "📤 Upload CSV": app.show_upload_data,
        "📖 Manual Book": app.show_manual_book
    }
    
    selected_menu = st.sidebar.radio("Pilih Menu", list(menu_options.keys()))
    
    # Show selected page
    menu_options[selected_menu]()

if __name__ == "__main__":
    main()