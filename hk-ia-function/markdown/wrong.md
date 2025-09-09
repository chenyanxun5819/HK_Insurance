BuildError
werkzeug.routing.exceptions.BuildError: Could not build url for endpoint 'index'. Did you mean 'login_page' instead?

Traceback (most recent call last)
File "/home/weschen/HK_insurance/hk-ia-function/venv/lib/python3.12/site-packages/flask/app.py", line 1536, in __call__
return self.wsgi_app(environ, start_response)
       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/home/weschen/HK_insurance/hk-ia-function/venv/lib/python3.12/site-packages/flask/app.py", line 1514, in wsgi_app
response = self.handle_exception(e)
           ^^^^^^^^^^^^^^^^^^^^^^^^
File "/home/weschen/HK_insurance/hk-ia-function/venv/lib/python3.12/site-packages/flask/app.py", line 1511, in wsgi_app
response = self.full_dispatch_request()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/home/weschen/HK_insurance/hk-ia-function/venv/lib/python3.12/site-packages/flask/app.py", line 919, in full_dispatch_request
rv = self.handle_user_exception(e)
     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/home/weschen/HK_insurance/hk-ia-function/venv/lib/python3.12/site-packages/flask/app.py", line 917, in full_dispatch_request
rv = self.dispatch_request()
     ^^^^^^^^^^^^^^^^^^^^^^^
File "/home/weschen/HK_insurance/hk-ia-function/venv/lib/python3.12/site-packages/flask/app.py", line 902, in dispatch_request
return self.ensure_sync(self.view_functions[rule.endpoint])(**view_args)  # type: ignore[no-any-return]
       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/home/weschen/HK_insurance/hk-ia-function/main_firebase.py", line 47, in login_page
response = make_response(render_template("login.html"))
                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/home/weschen/HK_insurance/hk-ia-function/venv/lib/python3.12/site-packages/flask/templating.py", line 150, in render_template
return _render(app, template, context)
       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/home/weschen/HK_insurance/hk-ia-function/venv/lib/python3.12/site-packages/flask/templating.py", line 131, in _render
rv = template.render(context)
     ^^^^^^^^^^^^^^^^^^^^^^^^
File "/home/weschen/HK_insurance/hk-ia-function/venv/lib/python3.12/site-packages/jinja2/environment.py", line 1295, in render
self.environment.handle_exception()
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/home/weschen/HK_insurance/hk-ia-function/venv/lib/python3.12/site-packages/jinja2/environment.py", line 942, in handle_exception
raise rewrite_traceback_stack(source=source)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/home/weschen/HK_insurance/hk-ia-function/templates/login.html", line 1, in top-level template code
{% extends "base.html" %}
File "/home/weschen/HK_insurance/hk-ia-function/templates/base.html", line 141, in top-level template code
<a class="navbar-brand" href="{{ url_for('index') }}">
File "/home/weschen/HK_insurance/hk-ia-function/venv/lib/python3.12/site-packages/flask/app.py", line 1121, in url_for
return self.handle_url_build_error(error, endpoint, values)
       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/home/weschen/HK_insurance/hk-ia-function/venv/lib/python3.12/site-packages/flask/app.py", line 1110, in url_for
rv = url_adapter.build(  # type: ignore[union-attr]
     
File "/home/weschen/HK_insurance/hk-ia-function/venv/lib/python3.12/site-packages/werkzeug/routing/map.py", line 924, in build
raise BuildError(endpoint, values, method, self)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
werkzeug.routing.exceptions.BuildError: Could not build url for endpoint 'index'. Did you mean 'login_page' instead?
The debugger caught an exception in your WSGI application. You can now look at the traceback which led to the error.
To switch between the interactive traceback and the plaintext one, you can click on the "Traceback" headline. From the text traceback you can also create a paste of it. For code execution mouse-over the frame you want to debug and click on the console icon on the right side.

You can execute arbitrary Python code in the stack frames and there are some extra helpers available for introspection:

dump() shows all variables in the frame
dump(obj) dumps all that's known about the object
Brought to you by DON'T PANIC, your friendly Werkzeug powered traceback interpreter.