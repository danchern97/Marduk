from flask import Blueprint, render_template, request, flash, jsonify, send_file
from flask_login import login_required, current_user
from .models import Project
from .utils import create_empty_table, serialize_project

views = Blueprint("views", __name__)

@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST': # create a new project
        project_name = request.form.get('project_name')

        if len(project_name) < 1:
            flash('Project name is too short!', category='error')
        else:
            new_project = Project(
                name=project_name,
                table=create_empty_table(),
                user_id=current_user.id)
            db.session.add(new_project)
            db.session.commit()
            flash('Project started...', category='success')
            return redirect(url_for("views.project"))
    return render_template("home.html", user=current_user)

@views.route('/delete-project/<int:project_id>', methods=['POST', 'GET'])
def delete_project(project_id):
    # project = json.loads(request.data)
    # project_id = project['project_id']
    project = Project.query.get(project_id).first()
    if project:
        if project.user_id == current_user.id:
            db.session.delete(project)
            db.session.commit()

    return jsonify({})

@views.route('/download-project/<int:project_id>', methods=['GET']) # maybe wrong
def download_project(project_id):
    project = Project.query.get(project_id).first()
    if project:
        if project.user_id == current_user.id:
            return send_file(serialize_project(project))

@views.route('/<project_id>', methods=['GET', 'POST'])
def project():
    return render_template("project.html")
