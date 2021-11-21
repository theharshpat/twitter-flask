from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import base64
from functools import wraps


app = Flask(__name__)

# Database models #################################################################

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///twitter.db"
db = SQLAlchemy(app)

# Many-to-many table for User table
user_to_user = db.Table('user_to_user',
                        db.Column("follower_username", db.String, db.ForeignKey(
                            "user.username"), primary_key=True),
                        db.Column("followed_username", db.String, db.ForeignKey(
                            "user.username"), primary_key=True)
                        )


# User data model
class User(db.Model):
    username = db.Column(db.String(20), primary_key=True)
    password = db.Column(db.String(100))
    tweets = db.relationship('Tweet', backref='user')

    following = db.relationship("User",
                                secondary=user_to_user,
                                primaryjoin=username == user_to_user.c.follower_username,
                                secondaryjoin=username == user_to_user.c.followed_username,
                                backref="followed_by"
                                )

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def to_dict(self):
        return {"username": self.username, "following": len(self.following), "followed_by": len(self.followed_by), "tweets": len(self.tweets)}


# Tweet data model
class Tweet(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    content = db.Column(db.Text)
    username = db.Column(db.Integer, db.ForeignKey('user.username'))
    epoch = db.Column(db.Integer)

    def __init__(self, content):
        self.content = content
        self.epoch = int(datetime.now().timestamp() * 1000000)

    def __repr__(self):
        return "ID "+str(self.id)+" content "+str(self.content)+" epoch "+str(self.epoch)+" username "+str(self.username)

    def to_dict(self):
        return {"username": self.username, "content": self.content, "time": self.epoch}



# Demo data: Uncomment and execute to create the tables and populate the demo data ####################

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



# Helper functions #####################################

# Returns base64 encoded token from the username
def create_token(username):
    user_string_bytes = username.encode("utf-8")
    base64_bytes = base64.b64encode(user_string_bytes)
    base64_string = base64_bytes.decode("utf-8")
    return base64_string


# Returns the username from the provided base64 encoded token
def decode_token(token):
    base64_bytes = token.encode("utf-8")
    token_string_bytes = base64.b64decode(base64_bytes)
    username = token_string_bytes.decode("utf-8")
    return username


# Wrapper function to get the token from query parameters
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            request.user = User.query.get(
                decode_token(request.args.get("token")))
        except:
            return jsonify({'error': 'Token is missing or invalid!'}), 400
        return f(*args, **kwargs)
    return decorated


# API Routes #################################################################


@app.route('/')
def index():
    return "Twitter Flask Clone!"


# User registration based on username and password
@app.route("/api/register", methods=["POST"])
def user_register():
    try:
        username = request.json["username"]
        password = request.json["password"]
        if (username and password):  # Checks if username, password are empty
            try:
                user = User(username, password)  # Creates a new record
                db.session.add(user)  # Adds the record for committing
                db.session.commit()  # Saves our changes
                return jsonify({"message": "User created successfully"}), 200
            except Exception as e:
                db.session.rollback()  # Rollback the database if user already exists
                return ({"error": "Could not create a new user"}), 400
        else:
            # jsonify converts python vars to json
            return jsonify({"error": "Username or password not provided"}), 400
    except:
        return jsonify({"error": "Username or password not provided"}), 400


# User login route
# Returns base64 encoded token from username, which needs to be added to protected routes in query parameters
@app.route("/api/login", methods=["POST"])
def user_login():
    try:
        username = request.json["username"]
        password = request.json["password"]
        if (username and password):  # Checks if username, password are empty
            try:
                user = User.query.get(username)
                if(user.password == password):

                    # use jwt token for more security
                    return jsonify({"token": create_token(username)}), 200
                else:
                    return ({"error": "Invalid username or password"}), 400
            except Exception as e:
                return ({"error": "Invalid username or password"}), 400
        else:
            # jsonify converts python vars to json
            return jsonify({"error": "Username or password not provided"}), 400
    except:
        return jsonify({"error": "Username or password invalid"}), 400


# Post a tweet for the user related to the provided token
@app.route("/api/tweet/post", methods=["POST"])
@token_required
def tweet_post():
    user = request.user
    content = request.json["content"]

    if len(content) > 140:
        return jsonify({"error": "Tweet content exceeds 140 characters limit"}), 400

    tweet = Tweet(content)
    user.tweets.append(tweet)

    try:
        db.session.add(user)
        db.session.commit()
    except:
        db.session.rollback()
        return jsonify({"error": "Could not create new tweet"}), 400

    return jsonify({"message": "User tweeted :D "}), 200


# Provide user token and feed will be returned in sorted order based on the tweet time
# Feed contains user's tweets and followed_user tweets
@app.route("/api/feed", methods=["GET"])
@token_required
def user_feed():
    user = request.user
    tweets_data = []
    tweets_data.extend(user.tweets)

    for followed_user in user.following:
        tweets_data.extend(followed_user.tweets)

    tweets_data = [t.to_dict() for t in tweets_data]
    tweets_data.sort(key=lambda t: t['time'], reverse=True)

    for tweet in tweets_data:
        divided_epoch = tweet["time"]/1000000
        tweet["time"] = datetime.fromtimestamp(
            divided_epoch).strftime('%Y-%m-%d %H:%M:%S')

    return jsonify(tweets_data), 200


# Returns list of other users sorted based on the username
@app.route("/api/users", methods=["GET"])
@token_required
def user_list():
    user = request.user
    users = User.query.all()
    users.remove(user)

    user_data = [u.to_dict() for u in users]
    user_data.sort(key=lambda u: u['username'])
    return jsonify(user_data), 200


# Follow the user from the provided username in the request body
@app.route("/api/follow", methods=["POST"])
@token_required
def user_follow():
    user = request.user
    to_follow_username = request.json["follow_username"]
    try:
        to_follow_user = User.query.get(to_follow_username)
    except:
        return jsonify({"error": "User not found"}), 400

    try:
        if to_follow_user in user.following:
            return jsonify({"error": "User already followed"}), 400

        user.following.append(to_follow_user)
        db.session.add(user)
        db.session.commit()

        return jsonify({"message": "User followed :D "}), 200
    except:
        db.session.rollback()
        return jsonify({"error": "User could not be followed"}), 400


# Get current user details
@app.route("/api/profile", methods=["GET"])
@token_required
def user_profile():
    user = request.user
    return jsonify(user.to_dict()),200


if __name__ == "__main__":
    app.run(debug=True)
