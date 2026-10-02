import os
import json
import shutil
from pathlib import Path

# Таблица транслитерации (украинская + русская кириллица)
TRANSLIT_MAP = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'h', 'ґ': 'g', 'д': 'd', 'е': 'e', 'є': 'ye',
    'ж': 'zh', 'з': 'z', 'и': 'y', 'і': 'i', 'ї': 'yi', 'й': 'y', 'к': 'k', 'л': 'l',
    'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
    'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch', 'ь': '',
    'ю': 'yu', 'я': 'ya', 'ъ': '', 'ы': 'y', 'э': 'e', 'ё': 'yo',
    # Заглавные буквы
    'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'H', 'Ґ': 'G', 'Д': 'D', 'Е': 'E', 'Є': 'Ye',
    'Ж': 'Zh', 'З': 'Z', 'И': 'Y', 'І': 'I', 'Ї': 'Yi', 'Й': 'Y', 'К': 'K', 'Л': 'L',
    'М': 'M', 'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U',
    'Ф': 'F', 'Х': 'Kh', 'Ц': 'Ts', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Shch', 'Ь': '',
    'Ю': 'Yu', 'Я': 'Ya', 'Ъ': '', 'Ы': 'Y', 'Э': 'E', 'Ё': 'Yo'
}

def transliterate(text: str) -> str:
    """Переводит кириллицу в латиницу, сохраняя регистр и остальные символы."""
    res = []
    for char in text:
        res.append(TRANSLIT_MAP.get(char, char))
    return ''.join(res).lower()  # приводим имя файла к нижнему регистру для единообразия

def process_rename(json_path: str, empl_dir: str):
    json_file = Path(json_path)
    empl_path = Path(empl_dir)

    if not json_file.exists():
        print(f"Ошибка: Файл {json_path} не найден!")
        return

    if not empl_path.exists():
        print(f"Ошибка: Директория {empl_dir} не найдена!")
        return

    # Создаём бэкап JSON файла перед изменением
    backup_path = json_file.with_suffix('.json.bak')
    shutil.copy(json_file, backup_path)
    print(f"Создан бэкап: {backup_path}")

    # Загружаем JSON
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Карта переименований файлов: {старое_имя: новое_имя}
    renamed_files = {}

    # 1. Переименовываем физические файлы в папке
    for file in empl_path.iterdir():
        if file.is_file():
            old_name = file.name
            # Разделяем имя и расширение, транслитерируем только stem (имя без расширения)
            stem = file.stem
            ext = file.suffix
            
            new_stem = transliterate(stem)
            new_name = f"{new_stem}{ext}"

            if old_name != new_name:
                old_file_path = file
                new_file_path = empl_path / new_name

                # Если файл с новым именем уже существует, избегаем перезаписи
                counter = 1
                while new_file_path.exists() and new_file_path != old_file_path:
                    new_file_path = empl_path / f"{new_stem}_{counter}{ext}"
                    new_name = new_file_path.name
                    counter += 1

                old_file_path.rename(new_file_path)
                renamed_files[old_name] = new_name
                print(f"[Файл переименован] {old_name} -> {new_name}")

    # 2. Обновляем пути в JSON
    updated_count = 0
    for specialist in data.get('specialists', []):
        avatar = specialist.get('avatar', '')
        if avatar:
            # Разбиваем путь "empl/имя.png" на директорию и файл
            parts = avatar.split('/')
            file_name = parts[-1]

            # Если файл переименовывался физически или требует транслитерации
            if file_name in renamed_files:
                parts[-1] = renamed_files[file_name]
                new_avatar_path = '/'.join(parts)
                specialist['avatar'] = new_avatar_path
                updated_count += 1
                print(f"[JSON обновлен] ID {specialist['id']}: {avatar} -> {new_avatar_path}")
            else:
                # На случай, если в JSON имя файла в кириллице, но файла на диске не было
                stem, ext = os.path.splitext(file_name)
                translit_name = f"{transliterate(stem)}{ext}"
                if file_name != translit_name:
                    parts[-1] = translit_name
                    new_avatar_path = '/'.join(parts)
                    specialist['avatar'] = new_avatar_path
                    updated_count += 1
                    print(f"[JSON обновлен (не найден на диске)] ID {specialist['id']}: {avatar} -> {new_avatar_path}")

    # Сохраняем обновленный JSON
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\nГотово! Переименовано файлов: {len(renamed_files)}, обновлено записей в JSON: {updated_count}")

if __name__ == '__main__':
    # Укажите реальные пути к вашему JSON и папке с картинками
    JSON_FILE_PATH = '/home/feq/Downloads/siis/employee.json'
    EMPL_DIR_PATH = '/home/feq/Downloads/empl'

    process_rename(JSON_FILE_PATH, EMPL_DIR_PATH)
