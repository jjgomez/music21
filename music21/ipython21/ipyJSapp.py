############
#
# IPythonNotebook like connections between Javascript and Python, but 

from __future__ import print_function
# start with
# ~/anaconda/bin/python ipythonNotebookStart 

#    -- needs ipython v.3 dev  
import os
import threading
import webbrowser #for opening browser tab
from IPython.html import notebookapp # @UnresolvedImport
from zmq.eventloop import ioloop
import time

from IPython.html.utils import url_path_join
class NewNotebookApp(notebookapp.NotebookApp):
    
    def start(self):
        """ Start the IPython Notebook server app, after initialization
        
        This method takes no arguments so all configuration and initialization
        must be done prior to calling this method."""
        if self.subapp is not None:
            return self.subapp.start()
    
        info = self.log.info
        for line in self.notebook_info().split("\n"):
            info(line)
        info("Use Control-C to stop this server and shut down all kernels (twice to skip confirmation).")
    
        self.write_server_info_file()
    
        if self.open_browser or self.file_to_run:
            try:
                browser = webbrowser.get(self.browser or None)
            except webbrowser.Error as e:
                self.log.warn('No web browser found: %s.' % e)
                browser = None
            
            if self.file_to_run:
                if not os.path.exists(self.file_to_run):
                    self.log.critical("%s does not exist" % self.file_to_run)
                    self.exit(1)
    
                relpath = os.path.relpath(self.file_to_run, self.notebook_dir)
                uri = url_path_join('notebooks', *relpath.split(os.sep))
            else:
                uri = self.uri_override
            if browser:
                b = lambda : browser.open(url_path_join(self.connection_url, uri),
                                          new=2)
                threading.Thread(target=b).start()
        try:
            ioloop.IOLoop.instance().start()
        except KeyboardInterrupt:
            info("Interrupted...")
        finally:
            self.cleanup_kernels()
            self.remove_server_info_file()


def runApp(htmlFile = 'm21pj.html'):
    '''
    run the Javascript to Python processor
    '''
    thisDirectory = os.path.abspath(os.path.dirname(__file__))
    nbDirectory = os.path.join(thisDirectory, 'notebookBlank')
    print(nbDirectory)
    staticDirectory = os.path.join(thisDirectory, 'static')
    
    relativeStaticFile = 'static/' + htmlFile
    print(relativeStaticFile)
    print(staticDirectory)
    
    npa = notebookapp.NotebookApp()
    #npa.uri_override = relativeStaticFile
    #npa.start = newStart
    npa.extra_static_paths = [staticDirectory]
    #print(npa.connection_url)
    OPEN_IN_NEW_TAB = 2
    
    
    # start the web browser after a delay so that the webserver can already have started...
    delayInSeconds = 2
    startWebbrowserDelayed = lambda: webbrowser.open(
                                    npa.connection_url + relativeStaticFile, new=OPEN_IN_NEW_TAB )
    threading.Timer(delayInSeconds, startWebbrowserDelayed).start()
    
    # now start the main app
    npa.launch_instance(open_browser=False, notebook_dir=nbDirectory, extra_static_paths = [staticDirectory])


if __name__ == '__main__':
    runApp('pureBlank3.html')