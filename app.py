# importing the necessary modules 
from flask import Flask,request,render_template,redirect,session,flash,jsonify
from flask_session import Session
from cs50 import SQL
from datetime import datetime
import json
import os 

# get the function from other file
from app_support import sorting_time,give_the_days_range

# configure flask app
app = Flask(__name__)

# connect database
db = SQL("mysql://root:YES@localhost:3306/db_for_flask")

# json
json_file_path = os.path.join(os.path.dirname(__file__),"static\datas\data.json")

# configure session
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# index rounte or home route of the website
@app.route("/")
def index():
    if not session.get("Uid"):
        return redirect("/login")
    Uid = session["Uid"]
    datas = db.execute("select name from user_login_data where Uid = ?",Uid)
    with open(json_file_path,"r") as file:
        x = json.load(file)
        if Uid in x:
            todos = x[Uid]
        else:
            todos = {}
    date_range = give_the_days_range()
    return render_template("index.html",datas=datas,todos = todos,date_range = date_range)

# login route 
@app.route("/login",methods=["POST","GET"])
def login():
    if session.get("Uid"):
        return render_template("index.html")
    if request.method == "POST":
        email = request.form.get("mail")
        pw = request.form.get("pw")
        data = db.execute("select pw,Uid from user_login_data where email = ?",email)
        if data == []:
            flash("Incorrect email!Please try again","warning")
            return redirect("/login")
        elif data[0]["pw"] == pw:
            session["Uid"] = data[0]["Uid"]
            return redirect("/")
        else:
            flash("Wrong Password. Try again!","warning")
            return redirect("/login")
    return render_template("authentication.html")

# signup route
@app.route("/signup",methods=["POST","GET"])
def signup():
    if request.method == "POST":
        name = request.form.get("name").capitalize()
        email = request.form.get("mail")
        pw = request.form.get("pw")
        now = datetime.now()
        uid = now.strftime("%m%d%Y") + name + now.strftime("%H%M%S")
        db.execute("insert into user_login_data(Uid,name,email,pw) values(?,?,?,?)",uid,name,email,pw)
        session["Uid"] = uid
        return redirect("/")

# log out route
@app.route("/logout")
def logout():
    session["Uid"] = None
    return redirect("/")

# todo add route
@app.route("/add",methods=["POST","GET"])
def add():
    acti = request.form.get("activity")
    time = request.form.get("tm")
    day_difference = request.form.get("day_diff")
    full_timestamp = time + ":" + str(day_difference)
    Uid = session["Uid"]
    with open(json_file_path,"r+") as file:
        data = json.load(file)
        if Uid in data and data[Uid] != {}:
            id_count = int(list(data[Uid].keys())[-1]) + 1
            dct = data[Uid]
            dct[id_count] = [acti.lower(),full_timestamp]
            data[Uid] = sorting_time(dct)
        else:
            id_count = 1
            dct = {}
            dct[id_count] = [acti.lower(),full_timestamp]
            data[Uid] = dct
        
        file.seek(0)
        json.dump(data, file,indent=4)
    return redirect("/")

# todo remove route
@app.route("/remove",methods=["POST","GET"])
def remove(auto=False):
    if not auto:
        de = request.form.get("de")
    else:
        de = auto
    uid = session["Uid"]
    if de:
        with open(json_file_path,"r+") as file:
            x = json.load(file)
            data = x[uid]
            print(data)
            try:
                del data[de]
            except:
                pass
            print(x[uid])
            x[uid] = sorting_time(data)
            print(x[uid])
            file.seek(0)
            json.dump(x,file,indent=4)
            file.truncate()
    return redirect("/")

# todo route when for ahead of time
@app.route("/delete-todo",methods=["GET","POST"])
def delete_finished():
    datas = json.loads(request.data)
    print(datas)
    todoId = datas["ToDoId"]
    print(todoId)
    remove(auto=todoId)
    return jsonify({})

# search route for user's todos
@app.route("/search")
def search_todo():
    q = request.args.get("q")
    if q:
        uid = session["Uid"]
        with open(json_file_path,"r+") as file:
            datas = json.load(file)
            data = datas[uid]
            result_dct = {}
            for key,value in data.items():
                todo = value[0]
                if q in todo:
                    result_dct[key] = value
    else:
        result_dct = {}
    return jsonify(result_dct)

# error handling for curious user
@app.errorhandler(404)
def page_not_found(error):
    return render_template("page_not_found.html"),404