# from bs4 import BeautifulSoup

# def wrap_annotations_with_raw(html_content):
#     soup = BeautifulSoup(html_content, 'html.parser')

#     # Найти все теги <annotation>
#     annotations = soup.find_all('annotation', {'encoding': 'application/x-tex'})

#     for annotation in annotations:
#         # Обернуть каждый тег в {% raw %} и {% endraw %}
#         annotation.insert_before("{% raw %}")
#         annotation.insert_after("{% endraw %}")

#     return str(soup)

from bs4 import BeautifulSoup, NavigableString
import re

def add_raw_tags_to_body(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Находим тег <body>
    body = soup.body

    if body:
        # Итерация по всем текстовым узлам внутри <body>
        for text_node in body.find_all(text=True):
            if isinstance(text_node, NavigableString):
                updated_text = re.sub(r'(\$\$.*?\$\$)', r'{% raw %}\1{% endraw %}', text_node, flags=re.DOTALL)
                text_node.replace_with(updated_text)

    return str(soup)

html_name = input("Введите имя HTML файла (без расширения): ")

# Чтение HTML-файла
with open(f'templates/lessons/{html_name}.html', 'r', encoding='utf-8') as file:
    html_content = file.read()

# Обработка HTML-файла
processed_html = add_raw_tags_to_body(html_content)

# Сохранение обработанного HTML-файла
with open(f'templates/lessons/{html_name}.html', 'w', encoding='utf-8') as file:
    file.write(processed_html)
