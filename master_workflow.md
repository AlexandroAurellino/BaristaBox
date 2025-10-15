### **Arsitektur Alur Kerja Sistem (System Workflow Architecture)**

Diagram ini memvisualisasikan alur kerja lengkap dari sistem BaristaBox AI, mulai dari input pengguna hingga output solusi. Arsitektur ini dibagi menjadi dua bagian utama: **Alur Tingkat Tinggi (Intent Routing)** dan **Alur Detail (Engine Logic)**, dengan fokus pada implementasi `DoctorEngine` yang paling komprehensif.

---

### **Bagian 1: Alur Tingkat Tinggi - Penentuan Tujuan (Intent Routing)**

Bagian atas diagram mengilustrasikan bagaimana sistem menangani setiap interaksi baru untuk menentukan tujuan pengguna.

1.  **App Started & User Input:** Alur dimulai saat aplikasi Streamlit siap dan pengguna memasukkan permintaan pertama mereka ke dalam antarmuka.

2.  **Call Classifier #1 (Master Intent):** Input teks pengguna pertama kali diproses oleh `Master Intent Classifier`. Model klasifikasi PyTorch ini bertugas untuk menganalisis kalimat dan mengkategorikannya ke dalam salah satu dari tiga _intent_ utama yang telah ditentukan.

3.  **Decide Intent (Titik Keputusan):** Hasil dari classifier (sebuah label `intent`) dievaluasi pada titik keputusan ini. Logika `if/elif/else` di dalam `app.py` mengarahkan alur kerja ke _engine_ yang sesuai berdasarkan hasil tersebut:
    - Jika `Intent == 'Doctor'`, sistem memanggil `CoffeeDoctor Engine`.
    - Jika `Intent == 'Sommelier'`, sistem memanggil `CoffeeSommelier Engine`.
    - Jika `Intent == 'MasterBrewer'`, sistem memanggil `MasterBrewer Engine`.

Setiap _engine_ kemudian mengambil alih kontrol untuk menangani permintaan pengguna sesuai dengan keahliannya.

### **Bagian 2: Alur Detail - Logika `DoctorEngine`**

Bagian bawah diagram adalah "pembesaran" dari apa yang terjadi di dalam `DoctorEngine`. Ini menunjukkan proses penalaran berbasis aturan yang canggih dan peka terhadap konteks.

1.  **Context Gathering:** Setelah dipanggil, langkah pertama _engine_ adalah mengumpulkan konteks. Ia memulai serangkaian pertanyaan untuk mendapatkan **`Initial Contex`**, yang terdiri dari tiga informasi penting: masalah yang telah diklasifikasikan sebelumnya, nama biji kopi, dan metode seduh yang digunakan.

2.  **Parallel Knowledge Retrieval:** Dengan `Initial Contex` yang tersedia, dua proses pencarian pengetahuan terjadi secara paralel:

    - **Look up Database (Beans & Recipes):** Sistem mencari di database biji kopi dan resep. Jika kecocokan ditemukan (**`IF BEAN FOUND`**), ia menginisialisasi objek data `bean_profile` dan `ideal_recipe`, yang disimpan sebagai **`Contextual Data`**. Jika tidak, data ini akan kosong.
    - **Get List of Causes From Database:** Berdasarkan label masalah dari `Initial Contex`, sistem mengambil daftar aturan diagnostik umum dari `troubleshooting_knowledge_base.json`. Hasilnya adalah **`General Data`** (atau `General Rules`).

3.  **Pre-Processing Rules (Apply Meta Rules):** Ini adalah inti dari kecerdasan sistem. Di sini, kedua cabang pengetahuan bertemu. Logika utama sistem menerapkan serangkaian "meta-aturan" di mana `Contextual Data` (jika ada) digunakan untuk memodifikasi `General Data`. Proses ini dapat **memprioritaskan ulang**, **menonaktifkan**, atau **mengubah** aturan umum agar sesuai dengan situasi spesifik pengguna.

4.  **List of Adjusted Rules:** Hasil dari pra-pemrosesan adalah sebuah rencana diagnostik yang telah disesuaikan secara dinamis, khusus untuk sesi tersebut.

5.  **Evidence Gathering (Loop & Ask User):** Sistem sekarang memasuki sebuah loop inferensi. Ia akan menguji setiap aturan dari `List of Adjusted Rules` dengan cara:

    - Mengajukan pertanyaan kepada pengguna.
    - Menginterpretasikan jawaban pengguna (menggunakan Gemini untuk menafsirkan `yes/no/unsure`).
    - Jika jawaban afirmatif, aturan tersebut dianggap sebagai "bukti".

6.  **List of Evidence:** Setelah loop selesai, sistem memiliki daftar semua penyebab yang telah dikonfirmasi oleh pengguna.

7.  **Synthesize Final Diagnosis & Generate Prompt:** Berdasarkan `List of Evidence` (apakah ada satu atau beberapa bukti), sistem menyusun sebuah prompt akhir yang komprehensif untuk Gemini. Prompt ini berisi instruksi untuk memberikan solusi yang terstruktur dan berprioritas.

8.  **Call Gemini API & Output Generation:** Prompt akhir dikirim ke Gemini, yang menghasilkan **`Final Solution Text`**.

9.  **Solution Served in Streamlit:** Teks solusi yang telah diformat dan kaya konteks ini akhirnya ditampilkan kepada pengguna, menandai akhir dari sesi diagnostik.
