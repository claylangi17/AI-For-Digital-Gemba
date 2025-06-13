import mysql.connector
import re
from datetime import datetime

# --- KONFIGURASI DATABASE BARU ---
DB_CONFIG = {
    'host': 'localhost',        # Ganti dengan host database Anda
    'user': 'your_user',        # Ganti dengan user database Anda
    'password': 'your_password',  # Ganti dengan password Anda
    'database': 'digital_gemba'  # Ganti dengan nama database baru Anda
}

# Path ke file SQL lama Anda
OLD_SQL_FILE_PATH = r'd:\Coding\AI For Digital Gemba\gemba_issues.sql'

def parse_sql_insert_values(line):
    """Mengekstrak nilai dari satu baris VALUES dalam pernyataan INSERT SQL."""
    match = re.search(r'\((.*?)\)', line)
    if not match:
        return None
    
    values_str = match.group(1)
    # Memecah berdasarkan koma, tetapi hati-hati dengan koma di dalam string
    # Regex ini mencoba menangani string yang diapit ' atau " dan nilai numerik/NULL
    # Ini adalah penyederhanaan dan mungkin perlu penyesuaian jika datanya kompleks
    raw_values = re.findall(r"'(?:[^']|'')*'|\d+\.\d+|\d+|NULL", values_str)
    
    parsed_values = []
    for val in raw_values:
        if val == 'NULL':
            parsed_values.append(None)
        elif val.startswith("'") and val.endswith("'"):
            # Menghapus tanda kutip dan mengganti '' dengan '
            parsed_values.append(val[1:-1].replace("''", "'")) 
        elif '.' in val:
            try:
                parsed_values.append(float(val))
            except ValueError:
                parsed_values.append(val) # Jika bukan float, simpan sebagai string
        else:
            try:
                parsed_values.append(int(val))
            except ValueError:
                parsed_values.append(val) # Jika bukan int, simpan sebagai string
    return parsed_values

def get_or_create_line(cursor, area_name):
    """Mendapatkan line_id untuk area_name, membuat jika belum ada."""
    if not area_name:
        return None
    cursor.execute("SELECT id FROM `lines` WHERE name = %s", (area_name,))
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        cursor.execute("INSERT INTO `lines` (name) VALUES (%s)", (area_name,))
        return cursor.lastrowid

def migrate_data():
    conn = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print("Berhasil terhubung ke database baru.")

        with open(OLD_SQL_FILE_PATH, 'r', encoding='utf-8') as f:
            in_insert_statement = False
            for line in f:
                line = line.strip()
                if line.upper().startswith('INSERT INTO `gemba_issues`'):
                    in_insert_statement = True
                    print(f"Memproses: {line[:100]}...")
                    continue
                
                if not in_insert_statement or not line:
                    continue

                # Baris data biasanya diakhiri dengan ; atau , 
                # Jika diakhiri ;, maka ini adalah akhir dari satu batch INSERT
                is_last_row_in_batch = line.endswith(';')
                current_line_values_str = line.rstrip(',')
                if is_last_row_in_batch:
                    current_line_values_str = current_line_values_str.rstrip(';')
                
                values = parse_sql_insert_values(current_line_values_str)
                if not values or len(values) != 9: # Sesuai jumlah kolom di gemba_issues
                    print(f"Peringatan: Melewatkan baris data yang tidak dapat diparsing atau tidak lengkap: {current_line_values_str}")
                    continue

                legacy_id, date_str, area, problem, root_cause_desc, temp_action, prev_action, source_file, category = values

                # 1. Tangani 'lines'
                line_id = get_or_create_line(cursor, area)

                # 2. Insert ke 'issues'
                # Asumsi 'date_str' adalah YYYY-MM-DD. Jika perlu konversi ke datetime:
                created_at_dt = None
                if date_str:
                    try:
                        created_at_dt = datetime.strptime(date_str, '%Y-%m-%d')
                    except ValueError:
                        print(f"Peringatan: Format tanggal tidak valid '{date_str}' untuk legacy_id {legacy_id}. Menggunakan NULL.")
                
                # Periksa apakah legacy_id sudah ada
                cursor.execute("SELECT id FROM issues WHERE legacy_id = %s", (legacy_id,))
                existing_issue = cursor.fetchone()
                if existing_issue:
                    print(f"Informasi: Data untuk legacy_id {legacy_id} sudah ada di tabel issues. Melewatkan.")
                    continue # Lanjut ke baris data berikutnya dari file SQL

                issue_sql = """
                INSERT INTO issues (description, created_at, line_id, source_file_name, legacy_id, status)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                # Asumsi status default, misal 'OPEN' atau 'REPORTED'
                # Sesuaikan 'status' jika diperlukan
                issue_status = 'OPEN' # Ganti jika perlu
                cursor.execute(issue_sql, (problem, created_at_dt, line_id, source_file, legacy_id, issue_status))
                new_issue_id = cursor.lastrowid

                # 3. Insert ke 'root_causes'
                # Asumsi setiap 'problem' memiliki satu 'root_cause' utama dari file lama
                new_root_cause_id = None
                if root_cause_desc:
                    rc_sql = """
                    INSERT INTO root_causes (issue_id, description, category, user_id, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                    """
                    # Asumsi user_id default jika tidak ada, atau bisa di-hardcode/dicari
                    # Asumsi created_at sama dengan issue
                    default_user_id = 'system_migration' # Ganti jika perlu
                    cursor.execute(rc_sql, (new_issue_id, root_cause_desc, category, default_user_id, created_at_dt))
                    new_root_cause_id = cursor.lastrowid
                    
                    # Update issues.root_cause_id jika desainnya demikian
                    # cursor.execute("UPDATE issues SET root_cause_id = %s WHERE id = %s", (new_root_cause_id, new_issue_id))

                # 4. Insert ke 'actions'
                if temp_action:
                    action_sql = """
                    INSERT INTO actions (issue_id, root_cause_id, type, description, created_at, user_id, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """
                    # Asumsi status default, misal 'PROPOSED' atau 'DONE'
                    action_status = 'DONE' # Ganti jika perlu
                    cursor.execute(action_sql, (new_issue_id, new_root_cause_id, 'CORRECTIVE', temp_action, created_at_dt, default_user_id, action_status))
                
                if prev_action:
                    action_sql = """
                    INSERT INTO actions (issue_id, root_cause_id, type, description, created_at, user_id, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """
                    action_status = 'DONE' # Ganti jika perlu
                    cursor.execute(action_sql, (new_issue_id, new_root_cause_id, 'PREVENTIVE', prev_action, created_at_dt, default_user_id, action_status))

                print(f"Berhasil memigrasikan legacy_id: {legacy_id} -> issue_id: {new_issue_id}")

                if is_last_row_in_batch:
                    in_insert_statement = False # Siap untuk pernyataan INSERT berikutnya
            
        conn.commit()
        print("Migrasi data selesai dan di-commit.")

    except mysql.connector.Error as err:
        print(f"Error MySQL: {err}")
        if conn:
            conn.rollback()
            print("Transaksi di-rollback.")
    except FileNotFoundError:
        print(f"Error: File SQL lama tidak ditemukan di {OLD_SQL_FILE_PATH}")
    except Exception as e:
        print(f"Terjadi error yang tidak terduga: {e}")
        if conn:
            conn.rollback()
            print("Transaksi di-rollback.")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
            print("Koneksi database ditutup.")

if __name__ == '__main__':
    migrate_data()
