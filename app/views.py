from app import app
from flask import render_template, redirect, url_for, request, send_file
from app.forms import ExtractForm
from app.models import Product
import io
import pandas as pd
import os
import json

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/extract")
def render_form():
    form = ExtractForm()
    return render_template("extract.html", form=form)

@app.route("/extract", methods=['POST'])
def extract():
    form = ExtractForm(request.form)
    if form.validate():
        product_id = form.product_id.data
        product = Product(product_id)
        if product.extract_name():
            product.extract_opinions()
            product.analyze()
            product.export_info()
            product.export_opinions()
            return redirect(url_for('product', product_id=product_id))
        form.product_id.errors.append('There is no product for provided id or product has no opinions')
        return render_template('extract.html', form=form)
    return render_template('extract.html', form=form)

@app.route("/products")
def products():
    products_data = []
    products_dir = "./app/data/products"
    opinions_dir = "./app/data/opinions"

    for filename in os.listdir(products_dir):
        if filename.endswith(".json"):
            product_id = filename.replace(".json", "")
            with open(os.path.join(products_dir, filename), encoding="utf-8") as f:
                data = json.load(f)
                stats = data.get("stats", {})
                products_data.append({
                    "product_id": product_id,
                    "product_name": data.get("product_name", "Unknown"),
                    "opinions_count": stats.get("opinions_count", 0),
                    "pros_count": stats.get("pros_count", 0),
                    "cons_count": stats.get("cons_count", 0),
                    "average_score": round(stats.get("average_rate", 0.0), 2),
                })
    return render_template("products.html", products=products_data)

@app.route("/product/<product_id>")
def product(product_id):
    return render_template("product.html", product_id=product_id)

@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/download/<product_id>/<filetype>")
def download_file(product_id, filetype):
    opinions_path = f"./app/data/opinions/{product_id}.json"

    if not os.path.exists(opinions_path):
        return "File not found", 404

    with open(opinions_path, encoding="utf-8") as f:
        opinions = json.load(f)

    if not opinions:
        return "No opinions to export", 400

    if filetype == "csv":
        df = pd.DataFrame(opinions)
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)
        return send_file(io.BytesIO(output.getvalue().encode()),
                         mimetype="text/csv",
                         download_name=f"{product_id}.csv",
                         as_attachment=True)

    elif filetype == "xlsx":
        df = pd.DataFrame(opinions)
        output = io.BytesIO()
        df.to_excel(output, index=False)
        output.seek(0)
        return send_file(output,
                         mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                         download_name=f"{product_id}.xlsx",
                         as_attachment=True)

    elif filetype == "json":
        output = io.StringIO()
        json.dump(opinions, output, indent=4, ensure_ascii=False)
        output.seek(0)
        return send_file(io.BytesIO(output.getvalue().encode()),
                         mimetype="application/json",
                         download_name=f"{product_id}.json",
                         as_attachment=True)

    return "Invalid file type", 400