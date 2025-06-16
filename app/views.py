from app import app
from flask import render_template, redirect, url_for, request, send_file
from app.forms import ExtractForm
from app.models import Product
import numpy as np
import io
import pandas as pd
import os
import json
import matplotlib.pyplot as plt
from shutil import copyfile

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
                    "average_score": round(stats.get("average_rate", 0.0), 2)
                })
    return render_template("products.html", products=products_data)

@app.route("/product/<product_id>")
def product(product_id):
    opinions_file = f"./app/data/opinions/{product_id}.json"
    if not os.path.exists(opinions_file):
        return f"Opinions for product {product_id} not found.", 404

    with open(opinions_file, encoding="utf-8") as f:
        opinions = json.load(f)
    
    df = pd.DataFrame(opinions)

    for col in ['author', 'stars', 'recommendation', 'content_pl']:
        val = request.args.get(f'filter_{col}')
        if val:
            df = df[df[col].astype(str).str.contains(val, case=False, na=False)]

    sort_by = request.args.get('sort_by', 'publish_date')
    if sort_by in df.columns:
        df = df.sort_values(by=sort_by)

    page = int(request.args.get('page', 1))
    per_page = 10
    total_pages = (len(df) - 1) // per_page + 1
    df_page = df.iloc[(page-1)*per_page : page*per_page]

    opinions_page = df_page.to_dict(orient='records')

    return render_template("product.html",
                           product_id=product_id,
                           opinions=opinions_page,
                           page=page,
                           total_pages=total_pages,
                           product_name=Product(product_id).product_name,
                           request=request)

@app.route("/charts/<product_id>")
def charts(product_id):
    info_path = f"./app/data/products/{product_id}.json"
    opinions_path = f"./app/data/opinions/{product_id}.json"

    if not os.path.exists(info_path) or not os.path.exists(opinions_path):
        return "Product data not found", 404

    with open(info_path, encoding="utf-8") as f:
        product_info = json.load(f)
    with open(opinions_path, encoding="utf-8") as f:
        opinions = json.load(f)

    df = pd.DataFrame(opinions)

    static_charts_dir = "./app/static/charts"
    os.makedirs(static_charts_dir, exist_ok=True)

    recommendation_counts = df['recommendation'].value_counts(dropna=False)
    labels = ['Not Recommended', 'Recommended', 'No Opinion']
    values = [
        recommendation_counts.get(False, 0),
        recommendation_counts.get(True, 0),
        recommendation_counts.get(np.nan, 0)
    ]
    colors = ['turquoise', 'magenta', 'steelblue']

    plt.figure(figsize=(6, 6))
    plt.pie(values, labels=labels, autopct='%1.1f%%', colors=colors, startangle=140)
    plt.title("Recommendation Share")
    pie_filename = f"{product_id}_pie.png"
    pie_path_static = os.path.join(static_charts_dir, pie_filename)
    plt.savefig(pie_path_static)
    plt.close()

    stars_count = df['stars'].value_counts().reindex(np.arange(0, 5.5, 0.5), fill_value=0).sort_index()
    plt.figure(figsize=(10, 6))
    stars_count.plot(kind='bar', color='#ffa726')
    plt.title("Star Ratings Distribution")
    plt.xlabel("Stars")
    plt.ylabel("Number of Opinions")
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    bar_filename = f"{product_id}_bar.png"
    bar_path_static = os.path.join(static_charts_dir, bar_filename)
    plt.savefig(bar_path_static)
    plt.close()

    pie_chart_url = url_for('static', filename=f"charts/{pie_filename}")
    bar_chart_url = url_for('static', filename=f"charts/{bar_filename}")

    return render_template(
        "charts.html",
        product_id=product_id,
        product_info=product_info,
        pie_chart_url=pie_chart_url,
        bar_chart_url=bar_chart_url
    )

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