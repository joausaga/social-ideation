Social Ideation
===============
Social Ideation is an application that connects one of today's leading online idea management platforms, [IdeaScale]
(http://www.ideascale.com), with the largest virtual space of participation and socialization, [Facebook]
(http://www.Facebook.com), allowing people to contribute to IdeaScale crowdsourcing ideation initiatives 
directly from Facebook. 

It is a concrete effort toward bringing internet-mediated civic participation tools, such as IdeaScale, closer to the 
large and diverse community of Facebook users. Apart from reaching wider and larger sources of information, it aims at 
reducing as much as possible the participation barrier, enabling people to take part on crowdsourcing ideation processes 
by using only Facebook elements, namely facebook pages, hashtags, posts, comments, and likes.

Examples
-------------

![app_scenarios](https://dl.dropboxusercontent.com/u/55956367/app_scenarios.png "Mapping Model")

Mapping Model
-------------

Social Ideation proposes the model outlined in the next figure to map Facebook posts with IdeaScale.

![mapping_model](https://dl.dropboxusercontent.com/u/55956367/mapping_model.png "Mapping Model")

As it is possible to appreciated in the figure the proposed model is based entirely on native elements of Facebook, 
namely posts, comments, pages, and hashtags. Posts published on the Facebook page that corresponds to an IdeaScale 
initiative and contain the hashtag of the initiative and the hashtag of one of initiative's campaigns are mapped to an 
idea. 

As the figure also shows, all the comments placed to the Facebook posts that are mapped ideas are taken and 
transformed into IdeaScale comments.

Integration Model
-----------------

The integration between the two platforms are performed mainly through API functions. Either Facebook and IdeaScale offer
primitives through which is possible to read and create new content. The following figure presents the details of how 
the integration works.

![integration_model](https://dl.dropboxusercontent.com/u/55956367/app_model.png "Social Ideation Model")

The app maintains records about the mapping between IdeaScale initiatives and Facebook pages. Each record saves also the 
hashtags that identify IdeaScale initiatives and their campaigns. To get content from IdeaScale, the app hits the API 
asking for the ideas and comments of the registered initiatives (1). The ideas and comment collected from Facebook
are posted on IdeaScale by calling the corresponding API function (2). 

Every time a new idea or comment are placed on the Facebook pages that correspond to the IdeaScale initiatives, Facebook 
API pushes a notification to the app (3). The ideas and comments gathered from the IdeaScale initiatives are posted to 
the Facebook pages by calling the corresponding Facebook API function.

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

7. Install Rabbit MQ broker. [Unix installation instructions](http://www.rabbitmq.com/install-generic-unix.html)

8. Set the static url in social-ideation/settings.py

Getting started
---------------

1. [Sign up to IdeaScale](http://www.ideascale.com)

2. Create an IdeaScale Community

3. [Request a API token for the new community](http://support.ideascale.com/customer/portal/articles/1001563-ideascale-rest-api)

4. [Enable attachments for ideas](http://support.ideascale.com/customer/portal/articles/1001385-how-to-upload-an-attachment-to-an-idea-or-comment)

5. [Create a Facebook App](http://nodotcom.org/python-facebook-tutorial.html)

6. Create a Facebook Page

7. Obtain a Facebook OAuth token

8. Go inside social ideation directory and create an admin user `python manage.py createsuperuser`

9. Hit the social ideation URL, i.e., http://socialideation.com, and log in with the admin credentials

10. Create a new IdeaScale initiative (Home->IdeaScale->Initiative->Add)

11. Update the URLs of the callbacks replacing the host part of the callback URLs with the URL where the app is installed 
(Home->Connectors->URL Callbacks)

12. Update IdeaScale connector token (Home->Connectors->IdeaScale) The correct token should be located in the table 
auth_token (username = admin)

13. Create a consultation platform choosing IdeaScale as the connector (Home->App->Consultation platforms->Add) 

14. Import the consultation platform initiatives. Select the new consultation platform in Home->App->Consultation Platforms
and choose the option 'Get Initiatives' from the Action menu located on top of the list.

15. Create a social network app choosing Facebook as the connector, configuring the app id and app secret of the created 
Facebook App, and setting the page id and access token of the recently created Facebook Page. Set also the callback field
if you want to receive notification from Facebook every time a new post or comment is placed in the page
(Home->App->Social network apps->Add)

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