from app import app
from flask import render_template,request,redirect,url_for
import requests
import os
import json
from app import utils
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
@app.route('/')
@app.route('/index')
def index():
  return render_template("index.html")

@app.route('/extract',methods=["GET","POST"])
def extract():
  if request.method == 'POST':
      product_id = request.form.get("product_id")
      url= f"https://www.ceneo.pl/{product_id}#tab=reviews"
      response = requests.get(url)
      if response.status_code==requests.codes["ok"]:
        page_dom = BeautifulSoup(response.text , 'html.parser')
        try:
          opinions_count = page_dom.select_one('a.product-review__link > span')       
        except AttributeError:
          opinions_count=0
        if opinions_count:
          all_opinions = []
          while(url):
              response = requests.get(url)
              page_dom = BeautifulSoup(response.text , 'html.parser')
              opinions = page_dom.select('.js_product-review')
              for opinion in opinions:
                  single_opinion = {
                      key : utils.extract(opinion , *value)
                          for key, value in utils. selectors.items()
                  }
                  for key, value in utils.transformations.items():
                      single_opinion[key] = value(single_opinion[key])
                      print(single_opinion[key])
                  all_opinions.append(single_opinion)
              try:
                  url = "https://www.ceneo.pl"+utils.extract(page_dom, 'a.pagination__next', 'href')
              except TypeError:
                  url = None
              
              score_distribution = opinions.score.value_counts().reindex(np.arange(0, 5.5, 0.5), fill_value = 0)
              fig, ax = plt.subplots()
              score_distribution.plot.bar(color = "turquoise")
              plt.xlabel("Number of stars")
              plt.xticks(rotation = 0)
              plt.ylabel("Number of opinions")
              plt.title(f"Score histogram for {product_id} product")
              ax.bar_label(ax.containers[0], label_type="edge", fmt= lambda l: int(l) if l else "")
              plt.savefig(f"app/charts/{product_id}_recommendation.png")
              plt.close()
              
              opinions= pd.DataFrame.from_dict(all_opinions)
              MAX_SCORE=5
              opinions_count= opinions.index.size
              pros_count= opinions.pros.apply(lambda p:None if  pd.isnull(p) else p).count()
              cons_count = opinions.cons.apply(lambda c : None if pd.isnull(c) else c).count()
              average_score=round(opinions.score.mean()*5,1)
              product={
                "product_id":product_id,
                "product_name":product_name,
                "opinions_count":int(opinions_count),
                "pros_count":int(pros_count),
                "cons_count":int(cons_count),
                "average_score":average_score,
                "score _distribution":score_distribution,
                "recommendation_distribution":recommendation_distribution
              }
              plt.title(f"Recommendation shares for {product_name}")
              plt.savefig(f"app/charts/{product_id}recommendation.png")
              if not os.path.exists('opinions'):
                  os.mkdir('opinions')
              jf = open(f'opinions/{product_id}.json' , 'w' , encoding='UTF-8')
              json.dump(all_opinions, jf, indent=4, ensure_ascii=False)
              jf.close()
          return redirect(url_for("product",product_id=product_id))
        return render_template("extract.html",error="Product has no opinions")
      return render_template("extract.html",error="Product page does not exist")
  return render_template("extract.html")

@app.route('/products')
def products():
  if os.path.exists("app/opinions"):
    products=[filename.split(".")[0] for filename in os.listdir("app/opinions")]
  else :products=[]
  products_list=[]
  for product in products:
    jf=(f"app/products/{product}.json","r",encoding=="UTF-8")
    single_opinion= json.loads(jf)
    products_list.append(single_product)
  return render_template("products.html")

@app.route('/author')
def author():
  return render_template("author.html")

@app.route('/product/<product_id>')
def product(product_id):
  return render_template("product.html", product_id=product_id)
