import pandas as pd
import re
import os

# IEEE CSV
def parse_ieee_csv(file_path):
    df = pd.read_csv(file_path)
    records = []

    for _, row in df.iterrows():
        record = {
            "Database": "IEEE",
            "Authors": row.get("Authors", ""),
            "Title": row.get("Document Title", ""),
            "Journal": row.get("Publication Title", ""),
            "Year": row.get("Publication Year", ""),
            "Volume": row.get("Volume", ""),
            "Issue": row.get("Issue", ""),
            "Pages": f"{row.get('Start Page', '')}-{row.get('End Page', '')}" if pd.notna(row.get("Start Page", "")) and pd.notna(row.get("End Page", "")) else "",
            "DOI": row.get("DOI", ""),
            "URL": row.get("PDF Link", ""),
            "Abstract": row.get("Abstract", ""),
            "Keywords": row.get("Author Keywords", "")
        }
        records.append(record)
    return records

# Scopus RIS 
def parse_ris_scopus(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    entries = []
    entry = {}
    current_key = ""
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("TY  -"):
            entry = {"Database": "Scopus"}
        elif line.startswith("ER  -"):
            entries.append(entry)
            entry = {}
        else:
            match = re.match(r'^([A-Z0-9]{2})\s*-\s*(.*)', line)
            if match:
                current_key, value = match.groups()
                if current_key in entry:
                    entry[current_key] += "; " + value
                else:
                    entry[current_key] = value
            else:
                if current_key in entry:
                    entry[current_key] += " " + line

    records = []
    for e in entries:
        record = {
            "Database": "Scopus",
            "Authors": e.get("AU", ""),
            "Title": e.get("TI", ""),
            "Journal": e.get("JO", ""),
            "Year": e.get("PY", ""),
            "Volume": e.get("VL", ""),
            "Issue": e.get("IS", ""),
            "Pages": f"{e.get('SP', '')}-{e.get('EP', '')}" if "SP" in e and "EP" in e else "",
            "DOI": e.get("DO", ""),
            "URL": e.get("UR", ""),
            "Abstract": e.get("AB", ""),
            "Keywords": e.get("KW", "")
        }
        records.append(record)
    return records

# ACM ENW (corrigido)
def parse_enw_ACM(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    entries = []
    entry = {}
    current_key = ""

    for line in lines:
        line = line.strip()

        if line.startswith("%0"):
            if entry:
                entries.append(entry)
                entry = {"Database": "ACM"}
            else:
                entry = {"Database": "ACM"}
            current_key = "%0"
            entry[current_key] = line[3:].strip()

        elif line.startswith("%"):
            current_key = line[:2]
            value = line[3:].strip()
            if current_key in entry:
                entry[current_key] += "; " + value
            else:
                entry[current_key] = value

        else:
            if current_key and current_key in entry:
                entry[current_key] += " " + line.strip()

    if entry:
        entries.append(entry)

    records = []
    for e in entries:
        record = {
            "Database": "ACM",
            "Authors": e.get("%A", ""),
            "Title": e.get("%T", ""),
            "Journal": e.get("%J", ""),
            "Year": e.get("%D", ""),
            "Volume": e.get("%V", ""),
            "Issue": e.get("%N", ""),
            "Pages": e.get("%P", ""),
            "DOI": e.get("%R", ""),
            "URL": e.get("%U", ""),
            "Abstract": e.get("%X", ""),
            "Keywords": e.get("%K", "")
        }
        records.append(record)
    return records

# ScienceDirect TXT
def parse_sciencedirect(txt):
    entries = txt.strip().split("\n\n")
    records = []

    for entry in entries:
        lines = entry.split("\n")
        record = {
            "Database": "ScienceDirect",
            "Authors": "",
            "Title": "",
            "Journal": "",
            "Year": "",
            "Volume": "",
            "Issue": "",
            "Pages": "",
            "DOI": "",
            "URL": "",
            "Abstract": "",
            "Keywords": ""
        }

        try:
            record["Authors"] = lines[0].strip()
            record["Title"] = lines[1].strip()
            record["Journal"] = lines[2].strip()

            for i in range(3, len(lines)):
                if "Volume" in lines[i]:
                    record["Volume"] = lines[i].replace("Volume", "").strip()
                elif re.match(r"\d{4}", lines[i]):
                    record["Year"] = lines[i].strip()
                elif "Pages" in lines[i]:
                    record["Pages"] = lines[i].replace("Pages", "").strip()
                elif "Issue" in lines[i]:
                    record["Issue"] = lines[i].replace("Issue", "").strip()
                elif lines[i].startswith("https://doi"):
                    record["DOI"] = lines[i].strip()
                elif lines[i].startswith("(") and "sciencedirect.com" in lines[i]:
                    record["URL"] = lines[i].strip("()")
                elif lines[i].startswith("Abstract:"):
                    record["Abstract"] = lines[i].replace("Abstract:", "").strip()
                elif lines[i].startswith("Keywords:"):
                    record["Keywords"] = lines[i].replace("Keywords:", "").strip()

        except Exception as e:
            print(f"Erro ao processar entrada: {e}")
        records.append(record)
    return records

# Caminho para a pasta "referencias"
referencias_dir = os.path.join(os.path.dirname(__file__), "referencias")

# Lista para todos os registros
todos_registros = []

# Processa todos os arquivos
for filename in os.listdir(referencias_dir):
    path = os.path.join(referencias_dir, filename)

    try:
        if filename.endswith(".csv"):
            registros = parse_ieee_csv(path)
        elif filename.endswith(".ris"):
            registros = parse_ris_scopus(path)
        elif filename.endswith(".enw"):
            registros = parse_enw_ACM(path)
        elif filename.endswith(".txt"):
            with open(path, "r", encoding="utf-8") as f:
                conteudo = f.read()
            registros = parse_sciencedirect(conteudo)
        else:
            print(f"Tipo de arquivo não suportado: {filename}")
            continue

        todos_registros.extend(registros)
        print(f"[✓] Processado: {filename}")
    except Exception as e:
        print(f"[X] Erro ao processar {filename}: {e}")

# Cria DataFrame e salva como CSV
df_merged = pd.DataFrame(todos_registros)
output_csv = os.path.join(os.path.dirname(__file__), "referencias_unificadas.csv")
df_merged.to_csv(output_csv, index=False, encoding='utf-8-sig')

print(f"\n Arquivo final gerado com sucesso: {output_csv}")
