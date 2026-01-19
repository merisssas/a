import os
import re

# ==========================================
# KONFIGURASI POLA PENCARIAN
# ==========================================
PATTERNS = {
    "BASIC_AUTH_CANDIDATE": r'Basic\s([a-zA-Z0-9+/=]{20,})',  # Cari string "Basic xxxx..."
    "POTENTIAL_SECRET": r'([a-zA-Z0-9]{60,150})',             # Cari string acak panjang (60-150 char)
    "XML_AUTH_KEY": r'<string name=".*?auth.*?">(.*?)</string>', # Cari di strings.xml
    "XML_ANY_KEY": r'<string name=".*?key.*?">(.*?)</string>'    # Cari key apapun di xml
}

# String lama untuk referensi (Script akan highlight jika nemu yang mirip strukturnya)
OLD_SECRET_PART = "mU1Y4n1vBjf3" 

def search_files(start_path):
    print(f"[*] Memulai perburuan di: {start_path}")
    
    findings = []
    
    # Walk through all directories
    for root, dirs, files in os.walk(start_path):
        for file in files:
            # Kita hanya cari di file XML (resources) dan Java (source code)
            if not file.endswith(('.xml', '.java', '.kt')):
                continue

            file_path = os.path.join(root, file)
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                    # 1. Cek Strings.xml (Tempat paling sering Basic Auth sembunyi)
                    if file == "strings.xml":
                        # Cari authorization basic
                        if "authorization" in content.lower() or "basic" in content.lower():
                            findings.append(f"\n[XML HIT] {file_path}")
                            # Extract baris yang relevan
                            for line in content.splitlines():
                                if "auth" in line.lower() or "basic" in line.lower():
                                    findings.append(f"   >> {line.strip()}")

                    # 2. Cek Source Code (Java/Kotlin) untuk Secret Key
                    # Strategi: Cari variabel yang menyimpan string sangat panjang
                    if file.endswith(('.java', '.kt')):
                        matches = re.findall(PATTERNS["POTENTIAL_SECRET"], content)
                        for m in matches:
                            # Filter sampah (bukan base64/hex murni)
                            if " " in m or "<" in m or "{" in m: continue
                            
                            # Filter Secret Key (biasanya panjangnya pas 128 char atau mirip)
                            if len(m) > 80: 
                                findings.append(f"[CODE HIT] {file_path} \n   >> Possible Secret: {m[:50]}... (Len: {len(m)})")

            except Exception as e:
                print(f"Error reading {file_path}: {e}")

    return findings

if __name__ == "__main__":
    # Folder output dari JADX
    TARGET_DIR = "out"
    
    if not os.path.exists(TARGET_DIR):
        print("Folder 'out' tidak ditemukan. Decompile gagal?")
        exit(1)

    results = search_files(TARGET_DIR)
    
    print("\n" + "="*50)
    print("HASIL PERBURUAN KEY")
    print("="*50)
    
    if results:
        for item in results:
            print(item)
    else:
        print("Tidak ditemukan kandidat yang jelas. Coba cek manual folder 'out/resources/res/values/strings.xml'")
