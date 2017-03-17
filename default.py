# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

# -------------------------------------------------------------------------
# This is a sample controller
# - index is the default action of any application
# - user is required for authentication and authorization
# - download is for downloading files uploaded in the db (does streaming)
# -------------------------------------------------------------------------


def index1():
    """
    lets users login or logout
    """

    return dict()

def index():
    """
    lets users login or logout
    """
    
    if(request.env.request_method == "POST"):
        numclasses = db.executesql('SELECT * FROM classes WHERE title=\'' + str(request.vars.cltitle) + '\';')
        if len(numclasses) == 0: 
            db.classes.insert(user_id= auth.user_id, title=request.vars.cltitle)
            clsses = db.executesql('SELECT * FROM classes WHERE user_id='
                                 + str(auth.user_id) +' AND title=\''
                                 + str(request.vars.cltitle) + '\';')

            clss = clsses[-1] #get last post if more posts
            cid = clss[0]
            db.classxuser.insert(classes_id = cid, user_id = auth.user_id)
        else: 
            response.flash = 'class already exists'
    elif(request.env.request_method == "PUT"):
        print "index"
        cls = db.executesql('SELECT * FROM classes WHERE title=\''
                      + str(request.vars.cltitle) + '\';')
        print cls
        clid = cls[0][0]
        print clid
        db.classxuser.insert(classes_id=clid,
                  user_id= auth.user_id)
    
    # for development purposes only:
    clses = []
    if auth.user_id == None:
        classes = []
    else: 
        #classes = db.executesql('SELECT * FROM classxuser WHERE user_id='+ str(auth.user_id) +';')
        classes = db(db.classxuser.user_id == auth.user_id).select()
        clses = []
        for c in classes:
            print c
            classRows = db(db.classes.id == c.classes_id).select()
            for cls in classRows:
                clses.append(cls)
    id = auth.user_id
    
    posts = get_posts()
    # most recent post:
    last_post = posts.first()
    # oldest post:
    first_post = posts.last()
    # number of posts:
    post_count = len(posts)
    
    classesTest = db(db.classes.user_id == auth.user_id).select()
    
    
    return dict(posts=posts,last_post=last_post, first_post=first_post, post_count=post_count, classes = clses) 

def get_posts():
    """get posts, in reverse chronological order"""
    return db(db.post).select().sort(lambda p: p.updated_on, reverse=True)

def classes():
    classes_id = request.args(0)
    postsTest = db(db.classxpost.classes_id == classes_id).select()
    prows, urows =[],[]
    for tpost in postsTest: # get rows aka posts for class 
        postrow = db(db.post.id == tpost.post_id).select()
        for prow in postrow: 
            # gets user row 
            urow = db(db.auth_user.id == prow.user_id).select()
            # gets post info 
            prows.append(prow)
            for u in urow: # gets user info 
                urows.append(u)
    users = db(db.classxuser.classes_id == classes_id).select()
    hangout_names = []
    for user in users:
        user_row = db(db.auth_user.id == user.user_id).select()
        for u in user_row:
            d =  dict()
            d['id'] = u.email
            d['invite_type'] = 'EMAIL'
            hangout_names.append(d)
    return dict(classes_id = classes_id, posts = prows, users = urows, hangout_names = hangout_names)    
  
def posts():
    classes_id = request.args(0)
    post_id = request.args(1)
    comTest = db(db.postxcomment.post_id == post_id).select()
    crows, urows = [],[]
    original_post = db(db.post.id == post_id).select()
    post = []
    for p in original_post:
        post.append(p)
    for tcom in comTest: # get rows aka posts for class 
        comrow = db(db.comment.id == tcom.comment_id).select()
        for crow in comrow: 
            # gets user row 
            urow = db(db.auth_user.id == crow.user_id).select()
            # gets post info 
            crows.append(crow)
            for u in urow: # gets user info 
                urows.append(u)
    return dict(post= post[0], classes_id = classes_id, post_id= post_id, users = urows, comments = crows) 

@auth.requires_login()
def create_post():
    cid = request.args(0)
    isImg = False
    isVid = False

    post_form = FORM(
        INPUT(_name='post_subj',_type='text'),
        INPUT(_name='post_cont',_type='text'),
        INPUT(_name='post_image',_type='file'),
        INPUT(_name='post_video',_type='file')
    )
    if post_form.accepts(request.vars,formname='post_form'):
        pid = 0
        
        if not post_form.vars.post_image == "":
            isImg = True
        if not post_form.vars.post_video == "":
            isVid = True

        if isVid and isImg:
            img = db.post.image.store(post_form.vars.post_image.file, post_form.vars.post_image.filename)
            vid = db.post.video.store(post_form.vars.post_video.file, post_form.vars.post_video.filename)
            pid = db.post.insert(video=vid, image=img, post_subject=post_form.vars.post_subj, post_content=post_form.vars.post_cont)
        elif isVid and not isImg:
            vid = db.post.video.store(post_form.vars.post_video.file, post_form.vars.post_video.filename)
            pid = db.post.insert(video=vid, post_subject=post_form.vars.post_subj, post_content=post_form.vars.post_cont)
        elif not isVid and isImg:
            img = db.post.image.store(post_form.vars.post_image.file, post_form.vars.post_image.filename)
            pid = db.post.insert(image=img, post_subject=post_form.vars.post_subj, post_content=post_form.vars.post_cont)
        else:
            pid = db.post.insert(post_subject=post_form.vars.post_subj, post_content=post_form.vars.post_cont)

        db.classxpost.insert(classes_id = cid, post_id = pid)
    return dict(classes_id = cid, post_form = post_form)

@auth.requires_login()
def edit_post():
    """form for posting a  new comment"""
    classes_id = request.args(0)
    post_id = request.args(1)
    post = db.post[request.args(1)]
    if not(post and post.user_id == auth.user_id):
        redirect(URL('index'))
    form = SQLFORM(db.post, post, deletable = True,
                 labels= {'post_subject': "Subject", 'post_content': "Comment", 'image': "Image", 'video': "Video"},
                 showid= False,
                 submit_button = 'Update your post',
                  )
    if form.process(keepvalues=True).accepted:
       response.flash = 'post accepted'
       #redirect(URL('default', 'classes', args = [classes_id]))

    elif form.errors:
       response.flash = 'please complete your post'
    else:
       response.flash = 'please post your post'
    
    return dict(classes_id=classes_id, post_id=post_id, form=form)

@auth.requires_login()
def create_comment():
    cid = request.args(0)
    pid = request.args(1)
    isImg = False
    isVid = False

    com_form = FORM(
        INPUT(_name='com_subj',_type='text'),
        INPUT(_name='com_cont',_type='text'),
        INPUT(_name='com_image',_type='file'),
        INPUT(_name='com_video',_type='file')
    )
    if com_form.accepts(request.vars,formname='com_form'):
        comid = 0
        
        if not com_form.vars.com_image == "":
            isImg = True
        if not com_form.vars.com_video == "":
            isVid = True

        if isVid and isImg:
            img = db.comment.image.store(com_form.vars.com_image.file, com_form.vars.com_image.filename)
            vid = db.comment.video.store(com_form.vars.com_video.file, com_form.vars.com_video.filename)
            comid = db.comment.insert(video=vid, image=img, comment_subject=com_form.vars.com_subj, comment_content=com_form.vars.com_cont)
        elif isVid and not isImg:
            vid = db.comment.video.store(com_form.vars.com_video.file, com_form.vars.com_video.filename)
            comid = db.comment.insert(video=vid, comment_subject=com_form.vars.com_subj, comment_content=com_form.vars.com_cont)
        elif not isVid and isImg:
            img = db.commet.image.store(com_form.vars.com_image.file, com_form.vars.com_image.filename)
            comid = db.comment.insert(image=img, comment_subject=com_form.vars.com_subj, comment_content=com_form.vars.com_cont)
        else:
            comid = db.comment.insert(comment_subject=com_form.vars.com_subj, comment_content=com_form.vars.com_cont)

        db.postxcomment.insert(post_id = pid, comment_id = comid)
    return dict(classes_id = cid, post_id = pid, com_form = com_form)

@auth.requires_login()
def edit_comment():
    """form for posting a  new comment"""
    classes_id = request.args(1)
    post_id = request.args(2)
    comm = db.comment[request.args(0)]
    if not(comm and comm.user_id == auth.user_id):
        redirect(URL('index'))
    form = SQLFORM(db.comment, comm, deletable = True,
                 labels= {'comment_subject': "Subject", 'comment_content': "Comment", 'image': "Image", 'video': "Video"},
                 showid= False,
                 submit_button = 'Update your comment',
                  )
    if form.process(keepvalues=True).accepted:
       response.flash = 'comment accepted'
       #redirect(URL('default', 'classes', args = [classes_id]))

    elif form.errors:
       response.flash = 'please complete your comment'
    else:
       response.flash = 'please post your comment'
    
    return dict(classes_id=classes_id, post_id=post_id, form=form)


@auth.requires_login()
def add_class():
    print "add class"
    if(request.env.request_method == "POST"):
        print request.vars.cltitle
        cls = db(db.classes.title == request.vars.cltitle).select()
        """cls = db.executesql('SELECT * FROM classes WHERE title=\''
                      + str(request.vars.cltitle) + '\';')"""
        print cls
        if cls:
            clarr=[]
            for c in cls:
                clarr.append(c)
            #clid = cls[0][0]
            print clarr
            clid=clarr[0].id
            print clid
            #print clid
            db.classxuser.insert(classes_id=clid,
                      user_id= auth.user_id)
        else:
            response.flash = "class does not exist"
    return dict()
@auth.requires_login()
def create_class():

    return dict()

def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    http://..../[app]/default/user/bulk_register
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    also notice there is http://..../[app]/appadmin/manage/auth to allow administrator to manage users
    """
    return dict(form=auth())


@cache.action()
def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)

def link(): 
    return response.download(request,db,attachment=False)

