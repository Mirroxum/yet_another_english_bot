EN = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
RU = ['а', 'б', 'в', 'г', 'д', 'е', 'ё', 'ж', 'з', 'и', 'й', 'к', 'л', 'м', 'н', 'о', 'п', 'р', 'с', 'т', 'у', 'ф', 'х', 'ц', 'ч', 'ш', 'щ', 'э', 'ю', 'я']

def detect(text):
    text = text.lower()
    ru_count = 0
    en_count = 0
    for word in text:
        if word in RU:
            ru_count += 1
        if word in EN:
            en_count += 1
    if ru_count == 0 and en_count == 0:
        return 'Я не знаю этого языка'
    return 'ru' if ru_count > en_count else 'en'
