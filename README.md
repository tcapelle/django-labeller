# fastlabel

#### A light-weight image labelling tool for Python designed for creating segmentation data sets.

- Flask based
- polygon, box, point and oriented ellipse annotations supported
- polygonal labels can have disjoint regions and can be editing using paintng and boolean operations; provided by
  [polybooljs](https://github.com/voidqk/polybooljs)
- can use the [DEXTR](http://people.ee.ethz.ch/~cvlsegmentation/dextr/) algorithm to automatically generate
  polygonal outlines of objects identified by the user with a few clicks; provided by the
  [dextr](https://github.com/Britefury/dextr) library


## Flask

If you want to run `django-labeller` on your local machine with minimum fuss and store the image and
label files on your file system, use the Flask application.

## Installation

If you to use the example Django application or use the provided example images, clone it from GitHub and
install (*recommended*): 

```bash
> pip install fastlabel
```

### Flask web app example

An example Flask-based web app is provided that displays the labelling tool within a web page. To start it,
change into the same directory into which you cloned the repo and run:
 
```bash
> python -m image_labelling_tool.flask_labeller 
```

Now open `0.0.0.0:5000` within a browser.

If you want to load images from a different directory, or if you installed from PyPI, tell `flask_labeller`
where to look:

```bash
> python -m image_labelling_tool.flask_labeller --images_pat=<images_directory>/*.<jpg|png>
```


#### Flask app with DEXTR assisted labelling

First, install the [dextr](https://github.com/Britefury/dextr) library:

```bash
> pip install dextr
```

Now tell the Flask app to enable DEXTR using the `--enable_dextr` option:

```shell script
> python -m image_labelling_tool.flask_labeller --enable_dextr
````
 
The above will use the ResNet-101 based DEXTR model trained on Pascal VOC 2012 that is provided by
the dextr library. 
If you want to use a custom DEXTR model that you trained for your purposes, use the `--dextr_weights` option:

```shell script
> python -m image_labelling_tool.flask_labeller --dextr_weights=path/to/model.pth
````


It is licensed under the MIT license.
