from translate import translator

t = translator()

translation = t(phrase="Hello, world!", dest='zh', from_lang='en')
print(translation)
