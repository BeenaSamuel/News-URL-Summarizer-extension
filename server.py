from flask import Flask, jsonify, request
from flask_cors import CORS
import requests 
from transformers import AutoTokenizer,  AutoModelForSeq2SeqLM, pipeline
from bs4 import BeautifulSoup
import spacy
from spacy.lang.en.stop_words import STOP_WORDS
from string import punctuation
from heapq import nlargest
import math


app = Flask(__name__)
CORS(app)
app.secret_key = "any-string-you-want-just-keep-it-secret"

# class Summarize(FlaskForm):
#     url = URLField(label='URL')
#     submit = SubmitField(label="Generate Summary")

# model_name= "BeenaSamuel/t5_small_cnn_multi_news_abstractive_summarizer_v2"
# model_name= "BeenaSamuel/t5_cnn_daily_mail_abstractive_summarizer_v2"
# model_name= "BeenaSamuel/bbc-news-summarizer"
nlp= spacy.load("en_core_web_sm")
punctuation=punctuation+'n'
stop_words= list(STOP_WORDS)

def spans_to_paragraph(spans):
    paragraph = ""
    for span in spans:
        paragraph += span.text + " "
    return paragraph.strip()

def get_data(URL):    
    r = requests.get(URL)
    soup = BeautifulSoup(r.text, 'html.parser')
    results = soup.find_all(['h1', lambda tag: tag.name == 'p' and not tag.find('time')])
    headline = soup.find('h1')
    headline = headline.text
    text = [result.text for result in results]
    NEWS = ' '.join(text)
    doc=nlp(NEWS)
    word_freq={}
    for word in doc:
      if word.text.lower() not in stop_words:
          if word.text.lower() not in punctuation:
              if word.text not in word_freq.keys():
                  word_freq[word.text]= 1
              else:
                  word_freq[word.text]+= 1
    # x=(word_freq.values())
    # a=list(x)
    # a.sort()
    # max_freq=a[-1]
    
    #  TF 
    max_freq = max(word_freq.values())
    for word in word_freq.keys():
        word_freq[word] = word_freq[word] / max_freq 

    # IDF 
    # total_docs = 1  
    # for word in word_freq.keys():
    #     word_count = sum(1 for doc in doc.sents if word in [token.text.lower() for token in doc])
    #     word_freq[word] *= math.log(total_docs / (1 + word_count))

    # for word in word_freq.keys():
    #   word_freq[word]=word_freq[word]/max_freq
    sent_score={}
    sent_tokens=[sent for sent in doc.sents]
    for sent in sent_tokens:
      for word in sent:
          if word.text.lower() in word_freq.keys():
              if sent not in sent_score.keys():
                  sent_score[sent]=word_freq[word.text.lower()]
              else:
                  sent_score[sent]+= word_freq[word.text.lower()]
    n_val = len(sent_tokens) * 0.8
    n_val= math.ceil(n_val)
    extractive_summary=nlargest(n=n_val,iterable=sent_score,key=sent_score.get)
    extractive_summary = spans_to_paragraph(extractive_summary)
    print(extractive_summary)
    return extractive_summary, headline

# @app.route("/")
# def hello():
#     return render_template("index.html")


# @app.route("/summarize", methods=['POST', 'GET'])
# def summarize():
#     summary_form = Summarize()
#     if request.method == "POST":
#         web_url = summary_form.url.data
#         content, headline = get_data(web_url)
#         max_chunk = 500
#         NEWS = content.replace('.', '.<eos>')
#         NEWS = NEWS.replace('?', '?<eos>')
#         NEWS = NEWS.replace('!', '!<eos>')

#         sentences = NEWS.split('<eos>')
#         current_chunk = 0
#         chunks = []
#         for sentence in sentences:
#             if len(chunks) == current_chunk + 1:
#                 if len(chunks[current_chunk]) + len(sentence.split(' ')) <= max_chunk:
#                     chunks[current_chunk].extend(sentence.split(' '))
#                 else:
#                     current_chunk += 1
#                     chunks.append(sentence.split(' '))
#             else:
#                 print(current_chunk)
#                 chunks.append(sentence.split(' '))

#         for chunk_id in range(len(chunks)):
#             chunks[chunk_id] = ' '.join(chunks[chunk_id])

#         res = summarizer(chunks, min_length=30, max_length=120, do_sample=False)
#         summary = ' '.join([summ['summary_text'] for summ in res])
#         return render_template('summarize.html', form=summary_form, summary=summary , headline= headline)
        
#     return render_template('summarize.html', form=summary_form)
    
@app.route("/", methods=['POST'])
def summarize_url():
    url = request.json['url']
    
    summary_type = request.json['summaryType']  
    summary_length = request.json['summaryLength']  
    content, headline = get_data(url) 
    
    article_words = [word for word in content.split() if word.strip(punctuation)]
    articleword_count = len(article_words)

    print(request.json) 
    print(f"Summary Type: {summary_type}")
    print(f"Summary Length: {summary_length}")
    

    def get_chunks(max_chunk):
        print(max_chunk)
        NEWS = content.replace('.', '.<eos>')
        NEWS = NEWS.replace('?', '?<eos>')
        NEWS = NEWS.replace('!', '!<eos>')

        sentences = NEWS.split('<eos>')
        current_chunk = 0
        chunks = []
        for sentence in sentences:
            if len(chunks) == current_chunk + 1:
                if len(chunks[current_chunk]) + len(sentence.split(' ')) <= max_chunk:
                    chunks[current_chunk].extend(sentence.split(' '))
                else:
                    current_chunk += 1
                    chunks.append(sentence.split(' '))
            else:
                print(current_chunk)
                chunks.append(sentence.split(' '))

        for chunk_id in range(len(chunks)):
            chunks[chunk_id] = ' '.join(chunks[chunk_id])
        return chunks
    

    if summary_type == "abstractive":
        # model_name= "BeenaSamuel/t5_small_cnn_multi_news_abstractive_summarizer_v2"
        # model_name= "BeenaSamuel/t5_cnn_daily_mail_abstractive_summarizer_v2"
        model_name= "BeenaSamuel/bart-cnn-dm-abstractive"
        
        if summary_length == "0":
            model_name= "BeenaSamuel/bart-cnn-dm-abstractive"
            print(model_name)
            print("small")
            chunks = get_chunks(1000)
            # summarizer = pipeline("summarization" , model= model_name)
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
            summarizer = pipeline("summarization", model=model, tokenizer=tokenizer, num_beams=5, do_sample=True, no_repeat_ngram_size=3 )
            # res = summarizer(chunks, min_length=30,max_length = 120, do_sample=False)
            # res = summarizer(chunks, min_length=30,max_length = 120, do_sample=False)
            res = summarizer(chunks)
        elif summary_length == "2":
            model_name= "BeenaSamuel/t5_small_cnn_multi_news_abstractive_summarizer_v2"
            print("large")
            print(model_name)
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
            summarizer = pipeline("summarization", model=model, tokenizer=tokenizer, num_beams=5, do_sample=True, no_repeat_ngram_size=3 )
            # summarizer = pipeline("summarization" , model= model_name)
            print(summarizer)
            chunks = get_chunks(500)
            res = summarizer(chunks, min_length=50, max_length= 200,  do_sample=False)
            # print(res)
            # res[0]['summary_text'].replace("–", " ")
            # print( res[0]['summary_text'])
            
        else:
            model_name= "BeenaSamuel/t5_cnn_daily_mail_abstractive_summarizer_v2"
            print(model_name)
            print("medium")
            chunks = get_chunks(500)
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
            summarizer = pipeline("summarization", model=model, tokenizer=tokenizer, num_beams=6, do_sample=True, no_repeat_ngram_size=3 )
            res = summarizer(chunks, min_length=30,max_length = 120, do_sample=False)
    else:
        # model_name= "BeenaSamuel/bbc-news-summarizer"
        # print(model_name)
        # tokenizer = AutoTokenizer.from_pretrained(model_name)
        # model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

        # summarizer = pipeline("summarization", model=model, tokenizer=tokenizer, num_beams=4, do_sample=True, no_repeat_ngram_size=3 )
        if summary_length == "0":
            model_name= "BeenaSamuel/t5_small_bbc_news_extractive_summarizer"
            print(model_name)
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
            print("small")
            chunks = get_chunks(500)
            summarizer = pipeline("summarization", model=model, tokenizer=tokenizer, num_beams=4, do_sample=True, no_repeat_ngram_size=3 )
            res = summarizer(chunks, do_sample=False)
            
        elif summary_length == "2":
            model_name= "BeenaSamuel/bbc-news-summarizer"
            print(model_name)
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
            print("large")
            chunks = get_chunks(250)
            summarizer = pipeline("summarization", model=model, tokenizer=tokenizer, num_beams=3, do_sample=True, no_repeat_ngram_size=3 )
            res = summarizer(chunks, do_sample=False)
            
            
        else:
            model_name= "BeenaSamuel/bbc-news-summarizer"
            print(model_name)
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
            print("medium")
            chunks = get_chunks(500)
            summarizer = pipeline("summarization", model=model, tokenizer=tokenizer, num_beams=5, do_sample=True, no_repeat_ngram_size=3 )
            res = summarizer(chunks, do_sample=False)
        


    summary = ' '.join([summ['summary_text'] for summ in res])
    # return jsonify({'summary': summary , 'headline': headline , 'summaryType': summary_type , 'summaryLength': summary_length})
    
    words = [word for word in summary.split() if word.strip(punctuation)]
    word_count = len(words)

    sentences = summary.split('.')

    # re.sub("–", " ", sentences[0])

    print(sentences[0])

    print(type(sentences[0]))

    
    sentences = [sentence.strip() for sentence in sentences if sentence.strip()]

    
    summary_list = [{'sentence': sentence, 'index': index} for index, sentence in enumerate(sentences, start=1)]

    
    formatted_summary_list = [{'sentence': item['sentence'], 'index': item['index']} for item in summary_list]

    return jsonify({'summary': formatted_summary_list, 'headline': headline, 'summaryType': summary_type , 'wordCount' : word_count, 'articleWords' : articleword_count  })

# @app.route("/", methods=['POST'])
# def summarize_url():
#     url = request.json['url']
    
#     summary_type = request.json['summaryType']  
#     # summary_length = request.json['summaryLength']  
#     content, headline = get_data(url) 
    
#     article_words = [word for word in content.split() if word.strip(punctuation)]
#     articleword_count = len(article_words)

#     print(request.json) 
#     print(f"Summary Type: {summary_type}")
#     # print(f"Summary Length: {summary_length}")
    
#     # print(headline)
#     # print(type(headline))
    
#     # max_chunk = 250

#     def remove_double_dash(text):
#     # Remove "--" from the text
#         return str.replace(text,'–', '')
    

#     def get_chunks(max_chunk):
#         print(max_chunk)
#         NEWS = content.replace('.', '.<eos>')
#         NEWS = NEWS.replace('?', '?<eos>')
#         NEWS = NEWS.replace('!', '!<eos>')

#         sentences = NEWS.split('<eos>')
#         current_chunk = 0
#         chunks = []
#         for sentence in sentences:
#             if len(chunks) == current_chunk + 1:
#                 if len(chunks[current_chunk]) + len(sentence.split(' ')) <= max_chunk:
#                     chunks[current_chunk].extend(sentence.split(' '))
#                 else:
#                     current_chunk += 1
#                     chunks.append(sentence.split(' '))
#             else:
#                 print(current_chunk)
#                 chunks.append(sentence.split(' '))

#         for chunk_id in range(len(chunks)):
#             chunks[chunk_id] = ' '.join(chunks[chunk_id])
#         return chunks
    

#     if summary_type == "abstractive":
#         # model_name= "BeenaSamuel/t5_small_cnn_multi_news_abstractive_summarizer_v2"
#         # model_name= "BeenaSamuel/t5_cnn_daily_mail_abstractive_summarizer_v2"
#         model_name= "BeenaSamuel/bart-cnn-dm-abstractive"
        
#         # if summary_length == "0":
#         print(model_name)
#         # print("small")
#         chunks = get_chunks(1000)
#         # summarizer = pipeline("summarization" , model= model_name)
#         tokenizer = AutoTokenizer.from_pretrained(model_name)
#         model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
#         summarizer = pipeline("summarization", model=model, tokenizer=tokenizer, num_beams=5, do_sample=True, no_repeat_ngram_size=3 )
#         print(summarizer)
#         # res = summarizer(chunks, min_length=30,max_length = 120, do_sample=False)
#         # res = summarizer(chunks, min_length=30,max_length = 120, do_sample=False)
#         res = summarizer(chunks)
#         # elif summary_length == "2":
#         #     model_name= "BeenaSamuel/t5_small_cnn_multi_news_abstractive_summarizer_v2"
#         #     # model_name= "knkarthick/MEETING_SUMMARY"
            
#         #     print("large")
#         #     print(model_name)
#         #     summarizer = pipeline("summarization" , model= model_name)
#         #     print(summarizer)
#         #     chunks = get_chunks(500)
#         #     res = summarizer(chunks, min_length=30, max_length= 200,  do_sample=False)
#         #     # print(res)
#         #     # res[0]['summary_text'].replace("–", " ")
#         #     # print( res[0]['summary_text'])
            
#         # else:
#         #     print(model_name)
#         #     print("medium")
#         #     chunks = get_chunks(300)
#         #     summarizer = pipeline("summarization" , model= model_name)
#         #     print(summarizer)
#         #     res = summarizer(chunks, min_length=30,max_length = 120, do_sample=False)
#     else:
#         model_name= "BeenaSamuel/bbc-news-summarizer"
#         print(model_name)
#         # summarizer = pipeline("summarization" , model= model_name)

#         tokenizer = AutoTokenizer.from_pretrained(model_name)
#         model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

#         summarizer = pipeline("summarization", model=model, tokenizer=tokenizer, num_beams=4, do_sample=True, no_repeat_ngram_size=3 )
#         # if summary_length == "0":
#         #     print(model_name)
#         #     print("small")
#         #     chunks = get_chunks(700)
#         #     res = summarizer(chunks, max_length=40, do_sample=False)
            
#         # elif summary_length == "2":
#         print(model_name) 
#         # print("large")  
#         chunks = get_chunks(500)         
#         # res = summarizer(chunks, min_length=30, max_length= 120, do_sample=False)
#         res = summarizer(chunks)
            
#         # else:
#         #     print(model_name)
#         #     print("medium")
#         #     chunks = get_chunks(500)
#         #     res = summarizer(chunks, min_length=30,max_length = 120, do_sample=False)
        


#     summary = ' '.join([summ['summary_text'] for summ in res])
#     # return jsonify({'summary': summary , 'headline': headline , 'summaryType': summary_type , 'summaryLength': summary_length})
    
#     words = [word for word in summary.split() if word.strip(punctuation)]
#     word_count = len(words)

#     sentences = summary.split('.')

#     # re.sub("–", " ", sentences[0])

#     print(sentences[0])

#     print(type(sentences[0]))

    
#     sentences = [sentence.strip() for sentence in sentences if sentence.strip()]

    
#     summary_list = [{'sentence': sentence, 'index': index} for index, sentence in enumerate(sentences, start=1)]

    
#     formatted_summary_list = [{'sentence': item['sentence'], 'index': item['index']} for item in summary_list]

#     return jsonify({'summary': formatted_summary_list, 'headline': headline, 'summaryType': summary_type , 'wordCount' : word_count, 'articleWords' : articleword_count  })

if __name__ == "__main__":
   app.run(debug=True)