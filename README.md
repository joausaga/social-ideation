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

Mapping Model
-------------

Social Ideation proposes the model outlined in the next figure to map Facebook posts with IdeaScale.

![handout](https://dl.dropboxusercontent.com/u/55956367/mapping_model.png "Mapping Model")

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

![handout](https://dl.dropboxusercontent.com/u/55956367/app_model.png "Social Ideation Model")

The app maintains records about the mapping between IdeaScale initiatives and Facebook pages. Each record saves also the 
hashtags that identify IdeaScale initiatives and their campaigns. To get content from IdeaScale, the app hits the API 
asking for the ideas and comments of the registered initiatives (1). The ideas and comment collected from Facebook
are posted on IdeaScale by calling the corresponding API function (2). 

Every time a new idea or comment are placed on the Facebook pages that correspond to the IdeaScale initiatives, Facebook 
API pushes a notification to the app (3). The ideas and comments gathered from the IdeaScale initiatives are posted to 
the Facebook pages by calling the corresponding Facebook API function.
