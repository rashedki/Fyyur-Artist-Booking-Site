#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import (
  Flask,
  render_template,
  request, Response,
  flash,
  redirect,
  url_for
)
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from models import *
from forms import *
from flask_migrate import Migrate
import sys
from init import create_app
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = create_app()
app.app_context().push()
moment = Moment(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

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
    data = []
    # Get areas
    areas = Venue.query.with_entities(Venue.city, Venue.state).group_by(Venue.city, Venue.state).all()
    # Iterate over each area
    for area in areas:
        data_venues = []
        # Get venues by area
        venues = Venue.query.filter_by(state=area.state).filter_by(city=area.city).all()
        # Iterate over each venue
        for venue in venues:
            # Get upcoming shows by venue
            upcoming_shows = db.session.query(Show).filter(Show.venue_id == venue.id).filter(Show.start_time > datetime.now()).all()
            # Map venues
            data_venues.append({
                'id': venue.id,
                'name': venue.name,
                'num_upcoming_shows': len(upcoming_shows)
            })
        # Map areas
        data.append({
            'city': area.city,
            'state': area.state,
            'venues': data_venues
        })
    return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_word = '%{}%'.format(request.form.get('search_term').lower())
  result = Venue.query.filter(Venue.name.ilike(search_word)).all()
  response = {}
  response["count"] = len(result)
  response["data"] = []
  for val in result:
    response.get("data").append({
      "id": val.id,
      "name": val.name,
      "num_upcoming_shows": Show.query.filter(val.id == Show.venue_id, Show.start_time > datetime.now()).count(),
    })
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    venue = Venue.query.filter(Venue.id==venue_id).first()
    shows = Show.query.filter(Show.venue_id == venue_id).all()
    upcoming_shows = []
    past_shows =[]
    data = {}
    if venue is None:
        return not_found_error('Venue does not found')
    for x in shows:
        if x.start_time >= datetime.now():
          upcoming_shows.append({
            "artist_id": x.artist_id,
            "artist_name": Artist.query.filter(Artist.id == x.artist_id).first().name,
            "artist_image_link": Artist.query.filter(Artist.id == x.artist_id).first().image_link,
            "start_time": x.start_time.strftime('%m/%d/%y'),
          })
        else:
          past_shows.append({
            "artist_id": x.artist_id,
            "artist_name": Artist.query.filter(Artist.id == x.artist_id).first().name,
            "artist_image_link": Artist.query.filter(Artist.id == x.artist_id).first().image_link,
            "start_time":  x.start_time.strftime('%m/%d/%y'),
          })
    data = {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres.split(','),
        "address": venue.address,
        "city":  venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_talent":venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": Show.query.filter(venue_id == Show.venue_id, Show.start_time < datetime.now()).count(),
        "upcoming_shows_count": Show.query.filter(venue_id == Show.venue_id, Show.start_time >= datetime.now()).count(),
    }
    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  try:
    name = request.form.get('name')
    city = request.form.get('city')
    state = request.form.get('state')
    adress = request.form.get('address')
    phone = request.form.get('phone')
    image_link = request.form.get('image_link')
    facebook_link = request.form.get('facebook_link')
    genres = request.form.getlist('genres')
    venue = Venue(name=name, city=city, state=state, address=adress,
                  phone=phone, image_link=image_link, facebook_link=facebook_link, genres=','.join(genres))
    db.session.add(venue)
    db.session.commit()
    # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully listed!', 'success')
  except:
    db.session.rollback()
    print(sys.exc_info())
    flash('An error occurred. Venue ' + request.form.get('name') + ' could not be listed.', 'error')
  finally:
    db.session.close()
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
     try:
        shows = Show.query.filter(Show.venue_id==venue_id).all()
        if len(shows) > 0:
          for show in shows:
            db.session.delete(show)
        val = Venue.query.filter(Venue.id==venue_id).first()
        if  val is not None:
          db.session.delete(val)
          db.session.commit()
          flash('Venue was successfully deleted!', 'success')
     except:
        db.session.rollback()
        print(sys.exc_info())
        flash('An error occurred. Venue '  + venue_id + ' could not be deleted.', 'error')
     finally:
        db.session.close()
     return render_template(url_for('pages/home.html'))

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    data = []
    # Get artists
    artists = Artist.query \
        .with_entities(Artist.id, Artist.name) \
        .order_by('id') \
        .all()
    # Iterate over each artist
    for artist in artists:
        # Get upcoming shows
        upcoming_shows = db.session \
                .query(Show) \
                .filter(Show.artist_id == artist.id) \
                .filter(Show.start_time > datetime.now()) \
                .all()
        # Map artists
        data.append({
            'id': artist.id,
            'name': artist.name,
            'num_upcoming_shows': len(upcoming_shows)
        })
    return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
    search_word = '%{}%'.format(request.form.get('search_term').lower())
    result = Artist.query.filter(Artist.name.ilike(search_word)).all()
    response = {}
    response["count"] = len(result)
    response["data"] = []
    for val in result:
        response.get("data").append({
          "id": val.id,
          "name": val.name,
          "num_upcoming_shows": Show.query.filter(val.id == Show.venue_id, Show.start_time > datetime.now()).count(),
        })
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist = Artist.query.filter(Artist.id==artist_id).first()
  shows = Show.query.filter(Show.artist_id == artist_id).all()
  upcoming_shows = []
  past_shows =[]
  data = {}
  if artist is None:
    return not_found_error('Venue does not found')
  for x in shows:
    if x.start_time >= datetime.now():
      upcoming_shows.append({
        "venue_id": x.venue_id,
        "venue_name": Venue.query.filter(Venue.id == x.venue_id).first().name,
        "venue_image_link": Venue.query.filter(Venue.id == x.venue_id).first().image_link,
        "start_time": x.start_time.strftime('%m/%d/%y'),
      })
    else:
      past_shows.append({
        "venue_id": x.artist_id,
        "venue_name": Venue.query.filter(Venue.id == x.venue_id).first().name,
        "venue_image_link": Venue.query.filter(Venue.id == x.venue_id).first().image_link,
        "start_time":  x.start_time.strftime('%m/%d/%y'),
      })
  data = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres.split(','),
        "city":  artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "seeking_talent":artist.seeking_talent,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": Show.query.filter(artist_id == Show.artist_id, Show.start_time < datetime.now()).count(),
        "upcoming_shows_count": Show.query.filter(artist_id == Show.artist_id, Show.start_time >= datetime.now()).count(),
    }
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  user = Artist.query.get(artist_id)
  if user is None:
    return not_found_error('User does not found')
  artist={
    "id": user.id,
    "name": user.name,
    "genres": user.genres.split(','),
    "city":  user.city,
    "state": user.state,
    "phone": user.phone,
    "website": user.website,
    "facebook_link": user.facebook_link,
    "seeking_venue": user.seeking_talent,
    "seeking_description": user.seeking_description,
    "image_link": user.image_link
  }
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    user = Artist.query.get(artist_id)
    if user is None:
        return not_found_error('User does not found')
    try:
        user.name = request.form.get('name')
        user.city = request.form.get('city')
        user.state = request.form.get('state')
        user.phone = request.form.get('phone')
        user.facebook_link = request.form.get('facebook_link')
        user.genres = ','.join(request.form.getlist('genres'))
        db.session.commit()
    except:
        print('An error occurred. Artist ' + request.form.get('name') + ' could not be updated.')
        db.session.rollback()
    finally:
        db.session.close()
    return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue_selected = Venue.query.get(venue_id)
  if venue_selected is None:
    return not_found_error('Venue does not found') #Msg does not hold by func
  venue={
    "id": venue_selected.id,
    "name": venue_selected.name,
    "genres":  venue_selected.genres.split(','),
    "address": venue_selected.address,
    "city":  venue_selected.city,
    "state": venue_selected.state,
    "phone": venue_selected.phone,
    "website": venue_selected.website,
    "facebook_link": venue_selected.facebook_link,
    "seeking_talent": venue_selected.seeking_talent,
    "seeking_description": venue_selected.seeking_description,
    "image_link": venue_selected.image_link
  }
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    selected_venue = Venue.query.get(venue_id)
    if selected_venue is None:
        return not_found_error('selected_venue does not found')
    try:
        selected_venue.name = request.form.get('name')
        selected_venue.city = request.form.get('city')
        selected_venue.state = request.form.get('state')
        selected_venue.phone = request.form.get('phone')
        selected_venue.facebook_link = request.form.get('facebook_link')
        selected_venue.genres = ','.join(request.form.getlist('genres'))
        selected_venue.address = request.form.get('address')
        db.session.commit()
    except:
        print('An error occurred. Venue ' + request.form.get('name') + ' could not be updated.')
        db.session.rollback()
    finally:
        db.session.close()
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    try:
      name = request.form.get('name')
      city = request.form.get('city')
      state = request.form.get('state')
      phone = request.form.get('phone')
      facebook_link = request.form.get('facebook_link')
      genres = request.form.getlist('genres')
      artist = Artist(name=name, city=city, state=state, phone=phone, facebook_link=facebook_link, genres=','.join(genres))
      db.session.add(artist)
      db.session.commit()
      flash('Artist ' + request.form['name'] + ' was successfully listed!', 'success')
    except:
      db.session.rollback()
      #print('An error occurred. Artist ' + request.form.get('name') + ' could not be listed.')
      flash('An error occurred. Artist ' + request.form.get('name') + ' could not be listed.', 'error')
    finally:
      db.session.close()
    return render_template('pages/home.html')

@app.route('/shows')
def shows():
    data = []
#    shows = Show.query.all()
    for show in Show.query.all():
        artist = Artist.query.filter(Artist.id == show.artist_id).one()
        data.append({
          "venue_id": show.venue_id,
          "venue_name": Venue.query.filter(Venue.id == show.venue_id).first().name,
          "artist_id": show.artist_id,
          "artist_name": artist.name,
          "artist_image_link": artist.image_link,
          "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M:%S"),
         })
    return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    try:
      art_id = request.form.get('artist_id')
      ven_id = request.form.get('venue_id')
      strt_time = request.form.get("start_time")
      newShow = Show(start_time = strt_time, artist_id = art_id, venue_id = ven_id)
      db.session.add(newShow)
      db.session.commit()
      flash('Show was successfully listed!', 'success')
    except:
      db.session.rollback()
      print(sys.exc_info())
      flash('An error occurred. Show could not be listed.', 'error')
    finally:
      db.session.close()
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
