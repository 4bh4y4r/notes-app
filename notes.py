from flask import Flask, render_template, session, request , redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import timedelta
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
app.secret_key = "hello"

class Users(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(40), nullable = False, unique = True)
    password = db.Column(db.String(30), nullable = False)
    
    notes = db.relationship("Notes")
    
    
class Notes(db.Model):
    notes_id = db.Column(db.Integer, primary_key= True)
    title = db.Column(db.String(100))
    description = db.Column(db.String(500))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    
    def to_dict(self):
        return(
            {
                "notes_id" : self.notes_id,
                "title": self.title,
                "description": self.description,
                "user_id" : self.user_id
                
                
            }

            
            
        )
        
    
    


@app.route("/", methods = ["POST", "GET"])
def login_page():
    if request.method == "GET":
        return render_template('login.html')
    else:
       name = request.form["username"]
       password = request.form["password"]
       if not name or not password:
           flash("Enter username and password")
           return redirect(url_for('login_page'))
           
       result = Users.query.filter_by(username=name).first()
       if result and check_password_hash(result.password, password):
           session["user_id"] = result.id
           session["password"] = password
           return redirect(url_for('home_page'))
       else:
           flash("Invalid Credentials")
           return redirect(url_for('login_page'))
           
        


@app.route("/register", methods = ["POST","GET"])
def register_page():
    
    if request.method == "GET":
        return render_template('register.html')
    else:
        username = request.form["username"]
        password = request.form["password"]
        if not username or not password:
           flash("Enter username and password")
           return redirect(url_for('register_page'))
        
        result = Users.query.filter_by(username = username).first()
        if result:
            flash("Username already taken")
            return redirect(url_for('register_page'))
        hashed_password = generate_password_hash(password)
        user = Users(username = username, password = hashed_password)
        db.session.add(user)
        db.session.commit()
        session["user_id"] = user.id
        return redirect(url_for("home_page"))



@app.route("/home", methods= ["POST","GET"])
def home_page():
    if request.method == "GET":
        if "user_id" in session:
           current_user_id = session["user_id"]
           
           user = Users.query.filter_by(id = current_user_id).first()
           note = user.notes
           return render_template('home.html', username = user.username, note = note)
        else:
            return redirect(url_for('login_page'))
    else:
        return(redirect(url_for('logout')))
    
    
    

@app.route("/logout", methods = ["POST", "GET"])
def logout():
    session.pop("user_id", None)
    flash("You have been successfully logged out!", "info")
    return redirect(url_for('login_page'))
    

@app.route("/notes", methods=["POST","GET"])
def create_notes():
    if request.method == "GET":
        return render_template('addnote.html')
    
    else:
        title = request.form['title']
        desc = request.form['desc']
        if not title or not desc:
            flash("Enter details to add the note!")
            return redirect(url_for('create_notes'))

        current_user_id = session["user_id"]
        note = Notes(title = title, description = desc, user_id = current_user_id)
        db.session.add(note)
        db.session.commit()
        flash("Note successfully added to profile")
        return redirect(url_for('create_notes'))



@app.route("/delete_notes/<id>", methods = ["POST", "GET"])
def delete_notes(id):
    note = Notes.query.filter_by(notes_id =id).first()
    if not note:
        flash("Invalid Delete Operation")
        return redirect(url_for('home_page'))
    if note.user_id == session["user_id"]:
        if note:
            db.session.delete(note)
            db.session.commit()
            return redirect(url_for('home_page'))
        else:
            flash("Not valid delete")
            return redirect(url_for('home_page'))
    else:
        flash("Unauthorized Action", "info")
        return redirect(url_for('home_page'))
    
    
    
@app.route("/edit_notes/<id>", methods = ["POST", "GET"])
def edit_notes(id):
    if request.method == "GET":
        notes = Notes.query.filter_by(notes_id=id).first()
        if not notes:
            flash("Invalid Delete Operation")
            return redirect(url_for('home_page'))
        if notes.user_id == session["user_id"]:
        
            return render_template('editnote.html', note = notes)
        else:
            flash("Unauthorized Action")
            return redirect(url_for('home_page'))
            
    else:
        
        notes = Notes.query.filter_by(notes_id=id).first()
        notes.title = request.form["title"]
        notes.description = request.form["desc"]
        db.session.commit()
        return redirect(url_for('home_page'))
        
        
   
@app.route("/api/notes", methods=["GET"])
def get_notes():

    notes = Notes.query.all()

    return jsonify(
        [note.to_dict() for note in notes]
    ), 200
    

@app.route("/api/notes/<int:id>", methods=["GET"])
def get_note(id):

    note = Notes.query.get(id)

    if not note:
        return jsonify({
            "message": "Note not found"
        }), 404

    return jsonify(note.to_dict()), 200


@app.route("/api/notes", methods=["POST"])
def create_note():

    data = request.get_json()

    note = Notes(
        title=data["title"],
        description=data["description"],
        user_id=data["user_id"]
    )

    db.session.add(note)
    db.session.commit()

    return jsonify(note.to_dict()), 201


@app.route("/api/notes/<int:id>", methods=["PUT"])
def update_note(id):

    note = Notes.query.get(id)

    if not note:
        return jsonify({
            "message": "Note not found"
        }), 404

    data = request.get_json()

    note.title = data["title"]
    note.description = data["description"]

    db.session.commit()

    return jsonify(note.to_dict()), 200



@app.route("/api/notes/<int:id>", methods=["DELETE"])
def delete_note(id):

    note = Notes.query.get(id)

    if not note:
        return jsonify({
            "message": "Note not found"
        }), 404

    db.session.delete(note)
    db.session.commit()

    return jsonify({
        "message": "Note deleted"
    }), 200
    
    

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)