import re
import unicodedata
from datetime import date

def slugify(value: str) -> str:
    txt = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", txt).strip("-")[:180] or "artikel"

def parse_meeting_notes(notes: str) -> dict:
    out = {"discussions": [], "decisions": [], "tasks": []}
    for raw in notes.splitlines():
        line = re.sub(r"^\s*(?:[-*•]|\d+[.)])\s*", "", raw).strip()
        if not line:
            continue
        match = re.match(r"^(keputusan|diputuskan|disepakati)\s*[:：-]\s*(.+)", line, flags=re.I)
        if match:
            out["decisions"].append(match.group(2).strip())
            continue
        match = re.match(r"^(tugas|tindak lanjut|aksi|action)\s*[:：-]\s*(.+)", line, flags=re.I)
        if match:
            pieces = re.split(r"\s*\|\s*", match.group(2))
            task = {"title": pieces.pop(0).strip(), "owner": "", "due": "", "status": "Belum mulai", "remark": ""}
            for piece in pieces:
                sub = re.match(r"^(pic|pj|penanggung jawab|owner|tenggat|target|deadline|batas waktu)\s*[:：-]\s*(.+)$", piece, flags=re.I)
                if sub:
                    key = "due" if sub.group(1).lower() in ["tenggat", "target", "deadline", "batas waktu"] else "owner"
                    task[key] = sub.group(2).strip()
            if task["title"]:
                out["tasks"].append(task)
        else:
            out["discussions"].append(line)
    return out

def letter_body(kind: str, recipient: str, subject: str, instructions: str, signer: str, date_value: str, number: str, attachment: str) -> str:
    date_value = date_value or str(date.today())
    common = ("BADAN PENGELOLA KAMPUS REMBANG\nUNIVERSITAS DIPONEGORO\n\n"
              + "Rembang, " + date_value + "\nNomor: " + number + "\nLampiran: " + attachment
              + "\nPerihal: " + subject + "\n\n" + recipient + "\n\nDengan hormat,\n\n")
    if kind == "Undangan rapat":
        body = "Dengan ini kami mengundang Bapak/Ibu untuk menghadiri rapat tentang " + subject + ".\n\n" + instructions
    elif kind == "Nota dinas":
        body = "Sehubungan dengan " + subject + ", disampaikan hal-hal berikut:\n\n" + instructions
    elif kind == "Laporan kegiatan":
        return "LAPORAN KEGIATAN\n" + subject.upper() + "\n\n" + instructions
    else:
        body = "Dalam rangka " + subject.lower() + ", berikut kami sampaikan:\n\n" + instructions
    return common + body + "\n\nAtas perhatian dan kerja sama Bapak/Ibu, kami mengucapkan terima kasih.\n\n" + signer
