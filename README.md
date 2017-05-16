Social Ideation
===============
Social Ideation is an application that connects [IdeaScale](http://www.ideascale.com) -- one of today's leading online 
idea management platforms -- with the world's largest virtual space of participation and socialization, 
[Facebook](http://www.Facebook.com), allowing people to participate on IdeaScale-based public consultations initiatives 
from Facebook. 

More specifically, it enables users to **participate** (submit ideas, place comments) **on IdeaScale** initiatives **without 
leaving facebook** and using *only* Facebook's native features: posts, hashtags, comments, and groups. At the same time, 
the ideas and comments published on IdeaScale are automatically replicated on the Facebook group linked to the initiative.

Social Ideation is a concrete effort toward bringing civic participation platforms, such as IdeaScale, closer to the 
large and diverse community of Facebook users. Apart from reaching wider and larger sources of information, it aims at 
reducing as much as possible the participation barrier.

Examples
-------------

![app_scenarios](/figures_repo/app_scenarios.png?raw=true "Scenarios")

Mapping Model
-------------

Social Ideation proposes the model outlined in the next figure to map IdeaScale elements (initiatives, campaigns, ideas,
comments) with Facebook elements (groups, hashtags, posts and comments).

![mapping_model](/figures_repo/mapping_scheme.png?raw=true "Mapping Model")

As seen on the figure the proposed mapping model is based entirely on native elements of Facebook (posts, comments, 
groups, and hashtags). Posts published on a Facebook group that is linked to an IdeaScale initiative and contain the 
hashtag of one of the initiative's campaigns are mapped to ideas. Similarly, ideas submitted on an IdeaScale initiatives 
that is linked to a Facebook groups are mapped to posts published on the timeline of the group.

As the figure also shows, the comments placed to Facebook posts mapped to ideas are taken and transformed into 
IdeaScale comments and comments published on IdeaScale ideas are mapped to Facebook comments.

On Facebook, hashtags are used to identify initiatives' campaigns.

Architecture
-----------------

The system architecture is composed of four modules and interfacing with IdeaScale and Facebook. The figure below shows on the sides the platforms IdeaScale and Facebook providing, through Web APIs, services to our system. The modules **Social Network Connector** and **Ideation Platform Connector** support the communication logic with the APIs of IdeaScale and Facebook, respectively.

![integration_model](/figures_repo/architecture.png?raw=true "Architecture")

The module Synchronization Launcher is in charge of launching synchronization tasks. Every certain time (5 minutes by default), it requests **Social Network Connector** and **Ideation Platform Connector** for the most recent content (e.g., ideas, comments, replies) of a given Facebook group and IdeaScale community. After receiving the information from **Social Network Connector** and **Ideation Platform Connector**, it passes the information to **Content Synchronizer**. At the request of Content Synchronizer, it asks the third party connectors for the creation, modification, or elimination of posts/ideas, comments, replies, and likes/upvotes.

The synchronization between platforms is carried out by the module **Content Synchronizer** by following the steps described in the section Algorithm. It also administers a database of records that used to map elements of IdeaScale platform (e.g., campaigns, ideas, comments) to features of Facebook. To detect inconsistencies between platforms, it checks whether the same number of ideas/posts, comments, and replies exists in both the community of IdeaScale and the Facebook group. Besides, the module ensures that mapped instances of ideas, comments, and replies share the same textual information. If inconsistencies are detected, the module fixes them by following the algorithm explain next. The module content synchronizer was also equipped with automatic functionalities to take care of possible failure in the use of our system and to encourage participation from Facebook. If a post is created inside the group and does not contain hashtag or the hashtag is not one of the campaign hashtags, the system automatically places a comment to the post noticing this situation. When a user, who is not already participating from Facebook, put an idea or comment on IdeaScale, the system sends an email motivating the participants to use our system so the new content can be visible by the people on Facebook.

Mapping records
-----------------

A key ingredient in our implementation is the set of records used to implement the mapping between the elements of IdeaScale platform presented previously (e.g., campaigns, ideas, comments) and the features of Facebook described before (e.g., posts, comments, hashtags). The records are saved in tables of the database controlled by the module Content Synchronizer. We define the record **Ideation Initiative (II)** to keep the association between instances of IdeaScale communities to concrete cases of Facebook groups. The pairing between campaigns and hashtags is registered in the record **Campaign Hashtag (CH)**. Our system saves the mapping between ideas and posts in the record **Idea Post (IP)**, it also registers the mapping between IdeaScale comments and Facebook comments in the record **Comments (C)**. Similarly, the association between replies in both platforms is kept in the record **Replies (R)**. The record **User (U)** is used to store the mapping between members of associated IdeaScale communities and Facebook groups. The figure below shows the records with their corresponding properties.

![mapping_records](/figures_repo/mapping_records.png?raw=true "Mapping Records")

Synchronization Algorithm
-----------------

We implement custom synchronization algorithms to handle change propagation. Let's say we want to synchronize the ideas posted on the Facebook group $fg_i$. A pseudocode of the algorithm is outlined in the figure below. First, the algorithm consults the records **Ideation Initiative (II)** looking for the IdeaScale community associated to *fg_i*, say $ic_i$ (line 1). Then, it asks for the list of posts published in *fg_i* (line 2). Later, for each post *pos_i* it checks whether the post is equipped with a campaign hashtag and if the post has not been replicated in IdeaScale yet (line 4). If the previous conditions are met, it saves the post into a record of the type *po*, say *po_i* (line 5). After that, it queries **Campaign Hashtag (CH)** records to obtain the campaign hashtag $ht_i$ of the post, e.g., *ca_i* (line 6-7). Then, it gets, by consulting **User (U)** records, information of the IdeaScale user associated with the author of the post, say *iu_i* (line 8). It publishes, later, an idea, say *ie_i*, on behalf of *iu_i* in the community *ic_i* with *po_i.text* as description, the first 64 characters of *po_i.text* as the title (titles in IdeaScale are limited to 64 characters), and within the campaign *ca_i* (line 9). A record **Idea Post (IP)** is created next to preserve the association between *po_i* and *ie_i* (line 10). If the post *pos_i* has already been mirrored, the algorithm updated the idea linked to *pos_i* if any change in the content of the post is detected (line 12-13).

![integration_model](/figures_repo/algorithm.png?raw=true "Synchronization Algorithm")

The synchronization finishes with a double loop that checks that still exist all posts registered in IP records as originally published on Facebook (posts created to mirror ideas are not considered here). If a post associated with an IP record cannot be found in the recently obtained list of posts, we assume that the post has been eliminated and thus its counterpart in IdeaScale together with the mapping record should be deleted to keep the system consistent (lines 15-23). The steps followed by the system to replicate ideas in the other direction, from IdeaScale to Facebook, are alike. Similar algorithms are also used to synchronize comment, replies, and likes.


The ideas and comments deleted on the Facebook group are deleted too on IdeaScale by calling the corresponding API function. On the other hand, IdeaScale doesn't provide the option delete ideas nor comments, only administrators of the initiative can do this. So, if the administrator deletes ideas or comments on IdeaScale, they will be deleted too on the Facebook group only if they have been posted by the Social Ideation App on behalf of the Facebook users.

Installation
------------

 1. Clone the repository `git clone https://github.com/joausaga/social-ideation.git`

 2. Go inside the repository folder and execute `pip install -r requirements.txt` to install dependencies.
    If an error occurs during the installation, it might be because some of these resons:
    a) Package *python-dev* is missing
    b) Package *libmysqlclient-dev* is missing
    c) The environment variables *LC_ALL* and/or *LC_CTYPE* are not defined or don't have a valid value

 3. Clone Facebook API client library `git clone https://github.com/pythonforfacebook/facebook-sdk`

 4. Go inside Facebook API client library and install it `python setup.py install`

 5. Create a mysql database. Make sure your database collation is set to UTF-8, if not, edit the script *fix_database_to_utf8.py* and set the *user* and *passwd* parameters of your database and then run the script `python fix_database_to_utf8.py`

 6. Set the configuration parameters of the database in social-ideation/settings.py

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

 7. Run `python manage.py migrate` to set up the database schema
 
 8. Run `python manage.py syncdb` to create an admin user and install the authentication system
 
 9. Install Rabbit MQ broker. [Unix installation instructions](http://www.rabbitmq.com/install-generic-unix.html)
 
 10. Set the static url in social-ideation/settings.py
 
 11. Add the following programs (rabbit, celery and celerybeat) at the *program section* of the supervisor configuration file (supervisord.conf). You can look at the example file (supervisord-example.conf) 

Getting started
---------------

 1. [Sign up to IdeaScale](http://www.ideascale.com)

 2. Create an IdeaScale Community

 3. [Request an API token for the new community](http://support.ideascale.com/customer/portal/articles/1001563-ideascale-rest-api)

 4. [Create a Facebook App](http://nodotcom.org/python-facebook-tutorial.html)

 5. Set the App Domains (Basic) and the Valid OAuth redirect URIs (Advanced) on the App Settings panel

 6. Create a Facebook Group and set the privacy setting to Public

 7. Go inside social ideation directory and load initial IdeaScale data `python manage.py loaddata ideascale_connector_data.json`

 8. Hit the social ideation URL, i.e., http://www.social-ideation.com, and log in with the admin credentials

 9. Create a new IdeaScale initiative (*Home->IdeaScale->Initiative->Add*)

 10. Update the URLs of the callbacks replacing the host part of the callback URLs with the URL where the app is installed 
(*Home->Connectors->URL Callbacks*)

 11. Update IdeaScale connector token (*Home->Connectors->IdeaScale*) The correct token should be located in the table 
authtoken_token (user_id = 1)

 12. Create a consultation platform (*Home->App->Consultation platforms->Add*) choosing IdeaScale as the connector  

 13. Import the consultation platform initiatives. Select the new consultation platform in (*Home->App->Consultation Platforms*) 
and choose the option **'Get Initiatives'** from the **Action menu** located on the top of the list

 14. Obtain Facebook OAuth token. Go to [Graph API Explorer](https://developers.facebook.com/tools/explorer/) and 
in the application drop down select the app created in Step 4. Click Get Access Token; in permissions popup go to 
extended permissions tab and select **publish_actions**. 

 15. Create a social network app (*Home->App->Social network apps->Add*) choosing Facebook as the connector, setting the **app id**, **app secret**, **app access token** (app id|app secret) and  the **redirect uri** (that matches the *Site URL*) of the created Facebook App in Step 4

 16.  Create a social network app user (*Home->App->Social network app users->Add*) setting in the field access token the previously obtained access token in Step 14

 17. Create a social network app community (*Home->App->Social network app communities->Add*) and put the user created in
Step 15 as the admin

 18. Edit the previously social network app created, configuring the **community** as the community created before.


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
