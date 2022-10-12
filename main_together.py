import csv
import datetime

from flask import Flask, render_template, redirect
####################
import json
import os
from flask import Flask, render_template, redirect, request
from werkzeug.utils import secure_filename
from flask_uploads import UploadSet, configure_uploads, IMAGES
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import SubmitField, StringField, SelectMultipleField, widgets
####################
from wtforms.validators import DataRequired
from werkzeug.utils import secure_filename
from werkzeug.datastructures import  FileStorage

from data import db_session
from data import file_loader
from data.Memes import Meme
from data.Users import User, RegisterForm
from data.Avatars import Avatar

####################
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
app.config['UPLOADED_PHOTOS_DEST'] = os.path.join(basedir, 'static/User')
photos = UploadSet('photos', IMAGES)
configure_uploads(app, photos)
# patch_request_class(app)
db_session.global_init("db/probnik.db")
session = None
curent_user = None
##########################################################################
categories = [('pol', 'Политика'), ('int', 'Интеллектуальные'),
              ('black', 'Черный юмор'), ('posti', 'Постирония'),
              ('kin', 'Кино'), ('games', 'Игры'),
              ('seleb', 'Знаменитости'),
              ('bai', 'Баяны'), ('rest', 'Просто кекес')]
curent_categories = []


class Comms(FlaskForm):
    com = StringField('Type your comment', validators=[DataRequired()])
    submit = SubmitField('Send')

##########################################################################
class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

##########################################################################
class Sort(FlaskForm):
    example = MultiCheckboxField('Label', choices=categories)


def update_lvl():
    global lvl
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == session).first()
    if user.lvl > 10:
        lvl = 10
    else:
        lvl = user.lvl


def get_avatar():
    avatar_filename = 'noname.jpg'
    db_sess = db_session.create_session()
    for ava in db_sess.query(Avatar).filter(Avatar.user_id == session):
        avatar_filename = ava.filename
    return avatar_filename

def another_avatar(id):
    avatar_filename = 'noname.jpg'
    db_sess = db_session.create_session()
    for ava in db_sess.query(Avatar).filter(Avatar.user_id == id):
        avatar_filename = ava.filename
    return avatar_filename


class UploadForm(FlaskForm):
    photo = FileField(validators=[FileAllowed(photos, 'Image only!'),
                                  FileRequired('File was empty!')])
    submit = SubmitField('Заменить')


class UploadMemeForm(FlaskForm):
    photo = FileField(validators=[FileAllowed(photos, 'Image only!'),
                                  FileRequired('File was empty!')])
    about = StringField('Подпись к мему', validators=[DataRequired()])
    category = SelectMultipleField(u'Категория мема', choices=categories)
    submit = SubmitField('Запостить')



def main():
    pass


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    global session
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация', form=form, message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация', form=form,
                                   message="Такой пользователь уже есть")
        user = User(name=form.name.data, email=form.email.data, nickname=form.nickname.data, surname=form.surname.data,
                    region=form.region.data)
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        file_loader.region_picture(form.region.data, user.id)
        global curent_user
        curent_user = user
        session = user.id
        update_lvl()
        return redirect('/feed')
        ##############

        ############
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/', methods=['GET', 'POST'])
@app.route('/1', methods=['GET', 'POST'])
def login():
    global session, lvl
    form = RegisterForm()
    if request.method == 'POST':
        if request.form.get('action') == 'new_user':
            return redirect('/register')
        elif request.form.get('action') == 'log':
            email = form.email.data
            pas = form.password.data
            db_sess = db_session.create_session()
            user = db_sess.query(User).filter(User.email == email).first()
            if user:
                if user.check_password(pas):
                    #######
                    global curent_user
                    curent_user = user
                    session = user.id
                    update_lvl()
                    ########
                    return redirect('/profile')
                else:
                    return render_template('login.html', title='Вход в систему', form=form,
                                           message='Неверный пароль')
            else:
                return render_template('login.html', title='Вход в систему', form=form,
                                       message='Такого пользователя нет')
    return render_template('login.html', title='Вход в систему', form=form)


@app.route('/feed', methods=['GET', 'POST'])
def feed():
    fe = []
    form = Comms()
    sor = Sort()
    mem = None
    ##########################################################################
    db_sess = db_session.create_session()
    ##########################################################################
    global curent_user, session, categories, curent_categories
    cats = [j for i, j in categories]
    if request.method == 'POST':
        if request.form.get('action'):
            mem = db_sess.query(Meme).filter(Meme.id == int(request.form.get('action'))).first()
            user = db_sess.query(User).filter(User.id == session).first()
            if f'i {session} i' not in mem.likers:
                mem.likes = mem.likes + 1
                mem.likers += f'i {session} i'
                user.liked += f'{mem.id},'
            db_sess.commit()
        elif request.form.get('comment'):
            mem = db_sess.query(Meme).filter(Meme.id == int(request.form.get('comment'))).first()
            with open('static/comments.csv', 'r', encoding='utf8') as file:
                inf = csv.DictReader(file, delimiter=';')
                e = sorted(inf, key=lambda x: x['time'])
                com = [i for i in e]
            com.append({'user_nick': curent_user.nickname, 'meme_id': mem.id, 'comment': form.com.data,
                        'time': datetime.date.today()})
            form.com.data = ''
            with open('static/comments.csv', 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=list(com[0].keys()), delimiter=';')
                writer.writeheader()
                for d in com:
                    writer.writerow(d)
        elif request.form.get('sort'):
            curent_categories = sor.example.data


    if not curent_categories:
        for mem in db_sess.query(Meme).all():
            with open('static/comments.csv', 'r', encoding='utf8') as file:
                inf = csv.DictReader(file, delimiter=';')
                com = [i for i in inf if i['meme_id'] == f'{mem.id}']
            user = db_sess.query(User).filter(User.id == mem.user_id).first()
            new = {'way': mem.way, 'about': mem.about, 'id': mem.id, 'likes': mem.likes, 'comments': com,
               'av': another_avatar(user.id), 'nick': user.nickname, 'us_id': int(user.id), 'act': session == user.id}
            fe.append(new)
    else:
        for mem in db_sess.query(Meme).filter(Meme.category.in_(curent_categories)):
            with open('static/comments.csv', 'r', encoding='utf8') as file:
                inf = csv.DictReader(file, delimiter=';')
                com = [i for i in inf if i['meme_id'] == f'{mem.id}']
            user = db_sess.query(User).filter(User.id == mem.user_id).first()
            new = {'way': mem.way, 'about': mem.about, 'id': mem.id, 'likes': mem.likes, 'comments': com,
               'av': another_avatar(user.id), 'nick': user.nickname, 'us_id': int(user.id), 'act': session == user.id}
            fe.append(new)
    adv = ['/static/adv1.png', '/static/adv2.png']
    return render_template('feed1.html', title='Лента новостей', fe=fe, adv=adv, avatar=get_avatar(), se=session, form=form,
                           cat=cats, sort=sor)


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    global lvl, session
    form = UploadForm()
    if form.validate_on_submit():
        razr = form.photo.data.filename.split('.')[-1]
        with open("data/info.json") as file:
            data = json.load(file)
        n = data['ava_num']
        data['ava_num'] = n + 1
        with open("data/info.json", 'w') as file:
            json.dump(data, file)
        fn = f'{n + 1}.{razr}'
        photos.save(form.photo.data, name=fn)
        db_sess = db_session.create_session()
        ava = Avatar(filename=fn, user_id=session)
        db_sess.add(ava)
        db_sess.commit()
    else:
        file_url = None
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == session).first()
    with open("data/info.json") as file:
        data = json.load(file)
    ln = data[f"{lvl}"]
    meme_id_data = []
    for mem in db_sess.query(Meme).filter(Meme.user_id == session):
        meme_id_data.append((mem.id, mem.about, mem.way))

    return render_template('profile1.html', title='Лента новостей', avatar=get_avatar(), form=form, name=user.name,
                           surname=user.surname, id=session, nick=user.nickname, mail=user.email, lvl=lvl, lvl_name=ln,
                           memes=meme_id_data)


@app.route('/stranger_profile/<int:id>', methods=['GET', 'POST'])
def stranger_profile(id):
    global lvl, session
    db_sess = db_session.create_session()
    other_user = db_sess.query(User).filter(User.id == id).first()
    with open("data/info.json") as file:
        data = json.load(file)
    ln = data[f"{other_user.lvl}"]
    meme_id_data = []
    for mem in db_sess.query(Meme).filter(Meme.user_id == id):
        meme_id_data.append((mem.id, mem.about, mem.way))
    return render_template('profile2.html', title='Лента новостей', avatar=get_avatar(),
                           another_avatar=another_avatar(id), name=other_user.name,
                           id=str(other_user.id), nick=other_user.nickname, lvl=str(other_user.lvl), lvl_name=ln,
                           memes=meme_id_data)


@app.route('/create', methods=['GET', 'POST'])
def creator():
    global lvl
    form = UploadMemeForm()
    if request.method == 'POST':
        razr = form.photo.data.filename.split('.')[-1]
        filename = f'Memes/{session}_{lvl}.{razr}'
        photos.save(form.photo.data, name=filename)
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.id == session).first()
        user.lvl += 1
        mem = Meme(about=form.about.data, category=request.form['category'], way=filename, user_id=session)
        db_sess.merge(user)
        db_sess.add(mem)

        db_sess.commit()
        update_lvl()
        return redirect('/profile')
    return render_template('redactor.html', avatar=get_avatar(), form=form)


@app.route('/best', methods=['GET', 'POST'])
def best():
    global session
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == session).first()
    fe = []
    k = user.liked.split(',')
    if k[-1] == '':
        k.pop(-1)
    for mem in db_sess.query(Meme).filter(Meme.id.in_(k)):
        auser = db_sess.query(User).filter(User.id == mem.user_id).first()
        new = {'way': mem.way, 'about': mem.about, 'id': mem.id,
               'av': another_avatar(auser.id), 'nick': auser.nickname, 'us_id': int(auser.id), 'act': session == mem.user_id}
        fe.append(new)
    print(fe)
    return render_template('best.html', title='Лента новостей', fe=fe, avatar=get_avatar(), se=session)

if __name__ == '__main__':
    main()
