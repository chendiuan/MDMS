import os
import zipfile
import tarfile
import rarfile
import patoolib
import pandas as pd
from pathlib import Path


def is_compressed_file(filename):
    """檢查檔案是否為支援的壓縮檔案格式"""
    supported_extensions = ('.7z', '.zip', '.tar.gz', '.tgz', '.rar')
    return filename.lower().endswith(supported_extensions)

def extract_rar_file(file_path, extract_path):
    """使用 patoolib 解壓縮 RAR 檔案"""
    try:
        patoolib.extract_archive(file_path, outdir=extract_path)
        print(f"✅ Extracted (patoolib): {file_path} -> {extract_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to extract {file_path} with patoolib: {e}")
        return False

def extract_compressed_file(file_path, extract_path):
    """解壓縮單一壓縮檔案"""
    try:
        if file_path.endswith('.7z'):
            print(f"⚠️ Skipping unsupported .7z file: {file_path}")
        elif file_path.endswith('.zip'):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
        elif file_path.endswith('.rar'):
            if not extract_rar_file(file_path, extract_path):
                print(f"❌ patoolib failed to extract {file_path}")
        elif file_path.endswith(('.tar.gz', '.tgz')):
            with tarfile.open(file_path, 'r:gz') as tar_ref:
                tar_ref.extractall(extract_path)

        print(f"✅ Extracted: {file_path} -> {extract_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to extract {file_path}: {e}")
        return False


def deep_recursive_extraction(root_folder, extracted_files=set()):
    """
    遞迴解壓縮所有支援的壓縮檔案，包括嵌套在資料夾內的壓縮檔
    """
    for dirpath, _, filenames in os.walk(root_folder):
        for filename in filenames:
            if is_compressed_file(filename):
                file_path = os.path.join(dirpath, filename)

                # 避免重複解壓縮已處理的檔案
                if file_path in extracted_files:
                    continue

                extract_path = dirpath  # 解壓縮到原始目錄
                success = extract_compressed_file(file_path, extract_path)

                if success:
                    extracted_files.add(file_path)
                    os.remove(file_path)  # 解壓縮成功後刪除壓縮檔
                    # 立即重新掃描新產生的目錄（確保嵌套的壓縮檔也能解壓）
                    deep_recursive_extraction(extract_path, extracted_files)


def find_results_folders(root_folder):
    """ 遞迴尋找 'Results_' 開頭的資料夾 """
    results_folders = []
    for dirpath, dirnames, _ in os.walk(root_folder):
        for dirname in dirnames:
            if dirname.startswith("Results_"):
                results_folders.append(os.path.join(dirpath, dirname))
    return results_folders


def split_tsv_by_port(file, header_line):
    """ 依據 PORT 欄位將 TSV 分割成不同檔案 """
    try:
        df = pd.read_csv(file, sep='\t', skiprows=header_line, engine='python', on_bad_lines='skip')
        if 'PORT' in df.columns:
            output_dir = Path(file).parent
            for port, df_port in df.groupby('PORT'):
                output_file = output_dir / f"PORT_{str(port)}.tsv"
                df_port.to_csv(output_file, sep='\t', index=False)
                print(f"📄 Created: {output_file}")
    except Exception as e:
        print(f"❌ Error splitting {file}: {e}")


def analyze_tsv_files(folder):
    """ 解析資料夾內的 tsv 檔案並找出最小面積的 port 和 lane """
    records = []

    for file in Path(folder).rglob("PORT_*.tsv"):
        try:
            df = pd.read_csv(file, sep='\t', engine='python', on_bad_lines='skip')

            # 計算最小面積
            if {'PORT', 'LANE', 'HIGH', 'LOW', 'LEFT', 'RIGHT'}.issubset(df.columns):
                df['Eye_Height'] = df['HIGH'] - df['LOW']
                df['Eye_Width'] = df['RIGHT'] - df['LEFT']
                df['EH x EW'] = df['Eye_Height'] * df['Eye_Width']

                min_row = df.loc[df['EH x EW'].idxmin()]
                records.append([folder, min_row['PORT'], min_row['LANE'], min_row['EH x EW']])
        except Exception as e:
            print(f"❌ Error processing {file}: {e}")

    return records


def main(root_folder, output_excel):
    # 完全遞迴解壓縮所有壓縮檔案
    deep_recursive_extraction(root_folder)

    # 找到所有 Results_* 資料夾
    results_folders = find_results_folders(root_folder)

    records = []
    for folder in results_folders:
        for file in Path(folder).rglob("*.tsv"):
            # 找到標題行位置
            with open(file, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f):
                    if "PORT" in line and "LANE" in line and "HIGH" in line and "LOW" in line and "LEFT" in line and "RIGHT" in line:
                        header_line = i
                        break
                else:
                    print(f"❌ Skipping {file}: No valid header found")
                    continue

            # 執行 TSV 分割
            split_tsv_by_port(file, header_line)

        # 分析已分割的 TSV 檔案
        records.extend(analyze_tsv_files(folder))

    # 匯出結果
    if records:
        df_out = pd.DataFrame(records, columns=["Folder", "Port", "Lane", "EH x EW"])
        df_out.to_excel(output_excel, index=False)
        print(f"📊 結果輸出到: {output_excel}")
    else:
        print("⚠️ 未找到合適的數據")


if __name__ == "__main__":
    root_folder = "H:/Sifnos Andros"
    output_excel = "H:/output.xlsx"
    main(root_folder, output_excel)
