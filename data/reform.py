import json
from pathlib import Path

VALID_EXTS = {".jpg", ".jpeg", ".png"}

def fix_questions(data):
    for block in data:  # каждый элемент верхнего списка
        if "questions" in block:
            for q in block["questions"]:
                qid = q.get("id")
                if not qid:
                    continue
                # определяем расширение (берём из первого img)
                ext = ".jpg"
                for item in q.get("body", []):
                    if item.get("type") == 2 and "value" in item:
                        ext = Path(item["value"]).suffix or ".jpg"
                        if ext.lower() == ".jpeg":
                            ext = ".jpg"
                        break
                # переписываем все картинки
                for item in q.get("body", []):
                    if item.get("type") == 2:
                        item["value"] = f"/images/{qid}{ext}"
    return data


if __name__ == "__main__":
    in_path = Path("/home/kanat/Codes/py_project/Avtotest/data/kaa_kiril.json")
    out_path = Path("/home/kanat/Codes/py_project/Avtotest/data/kaa_kiril.fixed.json")

    with in_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    fixed = fix_questions(data)

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(fixed, f, ensure_ascii=False, indent=2)

    print(f"✅ Готово! Результат сохранён в {out_path}")
