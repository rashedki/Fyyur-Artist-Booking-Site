from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, MigrateCommand
from flask_moment import Moment

app = Flask(__name__)
db = SQLAlchemy(app)
app.config.from_object('config')
migrate = Migrate(app, db)

# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Show(db.Model):
     __tablename__ = 'Show'

     id = db.Column(db.Integer, primary_key=True)
     artist_id  = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable = False)
     venue_id   = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable = False)
     start_time = db.Column(db.DateTime())

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500), nullable = True)
    facebook_link = db.Column(db.String(120))
    shows = db.relationship("Show", backref='venue', lazy = True)

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500), nullable = True)
    facebook_link = db.Column(db.String(120))
    shows = db.relationship("Show", backref='artist', lazy = True)

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.


db.create_all()
