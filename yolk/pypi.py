# -*- coding: utf-8 -*-
""" pypi.
    
    Desc: Library for getting information about Python packages by querying
          The CheeseShop (PYPI a.k.a. Python Package Index).
    
    Authors: Rob Cakebread <cakebread at gmail>;
             Alexander Böhn <fish2000, also at the geemail>
    License: BSD (See COPYING)
"""
from __future__ import print_function

import ast
import re
import platform
if platform.python_version().startswith('2'):
    import xmlrpclib
    import urllib2
else:
    import xmlrpc.client as xmlrpclib
    import urllib.request as urllib2
import sys
import os
import time

from yolk.utils import get_yolk_dir
from yolk.retrying import retry

XML_RPC_SERVER = 'https://pypi.python.org/pypi'

def get_debug(token='XMLRPC_DEBUG'):
    return token in os.environ


class ProxyTransport(xmlrpclib.Transport):
    """ Provides an XMl-RPC transport routing via a http proxy.
        
        This is done by using urllib2, which in turn uses the environment
        varable http_proxy and whatever else it is built to use (e.g. the
        windows registry).
        
        NOTE: the environment variable http_proxy should be set correctly.
        See check_proxy_setting() below.
        
        Written from scratch but inspired by xmlrpc_urllib_transport.py
        file from http://starship.python.net/crew/jjkunce/ by jjk.
        
        A. Ellerton 2006-07-06
    """
    
    def request(self, host, handler, request_body, verbose):
        """ Send an xmlrpc request using an HTTP proxy """
        # We get a traceback if we don't have this attribute:
        self.verbose = verbose
        url = 'https://' + host + handler
        request = urllib2.Request(url)
        try:
            request.add_data(request_body)
        except AttributeError:
            request.data = request_body
        # Note: 'Host' and 'Content-Length' are added automatically
        request.add_header('User-Agent', self.user_agent)
        request.add_header('Content-Type', 'text/xml')
        proxy_handler = urllib2.ProxyHandler()
        opener = urllib2.build_opener(proxy_handler)
        fhandle = opener.open(request)
        return self.parse_response(fhandle)


def check_proxy_setting():
    """ If the environmental variable 'HTTP_PROXY' is set, it will most likely
        be in one of these forms:
        * proxyhost:8080
        * http://proxyhost:8080
        … urlllib2 requires the proxy URL to start with the 'http://'.
        This routine ensures that it does, and returns the transport for xmlrpc.
    """
    try:
        http_proxy = os.environ['HTTP_PROXY']
    except KeyError:
        return
    if not http_proxy.startswith('http://'):
        match = re.match(r'(http://)?([-_\.A-Za-z]+):(\d+)', http_proxy)
        os.environ['HTTP_PROXY'] = 'http://%s:%s' % (match.group(2),
                                                     match.group(3))
    return

def retry_if(*retryable_types):
    """ Return a matcher function for an exception type """
    def exception_is(exc):
        # if get_debug():
        print(" + Intercepted exception: {0}".format(str(exc)), file=sys.stderr)
        return isinstance(exc, tuple(retryable_types))
    return exception_is

class CheeseShop(object):
    
    """ Interface to Python Package Index """
    
    def __init__(self, debug=False, no_cache=False, yolk_dir=None):
        self.debug = debug
        self.no_cache = no_cache
        if yolk_dir:
            self.yolk_dir = yolk_dir
        else:
            self.yolk_dir = get_yolk_dir()
        self.xmlrpc = self.get_xmlrpc_server()
        self.pkg_cache_file = self.get_pkg_cache_file()
        self.pkg_list = None
        self.get_cache()
    
    def get_cache(self):
        """ Get a package name list from disk cache or PyPI """
        # This is used by external programs that import `CheeseShop` and don't
        # want a cache file written to ~/.pypi and query PyPI every time.
        if self.no_cache:
            self.pkg_list = self.list_packages()
            return
        
        if not os.path.exists(self.yolk_dir):
            os.mkdir(self.yolk_dir)
        try:
            self.pkg_list = self.query_cached_package_list()
        except (IOError, ValueError):
            self.fetch_pkg_list(True)
    
    def get_xmlrpc_server(self):
        """ Return PyPI's XML-RPC server instance """
        check_proxy_setting()
        return xmlrpclib.Server(XML_RPC_SERVER, transport=ProxyTransport(),
                                                verbose=get_debug())
    
    def get_pkg_cache_file(self):
        """ Return filename of pkg cache """
        return os.path.abspath('%s/pkg_list.py' % self.yolk_dir)
    
    def query_versions_pypi(self, package_name):
        """ Fetch list of available versions for a package from PyPI """
        normalize_pkg_list = map(normalize, self.pkg_list)
        if normalize(package_name) not in normalize_pkg_list:
            self.fetch_pkg_list()
        # I have to set version=[] for edge cases like "Magic file extensions"
        # but I'm not sure why this happens. It's included with Python or
        # because it has a space in it's name?
        versions = []
        for pypi_pkg in self.pkg_list:
            if normalize(pypi_pkg) == normalize(package_name):
                versions = self.package_releases(pypi_pkg)
                package_name = pypi_pkg
                break
        return (package_name, versions)
    
    def query_cached_package_list(self):
        """ Return list of cached package names from PYPI """
        with open(self.pkg_cache_file, 'r') as input_file:
            return ast.literal_eval(input_file.read())
    
    def fetch_pkg_list(self, ignore_cache=False):
        """ Fetch and cache master list of package names
            from PYPI
        """
        package_list = self.list_packages()
        with open(self.pkg_cache_file, 'w') as output_file:
            print(package_list, file=output_file)
        self.pkg_list = package_list
    
    def search(self, spec, operator):
        """ Query PYPI via XMLRPC interface using search spec """
        return self.xmlrpc.search(spec, operator.lower())
    
    def changelog(self, hours):
        """ Query PYPI via XMLRPC interface using search spec """
        return self.xmlrpc.changelog(get_seconds(hours))
    
    def updated_releases(self, hours):
        """ Query PYPI via XMLRPC interface using search spec """
        return self.xmlrpc.updated_releases(get_seconds(hours))
    
    @retry(stop_max_attempt_number=10,
           retry_on_exception=retry_if(IOError, urllib2.URLError))
    def list_packages(self):
        """ Query PYPI via XMLRPC interface for a a list of
            all package names
        """
        return self.xmlrpc.list_packages()
    
    def release_urls(self, package_name, version):
        """ Query PYPI via XMLRPC interface for a pkg's
            available versions
        """
        return self.xmlrpc.release_urls(package_name, version)
    
    def release_data(self, package_name, version):
        """ Query PYPI via XMLRPC interface for a pkg's metadata """
        try:
            return self.xmlrpc.release_data(package_name, version)
        except xmlrpclib.Fault:
            # XXX Raises xmlrpclib.Fault if you give non-existent version
            # Could this be server bug?
            return
    
    @retry(stop_max_attempt_number=10,
           retry_on_exception=retry_if(IOError, urllib2.URLError))
    def package_releases(self, package_name):
        """ Query PYPI via XMLRPC interface for a pkg's
            available versions
        """
        return self.xmlrpc.package_releases(package_name)


def get_seconds(hours):
    """ Get number of seconds since epoch from now minus `hours`
        @param hours: Number of `hours` back in time we are checking
        @type hours: int
        Return integer for number of seconds for now minus hours
    """
    return int(time.time() - (60 * 60) * hours)


def normalize(name):
    """ Return normalized name """
    return name.lower().replace('_', '-')
