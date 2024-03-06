from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import Job, User
from . import db
from flask_login import login_user, login_required, logout_user, current_user
import re

auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
  if request.method == 'POST':
    accountName = request.form.get('accountName')
    password = request.form.get('password')

    user = User.query.filter_by(accountName=accountName).first()
    if user:
      # Directly compare the password without hashing
      if user.password == password:
        flash('Logged in successfully!', category='success')
        login_user(user, remember=True)
        return redirect(url_for('views.home'))
      else:
        flash('Incorrect password, try again.', category='error')
    else:
      flash('Account name does not exist.', category='error')

  return render_template("login.html", user=current_user)


@auth.route('/logout')
@login_required
def logout():
  logout_user()
  return redirect(url_for('auth.login'))


@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
  if request.method == 'POST':

    total_users = User.query.count()
    if total_users >= 10:
      flash('All permitted accounts have been created, please come back later',
            category='error')
      return render_template("login.html", user=current_user)

    fname = request.form.get('fname')
    lname = request.form.get('lname')
    accountName = request.form.get('accountName')   
    password1 = request.form.get('password1')
    password2 = request.form.get('password2')


    user = User.query.filter_by(accountName=accountName).first()
    if user:
      flash('Account name already exists.', category='error')
    elif password1 != password2:
      flash('Passwords don\'t match.', category='error')
    elif len(password1) < 8:
      flash('Password must be at least 8 characters.', category='error')
    elif len(password1) > 12:
      flash('Password must be at most 12 characters.', category='error')
    elif not re.search("[A-Z]", password1):
      flash('Password must contain at least one capital letter.',
            category='error')
    elif not re.search("\d", password1):
      flash('Password must contain at least one digit.', category='error')
    elif not re.search("[^A-Za-z0-9]", password1):
      flash('Password must contain at least one special character.',
            category='error')
    else:
      # Store the password directly without hashing
      new_user = User(fname=fname, lname=lname, accountName=accountName, password=password1)
      db.session.add(new_user)
      db.session.commit()
      login_user(new_user, remember=True)
      flash('Account created!', category='success')
      return redirect(url_for('views.home'))

  return render_template("sign_up.html", user=current_user)




@auth.route('/post-job', methods=['GET', 'POST'])
def post_job():
    if request.method == 'POST':
        total_jobs = Job.query.count()
        if total_jobs >= 5:
            flash('All permitted jobs have been posted, please come back later', category='error')
            return render_template("post_job.html", user=current_user)

        title = request.form.get('title')
        description = request.form.get('description')
        employer = request.form.get('employer')
        location = request.form.get('location')
        salary = request.form.get('salary')
        accountName = current_user.accountName

        # Include user_id when creating the new Job
        new_job = Job(title=title, description=description, employer=employer, location=location, salary=salary, accountName=accountName)

        db.session.add(new_job)
        db.session.commit()

        flash('Job posting created!', category='success')
        return redirect(url_for('views.job_search'))

    return render_template("post_job.html", user=current_user)
