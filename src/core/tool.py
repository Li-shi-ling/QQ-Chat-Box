import json

def read_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data

def write_json_file(data, file_path, indent=4, ensure_ascii=False):
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=indent, ensure_ascii=ensure_ascii)
