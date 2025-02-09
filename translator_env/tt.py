from translate import translator

t = translator()

translation = t(phrase="Hello, world!", dest='zh', from_lang='en')
print("Translation:", translation)  # Added "Translation:" prefix for clarity
