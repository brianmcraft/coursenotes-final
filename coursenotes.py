#import libraries
import cgi
import urllib
import os
import jinja2
import webapp2
import time
from google.appengine.api import users
from google.appengine.ext import ndb

#creates file folder, then initiates instance for jinja environment
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)


#set parent keys to include entities in same entity groups
DEFAULT_CARDLIST_NAME = 'default_cardlist'
DEFAULT_COMMENTS_NAME = 'default_comments'

def cardlist_key(cardlist_name=DEFAULT_CARDLIST_NAME):
    """Constructs a Datastore key for a cardlist entity.
    We use cardlist_name as the key.
    """
    return ndb.Key('Cardlist', cardlist_name)

def comments_key(comments_name=DEFAULT_COMMENTS_NAME):
    """Constructs a Datastore key for a comments entity.
    We use comments_name as the key.
    """
    return ndb.Key('Comments', comments_name)


#entity classes
class Card(ndb.Model):
  """A main model for representing a card."""
  title = ndb.StringProperty(indexed=True)
  content = ndb.TextProperty(indexed=False)
  date = ndb.DateTimeProperty(auto_now_add=True)

class Author(ndb.Model):
  """Sub model for representing an author."""
  identity = ndb.StringProperty(indexed=True)
  name = ndb.StringProperty(indexed=False)
  email = ndb.StringProperty(indexed=False)

class Comment(ndb.Model):
  """A main model for representing an individual comment."""
  author = ndb.StructuredProperty(Author)
  date = ndb.DateTimeProperty(auto_now_add=True)
  content = ndb.StringProperty(indexed=False)


#validation functions
def empty_identification(name, email):
  if name == "" and email == "":
    return True


#handlers act as gatekeepers that direct you to the right path
class Handler(webapp2.RequestHandler):
  def write(self, *a, **kw):
    self.response.out.write(*a, **kw)

  #finds file template and passes in parameters
  def render_str(self, template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

  #sends template created back to browser
  def render(self, template, **kw):
    self.write(self.render_str(template, **kw))


class MainHandler(Handler):
  def get(self):
    #use Google Users API to identify user
    user = users.get_current_user()
    if user:
        greeting = ('Welcome, %s (<a href="%s">sign out</a>)!' %
                    (user.nickname(), users.create_logout_url('/')))
    else:
        greeting = ('<a href="%s">Sign in or register</a>.' %
                    users.create_login_url('/'))

    #get the cards
    query_cards = Card.query().order(Card.date)
    cards = query_cards.fetch()

    #get the comments
    query_comments = Comment.query().order(-Comment.date)
    comments = query_comments.fetch()
    
    #build the webpage using jinja2 for variable substitution
    self.render("coursenotes.html",
      cards=cards,
      comments=comments,
      greeting=greeting)


    #logging messages for troubleshooing
    print '##### total cards fetched'
    print len(cards)
    print
    print '##### total comments fetched'
    print len(comments)
    print
    

  def post(self):
    #set variables for substitution
    content = self.request.get('content')
    name = self.request.get('name')
    email = self.request.get('email')

    #determine author by checking Google user,
    #then validating for empty ID fields
    if users.get_current_user():
      author = Author(
        identity = users.get_current_user().user_id(),
        name = users.get_current_user().nickname(),
        email = users.get_current_user().email())
    elif empty_identification(name, email):
      author = Author(
        identity = "Anonymous",
        name = "Anonymous",
        email = "Anonymous")
    else:
      author = Author(
        identity = "Anonymous",
        name = self.request.get('name'),
        email = self.request.get('email'))

    #create entity in Google Datastore based on user's data
    if content and author:
      comment = Comment(content=content, author=author)
      comment.put()
      time.sleep(.1)
      self.redirect('/#comments')
    else:
      self.redirect('/')


app = webapp2.WSGIApplication([
  ('/', MainHandler)
  ], debug = True)




#data for one-time insert into Google Datastore
#stage 1, worksession 1 cards
card1 = Card(title = 'Reflection',
  content = '''My browser displays content fetched from a server via the internet over http or secure http. That content is wrapped up in HTML. HTML is  structured with a series of elements, most of which contain an opening and closing tag. Tags, and their attributes, apply human-centered styling to simple content (like bold, italics, or an image). Tags can be grouped into inline and block tags, the latter of which create containers that hold other elements.''')
card2 = Card(title = 'The Basics',
  content = '''<p>Reference <a href="http://www.w3schools.com/default.asp">W3 Schools</a> and <a href="http://www.google.com">Google</a> for just about anything.</p>
            <p>Element = opening tag + content + closing tag</p>
            <p>HTML Attributes = belong to tags<br>
              <span class="italic">e.g. &lt;tag attribute="value"&gt;contents&lt;/tag&gt;</span>
            <p>One great example would be a link to another site <a href="http://www.udacity.com">like this using the   <span class="bold">href</span> attribute</a> or an image using the <span class="bold">src</span> attribute:<br><br>
              <img class="image-center-responsive" src="http://thisisinfamous.com/wp-content/uploads/2015/01/jurassic-park-logo.jpg" alt="Jurassic Park gates"><br></p>
            <p>Just don't forget your <span class="bold">alt</span> tag; it will make someone's life better when viewing your page.</p>
            <p>Or using <span class="bold">iframe</span> to embed a video like this:<p>
            <div class="video-center-embed">
              <iframe width="420" height="315" src="https://www.youtube.com/embed/Bim7RtKXv90?rel=0" allowfullscreen></iframe>
            </div>''')
card3 = Card(title = 'Void Tags',
  content = '''<p>No content, so no closing tag<br>
              <span class="italic">e.g. Images &lt;img&gt;</span> or <span class="italic">Break &lt;br&gt;</span>
            </p>''')
card4 = Card(title = 'Inline versus Block',
  content = '''<p>Inline = Just end the line and wrap to the next<br>
          <span class="italic">e.g. Break &lt;br&gt;</span></p>
            <p>Block = Create invisible box that can have height and width<br>
          <span class="italic">e.g. Paragraph &lt;p&gt;</span></p>''')
card5 = Card(title = 'Container Tags',
  content = '''<p>Hold other elements<br>
          <span class="italic">e.g. Span &lt;span&gt; (inline)</span> or <span class="italic">Div &lt;div&gt; (block)</span></p>''')
card6 = Card(title = 'Lists and Menus',
  content = '''<p>Add <a href="http://www.w3schools.com/html/html_lists.asp">ordered, unordered, or HTML lists</a> for bullets, numbers/alpha, or menus; use CSS for styling to create tabbed menus or use alternative images for bullet points.</p>
            <p>Lists can be nested; here,the nested list is part of a list item from the parent list:</p>
            <p class="code">&lt;ul&gt;Parent List<br>
            &nbsp;&nbsp;&lt;li&gt;First Item&lt;/li&gt;<br>
            &nbsp;&nbsp;&lt;li&gt;Second Item&lt;/li&gt;<br>
            &nbsp;&nbsp;&lt;li&gt;Third Item with a nested list<br>
            &nbsp;&nbsp;&nbsp;&nbsp;&lt;ul&gt;Nested List<br>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&lt;li&gt;Nested First Item&lt;/li&gt;<br>
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&lt;li&gt;Nested Second Item&lt;/li&gt;<br>
            &nbsp;&nbsp;&nbsp;&nbsp;&lt;/ul&gt;<br>
            &nbsp;&nbsp;&lt;/li&gt;<br>
            &nbsp;&nbsp;&lt;li&gt;Fourth Item&lt;/li&gt;<br>
            &lt;/ul&gt;</p>''')
card7 = Card(title = 'HTML Document Structure',
  content = '''<p>Simplified with HTML5, HTML documents follow this basic structure (but not needed for codepen...codepen just needs the typical &lt;body&gt; content):<br>
            <p class="code">&lt;!DOCTYPE HTML&gt; = doctype<br>
              &lt;html&gt; = opening html tag<br>
              &lt;head&gt; = metadata like js and css<br>
              &lt;title&gt; = title for browser window<br>
              &lt;body&gt; = content of doc</p>''')

#stage 1, worksession 2 cards
card8 = Card(title = 'Reflection',
  content = '''One word: boxify. With everything in HTML structured in rectangular boxes (even seemingly non-rectangular items), you can easily build or break-down a webpage into small, understandable parts. Classes provide the labeling for the boxes in your HTML structure, while CSS provides the styling.''')
card9 = Card(title = 'Definitions',
  content = '''<dl>
            <dt><span class="bold">HTML</span> (HyperText Markup Language)</dt>
              <dd>Standard markup language used to create web pages.</dd>
            <dt><span class="bold">CSS</span> (Cascading Style Sheets)</dt>
              <dd>Style sheet language used for describing the look and formatting of a document written in a markup language.</dd>
            <dt><span class="bold">DOM</span> (Document Object Model)</dt>
              <dd>Cross-platform and language-independent convention for representing and interacting with objects in HTML (and other markup languages). The nodes of every document are organized in a branching tree structure, called the DOM tree</dd>
          </dl>''')
card10 = Card(title = 'Boxify',
  content = '''<p>Everything is boxes; so when exploring a webpage, break it down into boxes that become divs and other elements</p>''')
card11 = Card(title = 'Good to Know',
  content = '''<p>HTML is the structure, CSS is the style, and JS is the interactive</p>
          <p>Create an HTML comment that is for people but not computers with &lt;!-- content --&gt;</p>
          <p>Use corresponding indentation to create an easy-to-follow, easy-to-modify, and easy-to-apply-CSS/JS webpage</p>
          <p>Use the class attribute to provide labeling to your divs; this will provide additional benefits when working with CSS and JS</p>''')
card12 = Card(title = 'Browser Tools',
  content = '''<p>You can inspect elements of a page using Developer Tools in Chrome<br>
            <ul>
              <li><span class="italic">Alt+Cmd+I to open the panel, </span>or</li>
              <li><span class="italic">Right-click and choose Inspect Element on a specific element</span></li>
            </ul>
          <p>From the style panel in Developer Tools, you can (temporarily) alter the CSS for specific elements</p>
          <p>Developer tools also includes a cool feature for resizing the page to meet different form factors for responsive design testing!</p>''')

#stage 1, worksession 3 cards
card13 = Card(title = 'Reflection',
  content = '''<p>CSS is a powerful tool for creating an experience around your HTML structure. It's important to follow a paradigm within your styling (this is where style guides are important) and to leverage classes to avoid unnecessary repetition as much as possible. Flexbox only works on modern browser versions but creates a simple way to stack divs next to each other.</p>''')
card14 = Card(title = 'Style Guides and Resources',
  content = '''<p><a href="http://udacity.github.io/frontend-nanodegree-styleguide/">Udacity Nanodegree</a></p>
        <p><a href="http://www.google.com/design/spec/material-design/introduction.html">Google Material Design</a></p>
        <p><a href="http://www.google.com/fonts/">Google Fonts</a></p>''')
card15 = Card(title = 'CSS Tags',
  content = '''<p class="code">tag name {<br><br>
              attribute:value<br><br>
              }</p>
          <p><span class="italic">You can do the same with classes for less repetition; instead of the tag name, use .class-name</span></p>
          <p>Use attribute:value pairs (each on their own line for clarity) to apply the rules to the tag or class specified (the selector)</p>
          <p>In CSS, code comments begin with /* and end with */</p>
          <p>Example of separating structure from presentation: replace emphasis and bold HTML tags with span tags that have an emphasis or bold class assigned; then in the CSS, define the rules for those classes to add italics via font-style or bold via font-weight</p>
          <p>Browsers use default style sheets for common elements like h1/h2/h3/etc. so you can use those tags and apply style/spacing to your content without the need for additional CSS</p>''')
card16 = Card(title = 'The Box Model',
  content = '''<p><a href="http://www.w3schools.com/css/box-model.gif">Visualizing the HTML element</a></p>
          <p><span class="italic">Box sizing</span></p>
            <p>Each HTML element has 4 components: margin, border, padding, content.</p>
            <p>To adjust sizing:</p>
            <ol>
              <li>Set sizes in terms of percents instead of pixels</li>
              <li>Set the box-sizing attribute = border-box for each element. Newer standard, so probably need to explicit define browser rules (webkit, moz, ms)</li>
            </ol>
          <p><span class="italic">Box positioning</span></p>
            <p>Divs are block (vs. inline) elements so they automaticaly take the full width of the page.</p>
            <p>Adding the rule "display: flex" to the parent div element in CSS allows them to sit next to each other (if the child elements have been given a size less than the automatic 100%). This uses an approach called <a href="http://css-tricks.com/snippets/css/a-guide-to-flexbox/">flexbox</a>; allowable in modern browsers only.</p>''')
card17 = Card(title = 'Code, Test, Refine',
  content = '''<ol>
            <li>Look for natural boxes</li>
            <li>Look for repeated styles and semantic elements</li>
            <li>Write your HTML</li>
            <li>Apply styles (from biggest on site to smallest on individual elements)</li>
            <li>Fix things</li>
            <li>Check for form factors (resize window, view in different browsers)</li>
          </ol>
          <p>Always <a href="http://validator.w3.org/#validate_by_input">verify your HTML</a> and <a href="http://jigsaw.w3.org/css-validator/#validate_by_input">your CSS</a> to check for errors or informational tips.</p>''')

#stage 2, worksession 1 cards
card18 = Card(title = 'Reflection',
  content = '''Computer science is based on simple arithmetic but extends into the highly theoretical. Computers are the universal machines that run programs, built with linguistic grammar seeking to remove ambiguity and verbosity. BNF showcases how to derive and complete expressions passed into the program.''')
card19 = Card(title = 'Computer Science Basics',
  content = '''<p>Computers are the universal machine (sound familiar, Alan Turing?) but only have a few routines themselves. They need programs to provide instructions for what to do and in what order.</p>
          <p>Computer languages created to prevent:</p>
          <ul>
            <li><span class="bold">Ambiguity</span> - in natural languages, individuals can interpret the same word or phrase completely differently (e.g. <span class="italic">biweekly</span> has two definitions: twice per week or every two weeks)</li>
            <li><span class="bold">Verbosity</span> - explaining a series of detailed instructions to a computer can happen in far fewer "words" than in natural languages</li>
          </ul>''')
card20 = Card(title = 'Backus-Naur Form (BNF)',
  content = '''<p>&lt;Non-Terminal&gt; --&gt; Replacement<br>
          Start with non-terminals, keep replacing until you hit all terminals through derivation</p>
          <ul>
            <li>Sentence = Subject Verb Object</li>
            <li>Subject = Noun</li>
            <li>Object = Noun</li>
            <li>Noun = I</li>
            <li>Noun = cookies</li>
            <li>Verb = like</li>
            <li>Derivation leads to "I like cookies"</li>
          </ul>
          <p>Recursive Grammar</p>
          <ul>
            <li>Expression --&gt; Expression Operator Expression</li>
            <li>Expression --&gt; Number</li>
          </ul>''')
card21 = Card(title = 'Additional CS Resources',
  content = '''<p><a href="https://www.udacity.com/wiki/cs101/resources">CS 101 Supplemental Resources</a></p>
          <p><a href="https://www.udacity.com/wiki/cs101/unit1-python-reference">Python Reference Guide, unit 1</a></p>''')

#stage 2, worksession 2 cards
card22 = Card(title = 'Reflection',
  content = '''Similar to CSS classes to apply styling to multiple HTML elements from one source, variables represent a named expression that can be evaluated or referenced by other variables within code. Using indexes or methods like ".find()" allow you to identify and evaluate string (or substring) variables in the context of your overall code.''')
card23 = Card(title = 'Writing Readable Code',
  content = '''<p><span class="italic">What is a variable?</span> A variable is a named representation of some expression; it defines "a" is "b". Variables can be used in their own assignment (e.g. days = days-1...when constantly re-evaluated, you get a countdown).</p>
          <p><span class="italic">What does it mean to assign a value to a variable?</span> Applying the definition of "b" to "a" is the assignment; similar to CSS classes or IDs, it allows for definitions to be made up front (where they can be easily changed in 1 location) but applied in multiple easy-to-understand uses throughout the code.</p>
          <p><span class="italic">What is the difference between math and programming for the "=" sign?</span> Algebraically, "=" means equality; in programming, "=" means assignment like a left-pointing arrow (take the expression value on the right side and use that anywhere you see the name on the left).</p>''')
card24 = Card(title = 'Python Playground',
  content = '''<p>Udacity has a python interpreter <a href="https://www.udacity.com/course/viewer#!/c-none/l-300029886/e-299271807/m-299271808">available here</a></p>''')
card25 = Card(title = 'Strings',
  content = '''<p>An index finds a portion of a string (e.g. the 2nd character)...the first character is at position 0</p>
          <p class="code"><span class="italic">string[n]</span> returns the nth character of the string</p>
          <p>An index subsequence can find multiple characters within a string...a few examples:</p>
          <p class="code"><span class="italic">string[n1:n2]</span> starts at the n1th character and evaluates to just before the n2nd character</p>
          <p class="code"><span class="italic">string[:]</span> starts at the beginning character and evaluates to the final character</p>
          <p class="code"><span class="italic">string[:-2]</span> starts at the beginning character and evaluates to just before the 2nd to last character</p>
          <p>Find method used to find strings in strings</p>
          <p class="code"><span class="italic">string1.find(string2)</span> finds string2 within string1 (precisely, it finds the position [number] within string1 where the first occurence of string2 exists unless you pass a position parameter)</p>''')

#stage 2, worksession 3 cards
card26 = Card(title = 'Reflection',
  content = '''Abstractly, functions are simply a tool for evaluating some inputs (or arguments) to produce some outputs. Leveraging functions allows a programmer to build small pieces of working code that can be combined with other pieces of working code to create bigger results. Practically, you define a function and the parameters it will accept, then perform some action (such as a return)...that's it.''')
card27 = Card(title = 'Functions',
  content = '''<p class="code">def function_name(arguments):<br>
          &nbsp;&nbsp;&nbsp;body<br>
          &nbsp;&nbsp;&nbsp;return output<br><br>
          print function_name(parameters_to_use)</p>
          <p>Define the function, then use the function</p>
          <p>Some variables, like strings and integers are <span class="italic">immutable</span>, meaning their value cannot be altered by any function</p>
          <p><a href="https://www.udacity.com/wiki/cs101/unit2-python-reference">Python Reference Guide, unit 2</a></p>
          <p><a href="https://www.udacity.com/wiki/cs101/unit-2">CS 101 Unit 2 full notes and quizzes</a></p>''')

#stage 2, worksession 4 cards
card28 = Card(title = 'Reflection',
  content = '''Your code can define alternative paths to follow by using comparison operators, logical statements (like if and or), and repetition statements (like while). Paired with our other constructs of variables and functions, we can technically write just about any program.''')
card29 = Card(title = 'Equality Comparisons',
  content = '''<p>Just like with arithematic statements, we can compare values to return Boolean results (True or False)</p>
          <p>Comparisons include:</p>
            <ul>
              <li>&lt;</li>
              <li>&gt;</li>
              <li>&lt;=</li>
              <li>&gt;=</li>
              <li>!= (not equal to)</li>
              <li>== (equal to)
                <ul>
                  <li>We use the double equals since single equals represents assignment</li>
                </ul>
              </li>
            </ul>
        <p>We can compare integers to integers, strings to strings, and in some cases, integers to strings...a few examples:</p>
        <p class="code">
          print 1 &lt; 2 #returns TRUE<br>
          print 5 &gt; 20 #returns FALSE<br>
          print 5 == 5 #returns TRUE<br>
          print "hello" == "hello" #returns TRUE<br>
          print 5 == '5' #returns FALSE<br>
          print 7 != 10 #returns TRUE
        </p>''')
card30 = Card(title = 'IF Statements',
  content = '''<p>"if" allows our code to make decisions on what to do based on the result of expressions tested</p>
          <p class="code">if &lt;test_expression&gt;:<br>
          &nbsp;&nbsp;&nbsp;block_to_evaluate_when_result_true<br><br>
          next_statement_to_evaluate_regardless_of_result</p>
          <p>This function takes the value of a number and returns the absolute value (if the number is negative, make it positive; either way, then return the number):</p>
          <p class="code">def absolute(x):<br>
          &nbsp;&nbsp;&nbsp;if x &lt; 0:<br>
          &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;x = -x<br>
          &nbsp;&nbsp;&nbsp;return x<br></p>
          <p>But it's better to close your if statements using else, to explicitly define what to do when the if result is false; this function returns the bigger of two numbers:</p>
          <p class="code">def bigger(x,y):<br>
          &nbsp;&nbsp;&nbsp;if x &gt; y:<br>
          &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;return x<br>
          &nbsp;&nbsp;&nbsp;else:<br>
          &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;return y<br></p>
          <p>The Boolean values True and False are not strings, so no quotes needed:</p>
          <p class="code">return True</p>''')
card31 = Card(title = 'OR Statements',
  content = '''<p>OR provides logical evaluation of two expressions to true or false but only evaluates what is needed to find true:</p>
          <ul>
            <li>If first expression is true, then "or" construct is true, and second expression is not evaluated</li>
            <li>If first expression is false, then "or" construct must evaluate second expression to take its value</li>
          </ul>''')
card32 = Card(title = 'While Loops',
  content = '''<p>Like an IF statement, the test expression is evaluated, and if true, the block is evaluated. However, with an IF statement, once the block has been evaluated, the code moves to the next statement outside of the IF. With WHILE, once the block has been evaluated, the code moves back to the test expression and repeats. The WHILE statement only ends (sending the code to the next statement) if the test expression evaluates to false.</p>
          <p>Use <span class="italic">break</span> to jump out of a while loop; leverage an if statement where, when true, the code to run is <span class="italic">break</span> which immediately moves to the code following the while loop.</p>
          <p>In this example, if the IF statement evaluates to true, hitting the break, then the code jumps out of the loop (skipping the second "some code") and moves straight to the "some code after the while loop":</p>
          <p class="code">while (something):<br>
          &nbsp;&nbsp;&nbsp;some code<br>
          &nbsp;&nbsp;&nbsp;if (something):<br>
          &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;break<br>
          &nbsp;&nbsp;&nbsp;some code<br>
          some code after the while loop<br></p>''')

#stage 2, worksession 5 cards
card33 = Card(title = 'Reflection',
  content = '''I can see how structured data like lists (and the methods/operations you can call upon them) open the door for more complex decision-making and problem solving. Loops, both while and for, represent the desire for efficiency in coding...less is more!''')
card34 = Card(title = 'Structured Data',
  content = '''<p>Strings are sequences of characters; Lists are sequences of anything (characters, numbers, even other lists)</p>
          <p>You can use an index on a list to return particular elements; you can also use multiple indexes if your list contains lists, for example:</p>
          <p class="code">beatles[3][0] will return the 1st element of the 4th element of a list named "beatles"</p>''')
card35 = Card(title = 'Mutation and Aliasing',
  content = '''<p><span class="italic">Mutation</span> - changing an element's values</p>
          <p><span class="italic">Aliasing</span> - referencing the same object through multiple assignments</p>
          <p>If the list [1,2,3] is assigned to p, and p is assigned to q, then changing the 2nd element of p (p[1] = 5), makes both p <span class="bold">and</span> q have the assignment of [1,5,3].</p>''')
card36 = Card(title = 'Other List Operations',
  content = '''<p><span class="italic">Append</span> - method (like .find) that mutates a list to include a new element at the end (that new element could be a reference to another list)</p>
          <p>Python has special syntax that operates like .append shown as +=, e.g. mylist += [3] is the same as mylist.append(3) but is not the same as mylist.append([3])</p>
          <p class = "code">mylist = [1,2]<br>
          mylist += [3] ---> [1,2,3]<br>
          mylist.append(3) ---> [1,2,3]<br>
          mylist.append([3]) ---> [1,2,[3]]<br>
          mylist + [3] ---> [1,2,3]</p>
          <p class="code">list.append(new_element)</p>
          <p><span class="italic">Addition</span> - operation like concatenation ("+") that creates a new list from other existing lists</p>
          <p class="code">list + list</p>
          <p><span class="italic">Length</span> - procedure operation (len) that determines the number of outer elements within a list (can also be used to count characters in a string)</p>
          <p class="code">len(list)</p>''')
card37 = Card(title = 'For Loops',
  content = '''<p>For loops iterate through each element in a given list, jumping out of the loop when all elements have been evaluated; each element in the list is assigned to the name variable below for each loop iteration:</p>
          <p class="code">for &lt;name&gt; in &lt;list&gt;:<br>
          &nbsp;&nbsp;&lt;block&gt;</p>
          <p><span class = "italic">Index</span> method invoked on a list provided a given value returns the first position of that value in the list (if the value is in the list; otherwise, error):</p>
          <p class="code">list.index(value)</p>
          <p><span class = "italic">In</span> operator returns true/false to determine if a value is in a list:</p>
          <p class="code">&lt;value&gt; in &lt;list&gt; will return True or False</p>
          <p><span class = "italic">Not In</span> operator returns true/false to determine if a value is <span class = "bold">not</span> in a list:</p>
          <p class="code">&lt;value&gt; not in &lt;list&gt; will return True or False</p>
          <p>Hold onto <a href="https://www.udacity.com/course/viewer#!/c-ud552-nd/l-3523729585/m-3772628708">this page</a> for generating HTML automatically</p>''')

#stage 3 cards
card38 = Card(title = 'Reflection',
  content = '''This stage introduced some powerful concepts around object oriented programming and the key is inheritance (much like our CSS classes and ids). The mini-projects, especially the final <span class="italic">Fresh Tomatoes</span> site demonstrated the ability to call existing code to create actions, interactive webpages, and more.''')
card39 = Card(title = 'Prereqs for programs in this stage',
  content = '''<p>If Statements</p>
            <p>Loops (<a href="http://learnpythonthehardway.org/book/ex33.html">helpful tutorials</a>)</p>
            <p>Functions (<a href="http://anh.cs.luc.edu/python/hands-on/3.1/handsonHtml/functions.html">helpful tutorials</a>)</p>''')
card40 = Card(title = 'Abstraction',
  content = '''<p>Abstraction allows us to focus on the programs we want to write by leveraging other components already created (such as the <a href="https://docs.python.org/2.7/library/index.html">Python Standard Library</a>)</p>
            <p>For example, I don't need to write a program to find the current time, I can just use <span class ="code">time.ctime()</span> after declaring <span class = "code">import time</span>, without having to even know how this standard function works.</p>''')
card41 = Card(title = 'Turtle (and Classes)',
  content = '''<p>Customizing your turtle</p>
          <ul>
            <li><a href="http://docs.python.org/2/library/turtle.html#turtle.shape">Changing turtle's shape</a></li>
            <li><a href="http://docs.python.org/2/library/turtle.html#turtle.color">Changing turtle's color</a></li>
            <li><a href="http://docs.python.org/2/library/turtle.html#turtle.speed">Changing turtle's speed</a></li>
          </ul>
        <p>A <span class = "italic">class</span>, like a class in CSS, groups items together. Here, a class can be initialized (brad = turtle.Turtle()) creating space in memory for a new instance. Then whatever has been assigned the class can call the functions within that class (.shape, .color, and so on).</p>
        <p>You can use a FOR loop <span class = "code">for i in range(1,5):</span> that can run the drawing commands a certain number of times (4, in this example); a safer alternative to WHILE loops with counters since you can never get into an infinite loop scenario.</p>
        <p>External Python packages <a href="https://pypi.python.org/pypi">listing</a></p>
        <p>Think of <span class = "italic">classes</span> as blueprints, containing basic information, and <span class = "italic">objects</span> as examples or instances of that blueprint</p>
        <p class = "bold">Simple Definitions</p>
        <p>A <span class = "italic">class</span> is a grouping of functions that can be accessed collectively. An <span class = "italic">instance of a class</span> is a defined object given the ability to call the functions of the class; multiple instances can exist simultaneously. Here's the benefit of OOP: you can take this class and create millions of individual instances (objects) that co-exist without interferring with each other.</p>
        <p><span class="italic">Libraries</span> are collections of <span class="italic">modules</span> that can be imported within your code; amplifies the tools at your disposal without having to write the code or even understand how it's working (like when we import "webbrowser" or "media" and can then call the classes within to create instances).</p>''')
card42 = Card(title = 'Movie Website',
  content = '''<p><a href="http://google-styleguide.googlecode.com/svn/trunk/pyguide.html">Google Python Style Guide</a></p>
          <p>Following the aforementioned style guide, classes should follow a proper case naming convention (e.g. class Movie)</p>
          <p><a href="https://www.udacity.com/course/viewer#!/c-ud645-nd/l-3567738950/m-1013629072">Object Oriented Programming Vocabulary</a>
          <img class="image-center-responsive" src="http://s23.postimg.org/tlvgsbiqz/Screen_Shot_2014_04_18_at_4_52_12_PM.png" alt="Object Oriented Programming">
          </p>
          <p><a href="https://docs.python.org/2/tutorial/introduction.html#lists">Using lists or arrays in Python</a></p>''')
card43 = Card(title = 'Advanced Topics in Object Oriented Programming (OOP)',
  content = '''<p>Class Variables are variables that apply to all instances of a class (like valid movie ratings across a list of movies)</p>
          <p>If class variables are constants (<span class = italic>i.e. not changing frequently</span>), then use ALL CAPS in the naming convention</p>
          <p><a href="http://www2.lib.uchicago.edu/keith/courses/python/class/5/">Predefined Variables</a></p>
          <p><span class="italic">Inheritance</span> is the act of child classes using variables or methods from a parent class<p>
          <p><span class="italic">Method overriding</span> occurs when a class explicitly defines some method that it also would have inherited from it's parent (the methods would have the same name in both classes)<p>
          <p><a href="http://learnpythonthehardway.org/book/">Learn Python the Hard Way</a> online book</p>''')

#stage 4 cards
card44 = Card(title = 'Reflection',
  content = '''I've been aware of many of these terms and syntax before but having a connected understanding of the web as a network and web responses as a way to supply information between user and server is a big "ah, I get it" moment.''')
card45 = Card(title = 'Networks',
  content = '''<ul>
            <li><span class="bold">Network</span> - group of entities that can communicate, even though not all are directly connected (two hops this time)</li>
            <ul>
              <li>Encode and interpret messages</li>
              <li>Route messages</li>
              <li>Rules for who uses the resources</li>
            </ul>
            <li><span class="bold">Latency</span> - time from source to destination (milliseconds)</li>
            <li><span class="bold">Bandwidth</span> - amount of information able to transmit per unit of time (megabits per second)</li>
            <li><span class="bold">Bit</span> - smallest unit of information (0 or 1)</li>
            <li><span class="bold">Protocol</span> - rules for client (browser) and server communication (http)</li>
          </ul>
          <p class="code">GET &lt;object&gt;<br>
            RESPONSE &lt;content of object&gt;</p>''')
card46 = Card(title = 'Internets',
  content = '''<ul>
            <li><span class="bold">URL</span> - Uniform Resource Locator, includes the protocol, the host, the path</li>
            <li><span class="bold">Query Parameter</span> - "GET" parameter, <span class="code">?p=1&q=neat</span> added to the end of the path</li>
            <li><span class="bold">Fragment</span> - not sent to server (exists only in the browser), <span class="code">#fragment</span> added to the end of the path or query parameter (if one exists)</li>
            <li><span class="bold">Port</span> - default is 80 <span class="code">http://localhost:8000/</span> added to the end of the host, before the path</li>
            <li><span class="bold">HTTP Request</span> - connect to host, and ask for method, path (no fragments), version...request line = <span class="code">GET /foo HTTP/1.1</span></li>
            <ul>
              <li>Multiple headers also included with request in a Name:Value pair; specifically "Host" (www.example.com) and "User-Agent" (Chrome v.42)</li>
              <li>Servers can respond differently to different headers; you can create any header name:value pair you want as long as the name is a single string and a colon is included</li>
            </ul>
            <li><span class="bold">HTTP Response</span> - response from host, provides document requested and version, status code, reason phrase, and any headers...status line = <span class="code">HTTP/1.1 200 Ok</span></li>
            <ul>
              <li>200 Ok = doc found</li>
              <li>302 Found = doc exists somewhere else</li>
              <li>404 Not found = doc not found</li>
              <li>500 Internal error = server error</li>
              <li>More specific <a href="http://www.w3.org/Protocols/HTTP/HTRESP.html">error codes</a></li>
            </ul>
            <li><span class="bold">Servers</span> - purpose is to respond to HTTP requests (either static or dynamic)</li>
            <ul>
              <li>Static - pre-written files, like an image</li>
              <li>Dynamic - made on the fly, like from a web application</li>
            </ul>
          </ul>''')
card47 = Card(title = 'Forms',
  content = '''<p>HTML forms allow users to submit data to the server</p>
        <p>Form ("action" indicates the path to which the form should submit the user-entered data as a query parameter...no action just submits the form to itself)</p>
        <p class="code">&lt;form action = "http://www.google.com/search"&gt;<br>
        &lt;/form&gt;</p>
        <p>Inputs</p>
        <ul>
          <li>Textbox (default input type)<br>
            <p class="code">&lt;input type = "type" name = "textbox1"&gt;</p></li>
          <li>Password (only hides the UI, not the results passed to query parameter)<br>
            <p class="code">&lt;input type = "password" name = "password1"&gt;</p></li>
          <li>Checkbox<br>
            <p class="code">&lt;input type = "checkbox" name = "checkbox1"&gt;</p></li>
          <li>Radio (use the same "name" but different "values" to enforce expected radio behavior)<br>
            <p class="code">&lt;input type = "radio" name = "radios" value = "1"&gt;</p></li>
          <li>Dropdown (select and option tags...no defined value means the option name itself is used)<br>
            <p class="code">&lt;select name = "q"&gt;<br>
              &lt;option value = "1"&gt;the number one&lt;/option&gt;<br>
              &lt;option&gt;two&lt;/option&gt;<br>
              &lt;option&gt;three&lt;/option&gt;<br>
              &lt;/select&gt;</p></li>
          <li>Label (wrap around the corresponding inputs)<br>
            <p class="code">&lt;label&gt;<br>
              Label Name<br>
              &lt;input type = "checkbox" name = "q" value = "2"&gt;<br>
              &lt;/label&gt;</p></li>''')
card48 = Card(title = 'Modulus and Dictionaries',
  content = '''<p class="italic">Modulus</p>
        <p>x [percent sign] y --> modulus</p>
        <ul>
          <li>Consider x divided by y, modulus is the remainder (14 % 12 --> modulus = 2)</li>
          <li>Consider a clock with y steps, take x steps around the clock, modulus is where you land (3 % 4 --> modulus = 3)</li>
        </ul>
        <p class="italic">Dictionaries</p>
          <ul>
            <li>Mutable set of key:value pairs held in {curly brackets}</li>
            <li>Look up the value based on a key index (or multiple key indexes)...<span class "italic">print elements['nitrogen']</span></li>
            <li>Make assignments to update the content or values in the dictionary...<span class "italic">elements['nitrogen'] = 7</span)</li>
            <li>Dictionary values can be other dictionaries</li>
          </ul>''')
card49 = Card(title = 'GET vs. POST',
  content = '''<table class="table">
          <tr>
            <th>GET</th>
            <th>POST</th>
          </tr>
          <tr>
            <td>parameters in URL</td>
            <td>parameters in request</td> 
          </tr>
          <tr>
            <td>used to fetch documents</td>
            <td>used to update data</td> 
          </tr>
          <tr>
            <td>max length = max URL length</td>
            <td>no max length</td> 
          </tr>
          <tr>
            <td>okay to cache (for speed)</td>
            <td>not okay to cache (since data is updated)</td> 
          </tr>
          <tr>
            <td>shouldn't change the server</td>
            <td>okay to change the server</td> 
          </tr>
        </table>''')
card50 = Card(title = 'Stop the hackers and more useful forms',
  content = '''<p class="bold">Stop the hackers and more useful forms</p>
          <ul>
            <li>Birthday project demonstrates simple get/post workflow and form characteristics like validations and retaining data for the user</li>
            <li>String substitution <span class="code">[percent sign](identifier)s</span> plugs values from code into your generated HTML</li>
            <li>HTML escaping (using <span class="code">import cgi</span> and</li>
          </ul>
        <p class="code">def escape_html(s):<br>
          return cgi.escape(s, quote = True)</p>''')
card51 = Card(title = 'HTML Templates',
  content = '''<p class="bold">HTML Templates</p>
        <p>Template Library = library to build complicated strings (largely html)</p>
        <p><a href="http://jinja.pocoo.org">jinja2</a> built into GoogleAppEngine</p>
        <p>Variable Substitution (jinja2 syntax) = {{variable}} where the curly brackets act like a print statement in the html</p>
        <p>Statement syntax example (jinja2)</p>
        <p class="code">{[percent sign] if name == "Steve" %}<br>
            Hello, Steve<br>
        {[percent sign] else %}<br>
            Who are you?<br>
        {[percent sign] endif %}</p>
        <br>
        <p>Helpful Tips</p>
        <ul>
          <li>Always automatically escape variable when possible (and then opt-in to unsafe mode with syntax like  "{{ item | safe }}"</li>
          <li>Minimize code in templates (keep it to if statements and for loops)</li>
          <li>Minimize html in code (keep code and html completely separate for best practice)</li>
        </ul>
        <p>Template Inheritance = use {[percent sign] extends "base.html" %} and {[percent sign] block content %} / {[percent sign] endblock %} syntax to inherit html from "master" page into other html pages</p>''')
card52 = Card(title = 'Databases',
  content = '''<p><span class="bold">Database</span> = program that stores and retrieves large amounts of structured data (or machines running this program)</p>
        <ul>
          <li>Relational (SQL)</li>
          <li>GAE Datastore</li>
          <li>Dynamo (Amazon)</li>
          <li>NoSQL</li>
        </ul>
        <p>Joins not commonly used in web app SQL</p>
        <p>Indexes - speeds up queries by jumping directly to a key and returning the value (index scan vs. sequential scan)</p>
        <ul>
          <li>Use index_name.get(index_key) instead of index_name.[index_key] to return a value if it exists and a friendly "None" if it does not</li>
          <li>Pro = make database reads faster</li>
          <li>Con = maintenance cost to update index with each new key (i.e. inserts/updates are likely slower)</li>
        </ul>
        <p class="bold">ACID</p>
        <ul>
          <li>Atomicity = all parts of a transaction success or fail together</li>
          <li>Consistency = the database will always be consistent (e.g. avoiding replication lag)</li>
          <li>Isolation = no transaction can interfere with anothers (e.g. locking)</li>
          <li>Durability = once the transaction is committed, it won't be lost (even if connectivity is lost)</li>
        </ul>
        <p class="bold">Google App Engine Datastore</p>
        <p>Tables = Entities (similar to NoSQL)</p>
        <ul>
          <li>Columns are not fixed</li>
          <li>All have an ID</li>
          <li>Parents/Ancestors</li>
        </ul>
        <p><a href="https://cloud.google.com/appengine/docs/python/gettingstartedpython27/usingdatastore">Documentation</a></p>
        <p><span class="bold">*a</span> = /args/ arguments = used to unpack a list or other structured data that is predictable (where you could retrieve the same value every time for a given index)</p>
        <p><span class="bold">*kw</span> = /kwargs/ keyword arguments = used to unpack a dictionary or other structured data that uses key:value pairs (where you could retrieve the same value every time for a given key)</p>
        <p>Incredibly helpful <a href="http://discussions.udacity.com/t/stage-4-webcasts/16367">notes, webcasts, and examples</a> on the stage 4 project</p>''')

#stage 5 cards


#insert data into Google Datastore
# card1.put()
# card2.put()
# card3.put()
# card4.put()
# card5.put()
# card6.put()
# card7.put()
# card8.put()
# card9.put()
# card10.put()
# card11.put()
# card12.put()
# card13.put()
# card14.put()
# card15.put()
# card16.put()
# card17.put()
# card18.put()
# card19.put()
# card20.put()
# card21.put()
# card22.put()
# card23.put()
# card24.put()
# card25.put()
# card26.put()
# card27.put()
# card28.put()
# card29.put()
# card30.put()
# card31.put()
# card32.put()
# card33.put()
# card34.put()
# card35.put()
# card36.put()
# card37.put()
# card38.put()
# card39.put()
# card40.put()
# card41.put()
# card42.put()
# card43.put()
# card44.put()
# card45.put()
# card46.put()
# card47.put()
# card48.put()
# card49.put()
# card50.put()
# card51.put()
# card52.put()

# time.sleep(.1)
