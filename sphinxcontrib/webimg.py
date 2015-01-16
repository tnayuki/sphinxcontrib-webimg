'''
    sphinxcontrib.webimg
    ~~~~~~~~~~~~~~~~~

    This module provides :rst:directive:`webimg`, which you can use to embed
    screen shots from web pages.

'''
import os
import sys
import urllib
import urlparse
from docutils import nodes
from docutils.parsers.rst.directives.images import Image
from hashlib import sha1
from selenium import webdriver
from sphinx.util.osutil import ensuredir

driver = None

class webimg(nodes.General, nodes.Inline, nodes.Element):
    def to_image(self, builder):
        global driver

        if builder.format == 'html':
            reldir = "_images"
            outdir = os.path.join(builder.outdir, '_images')
        else:
            reldir = ""
            outdir = builder.outdir

        try:
            o = urlparse.urlparse(self['url'])
            if o.scheme == '' and o.netloc == '':
                url = 'file:' + urllib.pathname2url(os.path.abspath(o.path))
            else:
                url = self['url']

            filename = "webimg-%s.png" % sha1(url).hexdigest()
            path = os.path.join(outdir, filename)
            ensuredir(outdir)

            if driver is None : driver = webdriver.Firefox()
            driver.get(url)
            driver.save_screenshot(path)
        except Exception as exc:
            builder.warn('Fail to save screenshot: %s' % exc)
            return nodes.Text('')

        relfn = os.path.join(reldir, filename)
        image_node = nodes.image(candidates={'*': relfn}, **self.attributes)
        image_node['uri'] = relfn

        return image_node


class WebImg(Image):
    def run(self):
        result = super(WebImg, self).run()
        if isinstance(result[0], nodes.image):
            image = webimg(url=self.arguments[0],
                           **result[0].attributes)
            result[0] = image
        else:
            for node in result[0].traverse(nodes.image):
                image = webimg(url=self.arguments[0],
                               **result[0].attributes)
                node.replace_self(image)

        return result


def on_doctree_resolved(app, doctree, docname):
    for node in doctree.traverse(webimg):
        image_node = node.to_image(app.builder)
        node.replace_self(image_node)


def on_build_finished(app, exception):
    global driver
    if not driver is None : driver.quit()


def setup(app):
    app.add_node(webimg)
    app.add_directive('webimg', WebImg)
    app.connect('doctree-resolved', on_doctree_resolved)
    app.connect('build-finished', on_build_finished)
