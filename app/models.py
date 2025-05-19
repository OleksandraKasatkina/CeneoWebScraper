import json
import os
import pandas as pd
import numpy as np

class Product:
    def __init__(self, product_id, product_name, opinions, stats):
        self.product_id = product_id
        self.product_name = product_name
        self.opinions = opinions
        self.stats = stats

    def __str__(self):
        return f"Product_id: {self.product_id}\nProduct_name: {self.product_name}\nOpinions: "+"\n\n".join([str(opinion) for opinion in self.opinions])+"\n"+json.dumps(self.stats, indent=4, ensure_ascii=False)+"\n"

    def __repr__(self):
        return f"Product(product_id={self.product_id}, product_name={self.product_name}, opinions=["+",".join(repr(opinion) for opinion in self.opinions)+f"], stats={self.stats})"

    def export_opinions(self):
        if not os.path.exists("./app/data"):
            os.mkdir("./app/data")
        if not os.path.exists("./app/data/opinions"):
            os.mkdir("./app/data/opinions")
        with open(f".app/data/opinions/{self.product_id}.json", "w", encoding="UTF-8") as jf:
            json.dump([opinion.transform_to_dict() for opinion in self.opinions], jf, ensure_ascii=False, indent=4)
    
    def export_info(self):
        if not os.path.exists("./app/data"):
            os.mkdir("./app/data")
        if not os.path.exists("./app/data/products"):
            os.mkdir("./app/data/products")
        with open(f".app/data/products/{self.product_id}.json", "w", encoding="UTF-8") as jf:
            json.dump(self.transform_to_dict(), jf, ensure_ascii=False, indent=4)

    def transform_to_dict(self):
        return {
            'product_id': self.product_id,
            'product_name': self.product_name,
            'stats': self.stats
        }

    def import_opinions(self):
        with open(f".app/data/opinions/{self.product_id}.json", "r", encoding="UTF-8") as jf:
            opinions = json.load(jf)
        for opinion in opinions:
            single_opinion = Opinion()
            for key, value in opinion.items():
                setattr(single_opinion, key, value)
            self.opinions.append()

    def import_info(self):
        with open(f".app/data/products/{self.product_id}.json", "r", encoding="UTF-8") as jf:
            info = json.load(jf)
            self.product_name = info['product_name']
            self.stats = info['stats']

    def analyze(self):
        opinions = pd.DataFrame.from_dict([opinion.transfor_to_dict() for opinion in self.opinions])
        self.stats["opinions_count"] = opinions.shape[0]
        self.stats["pros_count"] = opinions.pros_pl.astype(bool).sum()
        self.stats["cons_count"] = opinions.cons_pl.astype(bool).sum()
        self.stats["pros_cons_count"] = opinions.apply(lambda o: bool(o.pros_pl) and bool(o.cons_pl), axis=1).sum()
        self.stats["average_rate"] = opinions.stars.mean()
        self.stats["pros"] = opinions.pros_en.explode().value_counts()
        self.stats["cons"] = opinions.cons_en.explode().value_counts()
        self.stats["recommendations"] = opinions.recommendation.value_counts(dropna=False).reindex([False, True, np.nan], fill_value=0)
        self.stats["stars"] =  opinions.stars.value_counts().reindex(list(np.arange(0,5.5,0.5)), fill_value=0)

class Opinion:
    selectors = {
    "opinion_id": (None, "data-entry-id"),
    "author": ("span.user-post__author-name",),
    "recommendation": ("span.user-post__author-recomendation > em",),
    "stars": ("span.user-post__score-count",),
    "content_pl": ("div.user-post__text",),
    "pros_pl": ("div.review-feature__item--positive", None, True),
    "cons_pl": ("div.review-feature__item--negative", None, True),
    "vote_yes": ("button.vote-yes","data-total-vote"),
    "vote_no": ("button.vote-no","data-total-vote"),
    "published": ("span.user-post__published > time:nth-child(1)","datetime"),
    "purchased": ("span.user-post__published > time:nth-child(2)","datetime")
    }

    def __init__(self, opinion_id="", author="", recommendation=False, stars=0.0, content="", pros=[], cons=[], vote_yes=0, vote_no=0, publish_date="", purchase_date=""):
        self.opinion_id = opinion_id
        self.author = author
        self.recommendation = recommendation
        self.stars = stars
        self.content = content
        self.pros = pros
        self.cons = cons
        self.vote_yes = vote_yes
        self.vote_no = vote_no
        self.publish_date = publish_date
        self.purchase_date = purchase_date
    
    def __str__(self):
        return "\n".join([f"{key}: {getattr(self, key)}" for key in self.selectors.keys()])

    def __repr__(self):
        return "Opinion("+", ".join([f"{key}={str(getattr(self, key))}" for key in self.selectors.keys()])+")"

    def transform_to_dict(self):
        return {key: getattr(self, key) for key in self.selectors.keys()}