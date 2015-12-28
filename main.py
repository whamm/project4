
import os
import webapp2
import jinja2
import cgi
import urllib
from google.appengine.api import users
from google.appengine.ext import ndb

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)

class Handler(webapp2.RequestHandler):
    def write(self, *args, **kwargs):
        self.response.out.write(*args, **kwargs)

    def render_str(self, template, **kwargs):
        t = jinja_env.get_template(template)
        return t.render(kwargs)

    def render(self, template, **kwargs):
        self.write(self.render_str(template, **kwargs))

HtmlDoc = open('templates\wallcontent.html')
HTML_TEMPLATE = HtmlDoc.read()

DEFAULT_WALL = 'Public'

def wall_key(wall_name=DEFAULT_WALL):
  return ndb.Key('Wall', wall_name)

class Author(ndb.Model):

  identity = ndb.StringProperty(indexed=True)
  name = ndb.StringProperty(indexed=False)
  email = ndb.StringProperty(indexed=False)

class Post(ndb.Model):

  author = ndb.StructuredProperty(Author)
  content = ndb.StringProperty(indexed=False)
  date = ndb.DateTimeProperty(auto_now_add=True)


class Wall(webapp2.RequestHandler):
  def get(self):
    wall_name = self.request.get('wall_name',DEFAULT_WALL)
    if wall_name == DEFAULT_WALL.lower(): wall_name = DEFAULT_WALL

    posts_query = Post.query(ancestor = wall_key(wall_name)).order(-Post.date)

    posts =  posts_query.fetch()
    user = users.get_current_user()
    if user:
        url = users.create_logout_url(self.request.uri)
        url_linktext = 'Logout'
        user_name = user.nickname()
    else:
        url = users.create_login_url(self.request.uri)
        url_linktext = 'Login'
        user_name = 'Anonymous Poster'

    posts_html = ''
    for post in posts:
      if user and user.user_id() == post.author.identity:
        posts_html += '<div><h3>(You) ' + post.author.name + '</h3>\n'
      else:
        posts_html += '<div><h3>' + post.author.name + '</h3>\n'

      posts_html += 'wrote: <blockquote>' + cgi.escape(post.content) + '</blockquote>\n'
      posts_html += '</div>\n'

    sign_query_params = urllib.urlencode({'wall_name': wall_name})

    rendered_HTML = (HTML_TEMPLATE) .format(sign_query_params, cgi.escape(wall_name), user_name,
                                    url, url_linktext, posts_html)

    self.response.out.write(rendered_HTML)

class Posts(webapp2.RequestHandler):
  def post(self):
    wall_name = self.request.get('wall_name',DEFAULT_WALL)
    post = Post(parent=wall_key(wall_name))
    if users.get_current_user():
      post.author = Author(
            identity=users.get_current_user().user_id(),
            name=users.get_current_user().nickname(),
            email=users.get_current_user().email())
    else:
      post.author = Author(
            name='anonymous@anonymous.com',
            email='anonymous@anonymous.com')
    if post.content is None:
        post.content = "Please enter a comment"
    else:
        post.content = self.request.get('content')
    post.put()
    self.redirect('/wall')

class MainHandler(Handler):
    def get(self):
        self.render("content.html")

app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/sign', Posts),
    ('/wall', Wall)
], debug=True)
