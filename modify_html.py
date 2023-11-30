from bs4 import BeautifulSoup

html_name = input("Введите имя HTML файла (без расширения): ")

# Загрузка HTML-документа из файла
with open(f'templates/lessons/{html_name}.html', 'r', encoding='utf-8') as file:
    html_content = file.read()

soup = BeautifulSoup(html_content, 'html.parser')

# Поиск и удаление всех тегов с классом 'jp-InputPrompt jp-InputArea-prompt'
for div in soup.find_all('div', class_=['jp-InputPrompt', 'jp-OutputPrompt']):
    div.decompose()

# Поиск всех блоков кода с текстом '# решение'
code_cells = soup.find_all('div', class_='jp-CodeCell')
for cell in code_cells:
    if cell.find('span', string='# решение'):
        # Добавляем класс для скрытия блока кода
        cell['class'].append('hidden-solution')
        # Создаем и добавляем кнопку перед блоком кода
        toggle_button = soup.new_tag('button', type='button', onclick='toggleSolution(this)')
        toggle_button.string = 'Решение'
        cell.insert_before(toggle_button)

# Сохранение изменений в новом файле
with open(f'templates/lessons/{html_name}.html', 'w', encoding='utf-8') as file:
    file.write(str(soup))

print("Файл успешно обновлен и сохранен как 'modified_file.html'")
