#!flask/bin/python
import psycopg2
from flask import Flask, jsonify, request
app = Flask(__name__)


@app.route('/api/search', methods=['GET', 'POST'])
def search_articles():
    try:
        content = request.json
        serch_in = content['search']
    except:
        serch_in = ''
    con = psycopg2.connect(
        database="cyberlininka",
        user="postgres",
        password="7591362+q",
        host="127.0.0.1",
        port="5432"
    )
    search = f"""select ar.article_name, links.link, article_sourse.sourse_name,
    (select string_agg(themes.theme_name, ', ') from article_themes
    join themes ON themes.id = article_themes.theme_id
    where article_themes.articles_id = ar.id) as themes,
    ar.year_pub, ar.anonse
    from articles as ar
    JOIN links ON ar.link_id = links.id
    JOIN article_sourse ON ar.sourse_id = article_sourse.id
    where ar.article_name LIKE '%{serch_in}%'
    ;"""
    cur = con.cursor()
    cur.execute(search)
    results = cur.fetchall()
    ret_rez = []
    for row in results:
        r = {"article_name": row[0],
        "link": row[1],
        "sourse_name": row[2],
         "themes": row[3],
         "year": row[4],
         "anonse": row[5]
        }
        ret_rez.append(r)
    return jsonify({"search": ret_rez})


if __name__ == '__main__':
    app.run(debug=True)