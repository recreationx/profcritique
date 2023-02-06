from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import (
    login_manager,
    LoginManager,
    login_required,
    login_user,
    logout_user,
    current_user,
)
from utils.forms import LoginForm, SignUpForm
from utils.user import User
from utils.datastore import Datastore

db = Datastore("test.db")
db.tables_init()

app = Flask(__name__)
app.secret_key = "IDGAF"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    user = db.get_user_by_id(user_id)
    if user is None:
        return None
    else:
        return User(int(user["id"]), user["username"], user["password"])


@app.route("/")
def main():
    return render_template("index.html", current_user=current_user)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main"))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.get_user_by_name(form.username.data)
        if user is None:
            flash("Login unsuccessful", category="danger")
        else:
            user = load_user(user["id"])
            if (
                form.username.data == user.username
                and form.password.data == user.password
            ):
                login_user(user, remember=form.remember.data)
                return redirect(url_for("main"))
            else:
                flash("Login unsuccessful.", category="danger")
    return render_template("login.html", form=form)


@app.route("/logout", methods=["GET"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("main"))


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("main"))
    form = SignUpForm()
    if form.validate_on_submit():
        user = db.get_user_by_name(form.username.data)
        print(user)
        if user is None:
            db.create_user(form.username.data, form.password.data)
            flash(f"User {form.username.data} created", category="success")
        else:
            flash(
                f"User {form.username.data} already exist. Please login.",
                category="danger",
            )
    return render_template("signup.html", form=form)


@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    if request.method == "POST":
        teacher = request.form["teacher"]
        result = db.search_teacher(teacher)
        result = [result[i : i + 3] for i in range(0, len(result), 3)]
        print(result)
        return render_template("search.html", result=result)
    else:
        return render_template("search.html", result=[""])


@app.route("/teacher/<teacher_id>", methods=["GET"])
@login_required
def teacher_profile(teacher_id=""):
    result = db.get_teacher_by_id(teacher_id)
    reviews = db.get_review(teacher_id)
    print(result["rating"])
    print(round(result["rating"], None) * "⭐")
    result["bar"] = round(result["rating"], None) * "⭐"
    return render_template(
        "teacher.html", teacher_id=teacher_id, result=result, reviews=reviews
    )


@app.route("/teacher/<teacher_id>/review", methods=["GET"])
@login_required
def review_teacher(teacher_id=""):
    result = db.get_teacher_by_id(teacher_id)
    return render_template("review.html", teacher_id=teacher_id, result=result)


@app.route("/teacher/<teacher_id>/review/add", methods=["POST"])
@login_required
def add_review(teacher_id=""):
    review_id = db.add_review(
        teacher_id,
        current_user.id,
        5.0,
        request.form["review"],
        request.form["fallback_rating"],
        "Verified",
    )
    rating = db.get_review_by_id(review_id)["rating"]
    aggregated = db.get_teacher_by_id(teacher_id)["rating"]
    if abs(int(request.form["fallback_rating"]) - rating) > 1:
        flash(
            "AI-determined rating and manual rating varies. Please re-confirm your submission."
        )
        return redirect(
            url_for(
                "modify_review",
                teacher_id=teacher_id,
                review_id=review_id,
                modify_type=1,
            )
        )

    if aggregated + 1 <= rating or rating <= aggregated - 1:
        flash(
            "Your previous review differs by a huge margin from the reviewee's ratings. Please try again. If not, cancel to proceed regardless."
        )
        return redirect(
            url_for(
                "modify_review",
                teacher_id=teacher_id,
                review_id=review_id,
                modify_type=1,
            )
        )
    return redirect(url_for("teacher_profile", teacher_id=teacher_id))


@app.route(
    "/teacher/<teacher_id>/review/<review_id>/modify/<modify_type>",
    methods=["GET", "POST"],
)
@login_required
def modify_review(modify_type="", teacher_id="", review_id="", message=""):
    if request.method == "POST":
        if modify_type == "1":  # AI calulcated does not match aggregated score
            db.delete_review(review_id)
            review_id = db.add_review(
                teacher_id,
                current_user.id,
                5.0,
                request.form["review"],
                request.form["fallback_rating"],
                "Verified",
            )
            rating = db.get_review_by_id(review_id)["rating"]
            aggregated = db.get_teacher_by_id(teacher_id)["rating"]
            if abs(int(request.form["fallback_rating"]) - rating) > 1:
                flash(
                    "AI-determined rating and manual rating varies. Please re-confirm your submission."
                )
                return redirect(
                    url_for(
                        "modify_review",
                        teacher_id=teacher_id,
                        review_id=review_id,
                        modify_type=1,
                    )
                )

            if aggregated + 1 <= rating or rating <= aggregated - 1:
                flash(
                    "Your previous review differs by a huge margin from the reviewee's ratings. Please try again. If not, cancel to proceed regardless."
                )
                return redirect(
                    url_for(
                        "modify_review",
                        teacher_id=teacher_id,
                        review_id=review_id,
                        modify_type=1,
                    )
                )
            return redirect(url_for("teacher_profile", teacher_id=teacher_id))
        elif modify_type == "2":  # Cancellation
            db.update_review(review_id)
            return redirect(url_for("teacher_profile", teacher_id=teacher_id))

    result = db.get_teacher_by_id(teacher_id)
    return render_template(
        "manual_review.html", teacher_id=teacher_id, review_id=review_id, result=result
    )


if __name__ == "__main__":
    app.run(debug=True)
