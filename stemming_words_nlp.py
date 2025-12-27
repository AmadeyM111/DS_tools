from nltk import PorterStemmer

stemmer = PorterStemmer()
stemmed_text = [stemmer.stem(word) for word in text_without_stopwords]
print(f"Text without stopwords: {text_without_stopwords}")
print(f"Stemmed text: {stemmed_text}")

from nltk import WordNetLemmatizer

nltk.download("wordnet")
clear_output()

lemmatizer = WordNetLemmatizer()
lemmatized_text = [lemmatizer.lemmatize(word) for word in text_without_stopwords]
print(f"Text without stopwords: {text_without_stopwords}")
print(f"Lemmatized text: {lemmatized_text}")