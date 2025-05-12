 class Product:
    def __init__(self):
        pass

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

    def __init__(self, opinion_id, author, recommendation, stars, content, pros, cons, vote_yes, vote_no, publish_date, purchase_date):
        self.opinion_id = opinion_id
        self.author = author
        self.recommendation = recommendation
        self.stars = stars
        self.content = content
        self.pros = pros
        self.cons = cons
        self.vote_yes = vote_yes
        self.vote_no = opinion_id
        self.publish_date = publish_date
        self.purchase_date = purchase_date
    
    def __str__(self):
        return "\n".join([f"{key}: {getattr(self, key)}" for key in self.selectors.keys()])

    def __repr__(self):
        return "Opinion("+", ".join([f"{key}={str(getattr(self, key))}" for key in self.selectors.keys()])+")"