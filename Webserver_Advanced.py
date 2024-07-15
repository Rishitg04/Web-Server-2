import http.server
import os

class ServerException(Exception):
    """Custom exception class for server-related errors."""
    def __init__(self, message):
        super().__init__(message)

class base_case:
    def handle_file(self,brhandler,full_path):
        try:
            with open(full_path,'rb') as reader:
                content = reader.read()
            brhandler.send_content(content)
        except IOError as msg:
            msg = "'{0}' cannot be read: {1}".format(self.path, msg)
            brhandler.handle_error(msg)

    def test(self, handler):
        assert False, 'Not implemented.'

    def act(self, handler):
        assert False, 'Not implemented.'

    

class no_file(base_case):
    #Checks if path exists, if yes will iterate to next class
    def test(self,brhandler):
        return not os.path.exists(brhandler.full_path)

    def act(self,brhandler):
        raise ServerException("'{0}' not found".format(brhandler.path))

class existing_file(base_case):
    #Checks if the path points to a file, if yes will handle it else will iterate to the next class
    def test(self, brhandler):
        return os.path.isfile(brhandler.full_path)

    def act(self, brhandler):
        self.handle_file(brhandler,brhandler.full_path)

class serve_index_file(base_case):
    #Serve index.html page for a directory.

    def index_path(self, brhandler):
        return os.path.join(brhandler.full_path, 'index.html')

    def test(self, brhandler):
        return os.path.isdir(brhandler.full_path) and \
               os.path.isfile(self.index_path(brhandler))

    def act(self, brhandler):
        self.handle_file(brhandler,self.index_path(brhandler))

class directory_without_index_file(base_case):
    #Serve listing for a directory without an index.html page.

    Listing_Page ="""
        <html>
            <body>
                <h1>Directory listing</h1>
                <ul>{0}</ul>
            </body>
        </html>
        """

    def index_path(self, brhandler):
        return os.path.join(brhandler.full_path, 'index.html')
    
    def list_dir(self, brhandler, full_path):
        try:
            entries = os.listdir(full_path)
            bullets = ['<li>{0}</li>'.format(e) 
                for e in entries if not e.startswith('.')]
            page = self.Listing_Page.format('\n'.join(bullets))
            page_changed =  bytes(page,"utf-8")
            brhandler.send_content(page_changed)
        except OSError as msg:
            msg = "'{0}' cannot be listed: {1}".format(self.path, msg)
            brhandler.handle_error(msg)

    def test(self, brhandler):
        return os.path.isdir(brhandler.full_path) and \
               not os.path.isfile(self.index_path(brhandler))
    
    def act(self,brhandler):
        self.list_dir(brhandler,brhandler.full_path)

        
class fail(base_case):
    #Final case if none of the above work
    def test(self, brhandler):
        return True

    def act(self, brhandler):
        raise ServerException("Unknown object '{0}'".format(brhandler.path))


class RequestHandler(http.server.BaseHTTPRequestHandler):

    #To iterate through different cases
    Cases = [no_file(),existing_file(),serve_index_file(),directory_without_index_file(),fail()]

    full_path=""

    Error_Page = """
        <html>
        <body>
        <h1>Error accessing {path}</h1>
        <p>{msg}</p>
        </body>
        </html>
        """
    

    def do_GET(self):
        try:
            #Gets the full path of whatever file is requested
            self.full_path = os.getcwd() + self.path

            for case in self.Cases:
                if case.test(self):
                    case.act(self)
                    break
            
        except Exception as msg:
            self.handle_error(msg)

    
    def handle_error(self,msg):
        content = self.Error_Page.format(path=self.path, msg=msg)
        content_changed = bytes(content,"utf-8")
        self.send_content(content_changed, 404)

    

    def send_content(self,content,status=200):
        self.send_response(status)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)


if __name__=='__main__':
    serverAddress=("",8080)
    server = http.server.HTTPServer(serverAddress,RequestHandler)
    server.serve_forever()
