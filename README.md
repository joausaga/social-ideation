Social Ideation
===============
Social Ideation is an application that connects [IdeaScale](http://www.ideascale.com) -- one of today's leading online 
idea management platforms -- with the world's largest virtual space of participation and socialization, 
[Facebook](http://www.Facebook.com), allowing people to participate on IdeaScale-based civic participation initiatives 
from Facebook. 

More specifically, it enables users to **participate** (submit ideas, place comments) on IdeaScale initiatives **without 
leaving facebook** and using *only* Facebook's native features: posts, hashtags, comments, and groups. At the same time, 
the ideas and comments you publish on the IdeaScale site of the initiative are automatically replicated on behalf of the
user on the Facebook group linked to the initiative.

Social Ideation is a concrete effort toward bringing internet-mediated civic participation platforms, such as IdeaScale, 
closer to the large and diverse community of Facebook users. Apart from reaching wider and larger sources of information, 
it aims at reducing as much as possible the participation barrier.

Examples
-------------

![app_scenarios](https://dl.dropboxusercontent.com/u/55956367/app_scenarios.png "Mapping Model")

Mapping Model
-------------

Social Ideation proposes the model outlined in the next figure to map Facebook posts and comments with IdeaScale ideas
and comments.

![mapping_model](https://dl.dropboxusercontent.com/u/55956367/mapping_model.png "Mapping Model")

As seen on the figure the proposed model is based entirely on native elements of Facebook, namely posts, comments, 
groups, and hashtags. Posts published on a Facebook group that is linked to an IdeaScale initiative and contain the 
hashtag of the initiative and the hashtag of one of initiative's campaigns are mapped to an idea. 

As the figure also shows, all the comments placed to Facebook posts mapped to ideas are taken and transformed into 
IdeaScale comments.

Integration Model
-----------------

The integration between the two platforms are performed mainly through API functions. Both Facebook and IdeaScale offer
primitives through which is possible to read and create new content. The following figure presents the details of how 
the integration works.

![integration_model](https://dl.dropboxusercontent.com/u/55956367/app_model.png "Social Ideation Model")

The app maintains records about the mapping between IdeaScale initiatives and Facebook groups. Each record saves also the 
hashtags that identify IdeaScale initiatives and their campaigns. To get content from IdeaScale, the app hits the API 
asking for the ideas and comments of the registered initiatives (1). The ideas and comment collected from Facebook
are posted on IdeaScale by calling the corresponding API function (2). 

The ideas and comments published on the Facebook groups linked to the registered IdeaScale initiatives are gathered by 
hitting the API of Facebook (3). The ideas and comments gathered from the registered IdeaScale initiatives are 
posted to the Facebook groups associated to the initiatives by calling the corresponding Facebook API function.

Installation
------------

1. Clone the repository `git clone https://github.com/joausaga/social-ideation.git`

2. Go inside the repository folder and execute `pip install -r requirements.txt` to install dependencies

3. Clone Facebook API client library `git clone https://github.com/pythonforfacebook/facebook-sdk`

4. Go inside Facebook API client library and install it `python setup.py install`

4. Create a mysql database

5. Set the configuration parameters of the database in social-ideation/settings.py

    ```
    DATABASES = {
        ...
            'NAME': '',
            'USER': '',
            'PASSWORD': '',
            'HOST': '',
            'PORT': '',
        ...
    }
    ```

6. Run `python manage.py migrate` to set up the database schema

7. Run `python manage.py syncdb` to create an admin user and install the authentication system

7. Install Rabbit MQ broker. [Unix installation instructions](http://www.rabbitmq.com/install-generic-unix.html)

8. Set the static url in social-ideation/settings.py

Getting started
---------------

1. [Sign up to IdeaScale](http://www.ideascale.com)

2. Create an IdeaScale Community

3. [Request a API token for the new community](http://support.ideascale.com/customer/portal/articles/1001563-ideascale-rest-api)

<!-- 4. [Enable attachments for ideas]
(http://support.ideascale.com/customer/portal/articles/1001385-how-to-upload-an-attachment-to-an-idea-or-comment) -->

4. [Create a Facebook App](http://nodotcom.org/python-facebook-tutorial.html)

5. Set the App Domains (Basic) and the Valid OAuth redirect URIs (Advanced) on the App Settings panel

6. Create a Facebook Group

7. Go inside social ideation directory and load initial IdeaScale data `python manage.py loaddata ideascale_connector_data.json`

8. Hit the social ideation URL, i.e., http://www.social-ideation.com, and log in with the admin credentials

9. Create a new IdeaScale initiative (*Home->IdeaScale->Initiative->Add*)

10. Update the URLs of the callbacks replacing the host part of the callback URLs with the URL where the app is installed 
(*Home->Connectors->URL Callbacks*)

11. Update IdeaScale connector token (*Home->Connectors->IdeaScale*) The correct token should be located in the table 
authtoken_token (user_id = 1)

14. Create a consultation platform choosing IdeaScale as the connector (*Home->App->Consultation platforms->Add*) 

15. Import the consultation platform initiatives. Select the new consultation platform in *Home->App->Consultation Platforms* 
and choose the option **'Get Initiatives'** from the **Action menu** located on the top of the list.

16. Create a social network app community (*Home->App->Social network app communities->Add*)

17. Create a social network app choosing Facebook as the connector, setting the **app id**, **app access token** and 
**app secret** of the created Facebook App, and configuring the **community** as the community created before.
(*Home->App->Social network apps->Add*)

License
-------
MIT

Technologies
------------

1. [Django Framework 1.8](https://www.djangoproject.com/)

2. [MySQL](http://www.mysql.com) database and its corresponding python package

3. [Facebook SDK](https://github.com/pythonforfacebook/facebook-sdk) a python-based Facebook API client

4. [IdeaScaly](https://github.com/joausaga/ideascaly) a python-based IdeaScale API client

5. [Celery](http://www.celeryproject.org)

6. [Celery for Django](http://docs.celeryproject.org/en/latest/django/first-steps-with-django.html)

7. [Rabbit MQ](http://www.rabbitmq.com)

Let me know
-----------

If you use social ideation, please [write me](mailto:jorgesaldivar@gmail.com) a short message with a link to your project. 
It is not mandatory, but I will really appreciate it!