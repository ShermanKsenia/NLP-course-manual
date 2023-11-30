from bs4 import BeautifulSoup, Comment, NavigableString
import pymorphy2
import re
from urllib.parse import quote_plus
import json

# Инициализация морфологического анализатора
morph = pymorphy2.MorphAnalyzer()

def lemmatize_text(text):
    # Разбиваем текст с использованием регулярного выражения, которое учитывает различные символы
    words = re.split(r'([^А-яA-z-])', text)
    # Лемматизируем слова
    return [morph.parse(word)[0].normal_form for word in words]

def lemmatize_keywords(keywords):
    return [''.join(lemmatize_text(keyword)) for keyword in keywords]

def find_and_highlight(lemmatized_list, original_list, keywords, found_keywords, soup):  
    # Лемматизация ключевых слов
    lemmatized_keywords = lemmatize_keywords(keywords)

    new_content = []
    i = 0
    while i < len(lemmatized_list):
        match_found = False
        for n, keyword in enumerate(lemmatized_keywords):
            if found_keywords[keywords[n]]:  # Пропускаем уже найденные ключевые слова
                continue
            keyword_length = len(keyword.split())
            end = i
            if keyword.split()[0] == lemmatized_list[i]:
                if ' ' in keyword:
                    matches = [(j, word) for j, word in enumerate(lemmatized_list[i:]) if word.isalpha()][:len(keyword.split())]
                    match = ' '.join([word for _, word in matches])
                    if keyword == match:
                        end = i + matches[-1][0]
                    else:
                        continue
                
                # Создаем тег для выделения
                highlight_tag = soup.new_tag("span", **{'class': 'highlight'})

                # Вставляем тег в список
                tag_string = ''.join(original_list[i:end+1])
                highlight_tag.string = tag_string

                # Создаем ссылку
                keyword_url = quote_plus(keywords[n].lower().replace(' ', '_'), encoding='utf-8')
                link = soup.new_tag('a', href='/terms#' + keyword_url)
                link.insert(0, highlight_tag)

                new_content.append(link)
                if ' ' in keyword:
                    i += 1
                i += keyword_length
                match_found = True
                found_keywords[keywords[n]] = True  # Помечаем ключевое слово как найденное
                break
        
        if not match_found:
            new_content.append(original_list[i])
            i += 1
    
    return new_content

def process_html(html, keywords, found_keywords):
    soup = BeautifulSoup(html, 'html.parser')

    for element in soup.find_all(text=True):
        # Игнорируем шаблонные теги Jinja2
        if re.match(r'\{%.*?%\}', element) or re.match(r'\{\{.*?\}\}', element):
            continue

        # Получаем родительские классы элемента
        parent_classes = element.parent.get('class', [])

        # Пропускаем определенные элементы, элементы внутри блоков кода, шаблонные теги Jinja2 и специфичные div
        if (element.parent.name in ['script', 'style', 'a'] or
            isinstance(element, Comment) or
            'jp-CodeCell' in parent_classes or
            ('highlight' in parent_classes and 'hl-ipython3' in parent_classes)):
            continue

        if element.parent.name != 'h1' and element.parent.name != 'h2' and element.parent.name != 'h3' and element.parent.name != 'span':
            if isinstance(element, NavigableString):
                original_text = element.string
                original_text_list = re.split(r'([^А-яA-z-])', original_text)
                lemmatized_text_list = lemmatize_text(original_text)

                new_content = find_and_highlight(lemmatized_text_list, original_text_list, keywords, found_keywords, soup)
            
                # Заменяем содержимое элемента
                for content in new_content:
                    if isinstance(content, str):
                        element.insert_before(content)
                    else:
                        element.insert_before(content)
                element.extract()  # Используем extract вместо decompose
    
    # Добавляем <!DOCTYPE html> в начало результата, если он отсутствует
    result_html = str(soup)
    if result_html.startswith('html'):
        # Удаляем "html", если он есть, и добавляем <!DOCTYPE html>
        result_html = '<!DOCTYPE html>\n' + result_html[5:]

    return result_html

html_name = input("Введите имя HTML файла (без расширения): ")

# Загрузка данных об уроках из JSON-файла
with open('terms.json') as json_file:
    terms = json.load(json_file)

# Сортировка данных по ключам
sorted_terms = dict(sorted(terms.items()))

# Запись отсортированных данных обратно в файл
with open('terms.json', 'w', encoding='utf-8') as file:
    json.dump(sorted_terms, file, ensure_ascii=False, indent=4)

# Чтение HTML-файла
with open(f'templates/lessons/{html_name}.html', 'r', encoding='utf-8') as file:
    html_content = file.read()

# Список ключевых слов/фраз
keywords = [term for term in list(sorted_terms.keys())]

# Используем словарь для отслеживания найденных ключевых слов
found_keywords = {keyword: False for keyword in keywords}

# Обработка HTML
processed_html = process_html(html_content, keywords, found_keywords)

# Сохранение обработанного HTML
with open(f'templates/lessons/{html_name}.html', 'w', encoding='utf-8') as file:
    file.write(processed_html)
