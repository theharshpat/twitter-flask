from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

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


@app.route('/')
def index():
    return "Twitter Flask Clone!"

if __name__ == "__main__":
    app.run(debug=True)