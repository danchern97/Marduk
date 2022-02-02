import os
from flask import Blueprint, render_template, request, flash
from flask import redirect, url_for, send_file
from flask_login import login_required, current_user
from .models import Project
from .utils import create_empty_table, dump_project, serialize_table
from .forms import NewProjectForm
from . import db

views = Blueprint("views", __name__)

@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    form = NewProjectForm()
    if form.validate_on_submit(): # create a new project
        project_name = form.data.get('project_name')
        table = create_empty_table()
        new_project = Project(
            name=project_name,
            table=serialize_table(table),
            user_id=current_user.id
        )
        db.session.add(new_project)
        db.session.commit()
        flash('Project started...', category='success')
        return redirect(url_for(f"views.project", project_id=new_project.id))
    return render_template("home.html", user=current_user, form=form)

@views.route('/delete/<project_id>', methods=['POST', 'GET'])
def delete_project(project_id):
    project = Project.query.get(project_id)
    if project:
        if project.user_id == current_user.id:
            db.session.delete(project)
            db.session.commit()
    else:
        flash("Project doesn't exist! Something went wrong.", category='error')
    return redirect(url_for("views.home"))

@views.route('/uploads/<project_id>', methods=['GET']) # rewrite directories
def download_project(project_id):
    project = Project.query.get(project_id)
    if project:
        if project.user_id == current_user.id:
            current_dir = os.getcwd()
            print(f"CURRENT DIR: {current_dir}")
            filepath = dump_project(project, dir_path=os.path.join(current_dir, 'app/temp/'))
            return send_file(filepath, download_name=project.name, as_attachment=True)
        else:
            flash("You do not have access to this project.", category='error')
    else:
        flash("Project does not exists! Something went wrong.", category='error')
    return redirect(url_for("views.home"))

@views.route('/<project_id>', methods=['GET', 'POST'])
def project(project_id):
    project = Project.query.get(project_id)
    if not project:
        flash("Project does not exists!", category='error')
        return redirect(url_for("views.home"))
    if project.user_id != current_user.id:
        flash("You do not have access to this project", category='error')
        return redirect(url_for("views.home"))
    return render_template("project.html")
