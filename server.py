
"""
Columbia's COMS W4111.001 Introduction to Databases
Example Webserver
To run locally:
    python3 server.py
Go to http://localhost:8111 in your browser.
A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""
import os
import random
  # accessible as a variable in index.html:
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)


#
# The following is a dummy URI that does not connect to a valid database. You will need to modify it to connect to your Part 2 database in order to use the data.
#
# XXX: The URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@34.74.246.148/proj1part2
#
# For example, if you had username gravano and password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://gravano:foobar@34.74.246.148/proj1part2"
#
DATABASEURI = "postgresql://msa2213:2433@34.74.246.148/proj1part2"



#
# This line creates a database engine that knows how to connect to the URI above.
#
engine = create_engine(DATABASEURI)

#
# Example of running queries in your database
# Note that this will probably not work if you already have a table named 'test' in your database, containing meaningful data. This is only an example showing you how to run queries in your database using SQLAlchemy.
#
engine.execute("""CREATE TABLE IF NOT EXISTS test (
  id serial,
  name text
);""")
engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")

def create_id():
  return random.randrange(10000,99999)

@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request.

  The variable g is globally accessible.
  """
  try:
    g.conn = engine.connect()
  except:
    print("uh oh, problem connecting to database")
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't, the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to, for example, localhost:8111/foobar/ with POST or GET then you could use:
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: https://flask.palletsprojects.com/en/2.0.x/quickstart/?highlight=routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/')
def index():
  """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments, e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: https://flask.palletsprojects.com/en/2.0.x/api/?highlight=incoming%20request%20data

  """
  cursor = g.conn.execute("SELECT * FROM patient")
  names = []
  for result in cursor:
    names.append(result)  # can also be accessed using result[0]
  cursor.close()

  #
  # Flask uses Jinja templates, which is an extension to HTML where you can
  # pass data to a template and dynamically generate HTML based on the data
  # (you can think of it as simple PHP)
  # documentation: https://realpython.com/primer-on-jinja-templating/
  #
  # You can see an example template in templates/index.html
  #
  # context are the variables that are passed to the template.
  # for example, "data" key in the context variable defined below will be 
  # accessible as a variable in index.html:
  #
  #     # will print: [u'grace hopper', u'alan turing', u'ada lovelace']
  #     <div>{{data}}</div>
  #     
  #     # creates a <div> tag for each element in data
  #     # will print: 
  #     #
  #     #   <div>grace hopper</div>
  #     #   <div>alan turing</div>
  #     #   <div>ada lovelace</div>
  #     #
  #     {% for n in data %}
  #     <div>{{n}}</div>
  #     {% endfor %}
  #
  context = dict(data = names)


  #
  # render_template looks in the templates/ folder for files.
  # for example, the below file reads template/index.html
  #
  return render_template("index.html", **context)

#
# This is an example of a different path.  You can see it at:
# 
#     localhost:8111/another
#
# Notice that the function name is another() rather than index()
# The functions for each app.route need to have different names
#


def filter_condition(table, attribute, value):
  return "WHERE {}.{} LIKE \'%%{}%%\'".format(table, attribute, value)


def run_query(query):
  cursor = g.conn.execute(query)
  results = []
  for result in cursor:
    results.append(result)
  cursor.close()
  return results


##########
##########    BASIC VIEWS

@app.route('/patient_view')
def patient_view():
  table = 'patient'
  query = "SELECT {} FROM {}".format('*', table)
  results = run_query(query)
  context = dict(patients=results, patient_count=len(results))
  return render_template("patient.html", **context)


@app.route('/doctor_view')
def doctor_view():
  table1 = 'employee'
  table2 = 'doctor'
  key = 'employee_id'
  query = "SELECT {} FROM {}".format('*', table1)
  join_query = '\nINNER JOIN {} ON {}.{} = {}.{}'.format(table2, table2, key, table1, key)
  results = run_query(query + join_query)
  context = dict(doctors= results)
  return render_template("doctor.html", **context)


@app.route('/nurse_view')
def nurse_view():
  table1 = 'employee'
  table2 = 'nurse'
  key = 'employee_id'
  query = "SELECT {} FROM {}".format('*', table1)
  join_query = '\nINNER JOIN {} ON {}.{}={}.{}'.format(table2, table2, key, table1, key)
  results = run_query(query + join_query)
  context = dict(nurses= results)
  return render_template("nurse.html", **context)


@app.route('/billing_view')
def billing_view():
  query = render_template("admission_query.txt")
  results = run_query(query)
  context = dict(billing_entries=results)
  return render_template("billing.html", **context)


############
############ SEARCH VIEWS


@app.route('/search_patient_view', methods=['POST'])
def search_patient_view():
  table = 'patient'
  condition = filter_condition(table, request.form['attribute'], request.form['value'])
  query = "SELECT {} FROM {} {}".format('*', table, condition)
  results = run_query(query)
  context = dict(patients= results)
  return render_template("patient.html", **context)


@app.route('/search_doctor_view', methods=['POST'])
def search_doctor_view():
  table1 = 'employee'
  table2 = 'doctor'
  key = 'employee_id'
  condition = filter_condition(table1, request.form['attribute'], request.form['value'])
  join_query = '\nINNER JOIN {} ON {}.{} = {}.{}'.format(table2, table2, key, table1, key)
  query = "SELECT {} FROM {} {} {}".format('*', table1, join_query, condition)
  results = run_query(query)
  context = dict(doctors=results)
  return render_template("doctor.html", **context)


@app.route('/search_nurse_view', methods=['POST'])
def search_nurse_view():
  table1 = 'employee'
  table2 = 'nurse'
  key = 'employee_id'
  condition = filter_condition(table1, request.form['attribute'], request.form['value'])
  join_query = '\nINNER JOIN {} ON {}.{} = {}.{}'.format(table2, table2, key, table1, key)
  query = "SELECT {} FROM {} {} {}".format('*', table1, join_query, condition)
  results = run_query(query)
  context = dict(doctors=results)
  return render_template("doctor.html", **context)


@app.route('/search_billing_view', methods=['POST'])
def search_billing_view():
  condition=None
  if request.form['attribute']=='patient_id':
    condition = filter_condition('b', 'patient_id', request.form['value'])
  if request.form['attribute']=='medication':
    condition = filter_condition('m', 'medication_id', request.form['value'])
  if request.form['attribute']=='procedure':
    condition = filter_condition('p', 'procedure_id', request.form['value'])
  if request.form['attribute']=='diagnosis':
    condition = filter_condition('d', 'diagnosis_name', request.form['value'])
  query = render_template("admission_query.txt")
  if condition is not None:
    query = query + condition
  results = run_query(query)
  context = dict(billing_entries=results)
  return render_template("billing.html", **context)


############
############     ADD DELETE PATIENTS


@app.route('/add_patient_view')
def add_patient_view():
  return render_template("add_patient.html")


@app.route('/add_patient', methods=['POST'])
def add_patient():
  table = 'patient'
  r = request.form
  values = '{},\'{}\',\'{}\',{},{}'.format(create_id(), r['name'], r['address'], r['phone'], r['insurance_id'])
  query = "INSERT INTO {} VALUES ({})".format(table, values)
  g.conn.execute(query)
  return patient_view()


@app.route('/delete_patient', methods=['POST'])
def delete_patient():
  table = 'patient'
  key = "patient_id"
  query = 'DELETE FROM {} WHERE {}.{}=\'{}\''.format(table, table, key, request.form['patient_id'])
  g.conn.execute(query)
  return patient_view()


###########
###########  UTILS

@app.route('/another')
def another():
  return render_template("another.html")


# Example of adding new data to the database
@app.route('/add', methods=['POST'])
def add():
  name = request.form['name']
  g.conn.execute('INSERT INTO test(name) VALUES (%s)', name)
  return redirect('/')


@app.route('/login')
def login():
    abort(401)
    this_is_never_executed()


if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using:

        python3 server.py

    Show the help text using:

        python3 server.py --help

    """

    HOST, PORT = host, port
    print("running on %s:%d" % (HOST, PORT))
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)

  run()
