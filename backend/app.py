from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import base64

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///twitter.db"



# Database models #################################

db = SQLAlchemy(app)

# Many-to-many table for User table
user_to_user = db.Table('user_to_user',
    db.Column("follower_username", db.String, db.ForeignKey("user.username"), primary_key=True),
    db.Column("followed_username", db.String, db.ForeignKey("user.username"), primary_key=True)
)

# User data model
class User(db.Model):
    username = db.Column(db.String(20), primary_key=True)
    password = db.Column(db.String(100))
    tweets = db.relationship('Tweet', backref='user')

    following = db.relationship("User",
                    secondary=user_to_user,
                    primaryjoin=username==user_to_user.c.follower_username,
                    secondaryjoin=username==user_to_user.c.followed_username,
                    backref="followed_by"
    )

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def to_dict(self):
        return {"username": self.username, "following": len(self.following), "followed_by":len(self.followed_by), "tweets":len(self.tweets)}

# Tweet data model
class Tweet(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    content = db.Column(db.Text)
    username = db.Column(db.Integer, db.ForeignKey('user.username'))
    epoch = db.Column(db.Integer)


    def __init__(self, content):
        self.content = content
        self.epoch = int(datetime.now().timestamp()* 1000000)

    def __repr__(self):
        return "ID "+str(self.id)+" content "+str(self.content)+" epoch "+str(self.epoch)+" username "+str(self.username)
    
    def to_dict(self):
        return {"username":self.username, "content":self.content, "time":self.epoch}



# Demo data: Uncomment and execute to create the tables and add the demo data ####################

# db.drop_all()
# db.create_all()

# user = User("harsh","pass")
# user2 = User("mihir","pass")
# user3 = User("harshit","pass")


# tweet= Tweet("hi ads")
# tweet2= Tweet("heasd asdas daD23123213")
# tweet3= Tweet("hasdf sdf easd aasdfsdas daD23123213")
# tweet4= Tweet("sdf easd aasdfsdas daD23123213")

# user.tweets=[tweet,tweet2]
# user2.tweets=[tweet3]
# user3.tweets=[tweet4]

# user.following=[user2,user3]

# db.session.add(user)
# db.session.add(user2)
# db.session.add(user3)

# user = User.query.all()
# print(user)

# for u in user:
#     print("Following "+ str(u.following))
#     print("Followedby "+ str(u.followed_by))

# db.session.commit()




def create_token(username):
    user_string_bytes = username.encode("utf-8")
    base64_bytes = base64.b64encode(user_string_bytes)
    base64_string = base64_bytes.decode("utf-8")
    return base64_string

def decode_token(token):
    base64_bytes = token.encode("utf-8")
    token_string_bytes = base64.b64decode(base64_bytes)
    username = token_string_bytes.decode("utf-8")
    return username

@app.route('/')
def index():
    return "Twitter Flask Clone!"

@app.route("/api/register", methods=["POST"])
def user_register():
    try:
        username = request.json["username"]
        password = request.json["password"]
        if (username and password): # Checks if username, password are empty
            try:
                user = User(username, password) # Creates a new record
                db.session.add(user) # Adds the record for committing
                db.session.commit() # Saves our changes
                return jsonify({"message": "User created successfully"}),200
            except Exception as e:
                db.session.rollback() # Rollback the database if user already exists
                return ({"error": "Could not create a new user"}),400
        else:
            return jsonify({"error": "Username or password not provided"}),400 # jsonify converts python vars to json
    except:
        return jsonify({"error": "Username or password not provided"}),400


# Returns base64 encoded token from username, which needs to be added to protected routes in query parameters
@app.route("/api/login", methods=["POST"])
def user_login():
    try:
        username = request.json["username"]
        password = request.json["password"]
        if (username and password): # Checks if username, password are empty
            try:
                user = User.query.get(username)
                if(user.password == password):

                    #use jwt token for more security
                    return jsonify({"token": create_token(username)}),200
                else:
                    return ({"error": "Invalid username or password"}),400
            except Exception as e:
                return ({"error": "Invalid username or password"}),400
        else:
            return jsonify({"error": "Username or password not provided"}),400 # jsonify converts python vars to json
    except:
        return jsonify({"error": "Username or password invalid"}),400



if __name__ == "__main__":
    app.run(debug=True)