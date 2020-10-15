import os
import calendar
import datetime

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from datetime import date
from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")

def add_months(sourcedate, months):
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month // 12
    month = month % 12 + 1
    day = min(sourcedate.day, calendar.monthrange(year,month)[1])
    return datetime.date(year, month, day)



@app.route("/")
@login_required
def index():
    """Show portfolio of ALL SPENDINGS """
    return apology("TODO")

@app.route("/add", methods=["GET", "POST"])
@login_required
def add_funds():

    if request.method == "POST":
        try:
            amount = float(request.form.get("amount"))
        except:
            return apology("amount must be a real number", 400)

        db.execute("UPDATE users SET cash = cash + :amount WHERE id = :user_id", user_id=session["user_id"], amount=amount)

        return redirect("/")
    else:
        return render_template("add_funds.html")

@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    """Allow user to change her password"""

    if request.method == "POST":

        # Ensure current password is not empty
        if not request.form.get("current_password"):
            return apology("must provide current password", 400)

        # Query database for user_id
        rows = db.execute("SELECT hash FROM users WHERE id = :user_id", user_id=session["user_id"])

        # Ensure current password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("current_password")):
            return apology("invalid password", 400)

        # Ensure new password is not empty
        if not request.form.get("new_password"):
            return apology("must provide new password", 400)

        # Ensure new password confirmation is not empty
        elif not request.form.get("new_password_confirmation"):
            return apology("must provide new password confirmation", 400)

        # Ensure new password and confirmation match
        elif request.form.get("new_password") != request.form.get("new_password_confirmation"):
            return apology("new password and confirmation must match", 400)

        # Update database
        hash = generate_password_hash(request.form.get("new_password"))
        rows = db.execute("UPDATE users SET hash = :hash WHERE id = :user_id", user_id=session["user_id"], hash=hash)

        # Show flash
        flash("Changed!")

    return render_template("change_password.html")

@app.route("/stock")
@login_required
def stock():
    """Show portfolio of stocks"""
    """Show portfolio of stocks"""
    rows = db.execute("""SELECT symbol,stock_name, SUM(shares) as totalShares
    FROM history
    WHERE user_id = :user_id
    GROUP BY stock_name
    HAVING totalShares >0;
    """,user_id=session['user_id'])
    holdings = []
    grand_total = 0
    for row in rows:
        symbolic = row["symbol"]
        print(symbolic)
        stock = lookup(symbolic)
        holdings.append({
            "stock": row["symbol"].upper(),
            "name": row["stock_name"],
            "shares": row["totalShares"],
            "price": usd(stock["price"]),
            "total": usd(stock["price"] * row["totalShares"])
        })
        grand_total = stock["price"] * row["totalShares"] 
    cash = db.execute("SELECT cash FROM users WHERE id=:user_id",user_id=session["user_id"]) 
    cash = cash[0]["cash"] 
    grand_total = grand_total + cash  
    return render_template("stock.html",holdings=holdings, cash =usd(cash), grand_total=usd(grand_total))




    
@app.route("/personal", methods=["GET", "POST"])
@login_required
def personal():
    """Show portfolio of personal spendings"""
    if request.method == "POST":
        commodity = request.form.get("commodity")
        amount = request.form.get("amount")
        try:
            amount = int(amount)
        except:
            return apology("enter a proper value")
        if not commodity:
            return apology("Missing  commodity!")
        elif not amount:
            return apology("Missing number of shares!")
        elif int(amount)<= 0:
            return apology("enter a proper value")    
        else:  
            rows = db.execute("SELECT cash FROM users WHERE id=:id",id=session["user_id"])
            cash = rows[0]["cash"]
            updated_cash = cash - amount 
            if updated_cash <0:
                return apology("cant afford")
            db.execute("UPDATE users SET cash=:updated_cash WHERE id=:id",updated_cash=updated_cash,id=session["user_id"])
            db.execute("INSERT INTO personal (user_id,amount,commodity) VALUES (:user_id,:amount,:commodity)",user_id=session["user_id"],amount=amount,commodity=commodity)
            flash("Bought!!")
            return redirect("/personal") 
    else:
            prows = db.execute("""SELECT pid,commodity,amount,time 
            FROM personal
            WHERE user_id = :user_id
            ORDER BY pid;
            """,user_id=session['user_id'])
            pspendings = []
            grand_ptotal =0
            for prow in prows:
                pspendings.append({
                    "pid": prow["pid"],
                    "commodity": prow["commodity"],
                    "amount": prow["amount"],
                    "time": prow["time"],    
                }) 
                grand_ptotal = grand_ptotal + prow["amount"]
            cash = db.execute("SELECT cash FROM users WHERE id=:user_id",user_id=session["user_id"]) 
            cash = cash[0]["cash"]   
            return render_template("personal.html",pspendings=pspendings, cash =usd(cash), grand_ptotal=usd(grand_ptotal))
      

@app.route("/personal/delete/<int:pid>")
@login_required
def personaldelete(pid):
    """Delete personal spendings"""
    rows = db.execute("SELECT cash FROM users WHERE id=:id",id=session["user_id"])
    amount = db.execute("SELECT amount FROM personal WHERE pid=:pid",pid=pid)
    cash = rows[0]["cash"]
    amount = amount[0]["amount"]
    print(cash)
    print(amount)
    updated_cash = cash + amount 
    if updated_cash <0:
        return apology("cant afford")
    db.execute("UPDATE users SET cash=:updated_cash WHERE id=:id",updated_cash=updated_cash,id=session["user_id"])
    db.execute("DELETE FROM personal WHERE pid =:pid ",pid=pid)
    flash("Deleted!!")
    return redirect("/personal") 
     

@app.route("/personal/update/<int:pid>",methods=["GET", "POST"])
@login_required
def personalupdate(pid):
    if request.method == "POST":
        update_commodity = request.form.get("update_commodity")
        update_amount = request.form.get("update_amount")
        try:
            update_amount = int(update_amount)
        except:
            return apology("enter a proper value")
        if not update_commodity:
            return apology("Missing  commodity!")
        elif not update_amount:
            return apology("Missing number of shares!")
        elif int(update_amount)<= 0:
            return apology("enter a proper value")    
        else:  
            rows = db.execute("SELECT cash FROM users WHERE id=:id",id=session["user_id"])
            amount = db.execute("SELECT amount FROM personal WHERE pid=:pid",pid=pid)
            cash = rows[0]["cash"]
            amount = amount[0]["amount"]
            updated_cash = (cash + amount) - update_amount 
            db.execute("UPDATE users SET cash=:updated_cash WHERE id=:id",updated_cash=updated_cash,id=session["user_id"])
            db.execute("UPDATE personal SET user_id=:user_id,amount=:amount,commodity=:commodity WHERE pid=:pid",user_id=session["user_id"],amount=update_amount,commodity=update_commodity,pid=pid)
            flash("updated!!")
            return redirect("/personal")  
    else:
        return apology("UNDApakuru") 


@app.route("/education",methods=["GET", "POST"])
@login_required
def education():
    """Show portfolio of educational spendings"""
    if request.method == "POST":
        epurpose = request.form.get("epurpose")
        amount = request.form.get("amount")
        period = request.form.get("period")
        category = request.form.get("category")
        try:
            amount = int(amount)
            period = int(period)
            category = str(category)
        except:
            return apology("please check your inputs")
        if not epurpose:
            return apology("Missing  commodity!")
        elif not amount:
            return apology("Missing number of shares!")
        elif int(amount)<= 0:
            return apology("enter a proper value")    
        else:  
            rows = db.execute("SELECT cash FROM users WHERE id=:id",id=session["user_id"])
            cash = rows[0]["cash"]
            updated_cash = cash - amount 
            if updated_cash <0:
                return apology("cant afford")
            today = date.today() 
            duedate = add_months(today,period)   
            db.execute("UPDATE users SET cash=:updated_cash WHERE id=:id",updated_cash=updated_cash,id=session["user_id"])
            db.execute("INSERT INTO education (user_id,epurpose,amount,period,duedate,category) VALUES (:user_id,:epurpose,:amount,:period,:duedate,:category)",user_id=session["user_id"],epurpose=epurpose,amount=amount,period=period,duedate=duedate,category=category)
            flash("Educated!!")
            return redirect("/education") 
    else:
            erows = db.execute("""SELECT eid,epurpose,amount,period,datestamp,duedate,status,category 
            FROM education
            WHERE user_id = :user_id
            ORDER BY eid;
            """,user_id=session['user_id'])
            espendings = []
            grand_etotal =0
            for erow in erows:
                espendings.append({
                    "eid": erow["eid"],
                    "epurpose": erow["epurpose"],
                    "amount": erow["amount"],
                    "period": erow["period"],  
                    "datestamp": erow["datestamp"], 
                    "duedate": erow["duedate"],
                    "status" : erow["status"],
                    "category": erow["category"]
                }) 
                grand_etotal = grand_etotal + erow["amount"]
            cash = db.execute("SELECT cash FROM users WHERE id=:user_id",user_id=session["user_id"]) 
            cash = cash[0]["cash"]   
            today=str(date.today())
            return render_template("education.html",espendings=espendings, cash =usd(cash), grand_etotal=usd(grand_etotal),today=today)




@app.route("/education/edit/<int:eid>",methods=["GET", "POST"])
@login_required
def educationedit(eid):
    if request.method == "POST":
        """Show portfolio of personal spendings"""
        update_epurpose = request.form.get("update_epurpose")
        update_amount = request.form.get("update_amount")
        update_period = request.form.get("update_period")
        update_datestamp = request.form.get("update_datestamp")
        update_category = request.form.get("update_category")
        print("++++++++++++++++++",update_category)
        
        try:
            update_status = int(request.form.get("updatestatus"))   
                
        except:
            update_status = 1 
        
        print("STATUS******",update_status)
        try:
            update_amount = int(update_amount)
            update_period = int(update_period)
        except:
            return apology("enter a proper value")
        if not update_epurpose:
            return apology("Missing  commodity!")
        elif not update_amount:
            return apology("Missing number of shares!")
        elif int(update_amount)<= 0:
            return apology("enter a proper value")    
        else:  
            erowsD = db.execute("SELECT duedate FROM education WHERE eid=:eid",eid=eid)
            due_datestamp= erowsD[0]["duedate"].split('-')
            olddue_datestamp = datetime.date(int(due_datestamp[0]), int(due_datestamp[1]), int(due_datestamp[2]))
            update_datestamp= update_datestamp.split('-')
            update_datestamp = datetime.date(int(update_datestamp[0]), int(update_datestamp[1]), int(update_datestamp[2]))
            today = date.today() 
            update_duedate = add_months(update_datestamp,update_period)   
            db.execute("UPDATE education SET user_id=:user_id,epurpose=:epurpose,amount=:amount,period=:period,datestamp=:update_datestamp,duedate=:duedate,status=:update_status,category=:update_category WHERE eid=:eid",user_id=session["user_id"],epurpose=update_epurpose,amount=update_amount,period=update_period,update_datestamp=update_datestamp,duedate=update_duedate,update_status=update_status,update_category=update_category,eid=eid)
            flash("updated!!")
            return redirect("/education")      
 

@app.route("/education/pay/<int:eid>",methods=["GET", "POST"])
@login_required
def educationupdate(eid):
    if request.method == "POST":
        """Show portfolio of personal spendings"""
        update_epurpose = request.form.get("update_epurpose")
        update_amount = request.form.get("update_amount")
        update_period = request.form.get("update_period")
        update_datestamp = request.form.get("update_datestamp")
        try:
            update_status = int(request.form.get("updatestatus"))       
        except:
            update_status = 1 
        
        print("STATUS******",update_status)
        try:
            update_amount = int(update_amount)
            update_period = int(update_period)
        except:
            return apology("enter a proper value")
        if not update_epurpose:
            return apology("Missing  commodity!")
        elif not update_amount:
            return apology("Missing number of shares!")
        elif int(update_amount)<= 0:
            return apology("enter a proper value")    
        else:  
            erowsD = db.execute("SELECT duedate FROM education WHERE eid=:eid",eid=eid)
            due_datestamp= erowsD[0]["duedate"].split('-')
            olddue_datestamp = datetime.date(int(due_datestamp[0]), int(due_datestamp[1]), int(due_datestamp[2]))
            update_datestamp= update_datestamp.split('-')
            update_datestamp = datetime.date(int(update_datestamp[0]), int(update_datestamp[1]), int(update_datestamp[2]))
            today = date.today() 
            update_duedate = add_months(update_datestamp,update_period)   
            db.execute("UPDATE education SET user_id=:user_id,epurpose=:epurpose,amount=:amount,period=:period,duedate=:duedate,status=:update_status WHERE eid=:eid",user_id=session["user_id"],epurpose=update_epurpose,amount=update_amount,period=update_period,duedate=update_duedate,update_status=update_status,eid=eid)
            flash("updated!!")
            return redirect("/education")  

@app.route("/stock/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    """Buy shares of stock"""
    if request.method == "POST":
        symbol = request.form.get("symbol")
        amount = request.form.get("shares")
        try:
            amount = int(amount)
        except:
            return apology("not valid input")  
        print(amount)
        if not symbol:
            return apology("Missing stock symbol!")
        elif not amount:
            return apology("Missing number of shares!")
        elif int(amount)<= 0:
            return apology("enter a proper value")    
        else:  
            stock = lookup(symbol)
            price = float(stock["price"])
            rows = db.execute("SELECT cash FROM users WHERE id=:id",id=session["user_id"])
            cash = rows[0]["cash"]
            updated_cash = cash - amount * price
            if updated_cash <0:
                return apology("cant afford")
            db.execute("UPDATE users SET cash=:updated_cash WHERE id=:id",updated_cash=updated_cash,id=session["user_id"])
            db.execute("INSERT INTO history (user_id,stock_name,shares,price,symbol) VALUES (:user_id,:stock_name,:shares,:price,:symbol)",user_id=session["user_id"],stock_name=stock['name'],shares=int(amount),price=stock['price'],symbol=symbol)
            flash("Bought!!")
            return redirect("/stock")    
    else:
        return render_template("buystock.html")


@app.route("/stock/history")
@login_required
def history():
    """Show history of transactions"""
    """Show history of transactions"""
    transactions= db.execute("""
                                SELECT symbol,stock_name,shares,price,time
                                FROM history
                                WHERE user_id=:user_id;
    """, user_id=session["user_id"])
    revealing =[]
    for transaction in transactions:
            revealing.append({
            "symbol":  transaction["symbol"],
            "name": transaction["stock_name"],
            "shares": transaction["shares"],
            "price": transaction["price"],
            "time": transaction["time"]
        })
    return render_template("stockhistory.html",revealing=revealing)
    


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/stock/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":
        if not request.form.get("symbol"):
            return apology("Missing Symbol",400)
        symbol = request.form.get("symbol").lower()
        stock = lookup(symbol)
        if stock == None:
            return apology("invalid symbol",400)
        return render_template("stockquoted.html", stock=stock)
    else:
        return render_template("stockquote.html")
    return apology("TODO")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        """Register user"""
        uname = request.form.get('username')
        password = generate_password_hash(request.form.get('password'))
        status = True
        # check password confirmation
        if not request.form.get('password') == request.form.get('confirmation'):
            status = False
            text = "Passwords do not match"
        # check unique username
        exists_username= db.execute("SELECT username FROM users where username = :username", username = uname)
        if exists_username:
            status = False
            text = "Sorry Username already taken by another user"
        if status:
            # register
            register = db.execute("INSERT INTO users (username, hash) VALUES(:username, :hash)",
            username = uname, hash = password)
            text = "Registration Successfully Done!"
            # Remember which user has logged in
            session["user_id"] = register

            # Redirect user to home page
            return redirect("/")
        return apology(text)
    else:
        return render_template("register.html")


@app.route("/stock/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    """Sell shares of stock"""
    if request.method == "POST":
        symbol = request.form.get("symbol")
        amount = request.form.get("shares")
        try:
            amount = int(amount)
        except:
            return apology("enter a proper value")
        print(amount)
        if not symbol:
            return apology("Missing stock symbol!")
        elif not amount:
            return apology("Missing number of shares!")
        elif int(amount)<= 0:
            return apology("enter a proper value")    
        else:
            amount = int(amount)
            stock = lookup(symbol)
            if stock is None:
                return apology("invalid symbol")

            rows = db.execute(""" 
                        SELECT symbol,SUM(shares) as totalShares
                        FROM history
                        WHERE user_id=:user_id
                        GROUP BY symbol
                        HAVING totalShares >0;"""
            ,user_id=session["user_id"])

            for row in rows:
                if row["symbol"] == symbol:
                    if amount >row["totalShares"]:
                        return apology("too many shares")


            price = float(stock["price"])
            rows = db.execute("SELECT cash FROM users WHERE id=:id",id=session["user_id"])
            cash = rows[0]["cash"]
            updated_cash = cash + amount * price
            db.execute("UPDATE users SET cash=:updated_cash WHERE id=:id",updated_cash=updated_cash,id=session["user_id"])
            db.execute("INSERT INTO history (user_id,stock_name,shares,price,symbol) VALUES (:user_id,:stock_name,:shares,:price,:symbol)",user_id=session["user_id"],stock_name=stock['name'],shares= -1*int(amount),price=stock['price'],symbol=symbol)
            flash("Sold!!")
            return redirect("/") 
    else:

        rows = db.execute(""" 
        SELECT symbol FROM history WHERE user_id=:user_id GROUP BY symbol HAVING SUM(shares) >0;
        """, user_id=session["user_id"])
        return render_template("sellstock.html", symbols = [row["symbol"] for row in rows])



def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
