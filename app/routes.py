from app import app

from flask import render_template, request, redirect, url_for
import requests
import os
import json
from bs4 import BeautifulSoup


def get_data(ancestor, selector, attribute=None, return_list=False):
    if return_list:
        return [tag.text.strip() for tag in ancestor.select(selector)]
    if attribute:
        if selector:
            try:
                return ancestor.select_one(selector)[attribute].strip()
            except TypeError:
                return None
    try:
        return ancestor.select_one(selector).text.strip()
    except AttributeError:
        return None
    
selectors = {
    'opinion_id' : {None, "data-entry-id"},
    'author' : {"span.user-post__author-name"},
    'recommendation' : {"span.user-post__author-recomendation > em"},
    'stars' : {"span.user-post__score-count"},
    'content' : {"div.user-post__text"},
    #'pros' : {"div.review-feature__title--positives ~ div.review-feature__item", None, True},
    #'cons' : {"div.review-feature__title--negatives ~ div.review-feature__item", None, True},
    'post_date' : {"span.user-post__published > time:nth-child(1)", "datetime"},
    'purchase_date' : {"span.user-post__published > time:nth-child(2)", "datetime"},
    'useful' : {"button.vote-yes > span"},
    'useless' : {"button.vote-no > span"}
}







@app.route('/')
def index():
    return render_template('index.html.jinja')
@app.route('/extract', methods=["POST", "GET"])
def extract():
    if request.method == "POST":
        product_id = request.form.get("product_id")
        # walidacja
        url = f"https://www.ceneo.pl/{product_id}"
        response = requests.get(url)
        if response.status_code == requests.codes['ok']:
            page = BeautifulSoup(response.text, "html.parser")
            opinions_count = page.select_one("a.product-review__link > span")
            if opinions_count:
                url = f"https://www.ceneo.pl/{product_id}#tab-reviews"
                all_opinions = []
                while(url):
                    print(url)
                    response = requests.get(url)
                    page = BeautifulSoup(response.text, "html.parser")
                    opinions = page.select("div.js_product-review")

                    for opinion in opinions:
                        single_opinion = {
                            'opinion_id': opinion["data-entry-id"].strip(),
                            'author': get_data(opinion, ".user-post__author-name"),
                            'recommendation': get_data(opinion, "span.user-post__recomendation > em"),
                            'stars': get_data(opinion, "span.user-post__score-count"),
                            'content': get_data(opinion, "div.user-post__text"),
                            #'pros': get_data(opinion, "div.review-feature__title--positives ~ div.  review-feature__item", None, True),
                            #'cons': get_data(opinion, "div.review-feature__title--negatives ~ div.review-feature__item", None, True),
                            'post_date': get_data(opinion, "span.user-post__published > time:nth-child(1)", "datetime"),
                            'purchase_date': get_data(opinion, "span.user-post__published > time:nth-child(2)", "datetime"),
                            'useful': get_data(opinion, ".vote-yes > span"),
                            'useless': get_data(opinion, ".vote-no > span"),
                        }
                        all_opinions.append(single_opinion)
                    
                    try:
                        url = "https://ceneo.pl"+page.select_one('a.pagination__next')['href']
                    except TypeError:
                        url = None

                if not os.path.exists("app/data"):
                    os.mkdir("app/data")
                if not os.path.exists("app/data/opinions"):
                    os.mkdir("app/data/opinions")
                jf = open(f"app/data/opinions/{product_id}.json", "w", encoding="UTF-8")
                json.dump(all_opinions, jf, indent=4, ensure_ascii=False)
                jf.close()
                return redirect(url_for('product', product_id=product_id))
            return render_template('extract.html.jinja', error="Produkt o podanym kodzie nie ma opinii")
        return render_template('extract.html.jinja', error="Produkt o podanym kodzie nie istnieje")
    return render_template('extract.html.jinja')
@app.route('/products')
def products():
    products = *[filename.split(".")[0] for filename in os.listdir('opinions')], sep="\n"

    return render_template('products.html.jinja')
@app.route('/about')
def about():
    return render_template('about.html.jinja')
@app.route('/product/<product_id>')
def product(product_id):
    opinions = {}

    if not os.path.exists("app/data/opinions"):
        return redirect(url_for('extract'))
    jf = open(f"app/data/opinions/{product_id}.json", "r", encoding="UTF-8")
    opinions = json.load(jf)
    jf.close()

    return render_template('product.html.jinja', opinions=opinions, product_id=product_id)