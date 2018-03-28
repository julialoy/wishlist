# Ron-proof all uploading/deleting/editing elements

from datetime import date
import os

from flask import (Flask, flash, g, redirect, render_template, request,
                   send_from_directory, url_for)
from flask_bcrypt import check_password_hash
from flask_login import (current_user, LoginManager, login_required,
                         login_user, logout_user, UserMixin)
from werkzeug.utils import secure_filename

import forms
import models

DEBUG = True
UPLOAD_FOLDER = "static\images\pics_user"
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])


app = Flask(__name__)
app.config['SECRET_KEY'] = 'fdkdfjkewyi7or3w734u3irheklshf^&%RU^$TYiu1'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.session_protection = "strong"
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    try:
        return models.User.get(models.User.id==user_id)
    except models.DoesNotExist:
        return None


@app.before_request
def before_request():
    g.db = models.DATABASE
    g.db.get_conn()             # Ensures connection is not opened 2x
    g.user = current_user
    g.search_form = forms.SearchForm()  # Allows search bar to function in all views


@app.after_request
def after_request(response):
    g.db.close()
    return response


@app.route("/", methods=("GET", "POST"))
def index():
    if g.user.is_authenticated:
        wishlists = (models.Wishlist.select().join(models.User)
                     .where(models.User.id==g.user.id))
    else:
        wishlists = models.Wishlist.select()
    return render_template('index.html', wishlists=wishlists)


@app.route("/search", methods=["POST"])
def search():
    if not g.search_form.validate_on_submit():
        print(g.search_form.errors)
        flash("Not a valid search.")
        return redirect(url_for('index'))
    return redirect(url_for('search_results', query=g.search_form.search.data))


@app.route("/searchresults/<query>", methods=["GET", "POST"])
def search_results(query):
    results = []
    user_query = query.strip().lower()

    if user_query=='search':
        qry = models.User.select()
        results = qry
    else:
        qry = models.User.select().where(models.User.email.contains(user_query))
        if qry.exists():
            results = qry
        else:
            results =[]

    if not results:
        flash("No results found!", "failure")
        return redirect(url_for('index'))

    return render_template('searchresults.html', results=results)


@app.route("/register", methods=("GET", "POST"))
def register():
    form = forms.RegisterForm()

    if form.validate_on_submit():
        flash("Registration successful!", "success")
        models.User.create_user(
            email=form.email.data,
            password=form.password.data,
        )
        models.UserInfo.create(
            user=models.User.get(models.User.email==form.email.data),
            bio="",
            pic=""
        )
        return redirect(url_for('index'))
    return render_template('register.html', form=form)


@app.route("/login", methods=("GET", "POST"))
def login():
    form = forms.LoginForm()

    if form.validate_on_submit():
        try:
            user = models.User.get(models.User.email==form.email.data)
        except models.DoesNotExist:
            flash("That email or password is incorrect.", "error")
        else:
            if check_password_hash(user.password, form.password.data):
                login_user(user)
                flash(
                    "Hello, {}! You have been logged in.".format(g.user.email),
                    "success"
                )
                return redirect(url_for('index'))
            else:
                flash("That email or password is incorrect", "error")
    return render_template('login.html', form=form)


@app.route("/logout")
@login_required
def logout():
    user_email = g.user.email
    logout_user()
    flash("Goodbye, {}! You have been logged out.".format(user_email),
          "success")
    return redirect(url_for('index'))


@app.route("/profile/<int:user_id>")
@login_required
def profile(user_id):
    selected_user = models.User.get(models.User.id==user_id)
    selected_user_info, created = models.UserInfo.get_or_create(
        user_id=user_id,
        defaults={'bio': "", 'pic': ""}
    )
    wishlists = (models.Wishlist.select().join(models.User)
                 .where(models.User.id==selected_user.id))
    return render_template('profile.html',
                           selected_user=selected_user,
                           selected_user_info=selected_user_info,
                           wishlists=wishlists)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/uploader", methods=["GET", "POST"])
@login_required
def uploader():
    selected_user = g.user.id

    if request.method == "POST":
        if 'file' not in request.files:
            flash("No file part")
            return redirect(url_for('profile'))
    file = request.files['file']

    if file.filename == '':
        flash("No selected file")
        return redirect(request.url)

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        #return redirect(url_for('uploaded_file', filename=filename))
        selected_user_info, created = models.UserInfo.get_or_create(
            user_id=selected_user,
            defaults={'bio': "", 'pic': ""}
        )
        q = models.UserInfo.update(
            pic=filename
        ).where(models.UserInfo.user_id==selected_user_info.user_id)
        q.execute()
        return redirect(url_for('profile', user_id=selected_user))


@app.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route("/wishlist", methods=("GET", "POST"))
@login_required
def wishlist_create():
    form = forms.WishlistForm()

    if form.validate_on_submit():
        models.Wishlist.create(user=g.user.id,
                               title=form.title.data.strip())
        flash("List created!", "success")
        return redirect(url_for('index'))
    return render_template('wishlist.html', form=form)


@app.route("/wishlistview/<int:selected_wishlist_id>")
@login_required
def wishlist_view(selected_wishlist_id):
    selected_wishlist = (models.Wishlist
                         .get(models.Wishlist.id==selected_wishlist_id))
    items = (models.Item.select().join(models.Wishlist)
             .where(models.Wishlist.id==selected_wishlist_id))
    return render_template('wishlistview.html',
                           selected_wishlist=selected_wishlist,
                           items=items)


@app.route("/additem/<int:selected_list_id>", methods=("GET", "POST"))
@login_required
def add_item(selected_list_id):
    form = forms.ItemForm()
    selected_list = models.Wishlist.get(models.Wishlist.id==selected_list_id)

    if form.validate_on_submit() and current_user.id==selected_list.user_id:
        models.Item.create(
            wishlist=selected_list.id,
            name=form.name.data.strip(),
            link=form.link.data.strip()
        )
        flash("Item added!", "success")
        return redirect(url_for('index'))
    elif not current_user.id==selected_list.user_id:
        flash("You do not have access to that list.", "failure")
        return redirect(url_for('index'))
    return render_template('additem.html',
                           selected_list=selected_list,
                           form=form)


@app.route("/edititem/<int:selected_item_id>", methods=("GET", "POST"))
@login_required
def edit_item(selected_item_id):
    form = forms.EditItem()
    selected_item = models.Item.get(models.Item.id==selected_item_id)
    selected_list = models.Wishlist.get(models.Wishlist.id==selected_item.wishlist_id)

    if form.validate_on_submit() and current_user.id==selected_list.user_id:
        q = models.Item.update(
            name=form.name.data.strip(),
            link=form.link.data.strip()
        ).where(models.Item.id==selected_item_id)
        q.execute()
        flash("Item updated!", "success")
        return redirect(url_for('index'))
    elif not current_user.id==selected_list.user_id:
        flash("You do not have permission to edit this item.", "failure")
        redirect(url_for('index'))

    return render_template('edititem.html', form=form, selected_item=selected_item)


@app.route("/editlistname/<int:selected_list_id>", methods=["GET", "POST"])
@login_required
def edit_list_name(selected_list_id):
    form = forms.EditListName()
    selected_list = models.Wishlist.get(models.Wishlist.id==selected_list_id)
    if form.validate_on_submit() and selected_list.user_id==current_user.id:
        q = models.Wishlist.update(
            title=form.title.data.strip()
        ).where(models.Wishlist.id==selected_list_id)
        q.execute()
        flash("List name updated!", "success")
        return redirect(url_for('index'))
    elif not selected_list.user_id==current_user.id:
        flash("You do not have permission to edit this item.", "failure")
        redirect(url_for('index'))

    return render_template('editlistname.html', form=form, selected_list=selected_list)


@app.route("/deleteitem/<int:selected_item_id>/<int:selected_wishlist_id>",
           methods=("GET", "DELETE"))
@login_required
def delete_item(selected_item_id, selected_wishlist_id):
    selected_item = models.Item.get(models.Item.id==selected_item_id)
    selected_list = models.Wishlist.get(models.Wishlist.id==selected_wishlist_id)
    if selected_list.user_id==current_user.id:
        try:
            selected_item.delete_instance(recursive=True)
            flash("Item has been deleted.", "success")
        except:
            flash("Unable to delete item.", "failure")
    elif not selected_list.user_id==current_user.id:
        flash("You are not allowed to delete that item.", "failure")
    return redirect(url_for('wishlist_view', selected_wishlist_id=selected_list.id))


@app.route("/deletelist", methods=["POST"])
@login_required
def delete_list():
    selections =[*request.form.keys()]
    for selection in selections:
        selected_list = models.Wishlist.get(models.Wishlist.id==int(selection))
        if selected_list.user_id==current_user.id:
            selected_list.delete_instance(recursive=True)
            flash("{} has been deleted.".format(selected_list.title))
        else:
            flash("You don't have permission to delete {}".format(selected_list.title))
    return redirect(url_for('index'))

# Add functionality for:
# Changing email address
# Deleting account (user)
if __name__ == '__main__':
    models.initialize()
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.run(debug=DEBUG)