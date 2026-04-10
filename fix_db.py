import sqlite3
import datetime

def jalankan_perbaikan():
    # Hubungkan ke database
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()

    print("Memulai proses sinkronisasi database manual...")

    try:
        # 1. Ambil semua teks topik unik dari tabel question
        cursor.execute("SELECT DISTINCT topic FROM alp_app_question WHERE topic IS NOT NULL")
        topics = [row[0] for row in cursor.fetchall()]

        for topic_name in topics:
            if not topic_name: 
                continue
            
            # 2. Masukkan ke tabel alp_app_topic
            # Kita gunakan placeholder datetime agar tidak NOT NULL error
            now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("""
                INSERT OR IGNORE INTO alp_app_topic (name, created_at) 
                VALUES (?, ?)
            """, (topic_name, now))
            
            # 3. Ambil ID dari topik tersebut
            cursor.execute("SELECT id FROM alp_app_topic WHERE name = ?", (topic_name,))
            result = cursor.fetchone()
            if result:
                topic_id = result[0]
                
                # 4. Update tabel question: isi kolom topic_relation_id
                cursor.execute("""
                    UPDATE alp_app_question 
                    SET topic_relation_id = ? 
                    WHERE topic = ?
                """, (topic_id, topic_name))
                
                print(f"✅ Topik '{topic_name}' berhasil sinkron.")

        conn.commit()
        print("\n🎉 BERHASIL! Soal kamu sudah terhubung ke tabel Topic.")

    except Exception as e:
        print(f"❌ Terjadi kesalahan: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    jalankan_perbaikan()