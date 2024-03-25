# Gnome Search Projects Provider

A framework to quickly extend Gnome search for custom providers.

Primary Docs: https://developer.gnome.org/documentation/tutorials/search-provider.html

With help from:

* <https://gitlab.gnome.org/sthursfield/desktop-search/>
* [cnjhb/gnome-command-search-provider](https://github.com/cnjhb/gnome-command-search-provider), thanks for the example!

Full text indexing: <https://github.com/Sygil-Dev/whoosh-reloaded>

## Features

 - Create a search provider by extending a simple Python class
    - Other languages easily supported too by using a subprocess and "structured" output
 - Easy install/uninstall using `make install|uninstall PROJECT_DIR=[PROJECT_DIR]`
 - View logs for a custom search provider using `make logs PROJECT_DIR=[PROJECT_DIR]`
 -
