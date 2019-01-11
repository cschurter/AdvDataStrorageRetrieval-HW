import numpy as np

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from sqlalchemy.pool import StaticPool
import datetime as dt

from flask import Flask, jsonify
import sys

#################################################
# Database Setup
#################################################
#to set up sqlalchemy to handle multi threaded application
# https://docs.sqlalchemy.org/en/latest/dialects/sqlite.html#using-a-memory-database-in-multiple-threads
engine = create_engine("sqlite:///Resources/hawaii.sqlite",
                    connect_args={'check_same_thread':False},
                    poolclass=StaticPool)

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)

# Save reference to the table
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)

#create function to get start date for one year of data
def getOneYearAgo():
    maxdate = session.query(func.max(Measurement.date)).first()

    maxDate = dt.datetime.strptime(maxdate[0], '%Y-%m-%d')
    maxDate = maxDate.date()
    oneYearAgo = maxDate - dt.timedelta(days=365)
    return oneYearAgo

def getMostActiveStation():
    station_activity = session.query(Measurement.station, func.count(Measurement.tobs)).\
    group_by(Measurement.station).order_by(func.count(Measurement.tobs).desc()).all()
        
    most_active_station = station_activity[0][0]
    return most_active_station

def calc_temps(start_date, end_date):
    """TMIN, TAVG, and TMAX for a list of dates.
    
    Args:
        start_date (string): A date string in the format %Y-%m-%d
        end_date (string): A date string in the format %Y-%m-%d
        
    Returns:
        TMIN, TAVE, and TMAX
    """
    
    return session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
        filter(Measurement.date >= start_date).filter(Measurement.date <= end_date).all()

#https://stackoverflow.com/questions/16870663/how-do-i-validate-a-date-string-format-in-python/16870682
def validateDate(date_text):
    try:
        dt.datetime.strptime(date_text, '%Y-%m-%d')
    except ValueError:
        raise ValueError("Incorrect data format, should be YYYY-MM-DD")

#################################################
# Flask Setup
#################################################
app = Flask(__name__)


#################################################
# Flask Routes
#################################################

@app.route("/")
def welcome():
    """List all available api routes."""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/&lt;start&gt;/&ltend&gt;"
    )


@app.route("/api/v1.0/precipitation")
def precipitation():
    """Return last year's precipitation data"""
    # Query precipitation
    precipitation_12mos = session.query(Measurement.date,Measurement.prcp).filter(Measurement.date > getOneYearAgo()).\
    order_by(Measurement.date).all()

    precipitation_dict = {}
    for row in precipitation_12mos:
        precipitation_dict[row.date] = row.prcp
    return jsonify(precipitation_dict)


@app.route("/api/v1.0/stations")
def stations():
    #"""Return a list of stations"""
    results = session.query(Station.name).distinct().all()
    return jsonify(results)

@app.route("/api/v1.0/tobs")
def tobs():
    """Return last year's temperature obseravations"""
    # Query tobs
    temp_USC00519281 = session.query(Measurement.station,Measurement.date,Measurement.tobs).\
    filter(Measurement.station == getMostActiveStation()).\
    filter(Measurement.date > getOneYearAgo()).\
    order_by(Measurement.date).all()

    tobs_list = []
    for row in temp_USC00519281:
        tobs_dict = {}
        tobs_dict["date"] = row.date
        tobs_dict["tobs"] = row.tobs
        tobs_list.append(tobs_dict)
    return jsonify(tobs_list)

@app.route('/api/v1.0/<start>')
@app.route('/api/v1.0/<start>/<end>')

def temperature(start=None, end=None):
    today = dt.datetime.today().strftime('%Y-%m-%d')

    try:
        validateDate(start)
        if end != None:
            validateDate(end)
            temperature = calc_temps(start, end)
        else:
            temperature = calc_temps(start,today)
        return jsonify(temperature)
    except ValueError:
        return (
        f"Invalid Input"
            )

if __name__ == '__main__':
    app.run(debug=True)
