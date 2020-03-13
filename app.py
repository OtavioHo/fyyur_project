#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
import datetime
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

venue_genre = db.Table('venue_genre',
  db.Column('venue_id', db.Integer, db.ForeignKey('Venue.id'), primary_key=True),
  db.Column('genre_id', db.Integer, db.ForeignKey('Genre.id'), primary_key=True)
)

class Venue(db.Model):
  __tablename__ = 'Venue'

  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String)
  address = db.Column(db.String(120))
  phone = db.Column(db.String(120))
  image_link = db.Column(db.String(500))
  facebook_link = db.Column(db.String(120))
  website = db.Column(db.String(120))
  seeking_talent = db.Column(db.Boolean)
  seeking_description = db.Column(db.String)
  image_link = db.Column(db.String(120))
  location_id = db.Column(db.ForeignKey('Location.id'))
  shows = db.relationship('Show', backref='venue', lazy=True)
  genres = genres = db.relationship('Genre', secondary=venue_genre, backref=db.backref('venue'), lazy=True)

artist_genre = db.Table('artist_genre',
  db.Column('artist_id', db.Integer, db.ForeignKey('Artist.id'), primary_key=True),
  db.Column('genre_id', db.Integer, db.ForeignKey('Genre.id'), primary_key=True)
)

class Artist(db.Model):
  __tablename__ = 'Artist'

  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String)
  location = db.Column(db.ForeignKey('Location.id'))
  phone = db.Column(db.String(120))
  genres = db.relationship('Genre', secondary=artist_genre, backref=db.backref('artist'), lazy=True)
  image_link = db.Column(db.String(500))
  facebook_link = db.Column(db.String(120))
  shows = db.relationship('Show', backref='artist', lazy=True)

class Show(db.Model):
  __tablename__ = 'Show'

  id = db.Column(db.Integer, primary_key=True)
  artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
  venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
  start_time = db.Column(db.DateTime(), nullable=False)

class Location(db.Model):
  __tablename__ = 'Location'

  id = db.Column(db.Integer, primary_key=True)
  city = db.Column(db.String(120), nullable=False)
  state = db.Column(db.String(120), nullable=False)
  venues = db.relationship('Venue', backref='location', lazy=True)

class Genre(db.Model):
  __tablename__ = 'Genre'

  id = db.Column(db.Integer, primary_key=True, autoincrement=True)
  name = db.Column(db.String(120), nullable=False)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  locations = Location.query.all()

  data = []

  for location in locations:
    if location.venues:
      venues = []
      for v in location.venues:
        new_venue = {
          "id": v.id,
          "name": v.name,
          "num_upcoming_show": 0
        }

        venues.append(new_venue)
  
      new_data = {
        "city": location.city,
        "state": location.state,
        "venues": venues
      }

      data.append(new_data)
    
  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search = "%{}%".format(request.form['search_term'])
  venues = Venue.query.filter(Venue.name.ilike(search)).all()

  response={
    "count": len(venues),
    "data": venues
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):  
  venue = Venue.query.get(venue_id)

  upcoming_shows = []
  past_shows = []

  for show in venue.shows: 
    if show.start_time < datetime.datetime.now():
      past_shows.append(show)
    else:
      upcoming_shows.append(show)
  
  return render_template('pages/show_venue.html', 
    venue=venue, past_shows=past_shows, 
    upcoming_shows=upcoming_shows)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  genres = Genre.query.all()
  form = VenueForm()
  form.genres.choices = [(g.id, g.name) for g in genres]
  form.location.choices = [(l.id, l.city + ', ' + l.state) for l in Location.query.all()]
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  try:
    seeking = False
    if request.form['seeking_talent'] == 'y':
      seeking = True

    venue = Venue(name=request.form['name'],
                  location_id=request.form['location'],
                  address=request.form['address'],
                  phone=request.form['phone'],
                  image_link=request.form['image_link'],
                  facebook_link=request.form['facebook_link'],
                  seeking_talent=seeking,
                  seeking_description=request.form['seeking_description'])

    genres = request.form.getlist('genres')
    add_genres = [Genre.query.get(genre) for genre in genres]

    venue.genres = add_genres

    db.session.add(venue)
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except Exception as e:
    print(e)
    flash('Error.')

  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():

  artists = Artist.query.all()
  return render_template('pages/artists.html', artists=artists)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search = "%{}%".format(request.form['search_term'])
  artists = Artist.query.filter(Artist.name.ilike(search)).all()
  
  response={
    "count": len(artists),
    "data": artists
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist = Artist.query.get(artist_id)

  upcoming_shows = []
  past_shows = []

  for show in artist.shows: 
    if show.start_time < datetime.datetime.now():
      past_shows.append(show)
    else:
      upcoming_shows.append(show)

  return render_template('pages/show_artist.html',
     artist=artist,
     upcoming_shows=upcoming_shows,
     past_shows=past_shows)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist={
    "id": 4,
    "name": "Guns N Petals",
    "genres": ["Rock n Roll"],
    "city": "San Francisco",
    "state": "CA",
    "phone": "326-123-5000",
    "website": "https://www.gunsnpetalsband.com",
    "facebook_link": "https://www.facebook.com/GunsNPetals",
    "seeking_venue": True,
    "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
    "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80"
  }
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue={
    "id": 1,
    "name": "The Musical Hop",
    "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
    "address": "1015 Folsom Street",
    "city": "San Francisco",
    "state": "CA",
    "phone": "123-123-1234",
    "website": "https://www.themusicalhop.com",
    "facebook_link": "https://www.facebook.com/TheMusicalHop",
    "seeking_talent": True,
    "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
    "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60"
  }
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  locations = Location.query.all()
  form = ArtistForm()
  form.location.choices = [(location.id ,location.city + ', ' + location.state) for location in locations]
  form.genres.choices = [(g.id, g.name) for g in Genre.query.all()]
  return render_template('forms/new_artist.html', form=form, locations=locations)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  try:
    artist = Artist(
      name=request.form['name'],
      phone=request.form['phone'],
      location=request.form['location'],
      facebook_link=request.form['facebook_link'],
      image_link=request.form['image_link']
    )
    genres = request.form.getlist('genres')
    add_genres = [Genre.query.get(genre) for genre in genres]

    artist.genres = add_genres

    db.session.add(artist)
    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except Exception as e:
    print(e)
    flash('Error.')
  
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():

  shows = db.session.query(Show).join(Artist, Show.artist_id == Artist.id).join(Venue, Show.venue_id == Venue.id).all()

  return render_template('pages/shows.html', shows=shows)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  try:
    show = Show(
      artist_id=request.form['artist_id'],
      venue_id=request.form['venue_id'],
      start_time=request.form['start_time']
    )

    db.session.add(show)
    db.session.commit()
    flash('Show was successfully listed!')
  except Exception as e:
    flash('Error.')
    
  return render_template('pages/home.html')

@app.route('/genres/create')
def create_genre():
  form = GenreForm()
  return render_template('forms/new_genre.html', form=form)

@app.route('/genres/create', methods=['POST'])
def create_genres_submission():
  try:
    print(request.form)
    genre = Genre(
      name=request.form['genre_name']
    )

    db.session.add(genre)
    db.session.commit()
    flash('Genre was successfully listed!')
  except Exception as e:
    print(e)
    flash('Error.')
  return render_template('pages/home.html')

@app.route('/location/create')
def create_location():
  form = LocationForm()
  return render_template('forms/new_location.html', form=form)

@app.route('/location/create', methods=['POST'])
def create_location_submission():
  try:
    location = Location(
      city = request.form['city'],
      state = request.form['state']
    )

    db.session.add(location)
    db.session.commit()
    flash('Location was succefully listed!')
  except Exception as e:
    print(e)
    flash('Error.')
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500

if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
